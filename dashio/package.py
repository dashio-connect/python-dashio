"""PKG messages: several messages for one device packaged into a single message.

A PKG message is "\\t<device_id>\\tPKG\\tJAOS\\t<json>\\n". JAOS (JSON Array Of Strings) is the only encoding: the
payload is a compact JSON array, and each string is one message without its leading "\\t<device_id>\\t" and
trailing newline. The JSON encoding escapes the tabs inside each message, so the PKG message stays one line.
Packaging saves sending many separate messages, which matters most over MQTT, e.g. for Menu update replies.
"""
from __future__ import annotations

import json

PKG_ID = "PKG"
PKG_JAOS = "JAOS"
PKG_SIZE_LIMIT = 1000  # A new package is started once a package's messages are longer than this.


def _strip_device_id(message: str) -> str:
    """'\\t<device_id>\\tTEXT\\tT01\\t1\\n' -> 'TEXT\\tT01\\t1'"""
    parts = message.split("\t", 2)
    return parts[2].rstrip("\n") if len(parts) == 3 else ""


def make_packages(device_id: str, messages: str, limit: int = PKG_SIZE_LIMIT) -> str:
    """Package messages into one or more PKG messages.

    Parameters
    ----------
    device_id : str
        The device the messages are from.
    messages : str
        Complete messages, each "\\t<device_id>\\t...\\n", one after another.
    limit : int, optional
        A new package is started once a package's messages are longer than this. Defaults to 1000.

    Returns
    -------
    str
        The PKG messages, or "" if there are no messages.
    """
    packages = []
    items = []
    size = 0
    for message in messages.split("\n"):  # Not splitlines(), which also splits on characters inside text.
        item = _strip_device_id(message)
        if not item:
            continue
        items.append(item)
        size += len(item)
        if size > limit:
            packages.append(_package(device_id, items))
            items = []
            size = 0
    if items:
        packages.append(_package(device_id, items))
    return "".join(packages)


def _package(device_id: str, items: list[str]) -> str:
    payload = json.dumps(items, separators=(",", ":"), ensure_ascii=False)
    return f"\t{device_id}\t{PKG_ID}\t{PKG_JAOS}\t{payload}\n"
