from __future__ import annotations
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.noc_dashboard.config import DATA_DIR
from src.noc_dashboard.data import load_alarms, load_cells, load_kpi_history, filter_alarms
from src.noc_dashboard.packet_analyzer import parse_classic_pcap
from src.noc_dashboard.reports import build_daily_report


class DataTests(unittest.TestCase):
    def test_sample_data_loads(self):
        self.assertGreaterEqual(len(load_alarms()), 10)
        self.assertGreaterEqual(len(load_cells()), 5)
        self.assertGreaterEqual(len(load_kpi_history()), 24)

    def test_alarm_filtering(self):
        alarms = load_alarms()
        filtered = filter_alarms(alarms, severities=["Critical"], search="ALM-")
        self.assertTrue((filtered["severity"] == "Critical").all())
        self.assertGreater(len(filtered), 0)

    def test_pdf_report_generation(self):
        report = build_daily_report(load_kpi_history(), load_alarms(), load_cells())
        self.assertTrue(report.startswith(b"%PDF"))
        self.assertGreater(len(report), 1000)

    def test_demo_pcap_fallback(self):
        frame = parse_classic_pcap(str(DATA_DIR / "demo_traffic.pcap"))
        self.assertEqual(len(frame), 6)
        self.assertIn("TCP", set(frame["protocol"]))
        self.assertIn("UDP", set(frame["protocol"]))
        self.assertIn("ICMP", set(frame["protocol"]))


if __name__ == "__main__":
    unittest.main()
