"""Device certificates (dash_docs ClientCertificates/DashIO_Client_Certificates.md), tested with a local test PKI and a
fake MQTT v5 broker, so nothing contacts the Dash server."""
import base64
import datetime
import json
import os
import socket
import ssl
import tempfile
import threading
import time
import unittest

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

import dashio
from dashio import device_certificates
from dashio.device_certificates import CERT, PASSWORD, PENDING, CertificateError, DeviceCertificates
from dashio.iotcontrol.enums import ConnectionState

DAY = datetime.timedelta(days=1)


def make_ca(name: str):
    key = ec.generate_private_key(ec.SECP256R1())
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, name)])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder().subject_name(subject).issuer_name(subject).public_key(key.public_key())
        .serial_number(x509.random_serial_number()).not_valid_before(now - DAY).not_valid_after(now + 3650 * DAY)
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(x509.KeyUsage(False, False, False, False, False, True, True, False, False), critical=True)
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False)
        .sign(key, hashes.SHA256())
    )
    return key, cert


def issue(ca, public_key, common_name: str, days: float = 1826, server: bool = False) -> x509.Certificate:
    ca_key, ca_cert = ca
    now = datetime.datetime.now(datetime.timezone.utc)
    builder = (
        x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)]))
        .issuer_name(ca_cert.subject).public_key(public_key).serial_number(x509.random_serial_number())
        .not_valid_before(now - DAY).not_valid_after(now + days * DAY)
        .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), critical=False)
    )
    if server:
        import ipaddress
        builder = builder.add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]), critical=False)
    return builder.sign(ca_key, hashes.SHA256())


def sign_csr(ca, csr_b64: str, days: float = 1826) -> str:
    csr = x509.load_der_x509_csr(base64.b64decode(csr_b64))
    assert csr.is_signature_valid
    cert = issue(ca, csr.public_key(), csr.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value, days)
    return base64.b64encode(cert.public_bytes(serialization.Encoding.DER)).decode()


def pem(cert: x509.Certificate) -> bytes:
    return cert.public_bytes(serialization.Encoding.PEM)


class Recorder:
    """Stands in for the device's zmq PUB socket."""

    def __init__(self):
        self.sent = []

    def send_multipart(self, parts):
        self.sent.append((parts[0], parts[1].decode()))

    def close(self):
        pass


class PKI:
    """A test Device CA, and a Server CA with a certificate for 127.0.0.1."""

    def __init__(self, directory: str):
        self.device_ca = make_ca("Test Device CA")
        self.server_ca = make_ca("Test Server CA")
        server_key = ec.generate_private_key(ec.SECP256R1())
        server_cert = issue(self.server_ca, server_key.public_key(), "127.0.0.1", server=True)
        self.server_ca_file = os.path.join(directory, "server-ca.pem")
        self.device_ca_file = os.path.join(directory, "device-ca.pem")
        self.server_cert_file = os.path.join(directory, "server.pem")
        self.server_key_file = os.path.join(directory, "server-key.pem")
        with open(self.server_ca_file, "wb") as file:
            file.write(pem(self.server_ca[1]))
        with open(self.device_ca_file, "wb") as file:
            file.write(pem(self.device_ca[1]))
        with open(self.server_cert_file, "wb") as file:
            file.write(pem(server_cert))
        with open(self.server_key_file, "wb") as file:
            file.write(server_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))


class TestStore(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.pki = PKI(self.directory.name)
        self.states = []
        self.certificates = self.make_store()

    def tearDown(self):
        self.directory.cleanup()

    def make_store(self):
        certificates = DeviceCertificates(os.path.join(self.directory.name, "certs"), state_callback=self.states.append)
        certificates.device_id = "DEV1"
        return certificates

    def install_first(self):
        self.certificates.install(sign_csr(self.pki.device_ca, self.certificates.make_csr()))

    def test_csr(self):
        csr = x509.load_der_x509_csr(base64.b64decode(self.certificates.make_csr()))
        self.assertTrue(csr.is_signature_valid)
        self.assertEqual(csr.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value, "d-DEV1")
        self.assertIsInstance(csr.public_key().curve, ec.SECP256R1)
        again = x509.load_der_x509_csr(base64.b64decode(self.certificates.make_csr()))
        self.assertEqual(again.public_key(), csr.public_key(), "The outstanding request's key is kept")
        new = x509.load_der_x509_csr(base64.b64decode(self.certificates.make_csr(new_key=True)))
        self.assertNotEqual(new.public_key(), csr.public_key())
        with self.assertRaises(CertificateError) as raised:
            self.certificates.make_csr("EC-P384")
        self.assertEqual(raised.exception.code, 400)

    def test_key_readable_only_by_owner(self):
        self.certificates.make_csr()
        mode = os.stat(os.path.join(self.certificates.path, "new_key.pem")).st_mode & 0o777
        self.assertEqual(mode, 0o600)

    def test_install(self):
        self.assertEqual(self.certificates.state, PASSWORD)
        self.install_first()
        self.assertEqual(self.certificates.state, PENDING)
        self.assertEqual(self.states, [PENDING])
        info = self.certificates.info()
        self.assertEqual(info["state"], PENDING)
        self.assertEqual(info["keyType"], "EC-P256")
        self.assertEqual(info["lastError"], 0)
        self.assertGreater(info["notAfter"], time.time() + 1800 * 86400)
        self.assertRegex(info["serial"], "^[0-9a-f]+$")
        self.assertTrue(self.certificates.take_changed())
        self.assertTrue(self.certificates.use_certificate())
        self.assertTrue(self.certificates.needs_check())

    def test_install_checks(self):
        csr = self.certificates.make_csr()
        other_key = ec.generate_private_key(ec.SECP256R1())
        wrong_key = base64.b64encode(issue(self.pki.device_ca, other_key.public_key(), "d-DEV1").public_bytes(serialization.Encoding.DER)).decode()
        wrong_name = base64.b64encode(issue(self.pki.device_ca, x509.load_der_x509_csr(base64.b64decode(csr)).public_key(), "d-DEV2").public_bytes(serialization.Encoding.DER)).decode()
        for certificate in (wrong_key, wrong_name, "not base64!", base64.b64encode(b"junk").decode()):
            with self.assertRaises(CertificateError) as raised:
                self.certificates.install(certificate)
            self.assertEqual(raised.exception.code, 403)
        self.assertEqual(self.certificates.state, PASSWORD)

    def test_first_login_moves_to_cert(self):
        self.install_first()
        self.certificates.logged_in()
        self.assertEqual(self.certificates.state, CERT)
        self.assertEqual(self.states, [PENDING, CERT])
        self.assertTrue(self.certificates.take_status_due())
        self.assertFalse(self.certificates.needs_check())

    def test_refused_while_pending_uses_the_password_for_an_hour(self):
        self.install_first()
        self.certificates.use_certificate()
        self.certificates.refused()
        self.assertFalse(self.certificates.use_certificate())
        self.assertEqual(self.certificates.info()["lastError"], 420)
        self.assertTrue(self.certificates.take_status_due())
        self.assertFalse(self.certificates.pending_retry_due())
        self.certificates._pending_retry_at = time.monotonic() - 1
        self.assertTrue(self.certificates.pending_retry_due())
        self.assertTrue(self.certificates.use_certificate())
        self.assertFalse(self.certificates.pending_retry_due(), "Trying it again")

    def test_refused_in_cert_recorded(self):
        self.install_first()
        self.certificates.logged_in()
        self.certificates.login_refused()
        self.assertEqual(self.certificates.state, CERT, "Never back to the password by itself")
        self.assertEqual(self.certificates.info()["lastError"], 420)
        self.assertFalse(self.certificates.needs_check())
        self.certificates.logged_in()
        self.assertEqual(self.certificates.info()["lastError"], 0)

    def test_state_kept(self):
        self.install_first()
        self.certificates.logged_in()
        again = self.make_store()
        self.assertEqual(again.state, CERT)
        self.assertEqual(again.info()["serial"], self.certificates.info()["serial"])

    def renew(self):
        self.install_first()
        self.certificates.logged_in()
        self.first_serial = self.certificates.info()["serial"]
        csr = self.certificates.make_csr(new_key=True)
        self.certificates.install(sign_csr(self.pki.device_ca, csr), from_server=True)

    def test_renewal_used_once_it_works(self):
        self.renew()
        self.assertEqual(self.certificates.state, CERT)
        self.assertTrue(self.certificates.needs_check())
        self.assertNotEqual(self.certificates.info()["serial"], self.first_serial)
        self.certificates.logged_in()
        self.assertFalse(self.certificates.needs_check())
        self.assertTrue(self.certificates.take_status_due(), "SVR_STATUS with the new serial has the server revoke the old one")
        self.assertFalse(os.path.exists(os.path.join(self.certificates.path, "previous_cert.pem")))

    def test_refused_renewal_rolls_back(self):
        self.renew()
        self.certificates.refused()
        self.assertEqual(self.certificates.state, CERT)
        self.assertEqual(self.certificates.info()["serial"], self.first_serial)
        self.assertFalse(self.certificates.needs_check())

    def test_renewal_due(self):
        csr = self.certificates.make_csr()
        self.certificates.install(sign_csr(self.pki.device_ca, csr, days=300))
        self.assertFalse(self.certificates.renewal_due(), "Not before CERT")
        self.certificates.logged_in()
        self.assertTrue(self.certificates.renewal_due())
        self.certificates.renewal_requested()
        self.assertFalse(self.certificates.renewal_due(), "At most once a day")
        self.certificates.install(sign_csr(self.pki.device_ca, self.certificates.make_csr(new_key=True)), from_server=True)
        self.certificates.logged_in()
        long = self.make_store()
        long.install(sign_csr(self.pki.device_ca, long.make_csr(new_key=True)))
        long.logged_in()
        self.assertFalse(long.renewal_due(), "Not before the last year")

    def test_new_dash_login_resets(self):
        self.install_first()
        self.certificates.logged_in()
        self.certificates.take_changed()
        self.certificates.reset()
        self.assertEqual(self.certificates.state, PASSWORD)
        self.assertEqual(self.states[-1], PASSWORD)
        self.assertTrue(self.certificates.take_changed())
        self.assertNotIn("keyType", self.certificates.info())
        self.assertFalse(os.path.exists(self.certificates.cert_path))

    def test_bundled_server_ca(self):
        certificates = DeviceCertificates(os.path.join(self.directory.name, "other"))
        with open(certificates.ca_path, "rb") as file:
            ca = x509.load_pem_x509_certificate(file.read())
        self.assertEqual(ca.fingerprint(hashes.SHA256()).hex().upper(), "F43B751665F9ED7418EC70184ECF974A8E0F07D8CB7DC9D65B56937576A2488B")


class TestCrtMessages(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.pki = PKI(self.directory.name)
        self.certificates = DeviceCertificates(os.path.join(self.directory.name, "certs"))
        self.device = dashio.Device("TestType", "DEV1", "Test", certificates=self.certificates)
        self.device.tx_zmq_pub.close()
        self.device.tx_zmq_pub = Recorder()

    def tearDown(self):
        self.device.close()
        time.sleep(0.2)
        self.directory.cleanup()

    def request(self, *fields: str) -> list:
        reply = self.device._on_message(("\tDEV1\tDATA\tCRT\t" + "\t".join(fields) + "\n").encode(), b"TCP:abc")
        return reply.rstrip("\n").split("\t")

    def announced(self) -> list:
        return [message for topic, message in self.device.tx_zmq_pub.sent if topic == b"ANNOUNCE"]

    def test_info_without_certificates(self):
        device = dashio.Device("TestType", "DEV2", "Test")
        try:
            reply = device._on_message(b'\tDEV2\tDATA\tCRT\tREQUEST\t{"action":"INFO"}\n', b"TCP:abc")
            self.assertEqual(json.loads(reply.split("\t")[5]), {"action": "INFO", "state": "PASSWORD", "keyTypes": []})
            reply = device._on_message(b'\tDEV2\tDATA\tCRT\tREQUEST\t{"action":"CSR"}\n', b"TCP:abc")
            self.assertEqual(reply, "\tDEV2\tDATA\tCRT\tERR\t400\n")
        finally:
            device.close()

    def test_provisioning_from_the_app(self):
        fields = self.request("REQUEST", '{"action":"INFO"}')
        self.assertEqual(fields[1:5], ["DEV1", "DATA", "CRT", "REQUEST"])
        self.assertEqual(json.loads(fields[5]), {"action": "INFO", "state": "PASSWORD", "keyTypes": ["EC-P256", "RSA-2048"], "lastError": 0})
        fields = self.request("REQUEST", '{"action":"CSR","keyType":"EC-P256"}')
        self.assertEqual(json.loads(fields[5]), {"action": "CSR", "keyType": "EC-P256"})
        certificate = sign_csr(self.pki.device_ca, fields[6])
        ca = base64.b64encode(self.pki.server_ca[1].public_bytes(serialization.Encoding.DER)).decode()
        fields = self.request("UPDATE", json.dumps({"caCert": ca}), certificate)
        self.assertEqual(fields[4:], ["STATUS", "SUCCESS"])
        self.assertEqual(self.certificates.state, PENDING)
        with open(self.certificates.ca_path, "rb") as file:
            self.assertEqual(x509.load_pem_x509_certificate(file.read()), self.pki.server_ca[1], "caCert is installed")
        info = json.loads(self.request("REQUEST", '{"action":"INFO"}')[5])
        self.assertEqual(info["state"], PENDING)
        self.assertEqual(info["keyType"], "EC-P256")

    def test_update_refused(self):
        self.assertEqual(self.request("UPDATE", "{}", base64.b64encode(b"junk").decode())[4:], ["ERR", "403"])

    def connect(self, certificate_login=False):
        self.certificates.connection_ready(certificate_login)
        time.sleep(0.3)  # The device thread polls.

    def test_first_certificate_from_the_server(self):
        self.connect()
        requests = self.announced()
        self.assertEqual(len(requests), 1)
        fields = requests[0].rstrip("\n").split("\t")
        self.assertEqual(fields[1:5], ["DEV1", "DATA", "CRT", "SVR_CSR"])
        self.assertEqual(json.loads(fields[5]), {"keyType": "EC-P256", "renew": False, "needCA": False})
        certificate = sign_csr(self.pki.device_ca, fields[6])
        self.device._on_message(f'\tDEV1\tDATA\tCRT\tSVR_CRT\t{{"serial":"1","notAfter":1}}\t{certificate}\n'.encode(), b"DASH:abc")
        self.assertEqual(self.certificates.state, PENDING)

    def test_no_request_without_auto_issue(self):
        self.certificates.auto_issue = False
        self.connect()
        self.assertEqual(self.announced(), [])

    def test_asks_again_without_a_reply(self):
        timeout = device_certificates.REQUEST_TIMEOUT
        device_certificates.REQUEST_TIMEOUT = 0.4
        try:
            self.connect()  # Asks at once, then after 0.4 seconds, then after 0.8 more.
            time.sleep(0.4)
            self.assertEqual(len(self.announced()), 2)
            self.assertEqual(self.announced()[0], self.announced()[1], "The same request")
        finally:
            device_certificates.REQUEST_TIMEOUT = timeout

    def test_refused_stops_until_the_next_connection(self):
        timeout = device_certificates.REQUEST_TIMEOUT
        device_certificates.REQUEST_TIMEOUT = 0.6
        try:
            self.connect()
            self.device._on_message(b"\tDEV1\tDATA\tCRT\tERR\t410\n", b"DASH:abc")
            time.sleep(0.8)
            self.assertEqual(len(self.announced()), 1)
            self.connect()
            self.assertEqual(len(self.announced()), 2)
        finally:
            device_certificates.REQUEST_TIMEOUT = timeout

    def test_status_reported(self):
        self.certificates.install(sign_csr(self.pki.device_ca, self.certificates.make_csr()))
        self.certificates.logged_in()
        self.connect(certificate_login=True)
        reports = self.announced()
        self.assertEqual(len(reports), 1)
        fields = reports[0].rstrip("\n").split("\t")
        self.assertEqual(fields[4], "SVR_STATUS")
        status = json.loads(fields[5])
        self.assertEqual(status["state"], CERT)
        self.assertNotIn("action", status)
        self.connect(certificate_login=True)
        self.assertEqual(len(self.announced()), 1, "Only when it changes")

    def test_renewal_requested_in_the_last_year(self):
        self.certificates.install(sign_csr(self.pki.device_ca, self.certificates.make_csr(), days=300))
        self.certificates.logged_in()
        self.certificates.take_status_due()
        self.connect(certificate_login=True)
        fields = self.announced()[0].rstrip("\n").split("\t")
        self.assertEqual(fields[4], "SVR_CSR")
        self.assertTrue(json.loads(fields[5])["renew"])
        self.device._on_message(f'\tDEV1\tDATA\tCRT\tSVR_CRT\t{{}}\t{sign_csr(self.pki.device_ca, fields[6])}\n'.encode(), b"DASH:abc")
        self.assertTrue(self.certificates.needs_check(), "The renewed certificate is tried on the next login")

    def test_new_dash_login_resets(self):
        self.device.set_dashio_callback(lambda msg: True)
        self.certificates.install(sign_csr(self.pki.device_ca, self.certificates.make_csr()))
        self.device._on_message(b"\tDEV1\tDASHIO\tUSER\tPASS\n", b"TCP:abc")
        self.assertEqual(self.certificates.state, PASSWORD)


def read_packet(sock):
    header = sock.recv(1)
    if not header:
        raise ConnectionError
    length, shift = 0, 0
    while True:
        byte = sock.recv(1)[0]
        length += (byte & 0x7F) << shift
        shift += 7
        if byte < 0x80:
            break
    body = b""
    while len(body) < length:
        chunk = sock.recv(length - len(body))
        if not chunk:
            raise ConnectionError
        body += chunk
    return header[0], body


def encode_length(length: int) -> bytes:
    out = b""
    while True:
        byte = length % 128
        length //= 128
        out += bytes([byte | 0x80 if length else byte])
        if not length:
            return out


def read_varint(body: bytes, index: int):
    value, shift = 0, 0
    while True:
        byte = body[index]
        index += 1
        value += (byte & 0x7F) << shift
        shift += 7
        if byte < 0x80:
            return value, index


class FakeBroker(threading.Thread):
    """Just enough of an MQTT v5 broker: accepts every login, answers SUBSCRIBE and QoS 1 PUBLISH, and records them.
    With a TLS context, it requires a client certificate from the test Device CA."""

    def __init__(self, tls_context=None, on_publish=None):
        super().__init__(daemon=True)
        self.server = socket.socket()
        self.server.bind(("127.0.0.1", 0))
        self.server.listen()
        self.server.settimeout(0.2)
        self.port = self.server.getsockname()[1]
        self.tls_context = tls_context
        self.on_publish = on_publish
        self.client_ids = []
        self.published = []
        self.running = True
        self.start()

    def run(self):
        while self.running:
            try:
                client, _ = self.server.accept()
            except socket.timeout:
                continue
            threading.Thread(target=self.serve, args=(client,), daemon=True).start()

    def serve(self, client):
        try:
            if self.tls_context is not None:
                client = self.tls_context.wrap_socket(client, server_side=True)
            client.settimeout(30)
            while self.running:
                packet_type, body = read_packet(client)
                kind = packet_type >> 4
                if kind == 1:  # CONNECT
                    index = 2 + 4 + 1 + 1 + 2
                    properties, index = read_varint(body, index)
                    index += properties
                    id_length = int.from_bytes(body[index:index + 2], "big")
                    self.client_ids.append(body[index + 2:index + 2 + id_length].decode())
                    client.sendall(bytes([0x20, 0x03, 0x00, 0x00, 0x00]))
                elif kind == 8:  # SUBSCRIBE
                    client.sendall(bytes([0x90, 0x04]) + body[:2] + bytes([0x00, 0x00]))
                elif kind == 3:  # PUBLISH
                    qos = (packet_type >> 1) & 3
                    topic_length = int.from_bytes(body[:2], "big")
                    topic = body[2:2 + topic_length].decode()
                    index = 2 + topic_length
                    if qos:
                        packet_id = body[index:index + 2]
                        index += 2
                        client.sendall(bytes([0x40, 0x02]) + packet_id)
                    properties, index = read_varint(body, index)
                    payload = body[index + properties:].decode()
                    self.published.append((topic, payload))
                    if self.on_publish is not None:
                        for topic_out, payload_out in self.on_publish(topic, payload):
                            self.send(client, topic_out, payload_out)
                elif kind == 12:  # PINGREQ
                    client.sendall(bytes([0xD0, 0x00]))
                elif kind == 14:  # DISCONNECT
                    break
        except (ConnectionError, OSError, IndexError):
            pass
        finally:
            client.close()

    @staticmethod
    def send(client, topic: str, payload: str):
        body = len(topic).to_bytes(2, "big") + topic.encode() + b"\x00" + payload.encode()
        client.sendall(bytes([0x30]) + encode_length(len(body)) + body)

    def stop(self):
        self.running = False
        self.join()
        self.server.close()


def wait_for(condition, timeout=10.0) -> bool:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if condition():
            return True
        time.sleep(0.05)
    return False


class TestCertificateLogin(unittest.TestCase):
    """DashConnection with a device certificate, against fake brokers for the password and certificate logins."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.pki = PKI(self.directory.name)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(self.pki.server_cert_file, self.pki.server_key_file)
        context.load_verify_locations(self.pki.device_ca_file)
        context.verify_mode = ssl.CERT_REQUIRED
        self.cert_broker = FakeBroker(context)
        self.password_broker = FakeBroker(on_publish=self.sign_requests)
        self.states = []
        self.certificates = DeviceCertificates(os.path.join(self.directory.name, "certs"), ca_file=self.pki.server_ca_file, state_callback=self.states.append)
        self.device = None
        self.connection = None

    def tearDown(self):
        if self.connection is not None:
            self.connection.close()
            self.connection.join(timeout=5)
        if self.device is not None:
            self.device.close()
        self.cert_broker.stop()
        self.password_broker.stop()
        self.directory.cleanup()

    def sign_requests(self, topic, payload):
        """The Dash server's part: answer SVR_CSR with SVR_CRT on the control topic."""
        replies = []
        for line in payload.split("\n"):
            fields = line.split("\t")
            if len(fields) > 6 and fields[4] == "SVR_CSR":
                certificate = sign_csr(self.pki.device_ca, fields[6])
                replies.append((topic.replace("/announce", "/control"), f'\t{fields[1]}\tDATA\tCRT\tSVR_CRT\t{{"serial":"1","notAfter":1}}\t{certificate}\n'))
        return replies

    def start(self, password="PASSWORD"):
        self.device = dashio.Device("TestType", "DEV1", "Test", certificates=self.certificates)
        self.connection = dashio.DashConnection(
            "USER", password, host="127.0.0.1", port=self.password_broker.port, use_ssl=False, cert_port=self.cert_broker.port
        )
        self.connection.add_device(self.device)

    def install(self, ca):
        self.certificates.device_id = "DEV1"
        self.certificates.install(sign_csr(ca, self.certificates.make_csr()))
        self.certificates.take_changed()

    def statuses(self, broker):
        return [json.loads(line.split("\t")[5]) for _, payload in broker.published for line in payload.split("\n") if "\tSVR_STATUS\t" in line]

    def test_pending_certificate_logs_in_on_the_certificate_port(self):
        self.install(self.pki.device_ca)
        self.start()
        self.assertTrue(wait_for(lambda: self.certificates.state == CERT), "CERT after the first login")
        self.assertEqual(self.cert_broker.client_ids, ["d-DEV1"])
        self.assertEqual(self.password_broker.client_ids, [])
        self.assertEqual(self.connection.password, "", "The password is erased")
        self.assertEqual(self.states, [PENDING, CERT])
        self.assertTrue(wait_for(lambda: self.statuses(self.cert_broker)), "SVR_STATUS over the certificate login")
        self.assertEqual(self.statuses(self.cert_broker)[0]["state"], CERT)
        self.assertTrue(any(topic == "USER/DEV1/announce" and "\tWHO\t" in payload for topic, payload in self.cert_broker.published))

    def test_refused_pending_certificate_falls_back_to_the_password(self):
        self.install(make_ca("Another CA"))
        self.start()
        self.assertTrue(wait_for(lambda: self.password_broker.client_ids), "Logs in with the password")
        self.assertFalse(self.password_broker.client_ids[0].startswith("d-"))
        self.assertEqual(self.certificates.state, PENDING)
        self.assertTrue(wait_for(lambda: self.statuses(self.password_broker)), "Reports the error over the password")
        self.assertEqual(self.statuses(self.password_broker)[0]["lastError"], 420)
        self.assertEqual(self.cert_broker.client_ids, [], "The refused certificate isn't used to log in")

    def test_first_certificate_from_the_server(self):
        self.start()
        self.assertTrue(wait_for(lambda: self.certificates.state == CERT, timeout=15), "PASSWORD, then PENDING, then CERT")
        self.assertEqual(self.states, [PENDING, CERT])
        self.assertEqual(self.cert_broker.client_ids, ["d-DEV1"])
        self.assertTrue(wait_for(lambda: self.connection.connection_state == ConnectionState.CONNECTED))

    def test_cert_logs_in_without_a_password(self):
        self.install(self.pki.device_ca)
        self.certificates.logged_in()
        self.certificates.take_status_due()
        self.start(password="")
        self.assertTrue(wait_for(lambda: self.cert_broker.client_ids))
        self.assertEqual(self.password_broker.client_ids, [])

    def test_one_device_per_connection(self):
        self.start()
        other = dashio.Device("TestType", "DEV2", "Test")
        try:
            with self.assertRaises(ValueError):
                self.connection.add_device(other)
        finally:
            other.close()


if __name__ == '__main__':
    unittest.main()
