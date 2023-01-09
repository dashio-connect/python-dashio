import dashio
import random
import time

device = dashio.Device("aDeviceType", "aDeviceID", "aDeviceName")
tcp_con = dashio.TCPConnection()
tcp_con.add_device(device)
first_dial_control = dashio.Dial("FirstDial", control_position=dashio.ControlPosition(0.24, 0.36, 0.54, 0.26))
device.add_control(first_dial_control)

dv_dial = dashio.DeviceView("aDeviceViewID", "A Dial")
dv_dial.add_control(first_dial_control)
device.add_control(dv_dial)

while True:
    first_dial_control.dial_value = random.random() * 100
    time.sleep(5)
