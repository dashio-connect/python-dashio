"""Constants used by Device and xConnections."""
CONNECTION_PUB_URL = "inproc://DASHIO_CONN_PUB_{id}"
DEVICE_PUB_URL = "inproc://DASHIO_DVCE_PUB_{id}"
BAD_CHARS = {ord(i): None for i in '\t\n'}
