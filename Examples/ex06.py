import dashio
import random
import time

device = dashio.Device("aDeviceType", "aDeviceID3", "aDeviceName")
dash_con = dashio.DashConnection("your_dash_username", "your_dash_password")
dash_con.add_device(device)

first_dial_control = dashio.Dial("dial1", control_position=dashio.ControlPosition(0.24, 0.36, 0.54, 0.26))
device.add_control(first_dial_control)
dv = dashio.DeviceView("aView", "A Dial")
dv.add_control(first_dial_control)
device.add_control(dv)

alarm = dashio.Alarm("hiAlarm")
device.add_control(alarm)

high = False
while True:
    value = random.random() * 100
    first_dial_control.dial_value = value
    if value > 90 and not high:
        alarm.send("High value", f"The dial is at {value:.0f}")
    high = value > 90
    time.sleep(5)
