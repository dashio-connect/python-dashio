"""Memory Class"""
import threading
import time

import zmq
import logging


class ASControl(threading.Thread):
    """AS Template Class"""

    def send_message(self):
        """Send the message"""
        task_sender = self.context.socket(zmq.PUSH)
        task_sender.connect(self.push_url)
        task_sender.send(self.control_msg.encode())

    def close(self):
        """Close the thread"""
        self.running = False

    def __init__(self, device_id: str, control_type: str, control_id: str, push_url: str, pull_url: str,context: zmq.Context) -> None:
        threading.Thread.__init__(self, daemon=True)
        self.context = context
        self.running = True
        self.timer_type = None
        self.push_url = push_url
        self.pull_url = pull_url
        self.device_id = device_id
        self.control_type = control_type
        self.control_id = control_id
        self.control_msg = f"\t{device_id}\t{control_type}\t{control_id}\n"
        self.start()

    def run(self):

        receiver = self.context.socket(zmq.PULL)
        receiver.bind( self.pull_url)
        poller = zmq.Poller()
        poller.register(receiver, zmq.POLLIN)

        while self.running:
            try:
                socks = dict(poller.poll(15))
            except zmq.error.ContextTerminated:
                break
            if receiver in socks:
                message = receiver.recv()
                if message:
                    logging.debug("%s\t%s RX:\n%s", self.control_type, self.control_id, message.decode())
