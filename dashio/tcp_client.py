import zmq
import threading
import logging
import time


class tcpClientThread(threading.Thread):
    """Setups and manages a client thread via TCP."""

    def __on_message(self, data):
        pass

    def _zmq_send(self, id, data):
        logging.debug("TX: " + data.rstrip())
        try:
            self.socket.send(id, zmq.SNDMORE)
            self.socket.send_string(data, zmq.NOBLOCK)
        except zmq.error.ZMQError:
            logging.debug("Sending TX Error.")
        time.sleep(0.1)

    def send_data(self, data):
        self._zmq_send(self.id, data)

    def _connect(self, url):
        self.socket.connect(url)
        self.id = self.socket.getsockopt(zmq.IDENTITY)

    def __init__(self, context=None, url="tcp://*:5000"):

        threading.Thread.__init__(self, daemon=True)
        self.context = context or zmq.Context.instance()
        self.socket = self.context.socket(zmq.STREAM)
        self.socket.set(zmq.SNDTIMEO, 5)
        self._connect("tcp://localhost:5000")

        self.id = self.socket.getsockopt(zmq.IDENTITY)
        # Initialize poll set
        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

        self.running = True

    def run(self):
        # Continue the network loop, exit when an error occurs
        id = self.socket.recv()
        self.socket.recv()
        while self.running:
            socks = dict(self.poller.poll())
            if self.socket in socks:
                id = self.socket.recv()
                message = self.socket.recv_string()
                logging.debug("RX: " + message.rstrip())
                if not message:
                    time.sleep(5)
                    self._connect("tcp://localhost:5000")

            time.sleep(0.1)

        self.socket.close()
        self.context.term()


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
            filename=logfilename, level=log_level, format="%(asctime)s, %(message)s", datefmt="%Y-%m-%d %H:%M:%S",
        )
    logging.info("==== Started ====")


def main():
    shutdown = False
    init_logging("", 2)
    tcp = tcpClientThread()
    tcp.start()
    tcp.send_data("\tWHO\n")
    tcp.send_data("\t00001\tCONNECT\n")
    tcp.send_data("\t00001\tSTATUS\n")
    tcp.send_data("\t00001\tCFG\n")

    while not shutdown:
        time.sleep(5)
        # tcp.send_data("\t00001\tSTATUS\n")


if __name__ == "__main__":
    main()
