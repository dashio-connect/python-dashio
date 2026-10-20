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

from __future__ import annotations

import asyncio
import configparser
import logging
import socket
import threading

import shortuuid
import zmq

from .constants import CONNECTION_PUB_URL
from .device import Device

logger = logging.getLogger(__name__)

# The same service and characteristic as the DashIO firmware, so the Dash app finds the device.
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
NAME_PREFIX = "DashIO_"
# BlueZ puts the name in the 31-byte scan response, as a 2-byte header and the name.
MAX_NAME_BYTES = 29
# The longest attribute value BLE allows. BlueZ reads each notification from the notify socket into a 512-byte
# buffer, so a longer one loses its end, though the MTU can be 517.
MAX_NOTIFICATION_BYTES = 512
# How long a phone can write without a notify socket, or be connected without subscribing, before it's
# disconnected, so it subscribes again. The Dash app subscribes within about a second of connecting.
UNSUBSCRIBED_WRITE_TIMEOUT = 1.0
SUBSCRIBE_TIMEOUT = 30.0
# With several phones, BlueZ 5.87 and earlier close the wrong notify socket when a phone leaves (bluez#1452), and a
# recovery disconnect is a phone leaving. So only one phone is recovered at a time, until it subscribes again or
# RECOVERY_TIMEOUT passes, and none until QUIET_PERIOD after a phone subscribes, loses its socket or disconnects.
RECOVERY_TIMEOUT = 10.0
QUIET_PERIOD = 3.0
BLUEZ_MAIN_CONF = "/etc/bluetooth/main.conf"


class BLEError(Exception):
    """BlueZ couldn't do what the BLE connection asked."""


class BlueZBackend:
    """What a BLEConnection needs from BlueZ.

    The default is the dbus-fast backend in dashio.ble_bluez. Tests use a fake one. Every method is a coroutine
    run on the connection's event loop.

    The backend tells the connection about phones by calling, on the same loop:

    - connection._phone_subscribed(phone, notify_socket, mtu) when a phone turns on notifications. phone is the
      BlueZ device object path. Each chunk sent on notify_socket is one notification to that phone.
    - connection._phone_wrote(phone, data) when a phone writes to the characteristic.
    - connection._phone_connected(phone) and connection._phone_disconnected(phone) when BlueZ reports a phone
      connected or disconnected.

    A phone's notify socket closes when it unsubscribes or disconnects, though BlueZ 5.87 and earlier may close
    another phone's instead (bluez#1452).
    """

    async def start(self, connection: BLEConnection, adapter: str | None) -> None:
        """Connect to BlueZ and find the adapter: adapter, e.g. "hci0", or the first that can advertise."""
        raise NotImplementedError

    async def register(self, local_name: str) -> None:
        """Register the GATT application and the advertisement. Raises BLEError."""
        raise NotImplementedError

    async def unregister(self) -> None:
        """Unregister the advertisement and the GATT application."""
        raise NotImplementedError

    async def disconnect(self, phone: str) -> None:
        """Disconnect a phone."""
        raise NotImplementedError

    async def connected_unpaired(self) -> list[str]:
        """The LE devices connected to the adapter that aren't paired."""
        raise NotImplementedError

    async def close(self) -> None:
        """Disconnect from BlueZ."""
        raise NotImplementedError


def advertised_name(device_type: str) -> str:
    """The name the device advertises: DashIO_<device type>, cut short to fit the scan response."""
    name = NAME_PREFIX + device_type
    encoded = name.encode()
    if len(encoded) <= MAX_NAME_BYTES:
        return name
    short_name = encoded[:MAX_NAME_BYTES].decode(errors="ignore")
    logger.warning("BLE: the advertised name %s is too long, it's cut short to %s", name, short_name)
    return short_name


def gatt_client_disabled(path: str = BLUEZ_MAIN_CONF) -> bool:
    """Whether BlueZ's main.conf sets [GATT] Client = false.

    With BlueZ's default, true, bluetoothd reads an iPhone's protected Device Information when it connects, pairing
    fails, and BlueZ disconnects the iPhone two seconds later.
    """
    config = configparser.ConfigParser(strict=False, inline_comment_prefixes=("#",))
    try:
        if not config.read(path):
            return False
    except configparser.Error:
        return False
    return config.get("GATT", "Client", fallback="true").strip().lower() in ("false", "no", "off", "0")


class _Phone:
    """A phone connected over BLE."""

    def __init__(self, path: str, notify_socket: socket.socket, mtu: int):
        self.path = path
        self.client_id = path.rsplit("/", 1)[-1].encode()
        self.notify_socket = notify_socket
        self.mtu = mtu
        self.queue: asyncio.Queue[bytes] = asyncio.Queue()
        self.sender: asyncio.Task | None = None


class BLEConnection(threading.Thread):
    """A connection to the Dash app over Bluetooth Low Energy, as a BlueZ GATT server. Linux only.

    The device appears in the Dash app like a DashIO firmware device: the DashIO service and characteristic,
    advertised as DashIO_<device type>. Each phone gets the replies to its own messages, and control updates go to
    every connected phone.

    Needs `pip install dashio[ble]`, and for iPhones, [GATT] Client = false in /etc/bluetooth/main.conf.
    """

    def __init__(self, adapter: str | None = None, context: zmq.Context | None = None, backend: BlueZBackend | None = None):
        """BLE Connection

        Parameters
        ----------
            adapter : str, optional
                The Bluetooth adapter to use, e.g. "hci0". Defaults to the first adapter that can advertise.
            context : optional
                ZMQ context. Defaults to None.
            backend : BlueZBackend, optional
                Talks to BlueZ. Defaults to the dbus-fast backend.
        """
        threading.Thread.__init__(self, daemon=True)
        self.context = context or zmq.Context.instance()
        self.zmq_connection_uuid = "BLE:" + shortuuid.uuid()
        self.b_zmq_connection_uuid = self.zmq_connection_uuid.encode('utf-8')
        self.local_device_id_list = []
        self.adapter = adapter
        if backend is None:
            from .ble_bluez import DbusFastBackend  # pylint: disable=import-outside-toplevel
            backend = DbusFastBackend()
        self._backend = backend
        self._device: Device | None = None
        self._phones: dict[bytes, _Phone] = {}
        self._rx_buffers: dict[bytes, bytes] = {}
        self._pending_checks: dict[str, asyncio.TimerHandle] = {}
        self._recovering: str | None = None
        self._recovering_until = 0.0
        self._quiet_until = 0.0
        self._loop: asyncio.AbstractEventLoop | None = None
        self._bluez_ready = False
        self._registered = False
        self._loop_ready = threading.Event()
        self._stop_event: asyncio.Event | None = None

        self.tx_zmq_pub = self.context.socket(zmq.PUB)
        self.tx_zmq_pub.bind(CONNECTION_PUB_URL.format(id=self.zmq_connection_uuid))
        self.rx_zmq_sub = self.context.socket(zmq.SUB)
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "ALL")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "BLE")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, self.zmq_connection_uuid)

        self.running = True
        self.start()
        self._loop_ready.wait(5)

    def add_device(self, device: Device):
        """Add the device to the connection. A BLEConnection has one device, as it advertises its device type.

        Parameters
        ----------
        device : dashio.Device
            Add a device to the connection.
        """
        if self._device is device:
            return
        if self._device is not None:
            raise ValueError("A BLEConnection has one device, and already has " + self._device.device_id)
        self._device = device
        self.local_device_id_list.append(device.device_id)
        device.register_connection(self)
        self._call_soon(self._register())

    def close(self):
        """Close the connection: disconnect the phones and unregister from BlueZ."""
        if self._loop is None or not self.is_alive():
            return
        future = asyncio.run_coroutine_threadsafe(self._shutdown(), self._loop)
        try:
            future.result(5)
        except Exception as error:  # pylint: disable=broad-except
            logger.warning("BLE: closing failed: %s", error)
        self.join(5)

    def _call_soon(self, coroutine):
        if self._loop is None or not self.is_alive():
            coroutine.close()
            return
        asyncio.run_coroutine_threadsafe(coroutine, self._loop)

    # These run on the connection's event loop.

    async def _register(self):
        if self._device is None or not self._bluez_ready or self._registered:
            return
        self._registered = True
        try:
            await self._backend.register(advertised_name(self._device.device_type))
            logger.debug("BLE: registered with BlueZ")
        except BLEError as error:
            self._registered = False
            logger.error("BLE: couldn't register with BlueZ: %s", error)

    async def _shutdown(self):
        # Every phone, including one whose notify socket BlueZ closed: a phone left connected keeps its old GATT
        # state, and won't subscribe again to the next run.
        phone_paths = {phone.path for phone in self._phones.values()}
        if self._bluez_ready:
            try:
                phone_paths.update(await self._backend.connected_unpaired())
            except BLEError as error:
                logger.debug("BLE: listing connected phones failed: %s", error)
        # Together, as BlueZ only answers each Disconnect once its two-second disconnect timer has run.
        await asyncio.gather(*(self._disconnect(phone_path) for phone_path in sorted(phone_paths)))
        for phone in list(self._phones.values()):
            self._drop_phone(phone)
        if self._registered:
            try:
                await self._backend.unregister()
            except BLEError as error:
                logger.debug("BLE: unregister failed: %s", error)
            self._registered = False
        await self._backend.close()
        if self._stop_event is not None:
            self._stop_event.set()

    def _phone_changed(self):
        self._quiet_until = self._loop.time() + QUIET_PERIOD

    def _phone_subscribed(self, phone_path: str, notify_socket: socket.socket, mtu: int):
        self._phone_changed()
        check = self._pending_checks.pop(phone_path, None)
        if check is not None:
            check.cancel()
        if self._recovering == phone_path:
            # The recovery worked. Check the phones waiting for it once the quiet period is over.
            self._recovering = None
            for waiting_path in list(self._pending_checks):
                self._schedule_check(waiting_path, QUIET_PERIOD)
        phone = _Phone(phone_path, notify_socket, mtu)
        old = self._phones.get(phone.client_id)
        if old is not None:
            self._drop_phone(old)
        logger.debug("BLE: %s subscribed, MTU %d", phone_path, mtu)
        notify_socket.setblocking(False)
        self._phones[phone.client_id] = phone
        self._loop.add_reader(notify_socket.fileno(), self._notify_socket_readable, phone)
        phone.sender = self._loop.create_task(self._send_to_phone(phone))

    def _phone_wrote(self, phone_path: str, data: bytes):
        client_id = phone_path.rsplit("/", 1)[-1].encode()
        if client_id not in self._phones:
            check = self._pending_checks.get(phone_path)
            if check is None or check.when() > self._loop.time() + UNSUBSCRIBED_WRITE_TIMEOUT:
                self._schedule_check(phone_path, UNSUBSCRIBED_WRITE_TIMEOUT)
        buffer = self._rx_buffers.get(client_id, b"") + data
        *messages, buffer = buffer.split(b"\n")
        self._rx_buffers[client_id] = buffer
        msg_from = self.b_zmq_connection_uuid + b":" + client_id
        for message in messages:
            if message:
                logger.debug("BLE Rx %s ←\n%s", client_id.decode(), message.decode(errors="replace"))
                self.tx_zmq_pub.send_multipart([message, msg_from])

    def _phone_connected(self, phone_path: str):
        """BlueZ reports a phone connected. One that never subscribes is disconnected after SUBSCRIBE_TIMEOUT.

        Android can hold a connection outside the Dash app, e.g. from its Bluetooth settings, and while it does the
        Dash app on that phone can't find the device.
        """
        logger.debug("BLE: %s connected", phone_path)
        if phone_path.rsplit("/", 1)[-1].encode() not in self._phones:
            self._schedule_check(phone_path, SUBSCRIBE_TIMEOUT)

    def _phone_disconnected(self, phone_path: str):
        """BlueZ reports the phone disconnected. Its notify socket may still be open, because of bluez#1452."""
        client_id = phone_path.rsplit("/", 1)[-1].encode()
        logger.debug("BLE: %s disconnected", phone_path)
        check = self._pending_checks.pop(phone_path, None)
        if check is not None:
            check.cancel()
        phone = self._phones.get(client_id)
        if phone is not None:
            self._drop_phone(phone)
        self._rx_buffers.pop(client_id, None)
        self._phone_changed()

    def _schedule_check(self, phone_path: str, delay: float):
        check = self._pending_checks.pop(phone_path, None)
        if check is not None:
            check.cancel()
        self._pending_checks[phone_path] = self._loop.call_later(delay, self._check_subscribed, phone_path)

    def _check_subscribed(self, phone_path: str):
        """A phone wrote without a notify socket, or connected and didn't subscribe, so it gets no replies.

        BlueZ 5.87 and earlier can close another phone's notify socket when a phone disconnects (bluez#1452). That
        phone stays connected, thinks it's still subscribed, and never subscribes again. Disconnect it, so it
        reconnects and subscribes.
        """
        self._pending_checks.pop(phone_path, None)
        if phone_path.rsplit("/", 1)[-1].encode() in self._phones:
            return
        now = self._loop.time()
        if self._recovering is not None and now >= self._recovering_until:
            self._recovering = None
        wait_until = max(self._quiet_until, self._recovering_until if self._recovering else 0.0)
        if wait_until > now:
            self._schedule_check(phone_path, wait_until - now)
            return
        logger.info("BLE: %s has no notifications, disconnecting it so it subscribes again", phone_path)
        self._recovering = phone_path
        self._recovering_until = now + RECOVERY_TIMEOUT
        self._loop.create_task(self._disconnect(phone_path))

    async def _disconnect(self, phone_path: str):
        try:
            await self._backend.disconnect(phone_path)
        except BLEError as error:
            logger.debug("BLE: disconnect %s failed: %s", phone_path, error)

    def _notify_socket_readable(self, phone: _Phone):
        try:
            data = phone.notify_socket.recv(1024)
        except BlockingIOError:
            return
        except OSError:
            data = b""
        if not data:
            logger.debug("BLE: %s notify socket closed", phone.path)
            self._drop_phone(phone)
            self._phone_changed()

    def _drop_phone(self, phone: _Phone):
        if self._phones.get(phone.client_id) is not phone:
            return
        del self._phones[phone.client_id]
        self._rx_buffers.pop(phone.client_id, None)
        self._loop.remove_reader(phone.notify_socket.fileno())
        if phone.sender is not None:
            phone.sender.cancel()
        phone.notify_socket.close()

    def _queue_for_phone(self, phone: _Phone, data: bytes):
        phone.queue.put_nowait(data)

    async def _send_to_phone(self, phone: _Phone):
        """Send a phone its messages, as notifications of MTU - 3 bytes, at most 512."""
        chunk_size = min(max(phone.mtu - 3, 20), MAX_NOTIFICATION_BYTES)
        while True:
            data = await phone.queue.get()
            logger.debug("BLE Tx %s →\n%s", phone.client_id.decode(), data.decode(errors="replace").rstrip())
            for start in range(0, len(data), chunk_size):
                try:
                    await self._loop.sock_sendall(phone.notify_socket, data[start:start + chunk_size])
                except OSError as error:
                    logger.debug("BLE: sending to %s failed: %s", phone.path, error)
                    self._drop_phone(phone)
                    return

    def _zmq_readable(self):
        while self.rx_zmq_sub.getsockopt(zmq.EVENTS) & zmq.POLLIN:
            try:
                [msg_to, data] = self.rx_zmq_sub.recv_multipart(zmq.NOBLOCK)
            except zmq.Again:
                return
            except ValueError:
                continue
            if not data:
                continue
            if msg_to in (b"ALL", b"BLE"):
                for phone in self._phones.values():
                    self._queue_for_phone(phone, data)
            else:
                phone = self._phones.get(msg_to.split(b":")[-1])
                if phone is not None:
                    self._queue_for_phone(phone, data)

    async def _poll_zmq(self):
        # The zmq socket's fd is edge triggered, so check it now and then as well, in case an edge was missed.
        while True:
            await asyncio.sleep(0.5)
            self._zmq_readable()

    async def _main(self):
        self._loop = asyncio.get_running_loop()
        self._stop_event = asyncio.Event()
        self._loop.add_reader(self.rx_zmq_sub.getsockopt(zmq.FD), self._zmq_readable)
        poller = self._loop.create_task(self._poll_zmq())
        self._loop_ready.set()
        try:
            await self._backend.start(self, self.adapter)
        except BLEError as error:
            logger.error("BLE: couldn't connect to BlueZ: %s", error)
        else:
            if not gatt_client_disabled(BLUEZ_MAIN_CONF):
                logger.warning(
                    "BLE: set [GATT] Client = false in %s and restart bluetooth, or iPhones disconnect two seconds after connecting",
                    BLUEZ_MAIN_CONF
                )
            # A phone left connected from an earlier run keeps its old GATT state, and won't subscribe again.
            try:
                for phone_path in await self._backend.connected_unpaired():
                    logger.debug("BLE: disconnecting %s, left connected", phone_path)
                    await self._backend.disconnect(phone_path)
            except BLEError as error:
                logger.warning("BLE: couldn't disconnect phones left connected: %s", error)
            self._bluez_ready = True
            await self._register()
            await self._stop_event.wait()
        poller.cancel()
        self._loop.remove_reader(self.rx_zmq_sub.getsockopt(zmq.FD))

    def run(self):
        try:
            asyncio.run(self._main())
        finally:
            self._loop_ready.set()
            self.running = False
            self.tx_zmq_pub.close()
            self.rx_zmq_sub.close()
