from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import socket
import struct
import shutil
from typing import Any

import pandas as pd

from .config import MAX_PACKET_ROWS

COLUMNS = ["number", "timestamp", "source", "destination", "protocol", "length", "src_port", "dst_port", "tcp_flags", "info"]


def _safe_attr(obj: Any, name: str, default: str = "") -> str:
    try:
        value = getattr(obj, name)
        return str(value) if value is not None else default
    except Exception:
        return default


def parse_with_pyshark(path: str, packet_limit: int = MAX_PACKET_ROWS) -> pd.DataFrame:
    """Parse a capture through PyShark/TShark. Requires Wireshark's tshark binary."""
    import pyshark  # optional at runtime; declared in requirements

    capture = pyshark.FileCapture(path, keep_packets=False, use_json=True)
    rows: list[dict[str, Any]] = []
    try:
        for packet in capture:
            if len(rows) >= packet_limit:
                break
            layers = [str(x.layer_name).upper() for x in packet.layers]
            protocol = str(getattr(packet, "highest_layer", "OTHER")).upper()
            ip_layer = getattr(packet, "ip", None) or getattr(packet, "ipv6", None)
            source = _safe_attr(ip_layer, "src", "") if ip_layer else _safe_attr(getattr(packet, "eth", None), "src", "")
            destination = _safe_attr(ip_layer, "dst", "") if ip_layer else _safe_attr(getattr(packet, "eth", None), "dst", "")
            tcp = getattr(packet, "tcp", None)
            udp = getattr(packet, "udp", None)
            transport = tcp or udp
            src_port = _safe_attr(transport, "srcport", "") if transport else ""
            dst_port = _safe_attr(transport, "dstport", "") if transport else ""
            flags = _safe_attr(tcp, "flags", "") if tcp else ""
            info = f"{protocol} {src_port} → {dst_port}" if transport else protocol
            try:
                ts = datetime.fromtimestamp(float(packet.sniff_timestamp), tz=timezone.utc)
            except Exception:
                ts = datetime.now(timezone.utc)
            try:
                length = int(packet.length)
            except Exception:
                length = 0
            rows.append({
                "number": int(_safe_attr(packet, "number", str(len(rows) + 1)) or len(rows) + 1),
                "timestamp": ts, "source": source or "—", "destination": destination or "—",
                "protocol": protocol or (layers[-1] if layers else "OTHER"), "length": length,
                "src_port": src_port, "dst_port": dst_port, "tcp_flags": flags, "info": info,
            })
    finally:
        capture.close()
    return pd.DataFrame(rows, columns=COLUMNS)


def _ipv4(addr: bytes) -> str:
    return socket.inet_ntop(socket.AF_INET, addr)


def _parse_transport(payload: bytes, protocol_number: int) -> tuple[str, str, str, str, str]:
    if protocol_number == 6 and len(payload) >= 20:  # TCP
        src, dst = struct.unpack("!HH", payload[:4])
        offset = ((payload[12] >> 4) & 0xF) * 4
        flags_byte = payload[13]
        names = [("FIN", 0x01), ("SYN", 0x02), ("RST", 0x04), ("PSH", 0x08), ("ACK", 0x10), ("URG", 0x20)]
        flags = ",".join(name for name, mask in names if flags_byte & mask) or "—"
        return "TCP", str(src), str(dst), flags, f"TCP {src} → {dst} [{flags}]"
    if protocol_number == 17 and len(payload) >= 8:  # UDP
        src, dst = struct.unpack("!HH", payload[:4])
        return "UDP", str(src), str(dst), "", f"UDP {src} → {dst}"
    if protocol_number == 1:
        return "ICMP", "", "", "", "ICMP message"
    if protocol_number == 58:
        return "ICMPv6", "", "", "", "ICMPv6 message"
    return {2: "IGMP", 47: "GRE", 50: "ESP", 51: "AH"}.get(protocol_number, f"IP-{protocol_number}"), "", "", "", ""


def parse_classic_pcap(path: str, packet_limit: int = MAX_PACKET_ROWS) -> pd.DataFrame:
    """Small standard-library PCAP parser fallback for Ethernet captures (classic .pcap)."""
    rows: list[dict[str, Any]] = []
    with open(path, "rb") as fh:
        header = fh.read(24)
        if len(header) != 24:
            raise ValueError("Capture is too short to contain a classic PCAP header.")
        magic = header[:4]
        formats = {
            b"\xd4\xc3\xb2\xa1": ("<", 1_000_000),
            b"\xa1\xb2\xc3\xd4": (">", 1_000_000),
            b"\x4d\x3c\xb2\xa1": ("<", 1_000_000_000),
            b"\xa1\xb2\x3c\x4d": (">", 1_000_000_000),
        }
        if magic not in formats:
            raise ValueError("Built-in fallback supports classic .pcap files only. Install Wireshark/TShark to parse .pcapng files.")
        endian, resolution = formats[magic]
        _major, _minor, _zone, _sigfigs, _snaplen, linktype = struct.unpack(endian + "HHIIII", header[4:])
        if linktype != 1:
            raise ValueError(f"Built-in fallback currently supports Ethernet captures (link type 1); this file uses link type {linktype}. Install TShark for broader support.")
        number = 0
        while len(rows) < packet_limit:
            record_header = fh.read(16)
            if not record_header:
                break
            if len(record_header) != 16:
                raise ValueError("Capture ended unexpectedly inside a packet record header.")
            sec, fraction, incl_len, _orig_len = struct.unpack(endian + "IIII", record_header)
            frame = fh.read(incl_len)
            if len(frame) != incl_len:
                raise ValueError("Capture ended unexpectedly inside a packet frame.")
            number += 1
            timestamp = datetime.fromtimestamp(sec + fraction / resolution, tz=timezone.utc)
            source = destination = "—"
            protocol = "ETHERNET"
            src_port = dst_port = flags = ""
            info = "Ethernet frame"
            if len(frame) >= 14:
                ethertype = struct.unpack("!H", frame[12:14])[0]
                cursor = 14
                while ethertype in (0x8100, 0x88A8) and len(frame) >= cursor + 4:
                    ethertype = struct.unpack("!H", frame[cursor + 2:cursor + 4])[0]
                    cursor += 4
                if ethertype == 0x0800 and len(frame) >= cursor + 20:
                    ip = frame[cursor:]
                    ihl = (ip[0] & 0x0F) * 4
                    if ihl >= 20 and len(ip) >= ihl:
                        source, destination = _ipv4(ip[12:16]), _ipv4(ip[16:20])
                        ip_proto = ip[9]
                        protocol, src_port, dst_port, flags, info = _parse_transport(ip[ihl:], ip_proto)
                elif ethertype == 0x86DD and len(frame) >= cursor + 40:
                    ip6 = frame[cursor:]
                    source = socket.inet_ntop(socket.AF_INET6, ip6[8:24])
                    destination = socket.inet_ntop(socket.AF_INET6, ip6[24:40])
                    next_header = ip6[6]
                    protocol, src_port, dst_port, flags, info = _parse_transport(ip6[40:], next_header)
                elif ethertype == 0x0806:
                    protocol, info = "ARP", "Address Resolution Protocol"
                else:
                    protocol, info = {0x0800: ("IPv4", "IPv4 frame"), 0x86DD: ("IPv6", "IPv6 frame")}.get(ethertype, (f"ETHERTYPE-0x{ethertype:04x}", "Ethernet payload"))
            rows.append({"number": number, "timestamp": timestamp, "source": source, "destination": destination,
                         "protocol": protocol, "length": len(frame), "src_port": src_port, "dst_port": dst_port,
                         "tcp_flags": flags, "info": info})
    return pd.DataFrame(rows, columns=COLUMNS)


def analyze_capture(path: str, packet_limit: int = MAX_PACKET_ROWS) -> tuple[pd.DataFrame, str, str]:
    """Prefer PyShark/TShark, then fall back to the built-in classic-PCAP parser."""
    tshark = shutil.which("tshark")
    pyshark_error = ""
    if tshark:
        try:
            df = parse_with_pyshark(path, packet_limit)
            return df, "PyShark + TShark", f"Parsed with TShark at {tshark}."
        except Exception as exc:  # fallback keeps the dashboard usable on imperfect local installs
            pyshark_error = str(exc)
    else:
        pyshark_error = "TShark executable was not found on PATH."
    try:
        df = parse_classic_pcap(path, packet_limit)
        note = "TShark was unavailable or failed; parsed using the built-in Ethernet PCAP fallback."
        if pyshark_error:
            note += f" Detail: {pyshark_error[:220]}"
        return df, "Built-in PCAP fallback", note
    except Exception as fallback_exc:
        raise RuntimeError(f"Packet parsing could not be completed. {pyshark_error} Fallback detail: {fallback_exc}") from fallback_exc
