import socketserver
import threading
import logging
#from .iotcontrol.alarm import Alarm
#from .iotcontrol.page import Page
#from .iotcontrol.name import Name


class EchoRequestHandler(socketServer.BaseRequestHandler):
    
    def __init__(self, request, client_address, server):
        self.logger = logging.getLogger('EchoRequestHandler')
        self.logger.debug('__init__')
        SocketServer.BaseRequestHandler.__init__(self, request, client_address, server)
        return

    def setup(self):
        self.logger.debug('setup')
        return SocketServer.BaseRequestHandler.setup(self)

    def handle(self):
        self.logger.debug('handle')

        # Echo the back to the client
        data = self.request.recv(1024)
        self.logger.debug('recv()->"%s"', data)
        self.request.send(data)
        return

    def finish(self):
        self.logger.debug('finish')
        return SocketServer.BaseRequestHandler.finish(self)


class tcpConnectionThread(threading.Thread):
    """Setups and manages a connection thread to the Dash Server."""

    def __on_message(self, client, obj, msg):
        data = str(msg.payload, "utf-8").rstrip()
        logging.debug("RX: %s", data)
        data_array = data.split("\t")
        cntrl_type = data_array[1]
        reply = ""
        if cntrl_type == "CONNECT":
            reply = "\tCONNECT\t{}\t{}\t{}\n".format(self.device_name, self.device_id, self.connection_name)
        elif cntrl_type == "WHO":
            reply = self.who
        elif cntrl_type == "STATUS":
            reply = self.__make_status()
        elif cntrl_type == "CFG":
            reply = self.__make_cfg()
        else:
            key = cntrl_type + "_" + data_array[2]
            self.control_dict[key].message_rx_event(data_array[2:])
        return reply

    def __on_publish(self, client, obj, mid):
        self.watch_dog_counter = 1

    def __on_subscribe(self, client, obj, mid, granted_qos):
        logging.debug("Subscribed: %s %s", str(mid), str(granted_qos))

    def __on_log(self, client, obj, level, string):
        logging.debug(string)

    def __make_status(self):
        all_status = ""
        for key in self.control_dict.keys():
            all_status += self.control_dict[key].get_state()
        logging.debug(all_status)
        return all_status

    def __make_cfg(self):
        all_cfg = ""
        all_cfg += '\tCFG\tCFG\t{{"numPages": {}}}\n'.format(self.number_of_pages)
        for key in self.control_dict.keys():
            all_cfg += self.control_dict[key].get_cfg()
        for key in self.alarm_dict.keys():
            all_cfg += self.alarm_dict[key].get_cfg()
        logging.debug(all_cfg)
        return all_cfg

    def send_popup_message(self, title, header, message):
        """Send a popup message to the Dash server.

        Parameters
        ----------
        title : str
            Title of the message.
        header : str
            Header of the message.
        message : str
            Message body.
        """
        data = "\tMSSG\t{}\t{}\t{}\n".format(title, header, message)
        logging.debug("Tx: %s", data)
        self.mqttc.publish(self.data_topic, data)

    def send_data(self, data):
        """Send data to the Dash server.

        Parameters
        ----------
        data : str
            Data to be sent to the server
        """

        logging.debug("Tx: %s", data)
        self.mqttc.publish(self.data_topic, data)

    def add_control(self, iot_control):
        """Add a control to the connection.

        Parameters
        ----------
        iot_control : iotControl
        """
       
        #if isinstance(iot_control, Page):
        #    self.number_of_pages += 1
        iot_control.message_tx_event += self.send_data
        key = iot_control.msg_type + "_" + iot_control.control_id
        self.control_dict[key] = iot_control

    def __init__(
        self, connection_name, device_id, device_name, host='', port=5000, watch_dog=60
    ):
        """
        Arguments:
            connection_name {str} --  The connection name as advertised to iotdashboard.
            device_id {str} -- A string to uniquely identify the device connection. (In case of other connections with the same name.)
            device_name {str} -- A string for iotdashboard to use as an alias for the connection.
            host {str} -- The server name of the mqtt host.
            port {int} -- Port number to connect to.
            
        Keyword Arguments:
            watch_dog {int} -- Time in seconds between watch dog signals to iotdashboard.
                               Set to 0 to not send watchdog signal. (default: {60})
        """

        threading.Thread.__init__(self)
        self.control_dict = {}
        self.alarm_dict = {}
        self.host = host
        self.port = port
        self.tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.number_of_pages = 0
        self.watch_dog = watch_dog
        self.watch_dog_counter = 1  # If watch_dog is zero don't send anything
        self.running = True
        self.name = connection_name
        # self.name_cntrl = Name(device_name)
        self.device_name = device_name
        # self.add_control(self.name_cntrl)
        self.who = "\tWHO\n"
        self.connect = "\tCONNECT\t{}\t{}\t{}\n".format(device_name, device_id, connection_name)
        self.host = host
        self.port = port


    def __tcp_send(self, msg):
        totalsent = 0
        while totalsent < len(msg):
            sent = self.sock.send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent


    def run(self):
        # Continue the network loop, exit when an error occurs
        rc = 0
        self.watch_dog_counter = 1  # If watch_dog is zero don't send watchdog message.
        self.tcp_server.bind((self.host, self.port))
        self.tcp_server.listen(1)
        conn, addr = self.tcp_server.accept()
        print('Connection address:', addr)
        while True:
            full_msg = ''
            while True:
                msg = self.tcp_server.recv(8)
                if len(msg) <= 0:
                    break
                full_msg += msg.decode("utf-8")

            if len(full_msg) > 0:
                print(full_msg)



def main():
    tcp = tcpConnectionThread("texttcp", "1234567", "tcp")
    tcp.run()

if __name__ == "__main__":
    main()
