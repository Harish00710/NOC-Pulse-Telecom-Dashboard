from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "sample"
MAX_PCAP_MB = 25
MAX_PACKET_ROWS = 5000
APP_NAME = "NOC Pulse"
APP_VERSION = "1.0.0"
