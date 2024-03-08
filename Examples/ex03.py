import dashio
import time

device = dashio.Device("aDeviceType", "aDeviceID", "aDeviceName")
tcp_con = dashio.TCPConnection()
tcp_con.add_device(device)
first_dial_control = dashio.Dial("FirstDial", control_position=dashio.ControlPosition(0.24, 0.36, 0.54, 0.26))
device.add_control(first_dial_control)

dv = dashio.DeviceView("aDeviceViewID", "A Dial")
dv.add_control(first_dial_control)
device.add_control(dv)


def knob_event_handler(msg):
    first_dial_control.dial_value = float(msg[3])


aknob = dashio.Knob("aKNB", control_position=dashio.ControlPosition(0.24, 0.14, 0.54, 0.26))
aknob.add_receive_message_callback(knob_event_handler)
dv.add_control(aknob)
device.add_control(aknob)

while True:
    time.sleep(1)
