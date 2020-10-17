import zmq
import threading
import logging
import time

class tcpBridge(threading.Thread):
    """Setups and manages a connection thread to iotdashboard via TCP."""

    def __init__(self, zmq_in_url="localhost", tcp_out_url="tcp://*", tcp_out_port=5000, context=None):
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

        tx_url_internal = "tcp://{}:5555".format(zmq_in_url)
        rx_url_internal = "tcp://{}:5556".format(zmq_in_url)

        self.tx_zmq_pub = self.context.socket(zmq.PUB)
        self.tx_zmq_pub.bind(tx_url_internal)

        self.rx_zmq_sub = self.context.socket(zmq.SUB)
        self.rx_zmq_sub.bind(rx_url_internal)

        # Subscribe on ALL, and my connection
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"")

        self.tcpsocket = self.context.socket(zmq.STREAM)

        ext_url = tcp_out_url + ":" + str(tcp_out_port)
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
                self.socket_ids.remove(id)

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
                    logging.debug("ZMQ PUB: %s, TX: %s", id.hex(), message.decode('utf-8').rstrip())
                    data_l = message.split(b'\t')
                    self.tx_zmq_pub.send_multipart([data_l[1], message])
                else:
                    if id in self.socket_ids:
                        logging.debug("Removed Socket ID: " + id.hex())
                        self.socket_ids.remove(id)
            if self.rx_zmq_sub in socks:
                data = self.rx_zmq_sub.multipart()
                for id in self.socket_ids:
                        logging.debug("TCP ID: %s, Tx: %s", id.hex(), data.decode('utf-8').rstrip())
                        __zmq_tcp_send(id, data)

        for id in self.socket_ids:
            self._zmq_send(id, "")
        self.tcpsocket.close()
        self.tx_zmq_pub.close()
        self.rx_zmq_sub.close()
    


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


def main():
    init_logging("", 2)
    shutdown = False
    b = tcpBridge("*")

    while not shutdown:
        time.sleep(5)
        # tcp.send_data("\t00001\tSTATUS\n")


if __name__ == "__main__":
    main()
