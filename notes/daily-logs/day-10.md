# Day 10 — Live Host Detection + Port Scanning Modules

**Date:** JUNE 10, 2026
**Time spent:** ~90 minutes
**Project:** Project 2 — Recon Automation Pipeline

---

## 🎯 Today's Goal
Build two recon modules in a single session — live host detection (`httpx`) and port scanning (`nmap`). The goal isn't just the code; it's to validate that yesterday's architecture pays off. If modules 2 and 3 take half the time of module 1, the design is sound.

---

## ✅ What I accomplished today

- [x] Created `modules/livehosts.py` (~110 lines)
- [x] Implemented stdin-piping pattern with `subprocess.run(input=...)`
- [x] Parsed httpx's JSON-lines output (one JSON object per line)
- [x] Captured rich metadata per host: status code, title, web server, tech stack, response size
- [x] Tested against hackerone.com — found live hosts from upstream subdomains.json
- [x] Created `modules/ports.py` (~130 lines)
- [x] Used nmap's grepable output (`-oG -`) for easy parsing
- [x] Added `urllib.parse.urlparse()` to extract hostnames from URLs
- [x] Implemented `max_hosts` cap as a safety mechanism for port scanning
- [x] Added per-host timeout (so one slow host doesn't block the entire scan)
- [x] Tested ports module — captured services with version info
- [x] Committed both modules to GitHub
- [x] Posted Day 10 LinkedIn update emphasizing architectural compounding

---

## 🔧 Code I built today

### File: `modules/livehosts.py` (~110 lines)

**Function written:**
- `detect_live_hosts(target, output_dir, timeout=300)` — reads subdomains.json → pipes through httpx → returns structured live host data

**Key implementation details:**
- `subprocess.run(input="\n".join(subdomains))` — feeds subdomain list into httpx via stdin
- Parses JSON-lines output (each line is a separate JSON object)
- Uses `.get()` with defaults for resilient field access — avoids KeyError if a field is missing
- `try/except json.JSONDecodeError` per line — malformed lines are skipped, not fatal

### File: `modules/ports.py` (~130 lines)

**Functions written:**
- `extract_host(url_or_host)` — strips `https://` and paths to get clean hostnames
- `scan_ports_for_host(hostname, timeout)` — single-host nmap invocation
- `scan_all_live_hosts(target, output_dir, max_hosts)` — orchestration over all live hosts

**Key implementation details:**
- nmap flags: `-F -sV -Pn -T4 -oG -` (fast scan, version detection, skip ping, aggressive timing, grepable to stdout)
- Parses grepable output by splitting `"Ports:"` line and slash-delimited port entries
- `max_hosts` parameter caps scan scope — prevents accidental hour-long scans on large targets
- Per-host loop with progress indicator (`[i/N] Scanning ...`)

---

## 🧠 Key concepts I learned today

### 1. Stdin piping with subprocess
Yesterday's pattern: `subprocess.run([cmd, arg1, arg2])`. Today's evolution: `subprocess.run([cmd], input=data, ...)` to FEED data INTO the tool via stdin. This unlocks every tool that reads from stdin (httpx, nmap, ffuf, nuclei, gobuster). Same pattern as Unix piping (`echo "x" | tool`) but from Python.

### 2. JSON-lines is everywhere in security tooling
Many tools (httpx, masscan, nuclei) output **one JSON object per line** instead of a single JSON array. This is called "JSON Lines" or "ndjson". The parsing pattern is: loop over `result.stdout.splitlines()`, `json.loads()` each line, skip malformed ones. This format is streaming-friendly and easier to append to.

### 3. nmap grepable output (`-oG -`)
nmap has three output formats: normal (human-readable), XML (structured but verbose), and grepable (one host per line, easy to split). `-oG -` sends grepable output to stdout. For automation, grepable beats XML for simple parsing — XML would need an XML parser; grepable just needs `.split()`.

### 4. Per-host vs per-target operations
Subfinder is one-shot per target. nmap is one-shot per HOST. When wrapping per-host tools, you need a loop with progress indication and per-host error handling. One host failing shouldn't kill the whole scan.

### 5. Safety caps as production engineering
The `max_hosts` parameter isn't just a feature — it's a safety mechanism. Without it, an inexperienced user could accidentally launch a 10-hour scan against 1000 hosts. Defaults that prevent foot-guns ARE part of good design.

### 6. The compounding pattern (the meta-lesson of today)
Module 1 yesterday: 75 min. Module 2 today: ~35 min. Module 3 today: ~45 min. Total Day 10: ~80 min for two modules. **Why?** The architecture was already designed:
- subprocess wrapper pattern → just plug in new tool name
- JSON output structure → identical shape per module
- Per-target output folder → already established  
- Error handling philosophy → already decided
- Standalone-test pattern → already in place

This is the value of investing in architecture early. The cost is felt on Day 1. The benefit compounds on every day after.

---

## 🚧 What I struggled with

- **nmap output parsing:** my first attempt tried to parse nmap's "normal" output, which is human-readable but inconsistent across nmap versions. Switched to `-oG -` (grepable) which is stable and easy to split. Lesson: when wrapping a CLI tool, look for its machine-readable output format.
- **URL vs hostname confusion:** httpx returns URLs like `https://api.hackerone.com`, but nmap wants just `api.hackerone.com`. Wrote `extract_host()` to handle this — used `urlparse()` because manually stripping `https://` would miss edge cases (subdomains with `://` in titles, IPv6 brackets, etc.).
- Port scanning is **slow** — even with `-T4`, scanning top 100 ports per host takes 1-3 minutes. Capping `max_hosts` to 3-5 makes development iteration sane. Production users can bump it to 50+.

---

## 🔍 Sample output from `ports.json`

```json
{
  "target": "hackerone.com",
  "module": "ports",
  "tool": "nmap",
  "scan_type": "Top 100 TCP ports with service detection",
  "hosts_scanned": 3,
  "total_open_ports": 7,
  "results": [
    {
      "host": "api.hackerone.com",
      "open_ports": [
        {"port": 80, "protocol": "tcp", "service": "http", "version": "nginx"},
        {"port": 443, "protocol": "tcp", "service": "ssl/http", "version": "nginx"}
      ]
    }
  ]
}
```

---

## ❓ Questions I want to research / ask my mentor

- **Concurrency:** my ports module scans hosts sequentially. Could I use Python's `concurrent.futures` to scan multiple hosts in parallel? Trade-off is speed vs. politeness toward the target.
- **UDP scanning:** I'm only scanning TCP. UDP is slower and noisier but reveals different services (DNS, SNMP, NTP). Worth adding as a separate `--udp` flag?
- **Banner grabbing depth:** `-sV` does version detection but skips many service-specific banners. Tools like `whatweb` and `wappalyzer` go deeper for web tech fingerprinting (what Day 11 covers).

---

## 📌 Tomorrow's plan (Day 11)

Build the **tech fingerprinting + screenshot modules**:
- `modules/tech.py` — wraps `webtech` or `wappalyzer-cli` for deeper web tech detection per host
- `modules/screenshots.py` — wraps `gowitness` to capture visual screenshots of every live host
- Per-host screenshot gallery saved to `output/<target>/screenshots/`
- Same architectural pattern: subprocess wrap → structured JSON → upstream/downstream chaining

Day 12 = HTML report generator (reuse Project 1 Jinja2 pattern). Day 13 = orchestrator + ship.

---

## 🎯 Progress check

**Days completed:** 10 / 28 (36%)
**Project 2 progress:** 3 of 5 modules done (60% of detection layer)
**Confidence level:** 9/10 — the architecture pays off in real time
**Energy level for tomorrow:** 9/10

---

## 💭 Reflection — the unexpected lesson

Today proved a theory I built in Project 1 but couldn't verify until now: **good architecture compounds linearly with how often you reuse it.**

When I finished Project 1's modular scanner on Day 7, it felt like I had over-engineered things. Three different scanner files? Separate report.py? It seemed like more work than needed for a learning project.

Then today, I added two completely new modules and barely had to think about structure. `subprocess.run()`, parse output, save JSON, write standalone test. The shape was decided already.

The lesson scales beyond code. **Investing in clarity early — in code, in note-taking, in habits, in how I describe my work on LinkedIn — pays compounding dividends.** Architecture isn't optional. It's the difference between sprinting and dragging by Day 30.

---

## 📷 Screenshots saved

- `day10-livehosts-running.png` — terminal showing live host detection in progress
- `day10-ports-running.png` — nmap output showing open ports per host
- `day10-json-output.png` — sample of structured JSON output
