# Connections

A device reaches the Dash app through its connections. Add a device to each connection it should use: a device can have several connections, and a connection several devices. The app uses the most local connection it has to a device: BLE, then TCP, then the Dash server.

| Connection | |
|---|---|
| [DashConnection](#dashconnection) | The Dash server (MQTT): reach the device from anywhere, with notifications, history and shared devices. Needs a Dash account |
| [TCPConnection](#tcpconnection) | Your local network, found by the app with mDNS |
| [BLEConnection](#bleconnection) | Bluetooth LE, on Linux with BlueZ |
| [ZMQConnection](#zmqconnection) | ZMQ, for your own programs |

## DashConnection

```python
dash = dashio.DashConnection("your_dash_username", "your_dash_password")
dash.add_device(device)
```

The Dash server relays messages between the app and the device, wherever they are. It also:

- sends notifications to your phones, from [Alarms](controls.md#alarms);
- keeps time graph, event log and map history ([storage.md](storage.md));
- lets you share devices with other Dash users.

| Parameter | Default | |
|---|---|---|
| `username`, `password` | `""` | Your Dash account. Without them it doesn't connect; set them later with `set_connection()` |
| `host`, `port` | `"dash.dashio.io"`, 8883 | |
| `use_ssl` | True | |
| `context` | The shared `zmq.Context.instance()` | |
| `offline_delay` | 10 | Seconds after the connection is lost before the server says the device is offline ([below](#online-and-offline)) |
| `batch_delay` | 0.05 | Seconds to collect messages for one publish ([below](#what-its-sent)). 0 publishes each straight away |
| `auto_connect` | True | False waits for `connect()` |
| `app_timeout` | 120 | Seconds a device counts as watched after the app's last CONNECT or WHO ([below](#what-its-sent)). 0: always |
| `cert_port` | 8885 | The port for logging in with a [device certificate](#device-certificates) |

| Method | |
|---|---|
| `add_device(device)` | Adds a device |
| `set_connection(username, password)` | Changes the login and connects again, e.g. from `set_dashio_callback()` ([device.md](device.md#provisioning-from-the-dash-app)) |
| `connect()` | Connects, with `auto_connect=False` or after `disconnect()` |
| `disconnect()` | Publishes what the devices have already sent, says OFFLINE for each device and disconnects, until `connect()` |
| `close()` | Says OFFLINE for each device, and closes the connection |
| `app_active(device_id)` | Whether an app is watching the device |

The connection connects from its own thread a moment after it's created, so add the devices straight after creating it. If it can't connect, or the connection drops, it tries again, waiting twice as long after each failed attempt, up to 15 minutes, until it logs in.

### Online and offline

The connection tells the app when its devices go online and offline, so the app reconnects sooner:

- When it connects, it says ONLINE for each device, and for a device added later.
- `close()` and `disconnect()` say OFFLINE for each device.
- If the connection is lost, e.g. the program stops, the server says OFFLINE for the first device after `offline_delay` seconds, unless the connection comes back first. This is the connection's MQTT Last Will. An MQTT connection has a single will, set when it connects, so it only covers the first device.

### What it's sent

- **Control updates only go to the server while an app is watching the device.** The app sends CONNECT through the server about once a minute while it shows the device, so after a CONNECT or WHO the device counts as watched for `app_timeout` seconds. When the app opens, it asks for every control's value, so it's never out of date. This saves data and load on the server, e.g. on LTE.
- Replies to the app, alarms, and time graph, event log and map updates (the server keeps their history) are always sent.
- Messages within `batch_delay` of each other go in one publish, up to 4096 characters, so a device that updates several controls at once makes one publish, not one for each. Alarms go straight away.
- While disconnected with `disconnect()`, or before `connect()` with `auto_connect=False`, the devices' messages are dropped, rather than sent in a burst when it connects. A device with a [DashStore](storage.md) sends the server the history it missed, and the app gets current values from the device. Requests to the server, such as `storage_enable()`, are kept and sent once connected.

### Device certificates

A device can log in to the Dash server with its own certificate, rather than your username and password:

- your password isn't kept on the device;
- you can cut one device off, by revoking its certificate in the Dash app, without changing your password;
- the server knows which device is connected from its certificate.

```python
def certificate_state(state):
    if state == "CERT":
        settings.erase_dash_password()  # The certificate has worked: don't keep the password


certificates = dashio.DeviceCertificates("certs", state_callback=certificate_state)
device = dashio.Device("Greenhouse", "gh-7f3a", "Greenhouse", certificates=certificates)
dash = dashio.DashConnection(username, password)
dash.add_device(device)
```

`DeviceCertificates(path)` keeps the device's key, certificate and state in the directory `path`, readable only by its owner. The private key is made on the device and never leaves it. The device moves through three states:

| State | Logs in with | Moves on when |
|---|---|---|
| `PASSWORD` | Your username and password, on port 8883 | It gets a certificate: `PENDING` |
| `PENDING` | The certificate, on port 8885. If the server refuses it, the password, trying the certificate again an hour later | It logs in with the certificate: `CERT` |
| `CERT` | The certificate only. The password is erased | A new Dash login from the app: `PASSWORD` |

- **Getting a certificate:** logged in with your password, the device asks the Dash server for one, and the server signs it at once for a device on your account. `auto_issue=False` turns this off, leaving the Dash app to provision the certificate.
- **The password is erased** when the device reaches `CERT`: the connection forgets it, and `state_callback` is called so your program can erase its stored copy. A device that kept it would fall back to it when its certificate was revoked.
- **Renewal:** certificates last 5 years. In its last year, the device asks for a new one each time it connects, at most once a day, and uses it once it has logged in with it.
- **Revoking:** a revoked device is refused, and stays in `CERT`, offline, trying again up to once an hour. Setting its Dash login again from the app moves it back to `PASSWORD`, with a new key.
- **One device:** a certificate is one device's login, so a DashConnection with certificates has one device. Give each device its own connection.
- The topics are still under your username, so the connection needs it, but not the password, in `CERT`.
- The server's certificate on port 8885 is checked against the DashIO Server CA, which comes with the library.
- `certificates.state` and `certificates.info()` give the state and the certificate's serial number and expiry. The Dash app can also read them, and provision a certificate, over any connection.

#### Encrypting the key

By default the private key is protected only by its file's permissions: root, or anyone with the device's disk, can read it. `key_passphrase` keeps it encrypted, with a passphrase from somewhere else:

```python
certificates = dashio.DeviceCertificates("certs", key_passphrase=get_passphrase)
```

`key_passphrase` is a string, bytes, or a function returning one, called each time the key is loaded. A trailing newline is ignored. A key already stored unencrypted is encrypted the first time it's loaded with a passphrase. If the passphrase isn't available, the connection logs an error and tries again later, waiting twice as long each time; it doesn't count as the server refusing the certificate. If it's lost, the key can't be used again, and the device needs a new certificate, e.g. by setting its Dash login again from the app.

On Linux, run the device as a systemd service (systemd 250 or later, e.g. Raspberry Pi OS Bookworm) and keep the passphrase as an encrypted systemd credential. Make the passphrase and encrypt it:

```bash
sudo mkdir -p -m 0700 /etc/credstore.encrypted
openssl rand -base64 32 | sudo systemd-creds encrypt --name=dashio-key - /etc/credstore.encrypted/dashio-key
```

Give it to the service, in its unit file:

```ini
[Service]
LoadCredentialEncrypted=dashio-key:/etc/credstore.encrypted/dashio-key
```

systemd decrypts it when the service starts, into a directory only the service can read:

```python
import os


def get_passphrase() -> str:
    with open(os.path.join(os.environ["CREDENTIALS_DIRECTORY"], "dashio-key"), encoding="utf-8") as file:
        return file.read()
```

How much this protects depends on the hardware:

- **With a TPM** (`systemd-creds has-tpm2`), the credential is sealed to the TPM. Copying the disk to another machine gets neither the passphrase nor the key. Add `--with-key=tpm2` to `systemd-creds encrypt` to refuse to make it without one.
- **Without a TPM**, as on a Raspberry Pi, it's sealed with a key in `/var/lib/systemd/credential.secret`, readable only by root. The key file can't be used by other users, or from a copy of the program's directory or a backup of it, but someone with root or the whole disk can still decrypt it. Full disk encryption adds to this.

Either way, revoking the device in the Dash app cuts off a stolen key.

## TCPConnection

```python
tcp = dashio.TCPConnection()
tcp.add_device(device)
```

A connection on your local network. It advertises the device with mDNS (`_DashIO._tcp.`), so the app finds it.

| Parameter | Default | |
|---|---|---|
| `ip_address` | `"*"` | The address to listen on. `"*"` is every address |
| `port` | 5650 | |
| `use_zero_conf` | True | Advertise the device with mDNS, so the app finds it |
| `context` | The shared `zmq.Context.instance()` | |

`add_device(device)` adds a device, and `close()` closes the connection.

An always on TCPConnection beside a DashConnection lets the app provision the device on the local network, as firmware does over BLE. [Examples/intermittent_connection.py](../Examples/intermittent_connection.py) does that.

## BLEConnection

Bluetooth LE, on Linux with BlueZ 5.66 or later, e.g. Raspberry Pi OS. The device appears in the app like a DashIO firmware device, advertised as `DashIO_<device type>`, and the app can use it fully over BLE, including provisioning ([device.md](device.md#provisioning-from-the-dash-app)). Several phones can connect at once: each gets the replies to its own messages, and control updates go to all of them. BLE is experimental.

Install it with the `ble` extra, and import it on its own:

```sh
pip install dashio[ble]
```

```python
from dashio.ble_connection import BLEConnection

device = dashio.Device("PumpController", "pump1", "Pump")
ble = BLEConnection()
ble.add_device(device)
```

| Parameter | Default | |
|---|---|---|
| `adapter` | The first adapter that can advertise | e.g. `"hci0"` |
| `context` | The shared `zmq.Context.instance()` | |

- `add_device(device)` adds the device. A BLEConnection has one device, as it advertises its device type: a second raises `ValueError`.
- `close()` disconnects the phones and unregisters from BlueZ.
- BLE is a local connection, so history requests for controls with `storage_enable()` aren't answered over it ([storage.md](storage.md)).

### Setting up BlueZ for iPhones

BlueZ must not act as a GATT client. Otherwise it reads the iPhone's protected Device Information when it connects, the pairing that starts fails, and BlueZ disconnects the iPhone two seconds later. Set this in `/etc/bluetooth/main.conf`, then `sudo systemctl restart bluetooth`:

```ini
[GATT]
Client = false
```

The BLEConnection logs a warning when it isn't set. The machine then can't use BLE peripherals such as LE keyboards.

### Known issues with several phones

- **BlueZ 5.87 and earlier** close the wrong phone's notifications when a phone disconnects ([bluez#1452](https://github.com/bluez/bluez/issues/1452)), which every current distribution has. The BLEConnection notices a phone that has lost its notifications, or that connected and never subscribed, and disconnects it so that it reconnects. It recovers one phone at a time, so a phone leaving can drop another for a few seconds. One phone on its own isn't affected.
- **Some Linux kernels** (seen on 7.2) disconnect a phone that asks for new connection parameters within about 100 ms of connecting, before the kernel has finished setting the connection up. Android phones often do, so they can take several tries, or a minute or more, to connect.

## ZMQConnection

`ZMQConnection(zmq_out_url="*", pub_port=5555, sub_port=5556)` sends and receives the device's messages over ZMQ publish and subscribe sockets, advertised with mDNS as `_DashZMQ._tcp.`. It's for your own programs, not the Dash app.

## The DashIO comms module

`DashIOCommsModuleConnection` connects through a DashIO comms module on a serial port, which carries BLE, TCP and the Dash server. It's under development.
