"""
Shared message-framing module for the Recipe Discovery System.

Wire format
    [ 4-byte big-endian unsigned length N ][ N bytes of UTF-8 JSON payload ]

Both server and client exchange JSON objects framed this way, so a message
can safely span multiple TCP segments and several messages can share a
segment without ambiguity.
"""

import json
import socket
import struct

HEADER_FORMAT = "!I"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
MAX_MESSAGE_BYTES = 8 * 1024 * 1024  # 8 MiB sanity cap


class ProtocolError(Exception):
    """Raised when a malformed frame is received."""


def _recv_exact(sock, n):
    """Read exactly n bytes from sock or return None on clean EOF."""
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf.extend(chunk)
    return bytes(buf)


def send_message(sock, obj):
    """Encode obj as JSON, prefix with 4-byte length, send over sock."""
    payload = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    if len(payload) > MAX_MESSAGE_BYTES:
        raise ProtocolError(f"message too large: {len(payload)} bytes")
    header = struct.pack(HEADER_FORMAT, len(payload))
    sock.sendall(header + payload)


def recv_message(sock):
    """Receive one framed JSON message. Returns None if peer closed cleanly."""
    header = _recv_exact(sock, HEADER_SIZE)
    if header is None:
        return None
    (length,) = struct.unpack(HEADER_FORMAT, header)
    if length == 0:
        return {}
    if length > MAX_MESSAGE_BYTES:
        raise ProtocolError(f"declared length too large: {length} bytes")
    payload = _recv_exact(sock, length)
    if payload is None:
        raise ProtocolError("connection closed mid-message")
    try:
        return json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError(f"invalid JSON payload: {exc}") from exc
