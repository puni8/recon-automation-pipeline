# Day 9 — Subdomain Enumeration Module

**Date:** May 23, 2026
**Time spent:** ~75 minutes
**Project:** Project 2 — Recon Automation Pipeline

---

## 🎯 Today's Goal
Build the first module of the recon pipeline — a Python wrapper around `subfinder` that takes a target domain, enumerates subdomains via passive sources, and produces structured JSON output that downstream modules (httpx, nmap, etc.) can consume.

---

## ✅ What I accomplished today

- [x] Created `modules/subdomains.py` (~80 lines)
- [x] Learned and used Python's `subprocess` module to call CLI tools
- [x] Implemented proper error handling: TimeoutExpired, FileNotFoundError, non-zero return codes
- [x] Designed structured JSON output: target, module, tool, timestamp, count, subdomains list
- [x] Per-target output folders (`output/<domain>/`) for clean organization
- [x] Standalone-runnable module: `python3 -m modules.subdomains <target>`
- [x] Hit a 5-minute timeout on google.com — diagnosed the cause (huge subdomain space, not a code bug)
- [x] Successfully tested on hackerone.com and tesla.com
- [x] Committed and pushed to GitHub
- [x] Posted Day 9 LinkedIn update

---

## 🔧 Code I built today

### File: `modules/subdomains.py` (~80 lines)

**Function written:**
- `enumerate_subdomains(target, output_dir, timeout=300)` — full subfinder wrapper

**Key implementation details:**
- `subprocess.run()` with `capture_output=True, text=True` for clean stdout capture
- `timeout=300` parameter prevents hung processes from blocking the pipeline
- Three error paths: timeout, missing binary, non-zero exit code — each with helpful messages
- Deduplication: `sorted(set(...))` removes duplicates and sorts alphabetically
- Output writes to `output/<target>/subdomains.json` — keeps scans isolated per target

**Output:** Structured JSON ready for downstream consumption.

---

## 🧠 Key concepts I learned today

### 1. `subprocess` is the bridge between Python and CLI tools
Project 1 used `requests` to make HTTP calls — but Project 2 needs to call binary tools (subfinder, nmap, etc.). `subprocess.run()` lets Python run any terminal command, capture its output, and parse the results. This is the foundation of every recon framework ever built.

### 2. Always set a timeout
Recon tools can hang on slow API responses or massive target domains. Without `timeout=`, a single bad query could lock up the whole pipeline. The `try/except subprocess.TimeoutExpired` pattern is the safety net.

### 3. Three error paths every wrapper needs
When wrapping a CLI tool, three things can go wrong:
- **The tool isn't installed** → `FileNotFoundError`
- **The tool hangs forever** → `TimeoutExpired`
- **The tool runs but fails** → non-zero `returncode`

Each needs its own handler with a clear error message. I implemented all three.

### 4. Exit codes matter in Unix tools
`result.returncode == 0` means success in Unix convention. Non-zero means something went wrong. Many beginners just check stdout without checking returncode, missing silent failures. Catching this is professional behavior.

### 5. Per-target output folders prevent overlap
By writing to `output/<target>/subdomains.json` instead of just `output/subdomains.json`, I can scan multiple targets in sequence without overwriting results. This scales to bug bounty workflows where you scan many domains.

### 6. `python3 -m modules.subdomains` runs a module from a package
The `-m` flag means "run a module by its dotted name." This is how Python's standard library is invoked. Knowing this is a sign you understand Python's package system. Most beginners don't.

---

## 🚧 What I struggled with

- First test ran `python3 -m modules.subdomains google.com` — timed out at 300 seconds. Initial assumption: "my code is broken." Reality: google.com has thousands of subdomains across 30+ data sources, and subfinder was correctly trying to enumerate all of them. The timeout fired exactly as designed.
- **Lesson:** when something times out, the problem isn't always your code. Sometimes it's the *scope* of what you asked. I switched to a smaller target (hackerone.com) and it completed in 60 seconds with ~50 subdomains. Always pick test targets realistic to your timeout.
- Brief confusion about `python3 modules/subdomains.py` vs `python3 -m modules.subdomains` — the `-m` flag is needed when the file imports from its sibling files (because Python sets `sys.path` differently). For now my module is self-contained, so both work, but `-m` is the convention for package-internal modules.

---

## 🔍 Sample output

```json
{
  "target": "hackerone.com",
  "module": "subdomains",
  "tool": "subfinder",
  "timestamp": "2026-05-23T14:32:00",
  "count": 48,
  "subdomains": [
    "api.hackerone.com",
    "docs.hackerone.com",
    "mta-sts.hackerone.com",
    "..."
  ]
}
```

Each subdomain is a potential attack surface. Tomorrow's httpx module reads this JSON, hits each subdomain, and determines which are live.

---

## ❓ Questions I want to research / ask my mentor

- **Source selection:** subfinder by default queries 30+ data sources. For faster scans, can I limit to fast/reliable ones (crtsh, hackertarget, virustotal)? Trade-off is completeness vs. speed.
- **Active recon:** I'm using subfinder which is fully passive (pulls from public databases, never touches the target). For deeper enumeration, would adding active brute-forcing (with `puredns` + wordlist) be worth the complexity? Note: active enumeration usually needs explicit program permission.
- **Rate limiting:** if I run my pipeline on a bug bounty target nightly, am I going to get my IP blocked by data sources like Shodan/VirusTotal? Should the module support API key configuration?

---

## 📌 Tomorrow's plan (Day 10)

Build the **live host detection module** (`modules/livehosts.py`):
- Read `subdomains.json` as input
- Pipe every subdomain through `httpx` to check which are reachable on HTTP/HTTPS
- Capture status codes, page titles, response sizes, technologies detected
- Output: `output/<target>/livehosts.json`

Also add the **port scan module** (`modules/ports.py`) if time permits:
- Read live hosts → scan top 100 TCP ports with nmap
- Output: per-host port findings

The pattern repeats — `subprocess` wrapper, structured JSON, per-target isolation. Just like Project 1's modular detection scanners, but now wrapping external tools instead of writing internal logic.

---

## 🎯 Progress check

**Days completed:** 9 / 28 (32%)
**Project 2 progress:** Module 1 of ~5 complete (subdomains ✅)
**Confidence level:** 8/10 — subprocess pattern clicked fast, error handling came naturally
**Energy level for tomorrow:** 9/10 — now that the pattern is set, modules 2-3 should be fast

---

## 💭 Reflection — the unexpected lesson

The most valuable thing today wasn't the working code — it was the debugging instinct that kicked in when subfinder timed out.

Beginner instinct: "It broke. What did I do wrong?"
Trained instinct: "What does the error tell me? When does this fail? What's actually being asked?"

I noticed `subfinder timed out after 300s` — that's not a code error, that's a duration error. The code ran. It just couldn't finish in time. So either the timeout was wrong, the target was too big, or the tool needed configuring. Switching to a smaller target proved the third option correct.

**Pentesting is 90% reading error messages carefully.** Today I read one well and saved myself 30 minutes of debugging.

---

## 📷 Screenshots saved

- `day9-subfinder-working.png` — terminal showing `[+] Found X subdomains` with sample list
- `day9-subdomains-json.png` — `cat` output of structured JSON
