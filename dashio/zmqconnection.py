import zmq
import threading
import logging
import uuid


class zmqConnection(threading.Thread):
    """Setups and manages a connection thread to iotdashboard via TCP."""

    def add_device(self, device):
        device.add_connection(self.connection_id)

    def __init__(self, connection_id, device_id, zmq_out_url="*", pub_port=5555, sub_port=5556, context=None):
        """
        Arguments: figure it out for yourself.
        """

        threading.Thread.__init__(self, daemon=True)
        self.context = context or zmq.Context.instance()

        self.connection_id = uuid.uuid4()
        self.b_connection_id = self.connection_id.bytes

        tx_url_internal = "inproc://TX_{}".format(self.connection_id.hex)
        rx_url_internal = "inproc://RX_{}".format(self.connection_id.hex)

        self.tx_zmq_pub = self.context.socket(zmq.PUB)
        self.tx_zmq_pub.bind(tx_url_internal)

        self.rx_zmq_sub = self.context.socket(zmq.SUB)
        self.rx_zmq_sub.bind(rx_url_internal)

        #  Subscribe on ALL, and my connection
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"ALL")
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"ALARM")
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, self.b_connection_id)

        tx_url_external = "tcp://{}:{}".format(zmq_out_url, pub_port)
        rx_url_external = "tcp://{}:{}".format(zmq_out_url, sub_port)

        self.ext_tx_zmq_pub = self.context.socket(zmq.PUB)
        self.ext_tx_zmq_pub.bind(tx_url_external)

        self.ext_rx_zmq_sub = self.context.socket(zmq.SUB)
        self.ext_rx_zmq_sub.bind(rx_url_external)

        # Subscribe on WHO, and my deviceID
        sub_topic = "\t{}".format(device_id)
        self.ext_rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, sub_topic.encode('utf-8'))
        self.ext_rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b'\tWHO')

        self.poller = zmq.Poller()
        self.poller.register(self.ext_rx_zmq_sub, zmq.POLLIN)
        self.poller.register(self.rx_zmq_sub, zmq.POLLIN)

        self.running = True
        self.start()

    def run(self):

        while self.running:
            socks = dict(self.poller.poll())

            if self.ext_rx_zmq_sub in socks:
                message = self.ext_rx_zmq_sub.recv()
                logging.debug("ZMQ Rx: %s", message.decode('utf-8').rstrip())
                self.tx_zmq_pub.send_multipart([self.b_connection_id, b'', message])

            if self.rx_zmq_sub in socks:
                [address, msg_id, data] = self.rx_zmq_sub.recv_multipart()
                if address == b'ALL' or address == self.b_connection_id:
                    logging.debug("ZMQ Tx: %s", data.decode('utf-8').rstrip())
                    self.ext_tx_zmq_pub.send(data)

        self.tx_zmq_pub.close()
        self.rx_zmq_sub.close()
