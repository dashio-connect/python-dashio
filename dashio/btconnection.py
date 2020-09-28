

#!/usr/bin/python3

from gi.repository import GObject
import os
import spp_server


def my_read_cb(value):
    print('my callback: {}'.format(value))


def my_write_cb(my_server):
    cpu_temp = os.popen('vcgencmd measure_temp').readline()
    if my_server.fd_available():
        my_server.write_spp('{}'.format(float(cpu_temp.replace('temp=', '').replace("'C\n", ''))))
        print('Sending: {}'.format(float(cpu_temp.replace('temp=', '').replace("'C\n", ''))))
    return True

if __name__ == '__main__':
    my_spp_server = spp_server.SPP(my_read_cb)
    GObject.timeout_add(1000, my_write_cb, my_spp_server)
    my_spp_server.start()

