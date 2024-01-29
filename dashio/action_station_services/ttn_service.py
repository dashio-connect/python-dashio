"""Memory Class"""
import logging
import threading
import zmq
import shortuuid
import base64
import json
import datetime
import paho.mqtt.client as mqtt
from ctypes import c_uint8, c_uint16, c_uint32, memmove, pointer, sizeof, BigEndianStructure

from ..constants import TASK_CONN_PORT_OFFSET, TASK_PULL_PORT_OFFSET, TCP_URL
from .action_station_service_config import (ActionServiceCFG,
                                            IntParameterSpec,
                                            ListParameterSpec,
                                            SelectorParameterSpec,
                                            StringParameterSpec)


class TtnPayload(BigEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("temperature", c_uint16),
        ("humidity", c_uint16),
        ("ext_temperature", c_uint16),
        ("ext", c_uint8),
        ("time_stamp", c_uint32)
    ]


def make_ttn_config(num_tests):
    provisioning_list = [
        StringParameterSpec(name="Username", value="", uuid=shortuuid.uuid()),
        StringParameterSpec(name="Password", value="", uuid=shortuuid.uuid()),
        StringParameterSpec(name="Server", value="", uuid=shortuuid.uuid()),
        IntParameterSpec(name="Port", min=0, max=10000, units="", value=8883, uuid=shortuuid.uuid()),
        StringParameterSpec(name="TTN Device ID", value="", uuid=shortuuid.uuid()),
        ListParameterSpec(
            name="Payload Converter",
            text="Convert TTN Payload to values",
            uuid=shortuuid.uuid(),
            param_list=[
                SelectorParameterSpec(
                    name="Endianness",
                    selection=[
                        "Big Endian",
                        "Little Endian"
                    ],
                    value="Big Endian6",
                    uuid=shortuuid.uuid()
                ),
                SelectorParameterSpec(
                    name="Register Type",
                    selection=[
                        "char",
                        "int_8",
                        "uint_8",
                        "int_16",
                        "uint_16",
                        "int_32",
                        "uint_32",
                        "int_64",
                        "uint_64",
                        "float_32",
                        "float_64",
                        "Bit_Field_8",
                        "Bit_Field_16"
                    ],
                    value="uint_16",
                    uuid=shortuuid.uuid()
                ),
                StringParameterSpec(name="Field Name", value="", uuid=shortuuid.uuid())
            ]
        ),
    ]
    """Make a timer config
    provisioning_list = [
        SelectorParameterSpec(name="A Selector", selection=["Selection1", "Selection2", "Selection3"], value="Selection1", uuid=shortuuid.uuid()),
        IntParameterSpec(name="An Int", min=0, max=100, units="jiggers", value=42, uuid=shortuuid.uuid()),
        StringParameterSpec(name="A String", value="Little Bo Peep....", uuid=shortuuid.uuid()),
        FloatParameterSpec(name="A Float", min=2.71828, max=299792458.0, units="jiffies", value=1.4142, uuid=shortuuid.uuid()),
        BoolParameterSpec(name="A bool", value=True, uuid=shortuuid.uuid()),
        SliderParameterSpec(name="A Slider", min=1.0, max=10.0, step=1.0, value=5.0, uuid=shortuuid.uuid()),
        ListParameterSpec(
            name="List of Things",
            text="Create a list",
            uuid=shortuuid.uuid(),
            param_list=[
                IntParameterSpec(
                    name="Add a uint_16",
                    min=0,
                    max=65535,
                    units="",
                    value=0,
                    uuid=shortuuid.uuid()
                ),
                SelectorParameterSpec(
                    name="Choose a thing",
                    selection=[
                        "Thing One",
                        "Thing Two",
                        "The Lorax",
                        "The Grinch",
                        "Horton",
                        "Sam-I-Am",
                        "Thidwick",
                        "Yertle the Turtle",
                        "Lord Droon"
                    ],
                    value="Horton",
                    uuid=shortuuid.uuid()
                )
            ]
        )

    ]"""
    parameter_list = []

    timer_cfg = ActionServiceCFG(
        objectName="TTN",
        name="The Things Network",
        text="TTN Service",
        uuid=shortuuid.uuid(),
        controlID="TTN",
        numAvail=num_tests,
        isTrigger=True,
        isIO=True,
        provisioning=provisioning_list,
        parameters=parameter_list
        #  parameter_list_out
    )
    return timer_cfg


class TtnService(threading.Thread):
    """The Things Network Service Class"""

    # gives connection message
    def on_connect(self, mqttc, mosq, obj, rc):
        logging.debug("Connected with result code: " + str(rc))
        # subscribe for all devices of user
        mqttc.subscribe(f"v3/{self.ttn_username}/devices/{self.ttn_device_id}/up")

        # gives message from device
    def on_message(self, mqttc, obj, msg):
        x = json.loads(msg.payload.decode())
        logging.debug("MSG: %s", json.dumps(x, indent=4))
        payload = base64.b64decode(x['uplink_message']['frm_payload'])
        logging.debug("payload: %s", payload.hex())
        if len(payload) == 11:
            temperature = ((payload[0] << 8) + payload[1]) / 100
            humidity = ((payload[2] << 8) + payload[3]) / 10
            ext_temperature = ((payload[4] << 8) + payload[5]) / 100
            ext = payload[6]
            time_stamp = (payload[7] << 24) + (payload[8] << 16) + (payload[9] << 8) + payload[10]
            logging.debug(f"Temperature: {temperature}, Humidity: {humidity}, Ext Temperature: {ext_temperature}, ext: {ext}, Time stamp: {time_stamp}")

            ttn_payload = TtnPayload()

            memmove(pointer(ttn_payload), payload, sizeof(ttn_payload))
            temperature = ttn_payload.temperature / 100
            humidity = ttn_payload.humidity / 10
            ext_temperature = ttn_payload.ext_temperature / 100

            dt = datetime.datetime.fromtimestamp(time_stamp, datetime.timezone.utc)
            logging.debug("CT DT: %s", dt)
            time_stamp = ttn_payload.time_stamp
            dt = datetime.datetime.fromtimestamp(time_stamp, datetime.timezone.utc)
            logging.debug("JB DT: %s", dt)
            logging.debug(f"Temperature: {temperature}, Humidity: {humidity}, Ext Temperature: {ext_temperature}, ext: {ext}, Time stamp: {time_stamp}")

    def on_publish(self, mosq, obj, mid):
        logging.debug("mid: " + str(mid))

    def on_subscribe(self, mosq, obj, mid, granted_qos):
        logging.debug("Subscribed: " + str(mid) + " " + str(granted_qos))

    def on_log(self, mqttc, obj, level, buf):
        logging.debug("message:" + str(buf))
        logging.debug("userdata:" + str(obj))

    def send_message(self, out_message=""):
        """Send the message"""
        self.task_sender.send_multipart([b"ALL", out_message.encode('utf-8')])

    def close(self):
        """Close the thread"""
        self.running = False

    def __init__(self, device_id: str, local_port: int, control_config_dict: dict, context: zmq.Context) -> None:
        threading.Thread.__init__(self, daemon=True)

        self.context = context
        self.running = True

        self.control_id = control_config_dict['controlID']
        self.name = control_config_dict['name']
        self.control_type = control_config_dict['objectType']
        provision_list = control_config_dict['provisioning']

        self.ttn_username = provision_list[0]['value']
        self.ttn_password = provision_list[1]['value']
        self.ttn_server = provision_list[2]['value']
        self.ttn_port = provision_list[3]['value']
        self.ttn_device_id = provision_list[4]['value']

        self.sub_url = TCP_URL.format(port=local_port + TASK_CONN_PORT_OFFSET)
        self.push_url = TCP_URL.format(port=local_port + TASK_PULL_PORT_OFFSET)
        self.task_sender = self.context.socket(zmq.PUSH)
        self.task_sender.connect(self.push_url)

        self.control_msg = f"\t{device_id}\t{self.control_type}\t{self.control_id}"
        logging.debug("Init Class: %s, %s", self.control_type, self.name)

        self.mqttc = mqtt.Client()
        # Assign event callbacks
        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_message = self.on_message

        self.start()

    def run(self):
        receiver = self.context.socket(zmq.SUB)
        receiver.connect(self.sub_url)
        receiver.setsockopt_string(zmq.SUBSCRIBE, self.control_msg)
        poller = zmq.Poller()
        poller.register(receiver, zmq.POLLIN)

        self.mqttc.tls_set()
        self.mqttc.username_pw_set(self.ttn_username, self.ttn_password)
        self.mqttc.connect(self.ttn_server, self.ttn_port, 60)
        self.mqttc.loop_start()
        while self.running:
            try:
                socks = dict(poller.poll(15))
            except zmq.error.ContextTerminated:
                break
            if receiver in socks:
                message, _ = receiver.recv()
                if message:
                    logging.debug("%s\t%s RX:\n%s", self.control_type, self.control_id, message.decode())

        self.mqttc.loop_stop()
        self.task_sender.close()
        receiver.close()
