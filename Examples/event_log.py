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
import signal
import time
import random
import dashio


class random_insults:
    def __init__(self) -> None:
        self.insult_c1 = [
            "Artless",
            "Bawdy",
            "Beslubbering",
            "Bootless",
            "Churlish",
            "Cockered",
            "Clouted",
            "Craven",
            "Currish",
            "Dankish",
            "Dissembling",
            "Droning",
            "Errant",
            "Fawning",
            "Fobbing",
            "Froward",
            "Frothy",
            "Gleeking",
            "Goatish",
            "Gorbellied",
            "Impertinent",
            "Infectious",
            "Jarring",
            "Loggerheaded",
            "Lumpish",
            "Mammering",
            "Mangled",
            "Mewling",
            "Paunchy",
            "Pribbling",
            "Puking",
            "Puny",
            "Qualling",
            "Rank",
            "Reeky",
            "Roguish",
            "Ruttish",
            "Saucy",
            "Spleeny",
            "Spongy",
            "Surly",
            "Tottering",
            "Unmuzzled",
            "Vain",
            "Venomed",
            "Villainous",
            "Warped"
        ]
        self.insult_c2 = [
            "base-court",
            "bat-fowling",
            "beef-witted",
            "beetle-headed",
            "boil-brained",
            "common-kissing",
            "crook-pated",
            "dismal-dreaming",
            "dizzy-eyed",
            "dog-hearted",
            "dread-bolted",
            "earth-vexing",
            "elf-skinned",
            "fat-kidneyed",
            "fen-sucked",
            "flap-mouthed",
            "fly-bitten",
            "folly-fallen",
            "fool-born",
            "full-gorged",
            "futs-griping",
            "half-faced",
            "hasty-witted",
            "hedge-born",
            "hell-hated",
            "idle-headed",
            "ill-nurtured",
            "knotty-pated",
            "milk-livered",
            "motley-minded",
            "onion-eyed",
            "plume-plucked",
            "pottle-deep",
            "pox-marked",
            "reeling-ripe",
            "rough-hewn",
            "rude-growing",
            "rump-fed",
            "shard-borne",
            "sheep-biting",
            "spur-galled",
            "swag-bellied",
            "tardy-gaited",
            "tickle-brained",
            "toad-spotted",
            "unchin-snouted",
            "weather-bitten"
        ]
        self.insult_c3 = [
            "apple-john",
            "baggage",
            "barnacle",
            "bladder",
            "boar-pig",
            "bugbear",
            "bum-bailey",
            "canker-blossom",
            "clack-dish",
            "clotpole",
            "coxcomb",
            "death-token",
            "dewberry",
            "flap-dragon",
            "flax-wench",
            "flirt-gill",
            "foot-licker",
            "fustilarian",
            "giglet",
            "gudgeon",
            "haggard",
            "harpy",
            "hedge-pig",
            "horn-beast",
            "hugger-mugger",
            "jolthead",
            "lewdster",
            "lout",
            "maggot-pie",
            "malt-worm",
            "mammet",
            "measle",
            "minnow",
            "miscreant",
            "moldwarp",
            "mumble-news",
            "nut-hook",
            "pigeon-egg",
            "pignut",
            "puttock",
            "pumpion",
            "ratsbane",
            "scut",
            "skainsmate",
            "strumpet",
            "vartlot",
            "vassal"
        ]

    def get_insult(self):
        word1 = random.choice(self.insult_c1)
        word2 = random.choice(self.insult_c2)
        word3 = random.choice(self.insult_c3)
        return f"{word1} {word2} {word3}"


class TestEventLog:
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
        parser.add_argument(
            "-t", "--device_type", dest="device_type", default="TestEventLog", help="IotDashboard Device type"
        )
        parser.add_argument("-d", "--device_id", dest="device_id", default="1234321a", help="IotDashboard Device ID.")
        parser.add_argument("-n", "--device_name", dest="device_name", default="TestEventLog", help="IotDashboard Device name alias.")
        parser.add_argument("-u", "--username", help="DashIO Username", dest="username", default="")
        parser.add_argument("-w", "--password", help="DashIO Password", default="")
        parser.add_argument("-l", "--logfile", dest="logfilename", default="", help="logfile location", metavar="FILE")
        args = parser.parse_args()
        return args

    def __init__(self):
        self.bttn1_value = False
        ri = random_insults()
        # Catch CNTRL-C signal
        signal.signal(signal.SIGINT, self.signal_cntrl_c)
        self.shutdown = False
        args = self.parse_commandline_arguments()
        self.init_logging(args.logfilename, args.verbose)
        logging.info("       Connection ID: %s", args.device_type)
        logging.info("       Control topic: %s/%s/control", args.username, args.device_id)
        logging.info("          Data topic: %s/%s/data", args.username, args.device_id)

        device = dashio.Device(args.device_type, args.device_id, args.device_name)
        dash_conn = dashio.DashConnection(args.username, args.password)
        dash_conn.add_device(device)

        event_l = dashio.EventLog("ELTest")
        el_page = dashio.DeviceView("el_page", "Event Log Test")
        el_page.add_control(event_l)
        device.add_control(event_l)
        device.add_control(el_page)

        count = 1
        while not self.shutdown:
            time.sleep(60)
            insult = ri.get_insult()
            event_d = dashio.EventData(f"Count: {count}\n{insult}", color=random.choice(list(dashio.Color)))
            event_l.add_event_data(event_d)
            count += 1
        device.close()


if __name__ == "__main__":
    TestEventLog()
