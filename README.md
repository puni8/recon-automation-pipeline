#  Recon Automation Pipeline

> A Python-orchestrated reconnaissance pipeline for bug bounty programs. Chains **subfinder → httpx → nmap → gowitness** for automated attack surface mapping with structured JSON output and a polished HTML report.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-v1.0-success.svg)]()

---

##  Features

- **Subdomain enumeration** — passive discovery via `subfinder` across 30+ public sources
- **Live host detection** — probes every subdomain via `httpx`, captures status, title, tech stack
- **Port scanning** — `nmap` fast scan on top 100 TCP ports with service version detection
- **Tech fingerprinting** — aggregates httpx detection + custom HTTP header analysis
- **Screenshot capture** — visual triage via `gowitness` headless browser
- **HTML report** — single-page report with stats, tables, tech distribution bar chart, screenshot gallery
- **One-command pipeline** — `python3 main.py --target <domain>` runs everything

---

##  Architecture

subfinder → subdomains.json
↓
httpx    → livehosts.json
↓
nmap     → ports.json
↓
headers  → tech.json
↓
gowitness → screenshots.json + screenshots/
↓
Jinja2   → report.html

Each module reads structured JSON from upstream and produces structured JSON for downstream. Same pipeline philosophy as Unix tools — each does ONE thing well.

---

##  Installation

### Requirements
- Python 3.11+
- Go tools: `subfinder`, `httpx` (ProjectDiscovery), `gowitness`
- System tools: `nmap`

### Setup

```bash
# Clone
git clone git@github.com:puni8/recon-automation-pipeline.git
cd recon-automation-pipeline

# Python dependencies
pip install -r requirements.txt

# Go tools
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install github.com/projectdiscovery/httpx/cmd/httpx@latest
go install github.com/sensepost/gowitness@latest

# System tools
sudo apt install -y nmap
```

---

##  Usage

```bash
# Full pipeline
python3 main.py --target hackerone.com

# Custom options
python3 main.py --target example.com --max-hosts 20 --report myreport.html

# Individual modules
python3 -m modules.subdomains hackerone.com
python3 -m modules.livehosts hackerone.com
python3 -m modules.ports hackerone.com 5
python3 -m modules.tech hackerone.com
python3 -m modules.screenshots hackerone.com 10
python3 report.py hackerone.com

# Help
python3 main.py --help
```

### Output files

output/<target>/
├── subdomains.json      ← all discovered subdomains
├── livehosts.json       ← live hosts with metadata
├── ports.json           ← open ports per host
├── tech.json            ← tech distribution
├── screenshots.json     ← screenshot manifest
├── screenshots/         ← captured images
└── report.html          ← the final report (open in browser)

---

##  How Each Module Works

| Module | Tool | Technique |
|--------|------|-----------|
| `subdomains.py` | subfinder | Passive enumeration across 30+ public sources |
| `livehosts.py` | httpx | HTTP/HTTPS probing with metadata extraction |
| `ports.py` | nmap | Top-100 TCP port scan with service version detection |
| `tech.py` | httpx + custom | httpx auto-detect + regex header analysis |
| `screenshots.py` | gowitness | Headless Chrome capture per live URL |
| `report.py` | Jinja2 | Reads all JSONs → renders single HTML page |

---

##  Tested Against

- **HackerOne** (hackerone.com) — public bug bounty program, broad scope
- **Tesla** (tesla.com) — HackerOne program

> ⚠️ Only run this against targets you have explicit permission to test. Always read the program's scope rules before running active modules (nmap, gowitness).

---

##  Tech Stack

- **Python 3.11+** — orchestration, parsing, reporting
- **subprocess** — wraps all external CLI tools
- **requests** — HTTP header enrichment in tech module
- **jinja2** — HTML report templating
- **Go binaries** — subfinder, httpx, gowitness
- **nmap** — port scanning

---

##  Project Structure

recon-automation-pipeline/
├── main.py                    # Entry point + CLI orchestrator
├── report.py                  # HTML report generator
├── requirements.txt
├── modules/
│   ├── subdomains.py          # subfinder wrapper
│   ├── livehosts.py           # httpx wrapper
│   ├── ports.py               # nmap wrapper
│   ├── tech.py                # tech fingerprinting
│   └── screenshots.py         # gowitness wrapper
├── templates/
│   └── recon_report.html.j2   # Jinja2 report template
├── notes/
│   ├── daily-logs/            # Build journal (Day 8–14)
│   └── screenshots/           # Evidence screenshots
└── output/                    # Generated per-target (gitignored)

---

##  Roadmap

-  Interactive charts (Chart.js) in the report
-  Concurrent port scanning (10x faster)
-  Incremental rescans (only new subdomains)
-  Slack/Discord webhook notifications
-  Auto-nuclei scan on discovered live hosts

---

##  Author

**Puneeth Gowda** — Cybersecurity Graduate, Building in Public
- GitHub: [@puni8](https://github.com/puni8)
- Focus: Red Team, Web Pentesting, Bug Bounty

---

##  Legal Disclaimer

This tool is intended for **authorized security testing only**. Only run against systems you own or have explicit written permission to test. The author is not responsible for misuse.

---

##  License

MIT License — see [LICENSE](LICENSE) for details.