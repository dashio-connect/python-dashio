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
import argparse
import configparser
import logging
import signal
import time

import dashio
import shortuuid
import json

cfg = "pVXfT9swEH7nr4jyTFhCm5LubW1ZhQYUQWFI2x4c59JYOHbnOLQM8b/PTto4vzo2rZYi1Z999919d+fXI8uyU2B5ZlsfrW9H6u+PY71HUQi0vSlhKyd8C7t9S/1ei6/CMGdScHox05i9nNjHe2SNBDC5A27mrmegnBFZGLPNniSSQrE341yY/QTIKpG3SBKuUffEC5p3bnhGFMhKAnxdM6l4f6JkVUJTxQZqhmMuUiQL6JozMMDL3mLNqT9UyzexCcAk2zl1q+2nMFq+rMsorvMUBMHG7IZEMqmZHFfItseha5xhyjP4EkYLdgcs0rAUORToW6VRitZt2cJcSs7mgucHoD49eRxPOVUC6BhuITL8m0o/XsweDVbaO2copFAwjBHNoII5Mza/JkTWkv2HKukoPwz06qmYxRrY9w9TnadWQR0ujj6V3YFe/68YUbm6RqkpZ0sztFuSrQRaJx1lKEw5Y4D3rEtlbAEour/f5SmE0B8GA3AGI/Cc4SgInPAs9h1A7tlg5IWnIxTsIrUzEM8EQ3V3GKMYn7qe48Wh7wz9MThBjLGDfTzGg4E39obh/u5GKK3+zau6+FYE8sR42A4u/Sllb3QJz+T97WXhJkJZcqI/hJ+o3O6o5CqOKqVYILIyriKCOjMLq4LLRXsXUSTSzngjKcz7tIhAZ04RjpU3Q5bl6axAHghsijueodIE2sNSCnqFtp9VJ92RX0UsAzM9skT1gmqUPC1So5u8wpTPEin9HWjKZv9ob5OnFYtM801oDq0DXEQgFl2PBjzYu/rIYbACrpDgSu2evp0jgVZgNQd+RXspEMuK+YBf9PHAbZxZajPqWTIMFuqCMtecWrWTbYN+j8G6Nt6ov6OL56JATDNnQFVV807FZZSoFHYqi4iyB9oAPKtpeMlXfdXTN7HOfLUMzcMT672nsvH6WueaRvZXU7pZgeeXdeydMdkZ8KdeK6sojwh/IFneaPCjt98="

cfg_2 = "tZdtb+I4EMe/CvJrrkt4aCnvgLSoOloQod1Kt6uVSQz4cGzWcZZyVb/7jRMn5LGl96BIkDj2eObnmb+dV+QTHgZo8Mf3JmJ4RZi5"\
"V+RFjcQL0Y+vyBVcScHubDRAyxFqoj2WhKvoeT5pWdAScqqgM4JbRRUjcGsLIeFxS+hmqxZYUYEGrQurb3rMRUChjWubYo/iOYeM"\
"bnTLGMwTPXotpI8VtDwITuD5mAxLDfa6cPXAJ0lcGkQGW020W3nL41678RD6RFIXxh6op7bpuOsmeikZa4Ehl4mA/L7yZtwh3EMD"\
"JUPy1ixQeF5aeQ5LEqjleF6NYtjQwTWMhQoo7TKUkVBK+AUuU7JWZ1Hpd+uJDBlrjLdYYhcYByUwvW4VmXa3hgxki4/3Jm9WITjN"\
"J1KE+ZY4j8R6PRYMsmKAFsSDibNIn+/sZ5T0v+F4xaDLYI1ZQJpI8GTg1y1VpDIFC0y7fX2d1mC2J/zbl7EOAdWlYJljq6Ovs3OH"\
"QkQP2E/Sv6EnRTp53g3dnn19+DFaPpTD14Sz0U8kAYM1iVeXVJEzB14RdZpjFQl0WQy63a6Mul2I+nBGwI/z/zfcx/3ngm1Z/yhY"\
"mEan/0bi/dak+46Llbn1fyo1FpwTN3bgFW1FoB4XUxjp4WB7oX+ouADTIBoBkcbqn/AXAEPkUcziwslUMngQqGMU5QjLYiLdDae6"\
"FHz8ggZWqwacJN4TZiGYuOplNcqG+cpc21bsyS1lLL+inwB8CSW0F1SLemJjpD1oIh76KyIzVlLpD7bicE/5vY7FyMC5QpVIsP/t"\
"i9Y3n2oJ1EvlwuShNAuEGZa+uffIL+qSJ0oOZstTksHMtwDXoX8Bn05LewQ4wf/Q50mugvtxAwyz8othZElbGu023CsEHrUL6RE5"\
"S62d2opyp9+U2szzPZZCpOWtywa0fUMaZgNOHVhKzIMoI9wjGvRb8aulHgR7fWJ9Br1gsCnaTIf88F52+AmTdZmrkGh/ijbPIs/2"\
"p3meErgCKXZ3JaYmaWqgNhxf7CrRnt4UzCd8jSeDhr/aW5e/dS6YcKPSqUFdQzrrdTXksxg7P0PoHylRnMUgOmu60YIDNO1sYrff"\
"dBA+mWQUKyAMFErIOO/P0UZdd/WnlVROHGO4Tr+La5vpX13VRcHv6JADRj1inI/vC7tJdhpnai9+2KOpVhc4wcw4O874AubFcCgw"\
"/SPt7H0onRnldKJpodxCmLcsoNcVJ94UV4XIVS+B3ljy8rvC8lYwJg5B7EBqAF4UtKawt1UBvupHAx2ztzhk42sh9k7y2TwT8Idw"\
"z9iYdJc83jLXq86/5Wp1/luutWeG98HqwqUyPiaYRDad7ZvJ3CmUynh2P//w24PnS9FOzGc+QUCxhnyjO7Te4Vg8DLSrOHb6pd09"\
"PbnlTi7n7d8aCA49Kp5oEOLkk5T8gnCnYlOnU1c9uEqH1uvar83MV2rjRtsO8lCT7TuD/mYaNVUf/UvHprfvb38D"


SHUTDOWN = False
COUNTER = 0


def signal_cntrl_c(os_signal, os_frame):
    global SHUTDOWN
    print("Shutdown")
    SHUTDOWN = True


def init_logging(logfilename, level):
    log_level = logging.WARN
    if level == 1:
        log_level = logging.INFO
    elif level == 2:
        log_level = logging.DEBUG
    if not logfilename:
        formatter = logging.Formatter("%(asctime)s, %(message)s")
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger = logging.getLogger()
        logger.addHandler(handler)
        logger.setLevel(log_level)
    else:
        logging.basicConfig(
            filename=logfilename,
            level=log_level,
            format="%(asctime)s, %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    logging.info("==== Started ====")


def parse_commandline_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v",
        "--verbose",
        const=1,
        default=1,
        type=int,
        nargs="?",
        help="""increase verbosity:
                        0 = only warnings, 1 = info, 2 = debug.
                        No number means info. Default is no verbosity.""",
    )
    parser.add_argument("-u", "--username", help="Dashio Username", dest="username", default="")
    parser.add_argument("-w", "--password", help="DashIO Password", dest="password", default="")
    parser.add_argument("-l", "--logfile", dest="logfilename", default="", help="logfile location", metavar="FILE")
    args = parser.parse_args()
    return args


def main():


    signal.signal(signal.SIGINT, signal_cntrl_c)
    args = parse_commandline_arguments()
    init_logging(args.logfilename, args.verbose)

    new_ini_file = False
    ini_file = "load_cfg.ini"
    config_file_parser = configparser.ConfigParser()
    config_file_parser.defaults()

    try:
        ini_f = open(ini_file)
        ini_f.close()
    except FileNotFoundError:
        default = {
            'DeviceID': shortuuid.uuid(),
            'DeviceName': 'Load CFG Test',
            'DeviceType': 'DashIOTest',
            'username': args.username,
            'password': args.password
        }
        config_file_parser['DEFAULT'] = default
        with open(ini_file, 'w') as configfile:
            config_file_parser.write(configfile)
        new_ini_file = True

    if not new_ini_file:
        config_file_parser.read(ini_file)
    config_file_parser.get('DEFAULT', 'username')
    device = dashio.Device(
        config_file_parser.get('DEFAULT', 'DeviceType'),
        config_file_parser.get('DEFAULT', 'DeviceID'),
        config_file_parser.get('DEFAULT', 'DeviceName')
    )
    dash_conn = dashio.DashConnection(
        config_file_parser.get('DEFAULT', 'username'),
        config_file_parser.get('DEFAULT', 'password')
    )
    dash_conn.add_device(device)

    config_dict = dashio.decode_cfg(cfg_2)
    controls = dashio.load_controls_from_config(device, config_dict)

    global SHUTDOWN
    while not SHUTDOWN:
        time.sleep(1)

    device.close()


if __name__ == "__main__":
    main()
