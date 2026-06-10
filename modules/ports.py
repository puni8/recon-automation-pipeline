"""
Recon Automation Pipeline - Port Scanning Module
Author: Puneeth Gowda
Purpose: Reads livehosts.json, runs nmap against each live host,
         and captures open ports with service info.
"""

import subprocess
import json
import os
import re
from datetime import datetime
from urllib.parse import urlparse


def extract_host(url_or_host):
    """Extract hostname from a URL or pass through a plain hostname."""
    if "://" in url_or_host:
        return urlparse(url_or_host).hostname
    return url_or_host


def scan_ports_for_host(hostname, timeout=120):
    """
    Run nmap against a single host and return open ports.

    Uses -F (fast scan: top 100 ports) for speed.
    Use -p 1-1000 if you want more coverage but more time.
    """
    try:
        result = subprocess.run(
            # -F      = fast scan, top 100 TCP ports
            # -sV     = service version detection
            # -Pn     = skip ping check (some hosts block ICMP)
            # -T4     = aggressive timing (faster, still polite)
            # -oG -   = grepable output to stdout (easy to parse)
            ["nmap", "-F", "-sV", "-Pn", "-T4", "-oG", "-", hostname],
            capture_output=True,
            text=True,
            timeout=timeout
        )
    except subprocess.TimeoutExpired:
        print(f"        [-] nmap timed out for {hostname}")
        return []
    except FileNotFoundError:
        print(f"        [-] nmap not found in PATH")
        return []

    if result.returncode != 0:
        # nmap can return non-zero on partial results; don't always bail
        if not result.stdout:
            return []

    # Parse grepable output - lines starting with "Host:" contain port info
    open_ports = []
    for line in result.stdout.splitlines():
        if "Ports:" not in line:
            continue
        # Example line: Host: 1.2.3.4 (host.com)   Ports: 80/open/tcp//http//nginx/, 443/open/tcp//ssl|http//nginx/
        ports_section = line.split("Ports:")[1].strip()
        for port_entry in ports_section.split(","):
            port_entry = port_entry.strip()
            # Each entry: PORT/STATE/PROTO//SERVICE//VERSION/
            parts = port_entry.split("/")
            if len(parts) >= 6 and parts[1] == "open":
                open_ports.append({
                    "port": int(parts[0]),
                    "protocol": parts[2],
                    "service": parts[4] or "unknown",
                    "version": parts[6] if len(parts) > 6 else "",
                })

    return open_ports


def scan_all_live_hosts(target, output_dir, max_hosts=10, per_host_timeout=120):
    """
    Run port scans on every live host from livehosts.json.
    Limits to max_hosts to keep total runtime reasonable.
    """
    target_dir = os.path.join(output_dir, target)
    livehosts_file = os.path.join(target_dir, "livehosts.json")

    # === Load upstream data ===
    if not os.path.exists(livehosts_file):
        print(f"[-] {livehosts_file} not found. Run livehosts module first.")
        return None

    with open(livehosts_file, "r") as f:
        live_data = json.load(f)

    live_hosts = live_data.get("live_hosts", [])
    if not live_hosts:
        print(f"[-] No live hosts to scan")
        return None

    # Cap the number of hosts to scan (port scanning takes time)
    hosts_to_scan = live_hosts[:max_hosts]
    print(f"[*] Scanning ports on {len(hosts_to_scan)} hosts (of {len(live_hosts)} live)")
    if len(live_hosts) > max_hosts:
        print(f"[*] (Limited to first {max_hosts} for speed — adjust max_hosts to scan more)")

    # === Run nmap per host ===
    all_results = []
    for i, host_entry in enumerate(hosts_to_scan, 1):
        hostname = extract_host(host_entry.get("host") or host_entry.get("url"))
        if not hostname:
            continue

        print(f"    [{i}/{len(hosts_to_scan)}] Scanning {hostname}...")
        ports = scan_ports_for_host(hostname, timeout=per_host_timeout)
        print(f"        [+] {len(ports)} open ports found")

        all_results.append({
            "host": hostname,
            "open_ports": ports,
        })

    # === Build findings ===
    total_ports = sum(len(r["open_ports"]) for r in all_results)

    findings = {
        "target": target,
        "module": "ports",
        "tool": "nmap",
        "scan_type": "Top 100 TCP ports with service detection",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "hosts_scanned": len(all_results),
        "total_open_ports": total_ports,
        "results": all_results,
    }

    output_file = os.path.join(target_dir, "ports.json")
    with open(output_file, "w") as f:
        json.dump(findings, f, indent=2)

    print(f"\n[+] Total open ports across all hosts: {total_ports}")
    print(f"[+] Output saved to: {output_file}")
    return findings


# === Standalone test ===
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 -m modules.ports <target> [max_hosts]")
        print("Example: python3 -m modules.ports hackerone.com 5")
        sys.exit(1)

    target = sys.argv[1]
    max_hosts = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    output_dir = "output"

    result = scan_all_live_hosts(target, output_dir, max_hosts=max_hosts)

    if result and result["results"]:
        print(f"\n{'='*60}")
        print(f"  Port scan summary:")
        print(f"{'='*60}")
        for entry in result["results"]:
            print(f"\n  {entry['host']}: {len(entry['open_ports'])} open ports")
            for port in entry["open_ports"][:5]:
                print(f"    • {port['port']}/{port['protocol']} - {port['service']} {port['version']}")
            if len(entry["open_ports"]) > 5:
                print(f"    ... and {len(entry['open_ports']) - 5} more")