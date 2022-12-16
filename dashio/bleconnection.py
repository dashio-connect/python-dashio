"""ble.connection.py

Copyright (c) 2019, Douglas Otwell, DashIO-Connect

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
import json
import logging
import threading
import time
import uuid
import shortuuid

import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service
import zmq
from gi.repository import GLib

from dashio.device import Device

from .constants import CONNECTION_PUB_URL, DEVICE_PUB_URL


class BLEControl():
    """BLE connection control
    """
    def get_state(self) -> str:
        """A CFG only control"""
        return ""

    def get_cfg(self, data) -> str:
        """Called by iotdashboard app to get controls CFG
        """
        try:
            dashboard_id = data[2]
        except IndexError:
            return ""
        cfg_str = f"\tCFG\t{dashboard_id}\t" + self.cntrl_type + "\t" + json.dumps(self._cfg) + "\n"
        return cfg_str

    def get_cfg64(self, data) -> dict:
        """Returns the CFG dict for this TCP control

        Returns
        -------
        dict
            The CFG string for this control
        """
        return self._cfg

    def __init__(self, control_id, service_uuid="", read_uuid="", write_uuid=""):
        self._cfg = {}
        self.cntrl_type = "BLE"
        self._cfg["controlID"] = control_id
        self.control_id = control_id
        self.service_uuid = service_uuid
        self.read_uuid = read_uuid
        self.write_uuid = write_uuid

    @property
    def service_uuid(self) -> str:
        """ServiceUUID"""
        return self._cfg["serviceUUID"]

    @service_uuid.setter
    def service_uuid(self, val: str):
        self._cfg["serviceUUID"] = val

    @property
    def read_uuid(self) -> str:
        """readUUID"""
        return self._cfg["readUUID"]

    @read_uuid.setter
    def read_uuid(self, val: str):
        self._cfg["readUUID"] = val

    @property
    def write_uuid(self) -> str:
        """writeUUID"""
        return self._cfg["writeUUID"]

    @write_uuid.setter
    def write_uuid(self, val: str):
        self._cfg["writeUUID"] = val


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

class DashIOAdvertisement(dbus.service.Object):
    """BLE Advertisement
    """
    PATH_BASE = "/org/bluez/example/advertisement"

    def __init__(self, index, service_uuid):
        self.path = self.PATH_BASE + str(index)
        self.bus = dbus.SystemBus()
        self.service_uuids = []
        self.service_uuids.append(service_uuid)
        self.properties = {}
        self.properties["Type"] = "peripheral"
        self.properties["LocalName"] = dbus.String("DashIO")
        self.properties["ServiceUUIDs"] = dbus.Array(self.service_uuids, signature='s')
        self.properties["IncludeTxPower"] = dbus.Boolean(True)
        dbus.service.Object.__init__(self, self.bus, self.path)
        self.register()

    def find_adapter(self, bus):
        """Find BLE adapters"""
        remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, "/"), DBUS_OM_IFACE)
        objects = remote_om.GetManagedObjects()

        for obj, props in objects.items():
            if LE_ADVERTISING_MANAGER_IFACE in props:
                return obj
        return None

    def get_properties(self):
        """Return the properties dictionary"""
        return {LE_ADVERTISEMENT_IFACE: self.properties}

    def get_path(self):
        """Get the DBUS Path to BLE advertisement"""
        return dbus.ObjectPath(self.path)

    # pylint: disable=invalid-name
    @dbus.service.method(DBUS_PROP_IFACE, in_signature="s", out_signature="a{sv}")
    def GetAll(self, iface):
        """DBUS calls this to retrieve Advertisements"""
        if iface != LE_ADVERTISEMENT_IFACE:
            raise InvalidArgsException()
        return self.get_properties()[LE_ADVERTISEMENT_IFACE]

    # pylint: disable=invalid-name
    @dbus.service.method(LE_ADVERTISEMENT_IFACE, in_signature='', out_signature='')
    def Release(self):
        """DBUS calls this on release"""
        logging.debug('%s: Released!', self.path)

    def register_ad_callback(self):
        """DBUS calls this on release"""
        logging.debug("GATT advertisement registered")

    def register_ad_error_callback(self):
        """DBUS calls this on error"""
        logging.debug("Failed to register GATT advertisement")

    def register(self):
        """Register with DBUS"""
        bus = self.bus
        adapter = self.find_adapter(bus)
        ad_manager = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, adapter), LE_ADVERTISING_MANAGER_IFACE)
        ad_manager.RegisterAdvertisement(self.get_path(), {}, reply_handler=self.register_ad_callback, error_handler=self.register_ad_error_callback)


class InvalidArgsException(dbus.exceptions.DBusException):
    """DBUS errors"""
    _dbus_error_name = "org.freedesktop.DBus.Error.InvalidArgs"

class NotSupportedException(dbus.exceptions.DBusException):
    """DBUS errors"""
    _dbus_error_name = "org.bluez.Error.NotSupported"

class NotPermittedException(dbus.exceptions.DBusException):
    """DBUS errors"""
    _dbus_error_name = "org.bluez.Error.NotPermitted"

class BLEConnection(dbus.service.Object, threading.Thread):
    """BLEConnection
    """

    def add_device(self, device: Device):
        """Add a device to the connection

        Parameters
        ----------
        device : Device
            The device to add
        """
        device._add_connection(self)
        self.rx_zmq_sub.connect(DEVICE_PUB_URL.format(id=device.zmq_connection_uuid))
        # self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, device.zmq_pub_id)

    def close(self):
        """Close the connection
        """
        logging.debug("\nGATT application terminated")
        self.tx_zmq_pub.close()
        self.rx_zmq_sub.close()
        self.mainloop.quit()

    def _zmq_callback(self, queue, condition):
        # logging.debug('zmq_callback')

        while self.rx_zmq_sub.getsockopt(zmq.EVENTS) & zmq.POLLIN:
            try:
                [_, _, data] = self.rx_zmq_sub.recv_multipart()
            except ValueError:
                continue
            if not data:
                continue
            data_str = data.decode('utf-8')
            # TODO: need to set this for the negitiated MTU
            # 160 seems to work with iPhone
            mtu = 160
            data_chunks = [data_str[i: i + mtu] for i in range(0, len(data_str), mtu)]

            sent = False
            for data_chunk in data_chunks:
                sent |= self.dash_service.dash_characteristics.ble_send(data_chunk)
            if sent:
                logging.debug("BLE TX: %s", data_str.strip())

        return True

    def _ble_rx(self, msg: str):
        self.tx_zmq_pub.send_multipart([self.b_connection_id, b'1', msg.encode('utf-8')])

    def __init__(self, ble_uuid=None, context: zmq.Context=None):
        """BLE Connection

        Parameters
        ----------
        ble_uuid : str, optional
            The UUID used by the BLE connection, if None a UUID is generated
        context : ZMQ Context, optional
            ZMQ Context, by default None
        """
        threading.Thread.__init__(self, daemon=True)

        self.zmq_connection_uuid = "BLE:" + shortuuid.uuid()
        self.b_connection_id = self.zmq_connection_uuid.encode('utf-8')

        self.context = context or zmq.Context.instance()
        self.rx_zmq_sub = self.context.socket(zmq.SUB)
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"ALL")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, self.zmq_connection_uuid)
        # TODO: Need to figure out why this doesn't work
        # GLib.io_add_watch(
        #     self.rx_zmq_sub.getsockopt(zmq.FD),
        #     GLib.IO_IN | GLib.IO_ERR | GLib.IO_HUP | GLib.IO_PRI,
        #     self.zmq_callback
        # )
        GLib.timeout_add(10, self._zmq_callback, "q", "p")
        self.tx_zmq_pub = self.context.socket(zmq.PUB)
        self.tx_zmq_pub.bind(CONNECTION_PUB_URL.format(id=self.zmq_connection_uuid))
        dashio_service_uuid = ble_uuid or str(uuid.uuid4())

        # self.connection_control = BLEControl(self.zmq_connection_uuid, dashio_service_uuid, str(uuid.uuid4()), str(uuid.uuid4()))

        GLib.threads_init()
        dbus.mainloop.glib.threads_init()
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.mainloop = GLib.MainLoop()

        self.bus = dbus.SystemBus()
        self.path = "/"
        self.dash_service = DashIOService(0, dashio_service_uuid, self._ble_rx)
        self.response = {}

        chrc = self.dash_service.get_characteristics()
        self.response[chrc.get_path()] = chrc.get_properties()
        self.response[self.dash_service.get_path()] = self.dash_service.get_properties()

        dbus.service.Object.__init__(self, self.bus, self.path)
        self._register()
        self.adv = DashIOAdvertisement(0, dashio_service_uuid)
        self.start()
        time.sleep(0.5)

    def _find_adapter(self, bus):
        remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, "/"), DBUS_OM_IFACE)
        objects = remote_om.GetManagedObjects()

        for obj, props in objects.items():
            if LE_ADVERTISING_MANAGER_IFACE in props:
                return obj
        return None

    def get_path(self):
        """Get DBUS path"""
        return dbus.ObjectPath(self.path)

    # pylint: disable=invalid-name
    @dbus.service.method(DBUS_OM_IFACE, out_signature="a{oa{sa{sv}}}")
    def GetManagedObjects(self):
        """Called by DBUS"""
        return self.response

    def _register_app_callback(self):
        logging.debug("GATT application registered")

    def _register_app_error_callback(self, error):
        logging.debug("Failed to register application: %s", str(error))

    def _register(self):
        adapter = self._find_adapter(self.bus)
        service_manager = dbus.Interface(self.bus.get_object(BLUEZ_SERVICE_NAME, adapter), GATT_MANAGER_IFACE)
        service_manager.RegisterApplication(self._get_path(), {}, reply_handler=self._register_app_callback, error_handler=self._register_app_error_callback)

    def run(self):
        self.mainloop.run()


class DashIOService(dbus.service.Object):
    """DBUS DashIO BLE service
    """
    PATH_BASE = "/org/bluez/example/service"

    def __init__(self, index, service_uuid, ble_rx):
        self.bus = dbus.SystemBus()
        self.path = self.PATH_BASE + str(index)
        self.uuid = service_uuid
        self.primary = True

        self.dash_characteristics = DashConCharacteristic(self, service_uuid, ble_rx)

        dbus.service.Object.__init__(self, self.bus, self.path)

    def get_properties(self):
        """Get DBUS properties"""
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
        """Get DBUS path"""
        return dbus.ObjectPath(self.path)

    def get_characteristic_paths(self):
        """get DBUS properties"""
        result = []
        result.append(self.dash_characteristics.get_path())
        return result

    def get_characteristics(self):
        """Get Dashio charactoristics"""
        return self.dash_characteristics

    def get_bus(self):
        """Return the DBUS bus"""
        return self.bus

    # pylint: disable=invalid-name
    @dbus.service.method(DBUS_PROP_IFACE, in_signature='s', out_signature='a{sv}')
    def GetAll(self, iface):
        """Called by DBUS"""
        if iface != GATT_SERVICE_IFACE:
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
        """Get DBUS properties"""
        return {
            GATT_CHRC_IFACE: {
                'Service': self.service.get_path(),
                'UUID': self.uuid,
                'Flags': self.flags
            }
        }

    def get_path(self):
        """Get DBUS path"""
        return dbus.ObjectPath(self.path)

    # pylint: disable=invalid-name
    @dbus.service.method(DBUS_PROP_IFACE, in_signature='s', out_signature='a{sv}')
    def GetAll(self, iface):
        """Called by DBUS"""
        if iface != GATT_CHRC_IFACE:
            raise InvalidArgsException()
        return self.get_properties()[GATT_CHRC_IFACE]

    # pylint: disable=invalid-name
    @dbus.service.method(GATT_CHRC_IFACE, in_signature='a{sv}', out_signature='ay')
    def ReadValue(self, _):
        """Called by DBUS"""
        logging.debug('Default ReadValue called, returning error')
        raise NotSupportedException()

    # pylint: disable=invalid-name, unnecessary-pass
    @dbus.service.signal(DBUS_PROP_IFACE, signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed, invalidated):
        """Called by DBUS"""
        pass

    def get_bus(self):
        """Return DBUS bus"""
        bus = self.bus
        return bus

    def ble_send(self, tx_data):
        """Send data to BLE connection"""
        if self.notifying:
            value = [dbus.Byte(c.encode()) for c in tx_data]
            self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
        return self.notifying

    # pylint: disable=invalid-name
    @dbus.service.method(GATT_CHRC_IFACE)
    def StartNotify(self):
        """Called by DBUS"""
        if self.notifying:
            return
        self.notifying = True

    # pylint: disable=invalid-name
    @dbus.service.method(GATT_CHRC_IFACE)
    def StopNotify(self):
        """Called by DBUS"""
        self.notifying = False

    # pylint: disable=invalid-name
    @dbus.service.method(GATT_CHRC_IFACE, in_signature='aya{sv}')
    def WriteValue(self, value, options):
        """Called by DBUS"""
        rx_str = ''.join([str(v) for v in value])
        self.read_buffer += rx_str
        if rx_str[-1] == '\n':
            logging.debug("BLE RX: %s", self.read_buffer.strip())
            self._ble_rx(self.read_buffer)
            self.read_buffer = ''
