import zmq
import threading
import logging


class zmqConnectionThread(threading.Thread):
    """Setups and manages a connection thread to iotdashboard via TCP."""

    def __init__(self, connection_id, device_id, zmq_out_url="*", context=None):
        """
        Arguments: figure it out for yourself.
        """

        threading.Thread.__init__(self, daemon=True)
        self.context = context or zmq.Context.instance()
        self.b_connection_id = connection_id.encode('utf-8')

        tx_url_internal = "inproc://TX_{}".format(device_id)
        rx_url_internal = "inproc://RX_{}".format(device_id)

        self.tx_zmq_pub = self.context.socket(zmq.PUB)
        self.tx_zmq_pub.connect(tx_url_internal)

        self.rx_zmq_sub = self.context.socket(zmq.SUB)
        self.rx_zmq_sub.connect(rx_url_internal)

        # Subscribe on ALL, and my connection
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"ALL")
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, self.b_connection_id)


        tx_url_external = "tcp://{}:5556".format(zmq_out_url)
        rx_url_external = "tcp://{}:5555".format(zmq_out_url)

        self.ext_tx_zmq_pub = self.context.socket(zmq.PUB)
        self.ext_tx_zmq_pub.connect(tx_url_external)

        self.ext_rx_zmq_sub = self.context.socket(zmq.SUB)
        self.ext_rx_zmq_sub.connect(rx_url_external)

        # Subscribe on ALL, and my connection
        self.ext_rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, device_id.encode('utf-8'))
        self.ext_rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b'WHO')

        self.poller = zmq.Poller()
        self.poller.register(self.ext_rx_zmq_sub, zmq.POLLIN)
        self.poller.register(self.rx_zmq_sub, zmq.POLLIN)

        self.running = True
        self.start()

    def run(self):
        
        while self.running:
            socks = dict(self.poller.poll())

            if self.ext_rx_zmq_sub in socks:
                _, message = self.ext_rx_zmq_sub.recv_multipart()
                logging.debug("ZMQ Rx: %s", message.decode('utf-8').rstrip())
                self.tx_zmq_pub.send_multipart([self.b_connection_id, b'', message])

            if self.rx_zmq_sub in socks:
                [address, msg_id, data] = self.rx_zmq_sub.recv_multipart()
                if address == b'ALL' or address == self.b_connection_id:
                    logging.debug("ZMQ Tx: %s", data.decode('utf-8').rstrip())
                    self.ext_tx_zmq_pub.send(data)
            
        for id in self.socket_ids:
            self._zmq_send(id, "")
        self.tcpsocket.close()
        self.tx_zmq_pub.close()
        self.rx_zmq_sub.close()