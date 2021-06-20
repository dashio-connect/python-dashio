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
import zmq

import signal
import logging
import argparse
import configparser
import threading
import dbus
import dbus.service
import dbus.mainloop.glib
import dbus.exceptions

from gi.repository import GLib


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
        self.ad_type = "peripheral"
        self.local_name = dbus.String(device_type)
        self.service_uuids = []
        self.service_uuids.append(service_uuid)
        self.manufacturer_data = None
        self.include_tx_power = True
        dbus.service.Object.__init__(self, self.bus, self.path)
        self.register()

    def get_properties(self):
        properties = dict()
        properties["Type"] = self.ad_type

        if self.local_name is not None:
            properties["LocalName"] = dbus.String(self.local_name)

        if self.service_uuids is not None:
            properties["ServiceUUIDs"] = dbus.Array(self.service_uuids,
                                                    signature='s')

        if self.include_tx_power is not None:
            properties["IncludeTxPower"] = dbus.Boolean(self.include_tx_power)
        return {LE_ADVERTISEMENT_IFACE: properties}

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

class bleconnection(dbus.service.Object):
    def __init__(self):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.mainloop = GLib.MainLoop()
        self.bus = BleTools.get_bus()
        self.path = "/"
        self.services = []
        self.services.append(DashIOService(0, DASHIO_SERVICE_UUID))
        self.next_index = 0
        dbus.service.Object.__init__(self, self.bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service(self, service):
        self.services.append(service)

    @dbus.service.method(DBUS_OM_IFACE, out_signature="a{oa{sa{sv}}}")
    def GetManagedObjects(self):
        response = {}

        for service in self.services:
            response[service.get_path()] = service.get_properties()
            chrcs = service.get_characteristics()
            for chrc in chrcs:
                response[chrc.get_path()] = chrc.get_properties()
                descs = chrc.get_descriptors()
                for desc in descs:
                    response[desc.get_path()] = desc.get_properties()

        return response

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
        self.mainloop.quit()


class DashIOService(dbus.service.Object):
    PATH_BASE = "/org/bluez/example/service"

    def __init__(self, index, service_uuid):
        self.bus = BleTools.get_bus()
        self.path = self.PATH_BASE + str(index)
        self.uuid = service_uuid
        self.primary = True
        self.characteristics = []
        self.characteristics.append(DashConCharacteristic(self, service_uuid))
        self.next_index = 0
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

    def add_characteristic(self, characteristic):
        self.characteristics.append(characteristic)

    def get_characteristic_paths(self):
        result = []
        for chrc in self.characteristics:
            result.append(chrc.get_path())
        return result

    def get_characteristics(self):
        return self.characteristics

    def get_bus(self):
        return self.bus

    @dbus.service.method(DBUS_PROP_IFACE,
                         in_signature='s',
                         out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != GATT_SERVICE_IFACE:
            raise InvalidArgsException()

        return self.get_properties()[GATT_SERVICE_IFACE]


"""
class DashIOService(Service):
    def __init__(self, index, service_uuid):
        Service.__init__(self, index, service_uuid, True)
        self.add_characteristic(DashConCharacteristic(self, service_uuid))
"""

class DashConCharacteristic(dbus.service.Object):
    """
    org.bluez.GattCharacteristic1 interface implementation
    """
    def __init__(self, service, chacteristic_uuid):
        self.index = 1
        self.path = service.path + '/char' + str(self.index)
        self.bus = service.get_bus()
        self.uuid = chacteristic_uuid
        self.service = service
        self.flags = ["notify", "write-without-response"]
        self.descriptors = []
        self.descriptors.append(DashConDescriptor(self))
        self.next_index = 0
        self.notifying = False
        dbus.service.Object.__init__(self, self.bus, self.path)

    def get_properties(self):
        return {
            GATT_CHRC_IFACE: {
                'Service': self.service.get_path(),
                'UUID': self.uuid,
                'Flags': self.flags,
                'Descriptors': dbus.Array(
                    self.get_descriptor_paths(),
                    signature='o')
            }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_descriptor(self, descriptor):
        self.descriptors.append(descriptor)

    def get_descriptor_paths(self):
        result = []
        for desc in self.descriptors:
            result.append(desc.get_path())
        return result

    def get_descriptors(self):
        return self.descriptors

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

    def dashio_callback(self):
        if self.notifying:
            desc = "HELLO"
            value = []
            for c in desc:
                value.append(dbus.Byte(c.encode()))
            self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
        return self.notifying

    @dbus.service.method(GATT_CHRC_IFACE)
    def StartNotify(self):
        if self.notifying:
            return
        self.notifying = True
        self.dashio_callback()

    @dbus.service.method(GATT_CHRC_IFACE)
    def StopNotify(self):
        self.notifying = False

    @dbus.service.method(GATT_CHRC_IFACE, in_signature='aya{sv}')
    def WriteValue(self, value, options):
        rx_str = ''.join([str(v) for v in value])
        logging.debug("BLE RX: %s", rx_str)


class DashConDescriptor(dbus.service.Object):

    UNIT_DESCRIPTOR_UUID = "2901"
    UNIT_DESCRIPTOR_VALUE = "DashIOCon"

    def __init__(self, characteristic):
        self.notifying = True
        index = 1
        self.path = characteristic.path + '/desc' + str(index)
        self.uuid = self.UNIT_DESCRIPTOR_UUID
        self.flags = ["read"]
        self.chrc = characteristic
        self.bus = characteristic.get_bus()
        dbus.service.Object.__init__(self, self.bus, self.path)

    def get_properties(self):
        return {
            GATT_DESC_IFACE: {
                'Characteristic': self.chrc.get_path(),
                'UUID': self.uuid,
                'Flags': self.flags,
            }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    @dbus.service.method(DBUS_PROP_IFACE,
                         in_signature='s',
                         out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != GATT_DESC_IFACE:
            raise InvalidArgsException()

        return self.get_properties()[GATT_DESC_IFACE]

    # @dbus.service.method(GATT_DESC_IFACE, in_signature='a{sv}', out_signature='ay')
    def ReadValue(self, options):
        value = []
        desc = self.UNIT_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))
        return value
    
    @dbus.service.method(GATT_DESC_IFACE, in_signature='aya{sv}')
    def WriteValue(self, value, options):
        logging.debug('Default WriteValue called, returning error')
        raise NotSupportedException()


def signal_cntrl_c(os_signal, os_frame):
    global SHUTDOWN
    logging.debug("Shutdown")
    SHUTDOWN = True


def init_logging(logfilename, level):
    log_level = logging.WARN
    if level == 1:
        log_level = logging.INFO
    elif level == 2:
        log_level = logging.DEBUG
    if not logfilename:
        formatter = logging.Formatter("%(asctime)s, %(message)s")
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger = logging.getLogger()
        logger.addHandler(handler)
        logger.setLevel(log_level)
    else:
        logging.basicConfig(
            filename=logfilename,
            level=log_level,
            format="%(asctime)s, %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    logging.info("==== Started ====")


def parse_commandline_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v",
        "--verbose",
        const=1,
        default=1,
        type=int,
        nargs="?",
        help="""increase verbosity:
                        0 = only warnings, 1 = info, 2 = debug.
                        No number means info. Default is no verbosity.""",
    )
    parser.add_argument("-u", "--username", help="Dashio Username", dest="username", default="")
    parser.add_argument("-w", "--password", help="DashIO Password", dest="password", default="")
    parser.add_argument("-l", "--logfile", dest="logfilename", default="", help="logfile location", metavar="FILE")
    args = parser.parse_args()
    return args


def main():

    # signal.signal(signal.SIGINT, signal_cntrl_c)
    args = parse_commandline_arguments()
    init_logging(args.logfilename, args.verbose)
    config_file_parser = configparser.ConfigParser()
    config_file_parser.defaults()

    app = bleconnection()
    app.register()

    adv = DashIOAdvertisement(0, "DashIO", DASHIO_SERVICE_UUID)
    # adv.register()

    try:
        app.run()
    except KeyboardInterrupt:
        app.quit()



if __name__ == "__main__":
    main()


"""
import sys
from gi.repository import Clutter, GObject
import zmq

def Stage():
    "A Stage with a red spinning rectangle"
    stage = Clutter.Stage()

    stage.set_size(400, 400)
    rect = Clutter.Rectangle()
    color = Clutter.Color()
    color.from_string('red')
    rect.set_color(color)
    rect.set_size(100, 100)
    rect.set_position(150, 150)

    timeline = Clutter.Timeline.new(3000)
    timeline.set_loop(True)

    alpha = Clutter.Alpha.new_full(timeline, Clutter.AnimationMode.EASE_IN_OUT_SINE)
    rotate_behaviour = Clutter.BehaviourRotate.new(
        alpha, 
        Clutter.RotateAxis.Z_AXIS,
        Clutter.RotateDirection.CW,
        0.0, 359.0)
    rotate_behaviour.apply(rect)
    timeline.start()
    stage.add_actor(rect)

    stage.show_all()
    stage.connect('destroy', lambda stage: Clutter.main_quit())
    return stage, rotate_behaviour

def Socket(address):
    ctx = zmq.Context()
    sock = ctx.socket(zmq.SUB)
    sock.setsockopt(zmq.SUBSCRIBE, "")
    sock.connect(address)
    return sock

def zmq_callback(queue, condition, sock):
    print 'zmq_callback', queue, condition, sock

    while sock.getsockopt(zmq.EVENTS) & zmq.POLLIN:
        observed = sock.recv()
        print observed

    return True

def main():
    res, args = Clutter.init(sys.argv)
    if res != Clutter.InitError.SUCCESS:
        return 1

    stage, rotate_behaviour = Stage()

    sock = Socket(sys.argv[2])
    zmq_fd = sock.getsockopt(zmq.FD)
    GObject.io_add_watch(zmq_fd,
                         GObject.IO_IN|GObject.IO_ERR|GObject.IO_HUP,
                         zmq_callback, sock)

    return Clutter.main()

if __name__ == '__main__':
    sys.exit(main())
"""