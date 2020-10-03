
from .iotcontrol.name import Name
from .mqttconnection import mqttConnectionThread
from .tcpconnection import tcpConnectionThread

class dashDevice():
    def __init__(self, device_type, device_id, device_name) -> None:
        self.device_type = device_type
        self.device_id = device_id
        self.name_control = Name(device_name)
        self.num_mqtt_connections = 0
        self.connections = {}

    def add_mqtt_connection(self, host, port, username, password, use_ssl=False):
        self.num_mqtt_connections += 1
        connection_id = self.device_type + "_MQTT" + str(self.num_mqtt_connections)
        new_mqtt_con = mqttConnectionThread(connection_id, self.device_id, self.name_control, host, port, username, password, use_ssl)
        new_mqtt_con.start()
        new_mqtt_con.add_control(self.name_control)
        self.connections[connection_id] = new_mqtt_con

    def add_tcp_connection(self, url, port):
        self.num_mqtt_connections += 1
        connection_id = self.device_type + "_TCP:{}".format(str(port))
        new_tcp_con = tcpConnectionThread(connection_id ,self.device_id, self.name_control, url, port)
        new_tcp_con.start()
        new_tcp_con.add_control(self.name_control)
        self.connections[connection_id] = new_tcp_con

    def add_control(self, control):
        for conn in self.connections:
            self.connections[conn].add_control(control)

    def send_popup_message(self, title, header, message):
        for conn in self.connections:
            self.connections[conn].send_popup_message(title, header, message)

    def close(self):
        for conn in self.connections:
            self.connections[conn].running = False