"""
Recon Automation Pipeline - Subdomain Enumeration Module
Author: Puneeth Gowda
Purpose: Wraps subfinder via subprocess to enumerate subdomains of a target
         and produce structured JSON output for downstream modules.
"""

import subprocess
import json
import os
from datetime import datetime


def enumerate_subdomains(target, output_dir, timeout=300):
    """
    Run subfinder against a target domain and return discovered subdomains.

    Args:
        target (str): The root domain to enumerate (e.g., "example.com")
        output_dir (str): Directory where JSON output will be saved
        timeout (int): Max seconds to wait for subfinder (default 5 min)

    Returns:
        dict: Structured result with metadata and the subdomain list
    """
    print(f"[*] Starting subdomain enumeration for: {target}")
    print(f"[*] Running subfinder (timeout: {timeout}s)...")

    try:
        # Run subfinder as a subprocess and capture its output
        # -d   = domain to enumerate
        # -silent = output only domain names, no banner/logs
        result = subprocess.run(
            ["subfinder", "-d", target, "-silent"],
            capture_output=True,
            text=True,
            timeout=timeout
        )
    except subprocess.TimeoutExpired:
        print(f"[-] subfinder timed out after {timeout}s")
        return None
    except FileNotFoundError:
        print(f"[-] subfinder not found in PATH. Is it installed?")
        return None

    # Check if subfinder ran successfully
    if result.returncode != 0:
        print(f"[-] subfinder failed (exit code {result.returncode})")
        print(f"[-] stderr: {result.stderr[:200]}")
        return None

    # Parse the output - each subdomain is on its own line
    raw_output = result.stdout.strip()
    if not raw_output:
        print(f"[-] No subdomains discovered for {target}")
        subdomains = []
    else:
        # Split by newline, strip whitespace, remove duplicates and empties
        subdomains = sorted(set(
            line.strip() for line in raw_output.splitlines() if line.strip()
        ))

    print(f"[+] Found {len(subdomains)} unique subdomains")

    # Build structured result
    findings = {
        "target": target,
        "module": "subdomains",
        "tool": "subfinder",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "count": len(subdomains),
        "subdomains": subdomains,
    }

    # Save to JSON in target-specific output folder
    target_dir = os.path.join(output_dir, target)
    os.makedirs(target_dir, exist_ok=True)

    output_file = os.path.join(target_dir, "subdomains.json")
    with open(output_file, "w") as f:
        json.dump(findings, f, indent=2)

    print(f"[+] Output saved to: {output_file}")
    return findings


# === Standalone test (run this file directly to test the module) ===
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 -m modules.subdomains <target>")
        print("Example: python3 -m modules.subdomains example.com")
        sys.exit(1)

    target = sys.argv[1]
    output_dir = "output"

    result = enumerate_subdomains(target, output_dir)

    if result:
        print(f"\n{'='*50}")
        print(f"  Sample of discovered subdomains (first 5):")
        print(f"{'='*50}")
        for sub in result["subdomains"][:5]:
            print(f"  • {sub}")
        if result["count"] > 5:
            print(f"  ... and {result['count'] - 5} more")