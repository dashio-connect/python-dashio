import dashio
import random
import time

device = dashio.Device("aDeviceType", "aDeviceID", "aDeviceName")
tcp_con = dashio.TCPConnection()
tcp_con.add_device(device)
first_dial_control = dashio.Dial("FirstDial")
device.add_control(first_dial_control)

while True:
    first_dial_control.dial_value = random.random() * 100
    time.sleep(5)
