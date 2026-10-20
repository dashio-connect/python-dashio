"""
MIT License

Copyright (c) 2020 DashIO-Connect

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
# The BLE connection's BlueZ backend, on dbus-fast. See docs/adr/0001-ble-dbus-fast-acquire-notify.md.
# A dbus-fast ServiceInterface keeps its D-Bus interface name in self.name, so these classes never set it.

from __future__ import annotations

import logging
import os
import socket
from typing import Annotated

import shortuuid
from dbus_fast import BusType, Message, MessageType, Variant
from dbus_fast.aio import MessageBus
from dbus_fast.annotations import DBusBool, DBusBytes, DBusDict, DBusObjectPath, DBusSignature, DBusStr
from dbus_fast.service import PropertyAccess, ServiceInterface, dbus_method, dbus_property

from .ble_connection import CHARACTERISTIC_UUID, SERVICE_UUID, BLEConnection, BLEError, BlueZBackend

logger = logging.getLogger(__name__)

BLUEZ = "org.bluez"
DBusStrList = Annotated[list[str], DBusSignature("as")]
DBusFdMtu = Annotated[list, DBusSignature("hq")]


class _Service(ServiceInterface):
    def __init__(self):
        super().__init__("org.bluez.GattService1")

    @dbus_property(access=PropertyAccess.READ)
    def UUID(self) -> DBusStr:  # pylint: disable=invalid-name
        return SERVICE_UUID

    @dbus_property(access=PropertyAccess.READ)
    def Primary(self) -> DBusBool:  # pylint: disable=invalid-name
        return True


class _Characteristic(ServiceInterface):
    """The DashIO characteristic: phones write to it, and get notifications through an AcquireNotify socket each."""

    def __init__(self, backend: DbusFastBackend, service_path: str):
        super().__init__("org.bluez.GattCharacteristic1")
        self._backend = backend
        self._service_path = service_path

    @dbus_property(access=PropertyAccess.READ)
    def UUID(self) -> DBusStr:  # pylint: disable=invalid-name
        return CHARACTERISTIC_UUID

    @dbus_property(access=PropertyAccess.READ)
    def Service(self) -> DBusObjectPath:  # pylint: disable=invalid-name
        return self._service_path

    @dbus_property(access=PropertyAccess.READ)
    def Flags(self) -> DBusStrList:  # pylint: disable=invalid-name
        return ["notify", "write-without-response"]

    @dbus_property(access=PropertyAccess.READ)
    def NotifyAcquired(self) -> DBusBool:  # pylint: disable=invalid-name
        # Its presence tells BlueZ that AcquireNotify is supported.
        return False

    @dbus_method()
    def WriteValue(self, value: DBusBytes, options: DBusDict):  # pylint: disable=invalid-name
        device = options.get("device")
        if device is not None:
            self._backend.phone_wrote(device.value, bytes(value))

    @dbus_method()
    def AcquireNotify(self, options: DBusDict) -> DBusFdMtu:  # pylint: disable=invalid-name
        return list(self._backend.phone_subscribed(options["device"].value, options["mtu"].value))

    @dbus_method()
    def StartNotify(self):  # pylint: disable=invalid-name
        pass

    @dbus_method()
    def StopNotify(self):  # pylint: disable=invalid-name
        pass


class _Advertisement(ServiceInterface):
    """The advertisement. BlueZ puts the service UUID in the advertising data, and the name in the scan response."""

    def __init__(self):
        super().__init__("org.bluez.LEAdvertisement1")
        self.local_name = ""

    @dbus_property(access=PropertyAccess.READ)
    def Type(self) -> DBusStr:  # pylint: disable=invalid-name
        return "peripheral"

    @dbus_property(access=PropertyAccess.READ)
    def LocalName(self) -> DBusStr:  # pylint: disable=invalid-name
        return self.local_name

    @dbus_property(access=PropertyAccess.READ)
    def ServiceUUIDs(self) -> DBusStrList:  # pylint: disable=invalid-name
        return [SERVICE_UUID]

    @dbus_property(access=PropertyAccess.READ)
    def Discoverable(self) -> DBusBool:  # pylint: disable=invalid-name
        return True

    @dbus_method()
    def Release(self):  # pylint: disable=invalid-name
        logger.debug("BLE: BlueZ released the advertisement")


class DbusFastBackend(BlueZBackend):
    """Talks to BlueZ over the system D-Bus with dbus-fast."""

    def __init__(self):
        self._bus: MessageBus | None = None
        self._connection: BLEConnection | None = None
        self._adapter_path = ""
        self._app_path = "/io/dashio/ble" + shortuuid.uuid()
        self._service_path = self._app_path + "/service0"
        self._characteristic_path = self._service_path + "/char0"
        self._advertisement_path = self._app_path + "/advertisement0"
        self._advertisement = _Advertisement()

    async def _call(self, path: str, interface: str, member: str, signature: str = "", body: list | None = None):
        reply = await self._bus.call(Message(
            destination=BLUEZ, path=path, interface=interface, member=member, signature=signature, body=body or []
        ))
        if reply.message_type == MessageType.ERROR:
            raise BLEError(f"{interface}.{member}: {reply.error_name} {reply.body}")
        return reply.body

    async def start(self, connection, adapter):
        self._connection = connection
        try:
            self._bus = await MessageBus(bus_type=BusType.SYSTEM, negotiate_unix_fd=True).connect()
            [objects] = await self._call("/", "org.freedesktop.DBus.ObjectManager", "GetManagedObjects")
        except (OSError, BLEError) as error:
            raise BLEError(f"BlueZ isn't available: {error}") from error
        for path, interfaces in sorted(objects.items()):
            if "org.bluez.LEAdvertisingManager1" in interfaces and "org.bluez.GattManager1" in interfaces:
                if adapter is None or path.rsplit("/", 1)[-1] == adapter:
                    self._adapter_path = path
                    break
        else:
            raise BLEError(f"no Bluetooth adapter that can advertise{'' if adapter is None else ' called ' + adapter}")
        for rule in (
            f"type='signal',sender='{BLUEZ}',interface='org.freedesktop.DBus.Properties',member='PropertiesChanged',arg0='org.bluez.Device1'",
            f"type='signal',sender='{BLUEZ}',interface='org.freedesktop.DBus.ObjectManager',member='InterfacesRemoved'",
            f"type='signal',sender='{BLUEZ}',interface='org.freedesktop.DBus.ObjectManager',member='InterfacesAdded'",
        ):
            await self._bus.call(Message(
                destination="org.freedesktop.DBus", path="/org/freedesktop/DBus", interface="org.freedesktop.DBus",
                member="AddMatch", signature="s", body=[rule]
            ))
        self._bus.add_message_handler(self._on_signal)
        self._bus.export(self._service_path, _Service())
        self._bus.export(self._characteristic_path, _Characteristic(self, self._service_path))
        self._bus.export(self._advertisement_path, self._advertisement)
        logger.debug("BLE: using adapter %s", self._adapter_path)

    async def register(self, local_name):
        self._advertisement.local_name = local_name
        await self._call(self._adapter_path, "org.bluez.GattManager1", "RegisterApplication", "oa{sv}", [self._app_path, {}])
        await self._call(self._adapter_path, "org.bluez.LEAdvertisingManager1", "RegisterAdvertisement", "oa{sv}", [self._advertisement_path, {}])

    async def unregister(self):
        errors = []
        for interface, member, path in (
            ("org.bluez.LEAdvertisingManager1", "UnregisterAdvertisement", self._advertisement_path),
            ("org.bluez.GattManager1", "UnregisterApplication", self._app_path),
        ):
            try:
                await self._call(self._adapter_path, interface, member, "o", [path])
            except BLEError as error:
                errors.append(str(error))
        if errors:
            raise BLEError(", ".join(errors))

    async def disconnect(self, phone):
        await self._call(phone, "org.bluez.Device1", "Disconnect")

    async def connected_unpaired(self):
        [objects] = await self._call("/", "org.freedesktop.DBus.ObjectManager", "GetManagedObjects")
        phones = []
        for path, interfaces in objects.items():
            device = interfaces.get("org.bluez.Device1")
            if device is None or not path.startswith(self._adapter_path + "/"):
                continue
            if _value(device.get("Connected")) and not _value(device.get("Paired")):
                phones.append(path)
        return phones

    async def close(self):
        if self._bus is not None:
            self._bus.disconnect()
            self._bus = None

    def _on_signal(self, message: Message):
        """Tell the connection when a phone on the adapter connects or disconnects."""
        if message.message_type != MessageType.SIGNAL:
            return
        if message.member == "PropertiesChanged" and message.body and message.body[0] == "org.bluez.Device1":
            connected = message.body[1].get("Connected")
            if connected is not None and message.path.startswith(self._adapter_path + "/"):
                self._phone_connection_changed(message.path, connected.value)
        elif message.member == "InterfacesAdded" and len(message.body) == 2 and "org.bluez.Device1" in message.body[1]:
            connected = message.body[1]["org.bluez.Device1"].get("Connected")
            if connected is not None and connected.value and message.body[0].startswith(self._adapter_path + "/"):
                self._phone_connection_changed(message.body[0], True)
        elif message.member == "InterfacesRemoved" and len(message.body) == 2 and "org.bluez.Device1" in message.body[1]:
            if message.body[0].startswith(self._adapter_path + "/"):
                self._phone_connection_changed(message.body[0], False)

    def _phone_connection_changed(self, phone: str, connected: bool):
        if connected:
            self._connection._phone_connected(phone)
        else:
            self._connection._phone_disconnected(phone)

    def phone_subscribed(self, phone: str, mtu: int) -> tuple[int, int]:
        """AcquireNotify: give the connection one end of a socket pair, and BlueZ the other."""
        ours, theirs = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        self._connection._phone_subscribed(phone, ours, mtu)
        fd = theirs.detach()
        # dbus-fast sends the fd after this returns, and doesn't close it. Close our copy once it's sent, or the
        # connection never sees BlueZ close its end.
        self._connection._loop.call_later(1, os.close, fd)
        return fd, mtu

    def phone_wrote(self, phone: str, data: bytes):
        self._connection._phone_wrote(phone, data)


def _value(variant):
    return variant.value if isinstance(variant, Variant) else variant
