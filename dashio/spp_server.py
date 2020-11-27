import os
import dbus
import dbus.service
import dbus.mainloop.glib

try:
    from gi.repository import GObject
except ImportError:
    import gobject as GObject

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

bus = dbus.SystemBus()


class Profile(dbus.service.Object):
    fd = -1

    def __init__(self, bus, path, read_cb):
        self.read_io_cb = read_cb
        dbus.service.Object.__init__(self, bus, path)

    @dbus.service.method("org.bluez.Profile1", in_signature="", out_signature="")
    def Release(self):
        print("Release")
        mainloop.quit()

    @dbus.service.method("org.bluez.Profile1", in_signature="oha{sv}", out_signature="")
    def NewConnection(self, path, fd, properties):
        self.fd = fd.take()
        print("NewConnection(%s, %d)" % (path, self.fd))
        io_id = GObject.io_add_watch(self.fd, GObject.PRIORITY_DEFAULT, GObject.IO_IN | GObject.IO_PRI, self.io_cb)

    @dbus.service.method("org.bluez.Profile1", in_signature="o", out_signature="")
    def RequestDisconnection(self, path):
        print("RequestDisconnection(%s)" % (path))

        if self.fd > 0:
            os.close(self.fd)
            self.fd = -1

    def io_cb(self, fd, conditions):
        data = os.read(fd, 1024)
        self.read_io_cb("{0}".format(data.decode("ascii")))
        return True

    def write_io(self, value):
        try:
            os.write(self.fd, value.encode("utf8"))
        except ConnectionResetError:
            self.fd = -1


class SPP:
    def __init__(self, read_cb):
        self.profile = None
        manager = dbus.Interface(bus.get_object("org.bluez", "/org/bluez"), "org.bluez.ProfileManager1")

        self.mainloop = GObject.MainLoop()
        adapter_props = dbus.Interface(
            bus.get_object("org.bluez", "/org/bluez/hci0"), "org.freedesktop.DBus.Properties"
        )

        adapter_props.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(1))
        profile_path = "/foo/bar/profile"
        server_uuid = "00001101-0000-1000-8000-00805f9b34fb"
        opts = {"AutoConnect": True, "Role": "server", "Channel": dbus.UInt16(1), "Name": "SerialPort"}

        print("Starting Serial Port Profile...")

        if read_cb is None:
            self.profile = Profile(bus, profile_path, self.read_cb)
        else:
            self.profile = Profile(bus, profile_path, read_cb)

        manager.RegisterProfile(profile_path, server_uuid, opts)

    def read_cb(self, value):
        print(value)

    def write_spp(self, value):
        self.profile.write_io(value)

    def fd_available(self):
        if self.profile.fd > 0:
            return True
        else:
            return False

    def start(self):
        self.mainloop.run()

