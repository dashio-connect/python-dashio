import zmq
import threading
import logging


class tcpConnectionThread(threading.Thread):
    """Setups and manages a connection thread to iotdashboard via TCP."""

    def __init__(self, connection_id, device_id, name_control, url="tcp://*", port=5000, context=None):
        """
        Arguments:
            connection_id {str} --  The connection name as advertised to iotdashboard.
            device_id {str} -- A string to uniquely identify the device connection. (In case of other connections with the same name.)
            device_name {str} -- A string for iotdashboard to use as an alias for the connection.
            url {str} -- The address and port to set up a connection.

        Keyword Arguments:
            watch_dog {int} -- Time in seconds between watch dog signals to iotdashboard.
                               Set to 0 to not send watchdog signal. (default: {60})
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

        self.tcpsocket = self.context.socket(zmq.STREAM)

        ext_url = url + ":" + str(port)
        self.tcpsocket.bind(ext_url)
        self.tcpsocket.set(zmq.SNDTIMEO, 5)

        url_internal = "inproc://{}".format(device_id)
        self.frontend = self.context.socket(zmq.PUB)
        self.frontend.bind(url_internal)

        self.poller = zmq.Poller()
        self.poller.register(self.tcpsocket, zmq.POLLIN)
        self.poller.register(self.rx_zmq_sub, zmq.POLLIN)

        self.control_dict = {}
        self.alarm_dict = {}
        self.socket_ids = []
        self.number_of_pages = 0
        self.watch_dog = watch_dog
        self.watch_dog_counter = 1  # If watch_dog is zero don't send anything
        self.running = True
        self.connection_id = connection_id
        self.name_cntrl = name_control
        self.device_id = device_id
        self.add_control(self.name_cntrl)
        self.who = "\tWHO\n"

    def run(self):
        def __zmq_tcp_send(id, data):
            try:
                self.tcpsocket.send(id, zmq.SNDMORE)
                self.tcpsocket.send_string(data, zmq.NOBLOCK)
            except zmq.error.ZMQError as e:
                logging.debug("Sending TX Error: " + str(e))
                self.socket_ids.remove(id)

        # Continue the network loop, exit when an error occurs
        rc = 0
        id = self.tcpsocket.recv()
        self.tcpsocket.recv()  # empty data here
        while self.running:
            socks = dict(self.poller.poll())

            if self.tcpsocket in socks:
                id = self.tcpsocket.recv()
                message = self.tcpsocket.recv()
                if id not in self.socket_ids:
                    logging.debug("Added Socket ID: " + str(id))
                    self.socket_ids.append(id)
                logging.debug("TCP ID: %s, RX: %s", str(id), message.encode('utf-8').rstrip())
                if message:
                    self.tx_zmq_pub.send_multipart([self.b_connection_id, message])
                else:
                    if id in self.socket_ids:
                        logging.debug("Removed Socket ID: " + str(id))
                        self.socket_ids.remove(id)
            if self.rx_zmq_sub in socks:
                [address, msg_id, data] = self.rx_zmq_sub.recv_multipart()
                if address == b'ALL':
                    for id in self.socket_ids:
                        logging.debug("TCP ID: %s, Tx: %s", str(id), data.rstrip())
                        __zmq_tcp_send(id, data)
                elif address == self.b_connection_id:
                    if msg_id in self.socket_ids:
                        logging.debug("TCP ID: %s, Tx: %s", str(id), data.rstrip())
                        __zmq_tcp_send(msg_id, data)

        for id in self.socket_ids:
            self._zmq_send(id, "")
        self.tcpsocket.close()
        self.context.term()
