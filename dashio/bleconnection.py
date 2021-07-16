"""Copyright (c) 2019, Douglas Otwell

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import logging
import threading
import time

import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service

import shortuuid
import uuid
import zmq
from gi.repository import GLib

from dashio.dashdevice import DashDevice

from .constants import CONNECTION_PUB_URL, DEVICE_PUB_URL

GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
NOTIFY_TIMEOUT = 10
BLUEZ_SERVICE_NAME = "org.bluez"
LE_ADVERTISING_MANAGER_IFACE = "org.bluez.LEAdvertisingManager1"
DBUS_OM_IFACE = "org.freedesktop.DBus.ObjectManager"
DBUS_PROP_IFACE = "org.freedesktop.DBus.Properties"
LE_ADVERTISEMENT_IFACE = "org.bluez.LEAdvertisement1"
GATT_MANAGER_IFACE = "org.bluez.GattManager1"
GATT_SERVICE_IFACE = "org.bluez.GattService1"
GATT_DESC_IFACE = "org.bluez.GattDescriptor1"
DASHIO_SERVICE_UUID = "4FAFC201-1FB5-459E-8FCC-C5C9C331914B"

class BleTools(object):
    @classmethod
    def get_bus(self):
        bus = dbus.SystemBus()
        return bus

    @classmethod
    def find_adapter(self, bus):
        remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, "/"), DBUS_OM_IFACE)
        objects = remote_om.GetManagedObjects()

        for o, props in objects.items():
            if LE_ADVERTISING_MANAGER_IFACE in props:
                return o
        return None

    @classmethod
    def power_adapter(self):
        adapter = self.get_adapter()
        adapter_props = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, adapter), "org.freedesktop.DBus.Properties")
        adapter_props.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(1))

class DashIOAdvertisement(dbus.service.Object):
    PATH_BASE = "/org/bluez/example/advertisement"

    def __init__(self, index, device_type, service_uuid):
        self.path = self.PATH_BASE + str(index)
        self.bus = BleTools.get_bus()
        self.service_uuids = []
        self.service_uuids.append(service_uuid)
        self.properties = {}
        self.properties["Type"] = "peripheral"
        self.properties["LocalName"] = dbus.String(device_type)
        self.properties["ServiceUUIDs"] = dbus.Array(self.service_uuids, signature='s')
        self.properties["IncludeTxPower"] = dbus.Boolean(True)
        dbus.service.Object.__init__(self, self.bus, self.path)
        self.register()

    def get_properties(self):
        return {LE_ADVERTISEMENT_IFACE: self.properties}

    def get_path(self):
        return dbus.ObjectPath(self.path)

    @dbus.service.method(DBUS_PROP_IFACE, in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface):
        if interface != LE_ADVERTISEMENT_IFACE:
            raise InvalidArgsException()
        return self.get_properties()[LE_ADVERTISEMENT_IFACE]

    @dbus.service.method(LE_ADVERTISEMENT_IFACE, in_signature='', out_signature='')
    def Release(self):
        logging.debug('%s: Released!', self.path)

    def register_ad_callback(self):
        logging.debug("GATT advertisement registered")

    def register_ad_error_callback(self):
        logging.debug("Failed to register GATT advertisement")

    def register(self):
        bus = BleTools.get_bus()
        adapter = BleTools.find_adapter(bus)
        ad_manager = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, adapter), LE_ADVERTISING_MANAGER_IFACE)
        ad_manager.RegisterAdvertisement(self.get_path(), {}, reply_handler=self.register_ad_callback, error_handler=self.register_ad_error_callback)


class InvalidArgsException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.freedesktop.DBus.Error.InvalidArgs"

class NotSupportedException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.bluez.Error.NotSupported"

class NotPermittedException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.bluez.Error.NotPermitted"

class BLEConnection(dbus.service.Object, threading.Thread):

    def add_device(self, device: DashDevice):
        device.add_connection(self)
        self.rx_zmq_sub.connect(DEVICE_PUB_URL.format(id=device.zmq_pub_id))
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, device.zmq_pub_id)

    def close(self):
        self.quit()

    def zmq_callback(self, queue, condition):
        #logging.debug('zmq_callback')

        while self.rx_zmq_sub.getsockopt(zmq.EVENTS) & zmq.POLLIN:
            try:
                [address, msg_id, data] = self.rx_zmq_sub.recv_multipart()
            except ValueError:
                continue
            if not data:
                continue
            data_str = data.decode('utf-8')
            # TODO: need to set this for the negitiated MTU
            # 160 seems to work with iPhone
            mtu = 160
            date_lines = [data_str[i:i+mtu] for i in range(0, len(data_str), mtu)]
            # delimiter = '\n'
            # date_lines =  [e+delimiter for e in data_str.split(delimiter) if e]
            # date_lines = data.decode('utf-8').split("\n")
            logging.debug("BLE TX: %s", data_str.strip())
            for data_line in date_lines:
                self.dash_service.dash_characteristics.ble_send(data_line)
        return True

        
    def ble_rx(self, msg: str):
        self.tx_zmq_pub.send_multipart([self.b_connection_id, b'1', msg.encode('utf-8')])

    def __init__(self, context=None):
        threading.Thread.__init__(self, daemon=True)

        self.connection_id = shortuuid.uuid()
        self.b_connection_id = self.connection_id.encode('utf-8')

        self.context = context or zmq.Context.instance()

        self.rx_zmq_sub = self.context.socket(zmq.SUB)
        # TODO: Need to figure out why this doesn't work
        #GLib.io_add_watch(
        #    self.rx_zmq_sub.getsockopt(zmq.FD),
        #    GLib.IO_IN | GLib.IO_ERR | GLib.IO_HUP | GLib.IO_PRI,
        #    self.zmq_callback
        #)
        GLib.timeout_add(10, self.zmq_callback, "q", "p")
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"ALL")
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"ALARM")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, self.connection_id)
        
        self.tx_zmq_pub = self.context.socket(zmq.PUB)
        self.tx_zmq_pub.bind(CONNECTION_PUB_URL.format(id=self.connection_id))
        
        GLib.threads_init()
        dbus.mainloop.glib.threads_init()
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.mainloop = GLib.MainLoop()
        #GLib.MainLoop.threads_init()
         
        self.bus = BleTools.get_bus()
        self.path = "/"
        self.dash_service = DashIOService(0, DASHIO_SERVICE_UUID, self.ble_rx)
        self.response = {}

        chrc = self.dash_service.get_characteristics()
        self.response[chrc.get_path()] = chrc.get_properties()
        self.response[self.dash_service.get_path()] = self.dash_service.get_properties()

        dbus.service.Object.__init__(self, self.bus, self.path)
        self.register()
        self.adv = DashIOAdvertisement(0, "DashIO", DASHIO_SERVICE_UUID)
        self.start()
        time.sleep(0.5)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    @dbus.service.method(DBUS_OM_IFACE, out_signature="a{oa{sa{sv}}}")
    def GetManagedObjects(self):
        return self.response

    def register_app_callback(self):
        logging.debug("GATT application registered")

    def register_app_error_callback(self, error):
        logging.debug("Failed to register application: %s", str(error))

    def register(self):
        adapter = BleTools.find_adapter(self.bus)
        service_manager = dbus.Interface(self.bus.get_object(BLUEZ_SERVICE_NAME, adapter), GATT_MANAGER_IFACE)
        service_manager.RegisterApplication(self.get_path(), {}, reply_handler=self.register_app_callback, error_handler=self.register_app_error_callback)

    def run(self):
        self.mainloop.run()

    def quit(self):
        logging.debug("\nGATT application terminated")
        self.tx_zmq_pub.close()
        self.rx_zmq_sub.close()
        self.mainloop.quit()


class DashIOService(dbus.service.Object):
    PATH_BASE = "/org/bluez/example/service"

    def __init__(self, index, service_uuid, ble_rx):
        self.bus = BleTools.get_bus()
        self.path = self.PATH_BASE + str(index)
        self.uuid = service_uuid
        self.primary = True

        self.dash_characteristics = DashConCharacteristic(self, service_uuid, ble_rx)

        dbus.service.Object.__init__(self, self.bus, self.path)

    def get_properties(self):
        return {
            GATT_SERVICE_IFACE: {
                'UUID': self.uuid,
                'Primary': self.primary,
                'Characteristics': dbus.Array(
                    self.get_characteristic_paths(),
                    signature='o')
            }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def get_characteristic_paths(self):
        result = []
        result.append(self.dash_characteristics.get_path())
        return result

    def get_characteristics(self):
        return self.dash_characteristics

    def get_bus(self):
        return self.bus

    @dbus.service.method(DBUS_PROP_IFACE, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != GATT_SERVICE_IFACE:
            raise InvalidArgsException()
        return self.get_properties()[GATT_SERVICE_IFACE]

class DashConCharacteristic(dbus.service.Object):
    """
    org.bluez.GattCharacteristic1 interface implementation
    """
    def __init__(self, service, chacteristic_uuid, ble_rx):
        
        self.path = service.path + '/char' + str(1)
        self.bus = service.get_bus()
        self.uuid = chacteristic_uuid
        self.service = service
        self.flags = ["notify", "write-without-response"]
        self.notifying = False
        self._ble_rx = ble_rx
        self.read_buffer = ""
        dbus.service.Object.__init__(self, self.bus, self.path)

    def get_properties(self):
        return {
            GATT_CHRC_IFACE: {
                'Service': self.service.get_path(),
                'UUID': self.uuid,
                'Flags': self.flags
            }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    @dbus.service.method(DBUS_PROP_IFACE, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != GATT_CHRC_IFACE:
            raise InvalidArgsException()
        return self.get_properties()[GATT_CHRC_IFACE]

    @dbus.service.method(GATT_CHRC_IFACE, in_signature='a{sv}', out_signature='ay')
    def ReadValue(self, options):
        logging.debug('Default ReadValue called, returning error')
        raise NotSupportedException()

    @dbus.service.signal(DBUS_PROP_IFACE, signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed, invalidated):
        pass

    def get_bus(self):
        bus = self.bus
        return bus

    def ble_send(self, tx_data):
        if self.notifying:
            value = [dbus.Byte(c.encode()) for c in tx_data]
            self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
        return self.notifying

    @dbus.service.method(GATT_CHRC_IFACE)
    def StartNotify(self):
        if self.notifying:
            return
        self.notifying = True

    @dbus.service.method(GATT_CHRC_IFACE)
    def StopNotify(self):
        self.notifying = False

    @dbus.service.method(GATT_CHRC_IFACE, in_signature='aya{sv}')
    def WriteValue(self, value, options):
        rx_str = ''.join([str(v) for v in value])
        self.read_buffer += rx_str
        if rx_str[-1] == '\n':
            logging.debug("BLE RX: %s", self.read_buffer.strip())
            self._ble_rx(self.read_buffer)
            self.read_buffer = ''

