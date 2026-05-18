
import json
import socket
import struct

HEADER_FORMAT = "!I"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
MAX_MESSAGE_BYTES = 8 * 1024 * 1024


class ProtocolError(Exception):


def _recv_exact(sock, n):
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf.extend(chunk)
    return bytes(buf)


def send_message(sock, obj):
    payload = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    if len(payload) > MAX_MESSAGE_BYTES:
        raise ProtocolError(f"message too large: {len(payload)} bytes")
    header = struct.pack(HEADER_FORMAT, len(payload))
    sock.sendall(header + payload)


def recv_message(sock):
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
