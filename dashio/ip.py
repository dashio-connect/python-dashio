import socket


def get_local_ip_address():
    test_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        test_s.connect(('10.255.255.255', 1))
        i_address = test_s.getsockname()[0]
    except Exception:
        i_address = '127.0.0.1'
    finally:
        test_s.close()
    return i_address
