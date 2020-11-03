import zmq
import threading
import logging
import uuid


class tcpConnection(threading.Thread):
    """Setups and manages a connection thread to iotdashboard via TCP."""

    def add_device(self, device):
        device.add_connection(self.connection_id)

    def __init__(self, ip="*", port=5000, context=None):
        """
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

        # Subscribe on ALL, and my connection
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"ALL")
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"ALARM")
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, self.b_connection_id)

        self.tcpsocket = self.context.socket(zmq.STREAM)

        ext_url = "tcp://" + ip + ":" + str(port)
        self.tcpsocket.bind(ext_url)
        self.tcpsocket.set(zmq.SNDTIMEO, 5)

        self.poller = zmq.Poller()
        self.poller.register(self.tcpsocket, zmq.POLLIN)
        self.poller.register(self.rx_zmq_sub, zmq.POLLIN)

        self.socket_ids = []
        self.running = True
        self.start()

    def run(self):
        def __zmq_tcp_send(id, data):
            try:
                self.tcpsocket.send(id, zmq.SNDMORE)
                self.tcpsocket.send(data, zmq.NOBLOCK)
            except zmq.error.ZMQError as e:
                logging.debug("Sending TX Error: " + str(e))
                # self.socket_ids.remove(id)

        id = self.tcpsocket.recv()
        self.tcpsocket.recv()  # empty data here

        while self.running:
            socks = dict(self.poller.poll())

            if self.tcpsocket in socks:
                id = self.tcpsocket.recv()
                message = self.tcpsocket.recv()
                if id not in self.socket_ids:
                    logging.debug("Added Socket ID: " + id.hex())
                    self.socket_ids.append(id)
                logging.debug("TCP ID: %s, RX: %s", id.hex(), message.decode('utf-8').rstrip())
                if message:
                    self.tx_zmq_pub.send_multipart([self.b_connection_id, id, message])
                else:
                    if id in self.socket_ids:
                        logging.debug("Removed Socket ID: " + id.hex())
                        self.socket_ids.remove(id)
            if self.rx_zmq_sub in socks:
                [address, msg_id, data] = self.rx_zmq_sub.recv_multipart()
                if address == b'ALL':
                    for id in self.socket_ids:
                        logging.debug("TCP ID: %s, Tx: %s", id.hex(), data.decode('utf-8').rstrip())
                        __zmq_tcp_send(id, data)
                elif address == self.b_connection_id:
                    logging.debug("TCP ID: %s, Tx: %s", msg_id.hex(), data.decode('utf-8').rstrip())
                    __zmq_tcp_send(msg_id, data)

        for id in self.socket_ids:
            __zmq_tcp_send(id, b'')
        self.tcpsocket.close()
        self.tx_zmq_pub.close()
        self.rx_zmq_sub.close()
