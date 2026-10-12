import dashio
import time

cfg64 = "jVTbjtowEP0VlOeqImyXSn1LCLCIXFDiQqWqD97ESywSmzrOAl3x7+sxOAk3qW/jM+Pxseccf1jeLLZ+9H7/+dKzRpOpCj8sVpce"\
    "eacpWVKyqxRkq2SmkYTIeqsQy1JQ+raOyTvkj2o1DyMXOn1YKWdS8GLmQSGehy4U54SucxljSbmC+18HQwVKKguy4BVVKINqN0Io"\
    "CiyTAsjpzRl/BagiLItYcYhYTAqCK0hLUROVKils70NRzncBZQHeK+ANFxWkBcmWuKhhw/dntd5iQZg8E4RbQvuM4iLgmT50Evl+"\
    "tAJ0b+h1qH9T+I5mMm+xZ8A2iuiIF1xAi5hkpmuDucABSMrD6XJhFAeOD9Dh9hwbepb6Ina/f9Qj8ptpJb7XxM7SM2HgLEzoomkT"\
    "B+Pwp4nR+Bcyse/6JvSWy9V5gFK0nFc5laSXlHxzSd11ktlIy0BVu1xkRDzasxY0U7m6ZKCmwQA2XWjEjIAqOMSl7p/8rdWUrqTg"\
    "qddsztysWdZ5WpxuNMFcbTud1uoD6hG0cfn+dks3iwRmldZHejhLqklPFOmE/gMu9vCcUELrwAOoV/5pb2t32d5rfsMGXivm2nhP"\
    "Az11P5o2Hn2JUauAEYrbYaOwmeTM8U+T3AqS0upkrv71s4M0betE+JWIrg/98QRdTHsxG1uPjNNI9MKIW06Z7GjCaL9mVFbmC7n7"\
    "K1y7FXhOaFFcW+v/fg8jmUdGvmO8p+EDg99+Lno+aBovXvTjHz8B"


config_dict = dashio.decode_cfg64(cfg64)
device = dashio.Device("aDeviceType", "aDeviceID2", "aDeviceName1", cfg_dict=config_dict)
tcp_con = dashio.TCPConnection()
tcp_con.add_device(device)

aknob: dashio.Knob = device.get_control(dashio.ControlName.KNOB, "aKNB")
first_dial_control: dashio.Dial = device.get_control(dashio.ControlName.DIAL, "dial1")


def knob_event_handler(msg):
    aknob.knob_dial_value = float(msg[3])
    first_dial_control.dial_value = float(msg[3])


aknob.add_receive_message_callback(knob_event_handler)

while True:
    time.sleep(1)
