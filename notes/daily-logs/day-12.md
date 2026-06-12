# Day 12 — Screenshot Capture Module (Data Layer Complete)

**Date:** June 11, 2026
**Time spent:** ~80 minutes
**Project:** Project 2 — Recon Automation Pipeline

---

## 🎯 Today's Goal
Build the 5th and final data-gathering module — screenshot capture via gowitness — to complete the data layer of Project 2. After today, every recon module is in place and the project moves from "build features" to "package and ship."

---

## ✅ What I accomplished today

- [x] Created `modules/screenshots.py` (~150 lines)
- [x] Wrapped `gowitness scan single` via subprocess (gowitness v3 syntax)
- [x] Designed the manifest pattern — JSON stores paths to images, not images themselves
- [x] Implemented failure capture — each unsuccessful capture stores its reason
- [x] Captured real screenshots of hackerone.com pages (docs, support, www)
- [x] Verified screenshots visually in file manager
- [x] Iterated when first run produced low success rate (1/5) → adjusted to bigger host limit
- [x] Designed (but skipped applying) a smart filter to prioritize web apps over infrastructure subdomains — decided to move on since real captures were sufficient
- [x] Committed and pushed module
- [x] Posted Day 12 LinkedIn with visual screenshot gallery
- [x] All 5 data-gathering modules of Project 2 are now complete

---

## 🔧 Code I built today

### File: `modules/screenshots.py` (~150 lines)

**Functions written:**
- `safe_filename_from_url(url)` — sanitizes URLs into filename-safe strings
- `capture_screenshot(url, screenshot_dir, timeout)` — single-host capture; returns (path, status) tuple where status explains success or specific failure mode
- `capture_all_screenshots(target, output_dir, max_hosts, per_host_timeout)` — orchestrates capture across all live hosts

**Side-effect detection:** gowitness writes files; the module doesn't get an output filename from gowitness directly. Instead it watches the directory and grabs the most-recently-created file (`max(files, key=os.path.getmtime)`). This is a useful pattern when wrapping tools that don't tell you exactly what they produced.

**Manifest output:** `screenshots.json` is a manifest — it lists what was captured and where the file lives, NOT the image bytes. Real production systems (CDNs, cloud storage) all use this pattern. JSON for metadata, disk/object-storage for binaries.

---

## 🧠 Key concepts I learned today

### 1. Failures are data, not just errors
Every failed capture records WHY it failed — `timeout`, `no file produced`, `exit code N`. When the report generator runs tomorrow, I can render failed entries in the gallery with their reason, instead of silently hiding them. Real pentest reports do this — a "could not assess this subdomain because X" is far more credible than pretending the subdomain doesn't exist.

### 2. The manifest pattern
Big binary assets (images, video, datasets) don't belong inside JSON or any structured-data file. The professional pattern: keep the assets on disk (or object storage), and let a small JSON file act as the catalog. Every major file system has this pattern — package.json in Node, requirements.txt in Python, manifest.json in browser extensions, package-lock.json for dependency trees.

### 3. Side-effect tools need watchful wrappers
Tools that produce stdout (subfinder, httpx) are easy to wrap — you parse the output. Tools that produce files (gowitness, masscan with file output) need the wrapper to inspect the filesystem AFTER the run. Using `os.path.getmtime` to find the most recent file is a reliable way to track "what did this run actually produce?".

### 4. Pragmatic stopping point
I designed a smart filter to prioritize web apps over DNS infrastructure subdomains. After looking at the actual output, I realized the basic filter (status 2xx-3xx hosts) was already getting good captures, and the marginal improvement from the smart filter wasn't worth the time. **Engineering judgment includes knowing when "good enough" is actually good enough.** A v2.0 of this module could ship a better filter. v1.0 doesn't need it.

### 5. Realistic capture rates
Not every live host produces a screenshot. DNS nameservers respond to httpx but have no HTML. SSL-mismatched hosts time out. Cloudflare WAF blocks some captures. **A 40-60% capture rate is normal** even for professional tools like Aquatone. My module records the failures, so the report can show "scanned 100 hosts, captured 47, here's why 53 failed" — that's honest reporting.

---

## 🚧 What I struggled with

- The first capture run got 1/5 (20%). My initial instinct was "module is broken." Real cause: the first 5 hosts of `livehosts.json` happened to be infrastructure subdomains (ns., mta-sts.) that don't have visual content. Bumped the limit to 15, got 5/10 — and 3 of those were meaningful web pages.
- Spent some time trying to apply a smart-filter patch via a copy-paste edit in VS Code. Indentation got tangled in the paste process. Reverted to a clean "replace the whole function" approach, which is safer for any non-trivial change. **Lesson: for multi-line edits to existing code, replacing whole units (functions, classes) is more reliable than patching individual lines.**
- Eventually decided NOT to apply the smart filter at all — the unfiltered version already produced enough good captures for the portfolio. Saved 20 minutes by stopping when the result was sufficient.

---

## 🔍 Sample output

```json
{
  "target": "hackerone.com",
  "module": "screenshots",
  "tool": "gowitness",
  "hosts_attempted": 10,
  "hosts_captured": 5,
  "screenshot_dir": "screenshots",
  "results": [
    {
      "url": "https://docs.hackerone.com",
      "host": "docs.hackerone.com",
      "status_code": 200,
      "title": "HackerOne Documentation",
      "screenshot_path": "screenshots/https---docs.hackerone.com.jpeg",
      "captured": true
    },
    {
      "url": "https://gslink.hackerone.com",
      "captured": false,
      "error": "timeout"
    }
  ]
}
```

Both successes and failures are recorded. The HTML report tomorrow will render successes as a gallery and failures as a small "skipped" section with their reasons.

---

## ❓ Questions I want to research

- **Headless browser fingerprinting:** some sites detect gowitness's headless Chrome and serve different content (or block entirely). Is there a way to make captures more "real" looking?
- **Parallel capture:** my module captures sequentially. For 100+ hosts, parallel capture could cut runtime 5-10x. Trade-off: more memory used, harder to debug, possible rate-limit issues. Worth it for a v2.
- **Visual diff between scans:** if I scan the same target weekly, can I compute image diffs to alert when a subdomain's UI changes? That's how some serious bug bounty hunters monitor for new features (= new attack surface).

---

## 📌 Next session plan (Day 13)

Build the **HTML report generator** (`report.py`):
- Read all 5 module outputs (subdomains, livehosts, ports, tech, screenshots)
- Use Jinja2 templating (reuse Project 1's pattern — the architecture compounds again)
- Sections: executive summary, attack surface map, port summary, tech distribution, screenshot gallery
- Output: a single, polished `report.html` that visualizes all the recon in one page
- Estimated time: 90 minutes (Project 1's template system carries over)

Day 14: `main.py` orchestrator + README + ship v1.0.

---

## 🎯 Progress check

**Sessions completed:** 12
**Project 2 progress:** Data layer 100% complete (5 of 5 modules). Reporting layer next.
**Confidence level:** 9/10 — the architecture has held up beautifully across all 5 modules
**Energy level for next session:** 9/10 — excited to make this visually impressive

---

## 💭 Reflection — the engineering judgment lesson

The most valuable thing I learned today wasn't a technique — it was a *judgment call*.

When the first screenshot run got 1/5, I had two paths:
1. Engineer my way to a higher success rate (smart filter, retries, different tool)
2. Look at WHY the failures happened, accept them as legitimate, and move on

I started down path 1 (built the smart filter), then realized path 2 was the right call. The real-world value of recon screenshots isn't 100% capture — it's catching the few interesting hosts you can. 3 captures of `docs/support/www.hackerone.com` is genuinely useful. Spending an hour to also screenshot `a.ns.hackerone.com` (a DNS server with no UI) would be wasted time.

**Senior engineers don't just build well — they also know when to stop.** Today I practiced stopping. That's harder than building.

---

## 📷 Screenshots saved

- `day12-screenshot-gallery.png` — file manager showing captured screenshots of hackerone.com pages
- `day12-module-running.png` — terminal output showing capture progress and summary
