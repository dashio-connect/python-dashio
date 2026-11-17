"""Installations (dash_docs Installations/DashIO_Installations.md): the INS messages, the role report, remote moves,
and the DashConnection's topic prefix, against a fake MQTT v5 broker, so nothing contacts the Dash server."""
import json
import os
import ssl
import tempfile
import time
import unittest

import dashio
from dashio import installation as installation_module
from dashio.device_certificates import DeviceCertificates
from dashio.installation import MOVE_FAILED, InstallationError
from test_device_certificates import PKI, FakeBroker, Recorder, sign_csr, wait_for

INST_A = "inst-3f9a01c2b7de"
INST_B = "inst-a07c55e10b42"


def certify(certificates: DeviceCertificates, pki: PKI):
    """Put the device in the certificate state CERT."""
    certificates.device_id = "DEV1"
    certificates.install(sign_csr(pki.device_ca, certificates.make_csr()))
    certificates.logged_in()
    certificates.take_status_due()
    certificates.take_changed()


class TestInstallation(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.pki = PKI(self.directory.name)
        self.path = os.path.join(self.directory.name, "certs")
        self.certificates = DeviceCertificates(self.path)
        certify(self.certificates, self.pki)
        self.installation = self.certificates.installation
        self.installation.owner = "USER"
        self.changes = []
        self.installation.callback = lambda change, installation: self.changes.append(change)

    def tearDown(self):
        self.directory.cleanup()

    def test_starts_on_the_owners_account(self):
        self.assertEqual(self.installation.prefix, "")
        self.assertEqual(self.installation.topic_prefix("USER"), "USER")
        self.assertFalse(self.installation.in_installation())
        self.assertEqual(self.installation.info(), {"action": "INFO", "prefix": "USER", "role": "", "status": ""})

    def test_values_checked(self):
        for values in (
            {"prefix": "inst-3F9A01C2B7DE", "role": "pump-1"},
            {"prefix": "USER", "role": "pump-1"},
            {"prefix": INST_A, "role": ""},
            {"prefix": INST_A, "role": "pump 1"},
            {"prefix": INST_A, "role": "r" * 33},
            {"prefix": INST_A, "role": "pump-1", "lat": 10},
            {"prefix": INST_A, "role": "pump-1", "lat": 91, "lon": 0},
            {"prefix": INST_A, "role": "pump-1", "lat": True, "lon": 0},
            {"prefix": INST_A, "role": "pump-1", "metadata": "text"},
            {"prefix": INST_A, "role": "pump-1", "metadata": {"a": "x" * 520}},
            {"prefix": "", "role": ""},
        ):
            with self.assertRaises(InstallationError, msg=values) as context:
                self.installation.set(values, by_move=False)
            self.assertEqual(context.exception.code, 421)
        with self.assertRaises(InstallationError):
            self.installation.set({"prefix": "", "role": "pump-1"}, by_move=True)

    def test_needs_cert(self):
        certificates = DeviceCertificates(os.path.join(self.directory.name, "other"))
        with self.assertRaises(InstallationError) as context:
            certificates.installation.set({"prefix": INST_A, "role": "pump-1"}, by_move=False)
        self.assertEqual(context.exception.code, 420)

    def test_joined_and_kept(self):
        self.installation.set({"prefix": INST_A, "role": "pump-1", "lat": -36.5, "lon": 174.75, "metadata": {"site": 7}}, by_move=False)
        self.assertTrue(self.installation.take_changed())
        self.assertEqual(self.changes, ["SET_BY_APP"])
        self.assertEqual(self.installation.topic_prefix("USER"), INST_A)
        self.assertTrue(self.installation.in_installation())
        self.assertEqual(self.installation.info(), {
            "action": "INFO", "prefix": INST_A, "role": "pump-1", "lat": -36.5, "lon": 174.75, "status": "", "movingFrom": "USER"
        })
        self.assertEqual(oct(os.stat(os.path.join(self.path, "installation.json")).st_mode & 0o777), "0o600")
        again = DeviceCertificates(self.path).installation
        self.assertEqual((again.prefix, again.role, again.location, again.metadata, again.moving_from), (INST_A, "pump-1", (-36.5, 174.75), {"site": 7}, ""))

    def test_role_answer_confirms_the_move(self):
        self.installation.set({"prefix": INST_A, "role": "pump-1"}, by_move=False)
        self.assertFalse(self.installation.role_answer("ASSIGNED", "pump-2"), "Not its role")
        self.assertTrue(self.installation.role_answer("TAKEN", "pump-1"))
        self.assertIsNone(self.installation.moving_from, "Confirmed, even though the role is taken")
        self.assertEqual(self.installation.status, "TAKEN")
        self.assertEqual(self.installation.role, "pump-1", "The role is kept")
        self.installation.role_answer("ASSIGNED", "pump-1")
        self.assertEqual(self.installation.info()["status"], "ASSIGNED")

    def test_refused_move_goes_back(self):
        self.installation.set({"prefix": INST_A, "role": "pump-1"}, by_move=False)
        self.installation.role_answer("ASSIGNED", "pump-1")
        self.installation.set({"prefix": INST_B, "role": "level", "moveID": "m-1"}, by_move=True)
        self.assertEqual(self.installation.moving_from, INST_A)
        self.installation.take_changed()
        self.assertTrue(self.installation.topic_refused())
        self.assertTrue(self.installation.take_changed(), "Logs in again")
        self.assertEqual((self.installation.prefix, self.installation.role, self.installation.status), (INST_A, "pump-1", MOVE_FAILED))
        self.assertEqual(self.installation.connected(), (True, True), "ERR 423 on the next connection")
        self.assertEqual(self.installation.connected(), (True, False), "Only once")
        self.assertEqual(self.changes, ["SET_BY_APP", "STATUS", "SET_BY_MOVE", "WENT_BACK"])

    def test_refused_update_goes_back_to_the_owner(self):
        self.installation.set({"prefix": INST_A, "role": "pump-1"}, by_move=False)
        self.assertTrue(self.installation.topic_refused())
        self.assertEqual(self.installation.topic_prefix("USER"), "USER")
        self.assertFalse(self.installation.in_installation())
        self.assertEqual(self.installation.info()["status"], MOVE_FAILED)

    def test_refused_with_nowhere_to_go_back_to_stays(self):
        self.installation.set({"prefix": INST_A, "role": "pump-1"}, by_move=False)
        self.installation.role_answer("ASSIGNED", "pump-1")
        self.installation.take_changed()
        self.assertFalse(self.installation.topic_refused())
        self.assertFalse(self.installation.take_changed())
        self.assertEqual((self.installation.prefix, self.installation.status), (INST_A, MOVE_FAILED))

    def test_not_installation_during_a_move_goes_back(self):
        self.installation.set({"prefix": INST_A, "role": "pump-1"}, by_move=False)
        self.installation.role_answer("ASSIGNED", "pump-1")
        self.installation.set({"prefix": INST_B, "role": "pump-1"}, by_move=True)
        self.installation.role_answer("NOT_INSTALLATION", "pump-1")
        self.assertEqual((self.installation.prefix, self.installation.status), (INST_A, MOVE_FAILED))

    def test_a_second_move_keeps_the_confirmed_prefix(self):
        self.installation.set({"prefix": INST_A, "role": "pump-1"}, by_move=False)
        self.installation.role_answer("ASSIGNED", "pump-1")
        self.installation.set({"prefix": INST_B, "role": "level"}, by_move=True)
        self.installation.set({"prefix": "inst-000000000001", "role": "level"}, by_move=False)
        self.assertEqual(self.installation.moving_from, INST_A)

    def test_repeated_move_ignored(self):
        self.installation.set({"prefix": INST_B, "role": "level"}, by_move=True)
        self.installation.take_changed()
        self.assertFalse(self.installation.set({"prefix": INST_B, "role": "level"}, by_move=True))
        self.assertFalse(self.installation.take_changed())

    def test_move_home(self):
        self.installation.set({"prefix": INST_A, "role": "pump-1", "metadata": {"a": 1}}, by_move=False)
        self.installation.role_answer("ASSIGNED", "pump-1")
        self.installation.set({"prefix": "", "role": "", "moveID": "m-2"}, by_move=True)
        self.assertEqual(self.installation.topic_prefix("USER"), "USER")
        self.assertTrue(self.installation.in_installation(), "No password until it's home")
        self.assertEqual(self.installation.role, "")
        self.assertEqual(self.installation.connected(), (False, False), "The WHO confirms it")
        self.assertFalse(self.installation.in_installation())
        self.assertIsNone(self.installation.moving_from)
        self.assertEqual(self.changes[-1], "LEFT")
        self.assertFalse(os.path.exists(os.path.join(self.path, "installation.json")))

    def test_store_failure(self):
        os.chmod(self.path, 0o500)
        try:
            with self.assertRaises(InstallationError) as context:
                self.installation.set({"prefix": INST_A, "role": "pump-1"}, by_move=False)
        finally:
            os.chmod(self.path, 0o700)
        self.assertEqual(context.exception.code, 422)
        self.assertEqual(self.installation.prefix, "", "Unchanged")


class TestInsMessages(unittest.TestCase):
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

    def send(self, message_type: str, payload: str, msg_from: bytes = b"TCP:abc") -> list:
        reply = self.device._on_message(f"\tDEV1\tDATA\tINS\t{message_type}\t{payload}\n".encode(), msg_from)
        return reply.rstrip("\n").split("\t")[4:] if reply else []

    def announced(self) -> list:
        return [message.rstrip("\n").split("\t")[4:] for topic, message in self.device.tx_zmq_pub.sent if topic == b"ANNOUNCE" and "\tINS\t" in message]

    def connect(self):
        self.certificates.connection_ready(True)
        self.device._local_command({"msgType": "send_announce", "deviceID": "DEV1", "connectionUUID": "DASH:abc", "certificateLogin": True})

    def test_info_without_certificates(self):
        device = dashio.Device("TestType", "DEV2", "Test")
        try:
            reply = device._on_message(b'\tDEV2\tDATA\tINS\tREQUEST\t{"action":"INFO"}\n', b"TCP:abc")
            self.assertEqual(json.loads(reply.split("\t")[5]), {"action": "INFO", "prefix": "", "role": "", "status": ""})
            reply = device._on_message(b'\tDEV2\tDATA\tINS\tUPDATE\t{"prefix":"inst-3f9a01c2b7de","role":"a"}\n', b"TCP:abc")
            self.assertEqual(reply, "\tDEV2\tDATA\tINS\tERR\t420\n")
        finally:
            device.close()

    def test_provisioning(self):
        update = json.dumps({"prefix": INST_A, "role": "pump-1"})
        self.assertEqual(self.send("UPDATE", update), ["ERR", "420"], "Certificate first")
        certify(self.certificates, self.pki)
        self.assertEqual(self.send("UPDATE", "{not json"), ["ERR", "421"])
        self.assertEqual(self.send("UPDATE", update, b"DASH:abc"), [], "Only on site")
        self.assertEqual(self.device.installation.prefix, "")
        self.assertEqual(self.send("UPDATE", update), ["STATUS", "SUCCESS"])
        self.assertEqual(self.device.installation.prefix, INST_A)
        reply = self.send("REQUEST", '{"action":"INFO"}')
        self.assertEqual(reply[0], "REQUEST")
        self.assertEqual(json.loads(reply[1])["role"], "pump-1")

    def test_role_reported_after_who(self):
        certify(self.certificates, self.pki)
        self.send("UPDATE", json.dumps({"prefix": INST_A, "role": "pump-1"}))
        self.connect()
        self.assertEqual(self.announced(), [["SVR_ROLE", '{"role":"pump-1"}']])
        messages = [message for topic, message in self.device.tx_zmq_pub.sent if topic == b"ANNOUNCE"]
        self.assertIn("\tWHO\t", messages[0], "WHO first")
        self.send("SVR_ROLE", '{"status":"ASSIGNED","role":"pump-1"}', b"TCP:abc")
        self.assertEqual(self.device.installation.status, "", "Only from the server")
        self.send("SVR_ROLE", '{"status":"ASSIGNED","role":"pump-1"}', b"DASH:abc")
        self.assertEqual(self.device.installation.status, "ASSIGNED")

    def test_role_reported_again_without_an_answer(self):
        retry = installation_module.ROLE_RETRY_MIN
        installation_module.ROLE_RETRY_MIN = 0.3
        try:
            certify(self.certificates, self.pki)
            self.send("UPDATE", json.dumps({"prefix": INST_A, "role": "pump-1"}))
            self.connect()
            self.assertTrue(wait_for(lambda: len(self.announced()) == 2, timeout=2))
            self.send("SVR_ROLE", '{"status":"ASSIGNED","role":"pump-1"}', b"DASH:abc")
            time.sleep(1.0)
            self.assertEqual(len(self.announced()), 2, "Stops once answered")
        finally:
            installation_module.ROLE_RETRY_MIN = retry

    def test_no_report_without_a_role_or_on_a_password_login(self):
        certify(self.certificates, self.pki)
        self.connect()
        self.send("UPDATE", json.dumps({"prefix": INST_A, "role": "pump-1"}))
        self.device._local_command({"msgType": "send_announce", "deviceID": "DEV1", "connectionUUID": "DASH:abc", "certificateLogin": False})
        self.assertEqual(self.announced(), [])

    def test_move_from_the_server_only(self):
        certify(self.certificates, self.pki)
        move = json.dumps({"prefix": INST_B, "role": "level", "moveID": "m-8812"})
        self.assertEqual(self.send("SVR_MOVE", move), [])
        self.assertEqual(self.device.installation.prefix, "")
        self.assertEqual(self.send("SVR_MOVE", move, b"DASH:abc"), [], "No reply on the old connection")
        self.assertEqual(self.device.installation.prefix, INST_B)

    def test_err_423_after_going_back(self):
        certify(self.certificates, self.pki)
        self.send("UPDATE", json.dumps({"prefix": INST_A, "role": "pump-1"}))
        self.device.installation.topic_refused()
        self.connect()
        self.assertEqual(self.announced(), [["ERR", "423"]], "Back on the owner's account, with no role")

    def test_new_dash_login_leaves(self):
        certify(self.certificates, self.pki)
        self.send("UPDATE", json.dumps({"prefix": INST_A, "role": "pump-1"}))
        changes = []
        self.device.set_installation_callback(lambda change, installation: changes.append(change))
        self.device.set_dashio_callback(lambda msg: True)
        self.device._on_message(b"\tDEV1\tDASHIO\tUSER\tPASS\n", b"TCP:abc")
        self.assertEqual(self.device.installation.prefix, "")
        self.assertEqual(changes, ["LEFT"])

    def test_callback_needs_certificates(self):
        device = dashio.Device("TestType", "DEV2", "Test")
        try:
            self.assertIsNone(device.installation)
            with self.assertRaises(ValueError):
                device.set_installation_callback(lambda change, installation: None)
        finally:
            device.close()


class TestInstallationLogin(unittest.TestCase):
    """A DashConnection logging in with the certificate under the installation's prefix, against a fake broker that
    refuses the topics the login has no rows for, and answers SVR_ROLE."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.pki = PKI(self.directory.name)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(self.pki.server_cert_file, self.pki.server_key_file)
        context.load_verify_locations(self.pki.device_ca_file)
        context.verify_mode = ssl.CERT_REQUIRED
        self.rows = {"USER", INST_A}  # The prefixes the device's login may use.
        self.broker = FakeBroker(context, on_publish=self.answer_roles, refuse=lambda topic: topic.split("/")[0] not in self.rows)
        self.password_broker = FakeBroker()
        self.certificates = DeviceCertificates(os.path.join(self.directory.name, "certs"), ca_file=self.pki.server_ca_file)
        certify(self.certificates, self.pki)
        self.device = None
        self.connection = None

    def tearDown(self):
        if self.connection is not None:
            self.connection.close()
            self.connection.join(timeout=5)
        if self.device is not None:
            self.device.close()
        self.broker.stop()
        self.password_broker.stop()
        self.directory.cleanup()

    def answer_roles(self, topic, payload):
        replies = []
        for line in payload.split("\n"):
            fields = line.split("\t")
            if len(fields) > 5 and fields[3:5] == ["INS", "SVR_ROLE"]:
                answer = {"status": "ASSIGNED", "role": json.loads(fields[5])["role"]}
                replies.append((topic.replace("/announce", "/control"), f"\t{fields[1]}\tDATA\tINS\tSVR_ROLE\t{json.dumps(answer)}\n"))
        return replies

    def start(self):
        self.device = dashio.Device("TestType", "DEV1", "Test", certificates=self.certificates)
        self.connection = dashio.DashConnection("USER", "", host="127.0.0.1", port=self.password_broker.port, use_ssl=False, cert_port=self.broker.port)
        self.connection.add_device(self.device)

    def published(self, prefix: str, text: str) -> bool:
        return any(topic.startswith(prefix + "/") and text in payload for topic, payload in self.broker.published)

    def test_logs_in_under_the_installation(self):
        self.certificates.installation.set({"prefix": INST_A, "role": "pump-1"}, by_move=False)
        self.start()
        self.assertTrue(wait_for(lambda: self.certificates.installation.status == "ASSIGNED"))
        self.assertIsNone(self.certificates.installation.moving_from, "Confirmed")
        self.assertIn((f"{INST_A}/DEV1/control", True), self.broker.subscribed)
        self.assertTrue(self.published(INST_A, "\tWHO\t"))
        self.assertTrue(self.published(INST_A, '\tSVR_ROLE\t{"role":"pump-1"}'))
        self.assertFalse(self.published("USER", "\tWHO\t"))

    def test_remote_move_and_refused_move(self):
        self.certificates.installation.set({"prefix": INST_A, "role": "pump-1"}, by_move=False)
        self.start()
        self.assertTrue(wait_for(lambda: self.certificates.installation.status == "ASSIGNED"))
        # A move the server never gave the device rows for: refused, so back to INST_A, with ERR 423 there.
        self.device._on_message(f'\tDEV1\tDATA\tINS\tSVR_MOVE\t{{"prefix":"{INST_B}","role":"level","moveID":"m-1"}}\n'.encode(), b"DASH:abc")
        self.assertTrue(wait_for(lambda: self.published(INST_A, "\tINS\tERR\t423"), timeout=15))
        self.assertIn((f"{INST_B}/DEV1/control", False), self.broker.subscribed)
        self.assertEqual(self.certificates.installation.prefix, INST_A)
        # With the rows, the move is confirmed by the role report under the new prefix.
        self.rows.add(INST_B)
        self.device._on_message(f'\tDEV1\tDATA\tINS\tSVR_MOVE\t{{"prefix":"{INST_B}","role":"level","moveID":"m-2"}}\n'.encode(), b"DASH:abc")
        self.assertTrue(wait_for(lambda: self.published(INST_B, '\tSVR_ROLE\t{"role":"level"}'), timeout=15))
        self.assertTrue(wait_for(lambda: self.certificates.installation.moving_from is None and self.certificates.installation.status == "ASSIGNED"))
        self.assertEqual(self.certificates.installation.prefix, INST_B)

    def test_move_home(self):
        self.certificates.installation.set({"prefix": INST_A, "role": "pump-1"}, by_move=False)
        self.start()
        self.assertTrue(wait_for(lambda: self.certificates.installation.status == "ASSIGNED"))
        self.device._on_message(b'\tDEV1\tDATA\tINS\tSVR_MOVE\t{"prefix":"","role":"","moveID":"m-3"}\n', b"DASH:abc")
        self.assertTrue(wait_for(lambda: self.published("USER", "\tWHO\t"), timeout=15))
        self.assertTrue(wait_for(lambda: not self.certificates.installation.in_installation()))
        self.assertEqual(self.certificates.installation.role, "")

    def test_no_password_login_in_an_installation(self):
        self.certificates.installation.set({"prefix": INST_A, "role": "pump-1"}, by_move=False)
        self.certificates._state = "PASSWORD"  # As if the certificate were lost, without a new Dash login.
        self.device = dashio.Device("TestType", "DEV1", "Test", certificates=self.certificates)
        self.connection = dashio.DashConnection("USER", "PASSWORD", host="127.0.0.1", port=self.password_broker.port, use_ssl=False, cert_port=self.broker.port)
        self.connection.add_device(self.device)
        time.sleep(2.0)
        self.assertEqual(self.password_broker.client_ids, [])
        self.assertEqual(self.certificates.state, "PASSWORD")


if __name__ == '__main__':
    unittest.main()
