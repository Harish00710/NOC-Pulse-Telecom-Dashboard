# NOC Pulse — Telecom Network Operations Dashboard

A polished, local Streamlit project inspired by telecom Network Operations Center (NOC) workflows and the monitoring patterns found in platforms such as SolarWinds and NetAct. It is designed as a portfolio / interview demonstration and **does not connect to real network equipment**.

## Modules

1. **Live KPI Monitor** — availability, latency, throughput, packet loss, estimated active users, historical trends, and cell inventory.
2. **Alarm & Fault Tracker** — severity/status/region filters, text search across alarm and cell fields, issue-type charts, and CSV export.
3. **Wireshark Packet Analyzer** — upload `.pcap` or `.pcapng`, decode packet metadata, visualize protocol mix and top talkers, filter packet rows, and export CSV. It uses PyShark with Wireshark's `tshark` when available. A standard-library fallback handles classic Ethernet `.pcap` files when TShark is unavailable.
4. **Automated PDF Report** — generate a downloadable daily performance report with KPI summary, alarm severity overview, operational notes, and data classification.

## Project layout

```text
noc_dashboard_project/
├── app.py
├── pages/
│   ├── 1_Live_KPI_Monitor.py
│   ├── 2_Alarm_Fault_Tracker.py
│   ├── 3_Wireshark_Packet_Analyzer.py
│   └── 4_Daily_PDF_Reports.py
├── src/noc_dashboard/
│   ├── config.py
│   ├── data.py
│   ├── packet_analyzer.py
│   ├── reports.py
│   └── ui.py
├── data/sample/
│   ├── alarms.csv
│   ├── cells.csv
│   ├── kpi_history.csv
│   └── demo_traffic.pcap
├── tests/
├── requirements.txt
└── README.md
```

## Requirements

- Windows 10/11, macOS, or Linux
- Python 3.10–3.12 recommended
- VS Code with the Python extension
- Wireshark (recommended for `.pcapng` and broad protocol support). The app remains usable without it for classic Ethernet `.pcap` files.

## Run in VS Code on Windows

Open the extracted `noc_dashboard_project` folder in VS Code. Open **Terminal → New Terminal** and run:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks activation for the current terminal, use this once for that terminal session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

The app opens at `http://localhost:8501`. Keep the terminal running while you use the dashboard. Stop it with `Ctrl+C`.

### Install TShark (recommended)

Install Wireshark from the official Wireshark website and ensure the installation folder containing `tshark.exe` is on your Windows `PATH` (commonly `C:\Program Files\Wireshark`). Restart VS Code after changing PATH. Verify with:

```powershell
tshark --version
```

PyShark calls TShark to decode packet captures. If `tshark` is not detected, NOC Pulse attempts its built-in classic-PCAP parser. That fallback supports Ethernet link-layer classic `.pcap` files and common IPv4/IPv6 TCP, UDP, ICMP, and ARP metadata; it is intentionally not a replacement for Wireshark's full protocol dissectors. `.pcapng` and other link types need TShark.

## Try the included packet capture

Open **Wireshark Packet Analyzer** and choose **Analyze included demo_traffic.pcap**. The small capture is generated for this project and contains synthetic TCP, UDP, and ICMP traffic between private documentation/demo endpoints. No real user traffic is included.

## Data and demo mode

All KPI, cell, and alarm records under `data/sample/` are synthetic. The UI and PDF report explicitly identify this as demo data. Do not present the sample values as production network metrics or SLA evidence.

To use your own data, preserve the column names in the sample CSVs:

- `kpi_history.csv`: `timestamp,availability_pct,latency_ms,throughput_mbps,packet_loss_pct,active_users`
- `cells.csv`: `cell_id,site_name,region,technology,utilization_pct,availability_pct`
- `alarms.csv`: `alarm_id,timestamp,severity,cell_id,issue_type,description,status,region,assignee`

Use timezone-consistent timestamps. KPI timestamps are interpreted as UTC by the included sample data.

## Tests

Install the requirements, then run:

```powershell
python -m unittest discover -s tests -v
```

## Troubleshooting

- **`streamlit` is not recognized:** activate `.venv` and use `python -m streamlit run app.py`.
- **Import errors:** make sure VS Code opened the project root (the folder containing `app.py`) and the virtual environment is selected as the Python interpreter.
- **Packet parsing says TShark unavailable:** install Wireshark, add its folder to PATH, restart the terminal, and run `tshark --version`. Classic Ethernet PCAP still works with the fallback.
- **PDF generation fails:** confirm `reportlab` installed successfully with `pip show reportlab`.
- **Port 8501 is in use:** run `python -m streamlit run app.py --server.port 8502`.

## Important scope note

This is a self-contained portfolio-grade demo. It does not perform SNMP polling, connect to OSS/NMS platforms, ingest streaming telemetry, create real alarms, or automatically schedule reports. Those integrations require authorized endpoints, credentials, network access, and operator-specific data models. Do not add production credentials to source code; use Streamlit secrets or environment variables when adding integrations.
