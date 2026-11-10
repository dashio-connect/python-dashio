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

Device certificates: a device logs in to the Dash server with its own client certificate, on port 8885, instead of
its owner's password. The spec is dash_docs ClientCertificates/DashIO_Client_Certificates.md.
"""
from __future__ import annotations

import base64
import json
import logging
import os
import threading
import time
from importlib import resources
from pathlib import Path
from typing import Callable

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.x509.oid import NameOID

logger = logging.getLogger(__name__)

PASSWORD = "PASSWORD"  # No certificate: log in with the owner's password.
PENDING = "PENDING"  # A certificate that hasn't been used yet: falls back to the password if it's refused.
CERT = "CERT"  # A certificate that has worked: the password has been erased.

KEY_TYPES = ["EC-P256", "RSA-2048"]

CRT_NOT_SUPPORTED = 400
CRT_KEYGEN_ERR = 401
CRT_CSR_ERR = 402
CRT_INVALID = 403
CRT_STORE_ERR = 404
CRT_REFUSED = 410
CRT_NOT_DUE = 411
CRT_RATE_LIMIT = 412
CRT_SERVER_ERR = 413
CRT_HANDSHAKE_REFUSED = 420
CRT_EXPIRED = 421

RENEWAL_WINDOW = 365 * 24 * 3600  # A certificate is renewed in its last year.
RENEWAL_INTERVAL = 24 * 3600  # At most one renewal request a day.
PENDING_RETRY = 3600  # After a PENDING certificate is refused, the password is used for at least this long.
REQUEST_TIMEOUT = 60.0  # Seconds to wait for the server's reply to SVR_CSR before asking again.
REQUEST_MAX_WAIT = 3600.0  # The wait doubles after each unanswered request, up to this.

KEY_FILE = "key.pem"
CERT_FILE = "cert.pem"
CA_FILE = "ca.pem"
NEW_KEY_FILE = "new_key.pem"  # The key of an outstanding request, until its certificate is installed.
PREVIOUS_KEY_FILE = "previous_key.pem"  # A renewed certificate's predecessor, until the new one has worked.
PREVIOUS_CERT_FILE = "previous_cert.pem"
STATE_FILE = "state.json"


class CertificateError(Exception):
    """A CRT error, with its code."""

    def __init__(self, code: int, message: str = ""):
        super().__init__(message or str(code))
        self.code = code


def _key_type(key) -> str:
    if isinstance(key, ec.EllipticCurvePrivateKey) and isinstance(key.curve, ec.SECP256R1):
        return "EC-P256"
    if isinstance(key, rsa.RSAPrivateKey) and key.key_size == 2048:
        return "RSA-2048"
    return ""


def _public_der(key) -> bytes:
    return key.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)


def _b64decode(text: str) -> bytes:
    return base64.b64decode(text.strip(), validate=True)


def bundled_server_ca() -> str:
    """The path of the DashIO Server CA certificate included with the library."""
    return str(resources.files("dashio").joinpath("certs", "dashio-server-ca.crt"))


class DeviceCertificates:
    """A device's key and certificate for logging in to the Dash server on port 8885, kept in a directory.

    Give it to the Device, e.g. Device(..., certificates=DeviceCertificates("certs")), and add the device to a
    DashConnection, which then logs in with the certificate. A DashConnection with certificates has one device.

    The device starts in the state PASSWORD, logging in with its owner's password. It gets a certificate from the
    Dash server, which signs it at once for a device on the account it's logged in as (auto_issue), or from the
    Dash app. It's then PENDING: it logs in on port 8885 with the certificate, falling back to the password if the
    server refuses it. Once it has logged in with it, it's CERT: the password is no longer used, and the state
    callback is called so the program can erase its stored copy. A new Dash login from the Dash app returns it to
    PASSWORD. The certificate is renewed in its last year.

    Parameters
    ----------
    path : str
        The directory for the key, the certificates and the state. It's made if needed, readable only by its owner.
        The private key never leaves it.
    auto_issue : bool, optional
        Ask the Dash server for a certificate when logged in with the password. Defaults to True.
    ca_file : str, optional
        The CA that signs the server's certificate on port 8885. Defaults to the DashIO Server CA, included with
        the library, or the one the Dash app installed with the certificate.
    state_callback : Callable[[str], None], optional
        Called with the new state, "PASSWORD", "PENDING" or "CERT", when it changes. On CERT, erase the stored Dash
        password: a device that kept it would fall back to it when its certificate is revoked.
    key_passphrase : str | bytes | Callable[[], str | bytes], optional
        Keep the private key encrypted with this passphrase. A function is called each time the key is loaded, so
        the passphrase can come from somewhere other than the device's disk, e.g. a systemd credential. A trailing
        newline is ignored. A key stored unencrypted is encrypted when it's first loaded with a passphrase. Without
        the passphrase the key can't be used, and the device needs a new certificate. Defaults to None: the key is
        protected only by the file's permissions.
    """

    def __init__(
        self,
        path: str,
        auto_issue: bool = True,
        ca_file: str | None = None,
        state_callback: Callable[[str], None] | None = None,
        key_passphrase: str | bytes | Callable[[], str | bytes] | None = None
    ):
        self.path = Path(path)
        self.path.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.auto_issue = auto_issue
        self._ca_file = ca_file
        self.state_callback = state_callback
        self._key_passphrase = key_passphrase
        self.device_id = ""  # Set by the Device.
        self._lock = threading.RLock()
        self._changed = False  # The key or certificate changed, so the connection logs in again.
        self._pending_retry_at = 0.0  # PENDING: when to try the certificate again after it was refused.
        self._connection = (0, False)  # (count of connections, logged in with the certificate)
        state = {}
        try:
            state = json.loads((self.path / STATE_FILE).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
        self._state = state.get("state", PASSWORD) if state.get("state") in (PASSWORD, PENDING, CERT) else PASSWORD
        self._last_error = int(state.get("lastError", 0))
        self._unproven = bool(state.get("unproven", False))  # A renewed certificate not yet used to log in.
        self._status_due = bool(state.get("statusDue", False))  # SVR_STATUS to send when next connected.
        self._last_renewal_request = float(state.get("lastRenewalRequest", 0))
        if self._state != PASSWORD and not (self.path / CERT_FILE).exists():
            self._state = PASSWORD

    # Files

    def _file(self, name: str) -> Path:
        return self.path / name

    def _write(self, name: str, data: bytes):
        temporary = self._file(name + ".tmp")
        with open(os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "wb") as file:
            file.write(data)
        os.replace(temporary, self._file(name))

    def _remove(self, *names: str):
        for name in names:
            try:
                self._file(name).unlink()
            except FileNotFoundError:
                pass

    def _save_state(self):
        state = {
            "state": self._state, "lastError": self._last_error, "unproven": self._unproven,
            "statusDue": self._status_due, "lastRenewalRequest": self._last_renewal_request
        }
        self._write(STATE_FILE, json.dumps(state).encode())

    def key_passphrase(self) -> bytes | None:
        """The key's passphrase, or None if the key isn't encrypted. Raises whatever the passphrase function raises."""
        passphrase = self._key_passphrase() if callable(self._key_passphrase) else self._key_passphrase
        if passphrase is None:
            return None
        if isinstance(passphrase, str):
            passphrase = passphrase.encode()
        passphrase = passphrase.rstrip(b"\r\n")
        if not passphrase:
            raise ValueError("The key passphrase is empty")
        return passphrase

    def _key_bytes(self, key) -> bytes:
        """The key as PEM, encrypted with the passphrase if there is one."""
        passphrase = self.key_passphrase()
        encryption = serialization.BestAvailableEncryption(passphrase) if passphrase else serialization.NoEncryption()
        return key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, encryption)

    def _load_key(self, name: str):
        try:
            data = self._file(name).read_bytes()
        except OSError:
            return None
        encrypted = data.startswith(b"-----BEGIN ENCRYPTED PRIVATE KEY-----")
        try:
            passphrase = self.key_passphrase()
            if encrypted and passphrase is None:
                raise ValueError("the key is encrypted, and there's no key_passphrase")
            key = serialization.load_pem_private_key(data, password=passphrase if encrypted else None)
        except Exception as error:  # pylint: disable=broad-except
            logger.error("The device key %s can't be loaded: %s", name, error)
            return None
        if passphrase is not None and not encrypted:
            self._write(name, self._key_bytes(key))  # Encrypt a key stored before there was a passphrase.
        return key

    def _load_cert(self, name: str = CERT_FILE) -> x509.Certificate | None:
        try:
            return x509.load_pem_x509_certificate(self._file(name).read_bytes())
        except (OSError, ValueError):
            return None

    @property
    def key_path(self) -> str:
        return str(self._file(KEY_FILE))

    @property
    def cert_path(self) -> str:
        return str(self._file(CERT_FILE))

    @property
    def ca_path(self) -> str:
        """The CA to check the server's certificate on port 8885 against."""
        if self._ca_file:
            return self._ca_file
        if self._file(CA_FILE).exists():
            return str(self._file(CA_FILE))
        return bundled_server_ca()

    # State

    @property
    def state(self) -> str:
        """PASSWORD, PENDING or CERT."""
        return self._state

    @property
    def last_error(self) -> int:
        return self._last_error

    def _set_state(self, state: str) -> bool:
        changed = state != self._state
        self._state = state
        self._save_state()
        return changed

    def _notify(self, state: str):
        logger.info("Certificate state %s", state)
        if self.state_callback is not None:
            try:
                self.state_callback(state)
            except Exception:  # pylint: disable=broad-except
                logger.exception("Certificate state callback")

    def info(self) -> dict:
        """The device's certificate status, as in REQUEST INFO and SVR_STATUS."""
        with self._lock:
            info = {"state": self._state, "keyTypes": KEY_TYPES}
            key = self._load_key(KEY_FILE)
            if key is not None:
                info["keyType"] = _key_type(key)
            cert = self._load_cert() if self._state != PASSWORD else None
            last_error = self._last_error
            if cert is not None:
                info["serial"] = format(cert.serial_number, "x")
                not_after = int(cert.not_valid_after_utc.timestamp())
                info["notAfter"] = not_after
                if not last_error and time.time() > not_after:
                    last_error = CRT_EXPIRED
            info["lastError"] = last_error
            return info

    def not_after(self) -> float | None:
        cert = self._load_cert()
        return cert.not_valid_after_utc.timestamp() if cert is not None else None

    # Used by the connection

    def use_certificate(self) -> bool:
        """Whether to log in with the certificate, rather than the password."""
        with self._lock:
            if self._state == PENDING and time.monotonic() >= self._pending_retry_at:
                self._pending_retry_at = 0.0  # Trying it again now.
                return True
            return self._state == CERT

    def needs_check(self) -> bool:
        """Whether the certificate hasn't been used to log in yet, so the connection checks the server accepts it
        before logging in, and can fall back if it doesn't."""
        with self._lock:
            return self._state == PENDING or self._unproven

    def pending_retry_due(self) -> bool:
        """PENDING, logged in with the password, and it's time to try the certificate again."""
        with self._lock:
            return self._state == PENDING and self._pending_retry_at > 0 and time.monotonic() >= self._pending_retry_at

    def take_changed(self) -> bool:
        """Whether a certificate was installed or removed since the last call, so the connection logs in again."""
        with self._lock:
            changed, self._changed = self._changed, False
            return changed

    def login_refused(self):
        """A login with a certificate that has worked before was refused: revoked, or expired."""
        with self._lock:
            if self._state != CERT or self._unproven or self._last_error == CRT_HANDSHAKE_REFUSED:
                return
            logger.warning("The Dash server refused the device certificate. It needs a new one, or a new Dash login")
            self._last_error = CRT_HANDSHAKE_REFUSED
            self._save_state()

    def logged_in(self):
        """The connection logged in with the certificate."""
        notify = None
        with self._lock:
            if self._state == CERT and not self._unproven and self._last_error:
                self._last_error = 0
                self._save_state()
            if self._state == PENDING:
                self._last_error = 0
                self._status_due = True
                self._remove(PREVIOUS_KEY_FILE, PREVIOUS_CERT_FILE)
                self._set_state(CERT)
                notify = CERT
            elif self._unproven:
                # The renewed certificate works: SVR_STATUS with its serial has the server revoke the old ones.
                self._unproven = False
                self._last_error = 0
                self._status_due = True
                self._remove(PREVIOUS_KEY_FILE, PREVIOUS_CERT_FILE)
                self._save_state()
        if notify:
            self._notify(notify)

    def refused(self):
        """The server refused the certificate at the TLS handshake."""
        with self._lock:
            self._last_error = CRT_HANDSHAKE_REFUSED
            if self._state == PENDING:
                # Use the password, and report the error over it. Try the certificate again in an hour.
                logger.warning("The Dash server refused the device certificate: using the password")
                self._pending_retry_at = time.monotonic() + PENDING_RETRY
                self._status_due = True
            elif self._unproven:
                # Go back to the certificate that worked.
                logger.warning("The Dash server refused the renewed certificate: using the previous one")
                previous_key, previous_cert = self._file(PREVIOUS_KEY_FILE), self._file(PREVIOUS_CERT_FILE)
                if previous_key.exists() and previous_cert.exists():
                    os.replace(previous_key, self._file(KEY_FILE))
                    os.replace(previous_cert, self._file(CERT_FILE))
                self._unproven = False
                self._status_due = True
            else:
                logger.warning("The Dash server refused the device certificate. It needs a new one, or a new Dash login")
            self._save_state()

    def connection_ready(self, certificate_login: bool):
        """The connection is up and subscribed, so the device can talk to the server."""
        with self._lock:
            self._connection = (self._connection[0] + 1, certificate_login)

    def connection_lost(self):
        with self._lock:
            self._connection = (self._connection[0] + 1, None)

    def connection(self) -> tuple:
        with self._lock:
            return self._connection

    def reset(self):
        """A new Dash login from the Dash app: back to PASSWORD, with a new key next time."""
        with self._lock:
            had_certificate = self._state != PASSWORD or self._file(KEY_FILE).exists()
            self._remove(KEY_FILE, CERT_FILE, NEW_KEY_FILE, PREVIOUS_KEY_FILE, PREVIOUS_CERT_FILE)
            self._unproven = False
            self._status_due = False
            self._last_error = 0
            self._last_renewal_request = 0
            self._pending_retry_at = 0
            changed = self._set_state(PASSWORD)
            if had_certificate:
                self._changed = True
        if changed:
            self._notify(PASSWORD)

    # Used by the device

    def take_status_due(self) -> bool:
        """Whether the device has an SVR_STATUS to send. Clears it."""
        with self._lock:
            due = self._status_due
            if due:
                self._status_due = False
                self._save_state()
            return due

    def renewal_due(self) -> bool:
        """CERT, in the certificate's last year, and no renewal request in the last day."""
        with self._lock:
            if self._state != CERT or self._unproven:
                return False
            not_after = self.not_after()
            if not_after is None or time.time() < not_after - RENEWAL_WINDOW:
                return False
            return time.time() - self._last_renewal_request >= RENEWAL_INTERVAL

    def renewal_requested(self):
        with self._lock:
            self._last_renewal_request = time.time()
            self._save_state()

    def make_csr(self, key_type: str = "EC-P256", new_key: bool = False) -> str:
        """A certificate signing request for the device, base64 DER.

        It's for a new key if new_key, if the device has none, or if its key is of another type. The current key and
        certificate stay in use until the new certificate is installed.
        """
        if key_type not in KEY_TYPES:
            raise CertificateError(CRT_NOT_SUPPORTED, f"Key type {key_type}")
        with self._lock:
            key = None
            if not new_key:
                for name in (NEW_KEY_FILE, KEY_FILE):
                    candidate = self._load_key(name)
                    if candidate is not None and _key_type(candidate) == key_type:
                        key = candidate
                        break
            if key is None:
                try:
                    if key_type == "EC-P256":
                        key = ec.generate_private_key(ec.SECP256R1())
                    else:
                        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
                except Exception as error:  # pylint: disable=broad-except
                    raise CertificateError(CRT_KEYGEN_ERR, str(error)) from error
                try:
                    self._write(NEW_KEY_FILE, self._key_bytes(key))
                except Exception as error:  # pylint: disable=broad-except
                    raise CertificateError(CRT_STORE_ERR, str(error)) from error
            try:
                csr = (
                    x509.CertificateSigningRequestBuilder()
                    .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, f"d-{self.device_id}")]))
                    .sign(key, hashes.SHA256())
                )
            except Exception as error:  # pylint: disable=broad-except
                raise CertificateError(CRT_CSR_ERR, str(error)) from error
            return base64.b64encode(csr.public_bytes(serialization.Encoding.DER)).decode()

    def install(self, certificate: str, ca_cert: str = "", from_server: bool = False):
        """Check and install a certificate, base64 DER, and the Server CA if given.

        From the Dash app, or the server's first certificate, the device is then PENDING. A renewal from the server,
        when CERT, is used from the next login, falling back to the current certificate if it's refused.
        Raises CertificateError with CRT_INVALID or CRT_STORE_ERR.
        """
        try:
            cert = x509.load_der_x509_certificate(_b64decode(certificate))
            ca = x509.load_der_x509_certificate(_b64decode(ca_cert)) if ca_cert else None
        except ValueError as error:
            raise CertificateError(CRT_INVALID, "The certificate doesn't parse") from error
        names = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
        if not names or names[0].value != f"d-{self.device_id}":
            raise CertificateError(CRT_INVALID, "The certificate names another device")
        public = cert.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
        notify = None
        with self._lock:
            new_key, current_key = self._load_key(NEW_KEY_FILE), self._load_key(KEY_FILE)
            if new_key is not None and _public_der(new_key) == public:
                key_file = NEW_KEY_FILE
            elif current_key is not None and _public_der(current_key) == public:
                key_file = KEY_FILE
            else:
                raise CertificateError(CRT_INVALID, "The certificate isn't for the device's key")
            renewal = from_server and self._state == CERT
            try:
                if ca is not None:
                    self._write(CA_FILE, ca.public_bytes(serialization.Encoding.PEM))
                if renewal:
                    # Keep the certificate that works until the new one has.
                    if not self._unproven:
                        self._write(PREVIOUS_KEY_FILE, self._file(KEY_FILE).read_bytes())
                        self._write(PREVIOUS_CERT_FILE, self._file(CERT_FILE).read_bytes())
                else:
                    self._remove(PREVIOUS_KEY_FILE, PREVIOUS_CERT_FILE)
                if key_file == NEW_KEY_FILE:
                    os.replace(self._file(NEW_KEY_FILE), self._file(KEY_FILE))
                self._write(CERT_FILE, cert.public_bytes(serialization.Encoding.PEM))
            except OSError as error:
                raise CertificateError(CRT_STORE_ERR, str(error)) from error
            self._unproven = renewal
            self._last_error = 0
            self._pending_retry_at = 0
            self._changed = True
            if renewal:
                self._save_state()
            elif self._set_state(PENDING):
                notify = PENDING
            logger.info("Installed certificate %x", cert.serial_number)
        if notify:
            self._notify(notify)


class CertificateSession:
    """The device's requests to the Dash server for a certificate (SVR_CSR), and its status reports (SVR_STATUS).

    It runs on the device's thread: poll() is called from Device.run().
    """

    def __init__(self, certificates: DeviceCertificates, device_id: str, send: Callable[[str], None]):
        self.certificates = certificates
        self.device_id = device_id
        self._send = send
        self._connection = certificates.connection()
        self._request = ""  # The SVR_CSR being asked, sent again until the server replies.
        self._deadline: float | None = None
        self._wait = REQUEST_TIMEOUT

    def _message(self, *fields: str) -> str:
        return f"\t{self.device_id}\tDATA\tCRT\t" + "\t".join(fields) + "\n"

    def poll(self):
        connection = self.certificates.connection()
        if connection != self._connection:
            self._connection = connection
            if connection[1] is None:
                self._stop()  # The connection dropped: start again on the next.
            else:
                self._connected(connection[1])
        if self._deadline is not None and time.monotonic() >= self._deadline:
            self._wait = min(self._wait * 2, REQUEST_MAX_WAIT)
            self._ask()

    def _connected(self, certificate_login: bool):
        self._stop()
        certificates = self.certificates
        if certificates.take_status_due():
            info = certificates.info()
            self._send(self._message("SVR_STATUS", json.dumps(info, separators=(",", ":"))))
        if certificates.state == PASSWORD and not certificate_login and certificates.auto_issue:
            self._start(renew=False)
        elif certificates.state == CERT and certificate_login and certificates.renewal_due():
            certificates.renewal_requested()
            self._start(renew=True)

    def _start(self, renew: bool):
        try:
            csr = self.certificates.make_csr(new_key=renew)
        except CertificateError as error:
            logger.warning("Certificate request: %s", error)
            return
        options = {"keyType": "EC-P256", "renew": renew, "needCA": False}
        self._request = self._message("SVR_CSR", json.dumps(options, separators=(",", ":")), csr)
        self._wait = REQUEST_TIMEOUT
        self._ask()

    def _ask(self):
        logger.debug("Asking the Dash server for a certificate")
        self._send(self._request)
        self._deadline = time.monotonic() + self._wait

    def _stop(self):
        self._request = ""
        self._deadline = None

    def server_certificate(self, options: str, certificate: str):
        """SVR_CRT: the server signed the request."""
        if not self._request:
            return  # Not asked on this connection.
        self._stop()
        try:
            ca_cert = json.loads(options).get("caCert", "") if options else ""
        except (ValueError, AttributeError):
            ca_cert = ""
        try:
            self.certificates.install(certificate, ca_cert, from_server=True)
        except CertificateError as error:
            logger.warning("The Dash server's certificate wasn't installed: %s", error)

    def server_error(self, code: int):
        """ERR: the server didn't sign the request."""
        if not self._request:
            return
        logger.warning("The Dash server didn't sign the certificate request: %s", code)
        if code == CRT_RATE_LIMIT:
            self._deadline = time.monotonic() + REQUEST_TIMEOUT
        elif code == CRT_SERVER_ERR:
            pass  # Keep to the backoff.
        else:
            self._stop()  # CRT_REFUSED until the next connection, CRT_NOT_DUE until the next day.
