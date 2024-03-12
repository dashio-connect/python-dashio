"""Under Active Development - INCOMPLETE!"""

import dashio
from dashio import lte_767x_connection
import time
import logging

logging.getLogger('dashio').setLevel(logging.DEBUG)
formatter = logging.Formatter("[%(asctime)s][%(module)15s] -- %(message)s")
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


cfg64 = "pVNdr5pAEP0rN/tMjHCrbXnjQ60RxQD1Nmn6wIVVN8IuXZar1vjfOwuLeNWmTfo2OztzZnLmnBPybA+Z339oaLbwbYhOqBTHDCMT"\
    "LfxgbnlIQwmjgrNs6kIyni1sSJWYpj7Njj4NcIbjEuoFr7CG8viATL3f11ARc0xF0+TiN5LgFcF7eGuI43QVZxU0fRxoSBBRz7Oe"\
    "ZpS9wvcWk81WBLEgDJn9njFUNUtWEshRqLX9KPLncpEt288Jncux6zgrYYVjW3dB0D9oaAfYDssYh+4Ap9Cakjgbsyxj+7Ie3PbL"\
    "fFtpyy01tCep2F7gBgB3uBtiQDYnsFz/DGyGnhs0vEajb5GKnCUyT6hgXCBzMBwASaSw0pTjsoRZ+mejpw8/9fSebvTRWUPuVEHM"\
    "rWUTeP5EZUaLr000CZZfmshauU0Qek6kOh1PBe5q9fLuurYVTh15XMEzYG8MNw7JL/gxYK0NJylQUOUUFjMMSTNcs8m0l6ZVfinR"\
    "b0Ryc285w2Y8xbzl9WVLBH4Kc7bD7f9uQ9OO9jjZqY+/tEQ8pmWtteQI3MtF3mN08nLhsKo1kkmbHR4NbP/ukCUrAagFmc/GVWlH"\
    "nQ5KJUDEIs7lxPBnBd1IysGdWl5Nf8FxQspaxIDYHmM5Hd34bEx4KdTC/+UphfHAU7X+SXYhuHHFH512b6tnACkYoaK7q/ILaOMV"\
    "8ysUbzSOHrv1X61VUSKkS9C1y6JO/XYULdpoouzijCfScGnNVIhFVQAAheNoe7ImmkiKZteOSqXl9SbAbxCez78B"

config_dict = dashio.decode_cfg64(cfg64)
device = dashio.Device("aDeviceType", "aDeviceID", "aDeviceName", cfg_dict=config_dict)
lte_con = lte_767x_connection.Lte767xConnection("iot.lbo.gdsp.nz", "username", "password", 'dash.dashio.io', 8883, "/dev/cu.usbmodem56B30003703", 115200, None)
lte_con.add_device(device)

tcp_con = dashio.TCPConnection()
tcp_con.add_device(device)


aknob: dashio.Knob = device.get_control(dashio.ControlName.KNOB, "aKNB")
first_dial_control: dashio.Dial = device.get_control(dashio.ControlName.DIAL, "FirstDial")


def knob_event_handler(msg):
    aknob.knob_dial_value = float(msg[3])
    first_dial_control.dial_value = float(msg[3])


aknob.add_receive_message_callback(knob_event_handler)

while True:
    time.sleep(1)
