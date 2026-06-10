"""
Recon Automation Pipeline - Live Host Detection Module
Author: Puneeth Gowda
Purpose: Reads subdomains.json, probes each subdomain via httpx,
         and captures live hosts with metadata (status, title, tech, server).
"""

import subprocess
import json
import os
from datetime import datetime


def detect_live_hosts(target, output_dir, timeout=300):
    """
    Probe all subdomains of a target via httpx and capture live ones.

    Args:
        target (str): The root domain (e.g., "hackerone.com")
        output_dir (str): Directory containing the target's subdomains.json
        timeout (int): Max seconds for httpx run

    Returns:
        dict: Structured result with all live host metadata
    """
    target_dir = os.path.join(output_dir, target)
    subdomains_file = os.path.join(target_dir, "subdomains.json")

    # === Step 1: Load subdomains from upstream module ===
    if not os.path.exists(subdomains_file):
        print(f"[-] {subdomains_file} not found. Run subdomains module first.")
        return None

    with open(subdomains_file, "r") as f:
        subdomain_data = json.load(f)

    subdomains = subdomain_data.get("subdomains", [])
    if not subdomains:
        print(f"[-] No subdomains to probe")
        return None

    print(f"[*] Loaded {len(subdomains)} subdomains to probe")
    print(f"[*] Running httpx (timeout: {timeout}s)...")

    # === Step 2: Pipe subdomains into httpx ===
    # httpx reads from stdin when you pipe input to it
    # -json     = output as JSON lines (one JSON object per line)
    # -status-code, -title, -tech-detect, -web-server = extract these fields
    # -silent   = no banner
    # -timeout 10 = give each host 10s before giving up
    subdomain_input = "\n".join(subdomains)

    try:
        result = subprocess.run(
            ["httpx", "-json", "-silent", "-status-code", "-title",
             "-tech-detect", "-web-server", "-timeout", "10"],
            input=subdomain_input,
            capture_output=True,
            text=True,
            timeout=timeout
        )
    except subprocess.TimeoutExpired:
        print(f"[-] httpx timed out after {timeout}s")
        return None
    except FileNotFoundError:
        print(f"[-] httpx not found in PATH. Is it installed?")
        return None

    if result.returncode != 0:
        print(f"[-] httpx failed (exit code {result.returncode})")
        print(f"[-] stderr: {result.stderr[:200]}")
        return None

    # === Step 3: Parse httpx's JSON-lines output ===
    # Each line of stdout is a separate JSON object describing one live host
    live_hosts = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            host_data = json.loads(line)
            live_hosts.append({
                "url": host_data.get("url"),
                "host": host_data.get("host") or host_data.get("input"),
                "status_code": host_data.get("status_code"),
                "title": host_data.get("title", ""),
                "webserver": host_data.get("webserver", ""),
                "tech": host_data.get("tech", []),
                "content_length": host_data.get("content_length", 0),
            })
        except json.JSONDecodeError:
            continue  # Skip malformed lines (rare)

    print(f"[+] Found {len(live_hosts)} live hosts (out of {len(subdomains)} subdomains)")

    # === Step 4: Build structured findings ===
    findings = {
        "target": target,
        "module": "livehosts",
        "tool": "httpx",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "subdomains_probed": len(subdomains),
        "live_count": len(live_hosts),
        "live_hosts": live_hosts,
    }

    # === Step 5: Save to JSON ===
    output_file = os.path.join(target_dir, "livehosts.json")
    with open(output_file, "w") as f:
        json.dump(findings, f, indent=2)

    print(f"[+] Output saved to: {output_file}")
    return findings


# === Standalone test ===
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 -m modules.livehosts <target>")
        print("Example: python3 -m modules.livehosts hackerone.com")
        sys.exit(1)

    target = sys.argv[1]
    output_dir = "output"

    result = detect_live_hosts(target, output_dir)

    if result and result["live_hosts"]:
        print(f"\n{'='*60}")
        print(f"  Sample of live hosts (first 5):")
        print(f"{'='*60}")
        for host in result["live_hosts"][:5]:
            tech_str = ", ".join(host["tech"]) if host["tech"] else "—"
            print(f"  • {host['url']}")
            print(f"      Status: {host['status_code']}  |  Title: {host['title'][:50] or '—'}")
            print(f"      Tech: {tech_str}")
        if result["live_count"] > 5:
            print(f"\n  ... and {result['live_count'] - 5} more")