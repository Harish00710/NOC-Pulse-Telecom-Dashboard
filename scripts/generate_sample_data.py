"""Regenerate the synthetic CSV datasets and demo PCAP shipped with NOC Pulse."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from pathlib import Path
import csv, math, random, socket, struct

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "sample"
DATA.mkdir(parents=True, exist_ok=True)
random.seed(27)
now = datetime.now(timezone.utc).replace(second=0, microsecond=0)

# KPI history: 48 half-hour observations.
with (DATA / "kpi_history.csv").open("w", newline="", encoding="utf-8") as fh:
    writer = csv.writer(fh)
    writer.writerow(["timestamp", "availability_pct", "latency_ms", "throughput_mbps", "packet_loss_pct", "active_users"])
    for i in range(48):
        phase = i / 48 * 2 * math.pi
        availability = 99.72 + 0.13 * math.sin(phase) + random.uniform(-0.035, 0.035)
        latency = 34 + 8 * math.sin(phase - 0.8) + random.uniform(-2.5, 2.5)
        throughput = 620 + 155 * math.sin(phase - 1.4) + random.uniform(-35, 35)
        loss = max(0.01, 0.12 + 0.07 * math.sin(phase + 1.2) + random.uniform(-0.035, 0.035))
        users = int(14800 + 2600 * math.sin(phase - 1.0) + random.randint(-350, 350))
        ts = now - timedelta(minutes=30 * (47 - i))
        writer.writerow([ts.isoformat(), f"{availability:.3f}", f"{latency:.2f}", f"{throughput:.2f}", f"{loss:.3f}", users])

cells = [
    ("CELL-CHN-001", "Anna Nagar North", "Chennai", "5G", 72.4, 99.91),
    ("CELL-CHN-002", "T Nagar Central", "Chennai", "4G", 83.1, 99.78),
    ("CELL-CHN-003", "Guindy Industrial", "Chennai", "5G", 64.8, 99.96),
    ("CELL-CHN-004", "Velachery East", "Chennai", "4G", 91.2, 99.42),
    ("CELL-VLR-001", "Katpadi Junction", "Vellore", "4G", 58.6, 99.88),
    ("CELL-VLR-002", "Vellore Fort", "Vellore", "5G", 49.3, 99.93),
    ("CELL-RPT-001", "Ranipet SIPCOT", "Ranipet", "4G", 87.5, 99.61),
    ("CELL-RPT-002", "Walajah Road", "Ranipet", "5G", 53.7, 99.89),
    ("CELL-KPM-001", "Kanchipuram East", "Kanchipuram", "4G", 61.9, 99.84),
    ("CELL-KPM-002", "Oragadam Hub", "Kanchipuram", "5G", 78.2, 99.90),
    ("CELL-CGL-001", "Chengalpattu North", "Chengalpattu", "4G", 67.1, 99.86),
    ("CELL-CGL-002", "Mahindra World City", "Chengalpattu", "5G", 74.4, 99.95),
]
with (DATA / "cells.csv").open("w", newline="", encoding="utf-8") as fh:
    writer = csv.writer(fh); writer.writerow(["cell_id", "site_name", "region", "technology", "utilization_pct", "availability_pct"]); writer.writerows(cells)

alarm_specs = [
    ("Critical", "Backhaul Link Down", "Backhaul interface unreachable; traffic rerouted to secondary path.", "Open", "Chennai", "Transport NOC"),
    ("Major", "High PRB Utilization", "Downlink resource utilization above 85% for 15 minutes.", "Open", "Chennai", "RAN Optimization"),
    ("Major", "VSWR Threshold Breach", "Antenna feeder return loss outside configured threshold.", "Open", "Ranipet", "Field Operations"),
    ("Minor", "Cell Availability Degraded", "Short service interruption detected during observation window.", "Open", "Vellore", "RAN Support"),
    ("Warning", "Temperature Warning", "Cabinet temperature approaching configured warning threshold.", "Open", "Kanchipuram", "Field Operations"),
    ("Major", "Packet Loss Elevated", "Packet loss observed on aggregation path above baseline.", "Acknowledged", "Chengalpattu", "IP Operations"),
    ("Minor", "Neighbor Relation Missing", "Potential missing neighbor relation identified in handover audit.", "Resolved", "Chennai", "RAN Optimization"),
    ("Warning", "Power System on Battery", "Site running on battery following AC input fluctuation.", "Acknowledged", "Ranipet", "Power Team"),
    ("Critical", "Site Unreachable", "Management heartbeat missed for three consecutive intervals.", "Resolved", "Vellore", "Field Operations"),
    ("Minor", "S1 Signaling Retry", "Elevated retry count observed on control-plane signaling.", "Open", "Kanchipuram", "Core Network"),
    ("Major", "High CPU Utilization", "Network element processor utilization above 80%.", "Open", "Chengalpattu", "Core Network"),
    ("Warning", "Optical Power Low", "Received optical power trending near warning threshold.", "Resolved", "Chennai", "Transport NOC"),
    ("Minor", "Handover Failure Rate", "Handover failure rate slightly above the daily baseline.", "Acknowledged", "Vellore", "RAN Support"),
    ("Major", "DNS Query Latency", "Resolver response time elevated for the monitored service group.", "Open", "Chennai", "Core Network"),
    ("Warning", "Disk Utilization", "Log partition has reached 78% utilization.", "Open", "Ranipet", "Systems Team"),
]
cell_ids = [c[0] for c in cells]
with (DATA / "alarms.csv").open("w", newline="", encoding="utf-8") as fh:
    writer = csv.writer(fh); writer.writerow(["alarm_id", "timestamp", "severity", "cell_id", "issue_type", "description", "status", "region", "assignee"])
    for i, (severity, issue, desc, status, region, assignee) in enumerate(alarm_specs, 1):
        cell = cell_ids[(i * 3) % len(cell_ids)]
        ts = now - timedelta(minutes=(i * 37) % (24 * 60))
        writer.writerow([f"ALM-2026-{i:04d}", ts.isoformat(), severity, cell, issue, desc, status, region, assignee])

# Ethernet frames for a tiny classic PCAP (TCP, UDP/DNS-like, ICMP).
def checksum(data: bytes) -> int:
    if len(data) % 2: data += b"\x00"
    total = sum(struct.unpack("!%dH" % (len(data)//2), data))
    while total >> 16: total = (total & 0xffff) + (total >> 16)
    return (~total) & 0xffff

def frame(src_ip: str, dst_ip: str, proto: int, payload: bytes, ident: int) -> bytes:
    src_mac = bytes.fromhex("020000000001")
    dst_mac = bytes.fromhex("020000000002")
    total_len = 20 + len(payload)
    ip0 = struct.pack("!BBHHHBBH4s4s", 0x45, 0, total_len, ident, 0x4000, 64, proto, 0, socket.inet_aton(src_ip), socket.inet_aton(dst_ip))
    csum = checksum(ip0)
    iphdr = ip0[:10] + struct.pack("!H", csum) + ip0[12:]
    return dst_mac + src_mac + struct.pack("!H", 0x0800) + iphdr + payload

def tcp(src: int, dst: int, flags: int, body: bytes = b"demo") -> bytes:
    return struct.pack("!HHIIHHHH", src, dst, 1000, 0, (5 << 12) | flags, 64240, 0, 0) + body

def udp(src: int, dst: int, body: bytes = b"\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00") -> bytes:
    return struct.pack("!HHHH", src, dst, 8 + len(body), 0) + body

frames = [
    frame("192.0.2.10", "198.51.100.20", 6, tcp(51514, 443, 0x02), 1),
    frame("198.51.100.20", "192.0.2.10", 6, tcp(443, 51514, 0x12), 2),
    frame("192.0.2.10", "203.0.113.53", 17, udp(53001, 53), 3),
    frame("203.0.113.53", "192.0.2.10", 17, udp(53, 53001, b"\x12\x34\x81\x80\x00\x01\x00\x01\x00\x00\x00\x00"), 4),
    frame("192.0.2.10", "198.51.100.20", 1, b"\x08\x00\xf7\xff\x00\x01\x00\x01" + b"pingdemo", 5),
    frame("192.0.2.11", "198.51.100.20", 6, tcp(51515, 80, 0x18, b"GET / HTTP/1.1\r\n\r\n"), 6),
]
with (DATA / "demo_traffic.pcap").open("wb") as fh:
    fh.write(b"\xd4\xc3\xb2\xa1" + struct.pack("<HHIIII", 2, 4, 0, 0, 65535, 1))
    base = int(now.timestamp())
    for i, packet in enumerate(frames):
        fh.write(struct.pack("<IIII", base + i, 1000 * i, len(packet), len(packet)))
        fh.write(packet)
print(f"Generated demo datasets in {DATA}")
