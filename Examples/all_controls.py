#!/bin/python3
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
import logging
import random
import signal
import time
import json
import dashio

DEVICE_CFG64 = "pU9dc+JIEvwrCj3PcRI2tpk3CTDrGIQIofHuhcOx0aA26nDTzbVKg1iC/35V3Qj8wc7txka/dGVmZWXu/Xz0W+5/9Z72/lIrMFo+"\
    "DHH089/y0P/i+RtmuAKHRVIOnKYiqlYCKsJpAAGSW5EHvAHvaEZUycWqhIyB0CgIOldht9duzHQlEFe0Gad5nibWDB0iKVYWnozu"\
    "cwJftFkzIGSaTkeE7Nrts/fN3S15bwxfisr5Bji/Lop8t3H5JhPa3YoCynYvRKD5ZIbgUuqKf1sUqZpzVSAIpuaHZ2SGj4+/4vy0"\
    "9yvYueZxmg1H2Zzcl2Bkwpp7rWAu/iC2S3YrI4qBlvVaVQR1EapKZrjDjvYIqnp9ll2RHxoZLR+GtoGUAzdX7a1Ym4Ib3NGGFL+W"\
    "Arg3X+tXflK8rlRxEsSSLV9b6v+u5YapaoM51XKHusAG+ugEAiQ/xvPafF+99WIT3vzrqiP1ksnWNSdtrJvLeVr2wtmVEUWmtxWO"\
    "V9238ns8OBd/UIDwBgmx1GrK1jbQ/L81mviHZ8TjPJ8i9rT39cvL6XzGC3vcpX4YEpZwVccoRnxRA2g1UmwhUfjVA1NzhLV6k7/m"\
    "pLRp4Wgwmn4nrORiVULGQGhq0aHcQJnbK57z91t8piuBYmWN0zxPE6J2LXxyIj1vgGQk2IoCyvdnmks7AmtO2dqen2rF/cMXb+/r"\
    "l5dTmwxbohB1YLR0beJ8+vs4mxHu4o4UW0gUfvXA1BxhrU4Gsaw5KTfMcAVHA9wOCSy5WJXwPqjtTarIi62734JtA2uR5nmaELW7"\
    "VAx4AyQjwVYUUL6/0VzaEVhyytb29lQr7h++eHtfv7ycumTYEYWoA6PlsUs+JWxho44UW0gUffXA1BxhrU7LY8O57bJhhitw25GU"\
    "A+dWEVVysSrhTdbw7rZHdQRImyvyYnvIb8G2iI2S5nmaELX71O9sxRsgMcm2ooDyLLkO+kE/RLz5vB7e0UNOLLWasrVNE3Mp/cMz"\
    "ot+maYzI096vYOeiTtMsiSZ0ZukausbfpjFhFVdFquQuVRmXnFW0AqbmSK1Zg0MY4HfDDFfgFiMpB86oIgPDi0cma95KQYC7G3nf"\
    "lF6QpORiVcK5Qze8u+210rai7ZHmeZrYWKXeJkIlNsILkxUF2rXakxWCr3hkoKU2ZJDxgrYLweS9llJvK5vhbEHMSR1TbAS3ooDy"\
    "HO866Af9EPHm071Or08kcmtBiYPDM/4n8QT/T/sLATt311e267sbZA4CJG/1Nk2a52lCeSrYSU7QOEu/z/xWTEjkSbbgkrANM1zB"\
    "w9DCElspMFpWRC3d33GTdmH5sfenfpSr5GJVwrlA2Lvp9mzNJJpRTfrOJ8PMVa6kKLgZKbaQvEAITM0/JrBq6sVVkSq5S1XGJWcV"\
    "P+vXrKH7wc97GV48Mgp/lIIAye0Fm8K/EP/m7rbXKtu6tBGneZ4mNlWpt4lQiU3wwmRFeXat9uSE4KvSi4GW2pBBhnURWzBzr6XU"\
    "2+qY4eyB1EkdU2rEtqKA8pwuvKOHeHPpHhrMYXdsOBrT/lpQ+uDwjP/BL1mOw9Pe30WNqBJHkRmNE7bgsjrtp1NaX2oFRsuHIUF2"\
    "v5Wft50Za3AMAwI2zHAFbieScuA8qvPqGy0IcPcib1AyA/67OET4raptTGCc5nmaEFVysSohY8hQnk6PErXSE9zGfOdqkWm9jpmp"\
    "EOu1p99DW1FA2RqFpPno3j08IxxNEvw/0Xf4EE3ov/c3hi9F5UJ3kalg5+rGUUYRllqB0fJhSBithYSuWUO3KPWGGa7A8ZGUA6ev"\
    "SGV48chkTXa3FBQEOO/IGwomSVJysSqhzRl0uuGdlRbI3wuyk9rQSsYLv7Vo69mYaZ6nCVG7j63PbhstFHBzMospFOKqXi+4eWs3"\
    "GE3zkS1elXqbCJXYpi9MVhzBrSigPPtfB/2gHyLefL7d6xOJXK0EVOS9/ndFxmtBl4LDM/7nk0Ge4fS0vxT/6vrKxn93lc6BAMnf"\
    "xo7TPE8Tv6UIirw5l3wJ2BjhDTNcwcPQMlIOtAKjpc2zdH/H5byCt3ufitH5kotVCeecQR9z2j6TdPynbf5RGeWNfmABb6JXf6fO"\
    "iAL91Rph76brakSPwz+t0ev/sx6sLoT2foiqZtI7hv07laLH8C83OtaJ8/HsT/tcX6gTdO5CfN2ftxKYa8rWtljCVf2+qRfXAFp5"\
    "Y6Przd8pGI+zma0IvIF3Viuy8rYCSi8nDjUrI4pHwbeoA1NzRJrPFUPbBrmSi1UJb4hu7/CM+GCS4fy093eflpHdigLKFgjbkq3S"\
    "Rk7zPE38lnKhB1pq483E8pUbojbMcAWuYyTlwHWuiFq6v+MGv8++ZXbBrs5h5xx//WU0mhBecVWkSu5SlXHJWUUsmJoj1XzMH15o"\
    "fXV9det65+Ns9ovvmkeNqBKhjp3fJXIyRJ2INWQcBD/v9PFqDzEQ4LpEXi7W3BsbtilPxhO24JLY/3gMR79daDsRFad5niZ25WNV"\
    "d8I6Tet1zEyFIEFbUUDZqkIEmo+r3cMzwslo+h2Hp/1F75vuJ6+gcxfi6/48qFhqNWVr2zvhqj71IiDyWmjDDFfwMLSolAOtwGhZ"\
    "EbV0f8fZlGTBGzg7eFsBpZcTdqlg0AltVORKLlYlvCG6vcMz4oP7Mc57v+A/xJLPOdQbsleY/MtWvIgvsNyQt6rXQyt5FHxboeSK"\
    "Er6sMv6D/A44DR8y/D7t/Qp2ruZwNJ7NP1UZpMksJHTDDFfgwEjKgRNVRNVKQGWDrG1rAc4x8obC8CWV9I6m1p/JSK2sJGjlM10J"\
    "0tFanOZ5mpCy5GJVQsaQIXGnG97d9hDftfITRQG1UMDNQEttyGZsOFc2OWYQlTPv4rwVBZRn0+ugH/RDxJtPrp3wjt7hGdl8MENo"\
    "j2cM4Kd306OjYhMVheFVRRfDfrcT3tx1wk7YDfzD4X8="


class AllControls:
    def signal_cntrl_c(self, os_signal, os_frame):
        self.shutdown = True

    def init_logging(self, logfilename, level):
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

    def parse_commandline_arguments(self):
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
        parser.add_argument("-u", "--url", help="Host URL.", dest="url", default="tcp://*")
        parser.add_argument("-d", "--device_id", dest="device_id", default="12345678987654321", help="IotDashboard Device ID.")
        parser.add_argument("-p", "--port", dest="port", type=int, default=5650, help="Port number")
        parser.add_argument(
            "-n", "--device_name", dest="device_name", default="AllControls", help="Alias name for device."
        )
        parser.add_argument("-l", "--logfile", dest="logfilename", default="", help="logfile location", metavar="FILE")
        args = parser.parse_args()
        return args

    config_dict = dashio.decode_cfg64(DEVICE_CFG64)

    def selector_ctrl_handler(self, msg):
        print(self.selector_ctrl.selection_list[int(msg[3])])

    def __init__(self):

        # Catch CNTRL-C signel
        signal.signal(signal.SIGINT, self.signal_cntrl_c)
        self.shutdown = False
        args = self.parse_commandline_arguments()
        self.init_logging(args.logfilename, args.verbose)

        logging.info("   Serving on: %s:%s", args.url, str(args.port))
        logging.info("    Device ID: %s", args.device_id)
        logging.info("  Device Name: %s", args.device_name)

        config_dict = dashio.decode_cfg64(DEVICE_CFG64)
        logging.debug("CFG: %s", json.dumps(config_dict, indent=4))

        self.tcp_con = dashio.TCPConnection()
        self.device = dashio.Device("AllControlsTest", args.device_id, args.device_name, cfg_dict=config_dict)
        self.tcp_con.add_device(self.device)

        self.avd: dashio.AudioVisualDisplay = self.device.get_control(dashio.ControlName.AVD, "AV1")
        self.avd.url = "https://bit.ly/swswift"
        self.comp_control: dashio.Direction = self.device.get_control(dashio.ControlName.DIR, "COMP1")
        self.selector_ctrl: dashio.Selector = self.device.get_control(dashio.ControlName.SLCTR, "TestSelector")
        self.selector_ctrl.add_selection("First")
        self.selector_ctrl.add_selection("Second")
        self.selector_ctrl.add_selection("Third")
        self.selector_ctrl.add_selection("Forth")
        self.selector_ctrl.add_selection("Fifth")

        while not self.shutdown:
            time.sleep(5)
            self.comp_control.direction_value = random.random() * 360

        self.tcp_con.close()
        self.device.close()


if __name__ == "__main__":
    AllControls()
