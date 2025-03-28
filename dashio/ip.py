"""
MIT License

Copyright (c) 2020 DashIO-Connect

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import socket


def get_local_ip_v4_address():
    """Find the external IP address."""
    test_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        test_s.connect(('10.255.255.255', 1))
        i_address = test_s.getsockname()[0]
    except socket.error:
        i_address = ''
    finally:
        test_s.close()
    return i_address


def get_local_ip_v6_address():
    """Find the external IP address."""
    test_s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        test_s.connect(('google.com', 8888))
        i_address = test_s.getsockname()[0]
    except socket.error:
        return ''
    return i_address


def get_local_ip_addresses():
    """Retrieve local IPv4 and IPv6 addresses."""
    ipv4 = get_local_ip_v4_address()
    ipv6 = get_local_ip_v6_address()
    return ipv4, ipv6


def is_port_in_use(ip_address, port):
    "Checks if port is in use"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as port_s:
        return port_s.connect_ex((ip_address, port)) == 0
