# Storing history

A time graph in the Dash app shows the history of its lines, not only the points sent while the app was open. The app asks for the history it's missing, from the device or from the Dash server. The same goes for event logs and maps.

There are three places to keep it:

| | Where the history is kept | |
|---|---|---|
| In memory | Each control's ring buffer | The default. Short, and lost when the program stops |
| [On the Dash server](#on-the-dash-server) | The Dash server, from the values the device sends while connected | `storage_enable()`. Gaps while the device is offline |
| [On the device and the Dash server](#with-a-dashstore) | An sqlite database, uploaded to the Dash server | A `DashStore`. No gaps, even when the device was offline |

## In memory

Without a store, each TimeGraphLine keeps its last `max_data_points` points (60 by default), each EventLog its last `max_log_entries` entries (100), and each Map its tracks. The app's history requests are answered from them, over any connection.

## On the Dash server

The Dash server can keep a control's history from the values the device sends while it's connected. Ask it to, once at startup:

```python
device.storage_enable(dashio.ControlName.TGRPH, "tg1")
device.storage_enable(dashio.ControlName.LOG, "log1")
device.storage_enable(dashio.ControlName.MAP, "map1")
```

- It needs a [DashConnection](connections.md#dashconnection). The server remembers the setting.
- The server is then the app's **source of truth** for the control's history, so the device only answers history requests for it from the server, never over TCP or BLE. Otherwise an app connected locally would take the device's short history as complete, and not ask the server for the rest.
- There are gaps in the history while the device is offline. A DashStore fills them.
- `dashio_data_exporter` exports what the server keeps ([data-exporter.md](data-exporter.md)).

## With a DashStore

A `DashStore` keeps the time graph, event log and map history in an sqlite database, so it isn't lost when the program stops, and uploads it to the Dash server:

```python
store = dashio.DashStore("greenhouse.db", max_entries=100000, max_days=31)
device = dashio.Device("Greenhouse", device_id, "Greenhouse", store=store)
device.storage_enable(dashio.ControlName.TGRPH, "tg1")  # So the server keeps what's uploaded
```

- Every point added to a TimeGraphLine, event added to an EventLog and location added to a Map is stored.
- The app's history requests are answered from the store, including what was stored before the program restarted.
- Each time the device connects to the Dash server, it sends the server what it's missing, e.g. what was stored while the connection was down. **The server only keeps it for controls with `storage_enable()`**, so call that for each stored control.

| DashStore parameter | Default | |
|---|---|---|
| `path` | `":memory:"` | The sqlite database file. `":memory:"` isn't kept after the program stops |
| `max_entries` | 100000 | The most entries kept. The oldest make way for new ones |
| `max_days` | 31 | Entries older than this many days are deleted. None keeps them, up to `max_entries` |

Once uploaded, the history is kept by the Dash server, so the store only needs to cover the time the device might be offline.

| DashStore method | |
|---|---|
| `entries(control_type, control_id, sub_id="", after=0)` | A line's, track's or log's entries (`"TGRPH"`, `"MAP"` or `"LOG"`) later than `after`, a datetime or seconds since the epoch. `sub_id` is the line or track ID, `""` for a log |
| `delete(control_type, control_id, sub_id="")` | Deletes a line's, track's or log's entries, here and on the Dash server. The controls' `delete_history()` call it ([below](#starting-a-line-again)) |
| `clear()` | Deletes every entry, without telling the Dash server |
| `close()` | Closes the database |

### How the upload works

1. When the device connects to the Dash server, it lists the lines, tracks and logs it stores.
2. The server replies with the newest point it has of each.
3. The device sends the newer points, in packets of up to 4096 bytes, each acknowledged by the server before the next. A line's or track's name and colour go with its first points when the server doesn't have them.
4. The app gets the history from the server.

If a packet isn't acknowledged within 10 seconds, the device sends it again once, then gives up until it next connects. This is the DashIO Store Data Update (SDU) protocol, as in the DashIO firmware.

### Starting a line again

```python
def reset(msg):
    if len(msg) > 2 and msg[2] == "FRST":
        temperature_graph.delete_history()   # Every line, or delete_history("temp") for one
        events.delete_history()
        fleet.delete_history()               # Every track, or delete_history("trip") for one


device.set_reset_callback(reset)
```

`delete_history()` on a TimeGraph, EventLog or Map deletes a line's, log's or track's history on the device straight away, and on the Dash server at the next upload. Use it when the old history no longer belongs with the new, e.g. after a factory reset, or when a line is reused for another sensor. A line's or track's name and colour stay on the server.

The deletes are kept in the store until the server has them, so they survive a restart or a failed upload. Without a store, `delete_history()` only clears the controls' ring buffers.

### A track of the latest position

A Map track made with `MapTrack(track_id, name, color, replace=True)` and added with `map.add_track()` is a "where it is now" marker: the Dash server keeps only its latest location, rather than a track log. See [controls.md](controls.md#maps).

## A connection that's only on now and then

A device on LTE or a battery may connect to the Dash server only now and then, store values meanwhile, and disconnect once the server has them:

```python
connection = dashio.DashConnection(username, password, auto_connect=False)
connection.add_device(device)
device.set_store_sync_callback(lambda completed: connection.disconnect())
...
connection.connect()  # e.g. every 15 minutes
```

- `set_store_sync_callback(callback)` is called on the device thread when each connection's upload ends: True when the server has everything, or there was nothing to send, and False when it failed, e.g. the server didn't answer within 30 seconds. So waiting for it never waits for ever. On a failure the values stay stored, and the next connection uploads them.
- Give the connection a time limit of your own too, from your own thread, for when it never connects.
- While disconnected, live control updates are dropped rather than sent in a burst when it connects ([connections.md](connections.md#what-its-sent)).
- `device.store_and_forward = True` lets the user turn on the Dash server's store and forward for the device: the server keeps the app's messages until the device connects, and asks it for its values when it does ([device.md](device.md#what-the-device-offers-the-app)).
- An always on TCPConnection lets the app provision the device on the local network: get its layout, set its Dash server login, and set how often it connects in its provisioning menu.

[Examples/intermittent_connection.py](../Examples/intermittent_connection.py) does all of this.
