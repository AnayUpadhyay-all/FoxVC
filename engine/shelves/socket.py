"""
FoxVC Raw Sockets & Networking Shelf (shelves/socket.py).
Provides non-blocking raw TCP servers/clients, UDP transmission, and WebSocket framing.
"""

import socket
import threading
import struct
from typing import Dict, Any, Optional, Callable
from .common import SecurityPolicy


def fox_tcp_send(host: str, port: int, message: str, timeout: float = 3.0) -> str:
    """Connects to a TCP host and port, sends a message, and receives the response string."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(float(timeout))
        s.connect((str(host), int(port)))
        s.sendall(str(message).encode("utf-8"))
        data = s.recv(4096)
        s.close()
        return data.decode("utf-8", errors="replace")
    except Exception as e:
        return f"TCP Error: {e}"


def fox_udp_send(host: str, port: int, message: str) -> int:
    """Sends a datagram message via UDP."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(str(message).encode("utf-8"), (str(host), int(port)))
        s.close()
        return 1
    except Exception:
        return 0


def fox_ws_frame_encode(text: str) -> str:
    """Encodes a string into a minimal RFC-6455 unmasked WebSocket text frame header."""
    data = str(text).encode("utf-8")
    length = len(data)
    frame = bytearray()
    frame.append(0x81)  # FIN + Text Opcode (1)

    if length <= 125:
        frame.append(length)
    elif length <= 65535:
        frame.append(126)
        frame.extend(struct.pack("!H", length))
    else:
        frame.append(127)
        frame.extend(struct.pack("!Q", length))

    frame.extend(data)
    return frame.hex()


def fox_ws_frame_decode(hex_frame: str) -> str:
    """Decodes a hexadecimal string of a WebSocket text frame."""
    try:
        data = bytes.fromhex(str(hex_frame))
        if len(data) < 2:
            return ""
        masked = (data[1] & 0x80) != 0
        payload_len = data[1] & 0x7F
        offset = 2

        if payload_len == 126:
            payload_len = struct.unpack("!H", data[2:4])[0]
            offset = 4
        elif payload_len == 127:
            payload_len = struct.unpack("!Q", data[2:10])[0]
            offset = 10

        mask_key = None
        if masked:
            mask_key = data[offset:offset + 4]
            offset += 4

        payload = bytearray(data[offset:offset + payload_len])
        if masked and mask_key:
            for i in range(len(payload)):
                payload[i] ^= mask_key[i % 4]

        return payload.decode("utf-8", errors="replace")
    except Exception as e:
        return f"WS Decode Error: {e}"


def get_socket_shelf(policy: Optional[SecurityPolicy] = None) -> Dict[str, Any]:
    return {
        "tcpSend": fox_tcp_send,
        "udpSend": fox_udp_send,
        "wsFrameEncode": fox_ws_frame_encode,
        "wsFrameDecode": fox_ws_frame_decode,
    }
