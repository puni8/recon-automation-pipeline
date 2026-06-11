"""
Recon Automation Pipeline - Tech Fingerprinting Module
Author: Puneeth Gowda
Purpose: Reads livehosts.json, aggregates the tech stack data captured
         by httpx, enriches it with HTTP header analysis, and produces
         a structured technology profile per host plus a target-wide summary.
"""

import json
import os
import re
from collections import Counter
from datetime import datetime
import requests


# === Patterns to detect tech from HTTP headers ===
# Each pattern checks a specific header for a specific signature.
HEADER_FINGERPRINTS = {
    "Server": {
        r"nginx": "nginx",
        r"apache": "Apache",
        r"cloudflare": "Cloudflare",
        r"openresty": "OpenResty",
        r"litespeed": "LiteSpeed",
        r"iis": "Microsoft IIS",
    },
    "X-Powered-By": {
        r"php": "PHP",
        r"asp\.net": "ASP.NET",
        r"express": "Express.js",
        r"next\.js": "Next.js",
    },
    "X-Generator": {
        r"wordpress": "WordPress",
        r"drupal": "Drupal",
        r"joomla": "Joomla",
    },
    "X-Drupal-Cache": {
        r".+": "Drupal",
    },
    "Set-Cookie": {
        r"wordpress_": "WordPress",
        r"laravel_session": "Laravel",
        r"phpsessid": "PHP",
        r"jsessionid": "Java/JSP",
        r"asp\.net_sessionid": "ASP.NET",
        r"connect\.sid": "Express.js",
    },
    "X-AspNet-Version": {
        r".+": "ASP.NET",
    },
    "X-Cache": {
        r"cloudfront": "AWS CloudFront",
        r"varnish": "Varnish",
    },
}


def fingerprint_from_headers(url, timeout=8):
    """
    Make a single HEAD/GET request and analyze response headers
    for additional technology indicators that httpx may have missed.

    Returns a list of detected technology names.
    """
    detected = set()
    try:
        response = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            verify=False,  # Many target certs are misconfigured - we don't care, we're not authenticating
        )
    except requests.RequestException:
        return list(detected)

    headers = {k.lower(): v for k, v in response.headers.items()}

    for header_name, patterns in HEADER_FINGERPRINTS.items():
        header_value = headers.get(header_name.lower(), "")
        if not header_value:
            continue
        for pattern, tech_name in patterns.items():
            if re.search(pattern, header_value, re.IGNORECASE):
                detected.add(tech_name)

    return list(detected)


def aggregate_tech(target, output_dir, enrich_with_headers=True, enrich_limit=15):
    """
    Read livehosts.json, aggregate tech stack data, optionally enrich
    with additional header-based fingerprinting per host.

    Args:
        target: Root domain
        output_dir: Base output dir
        enrich_with_headers: Whether to do extra fingerprinting per host
        enrich_limit: Max hosts to do extra fingerprinting on (saves time)
    """
    target_dir = os.path.join(output_dir, target)
    livehosts_file = os.path.join(target_dir, "livehosts.json")

    # === Step 1: Load upstream data ===
    if not os.path.exists(livehosts_file):
        print(f"[-] {livehosts_file} not found. Run livehosts module first.")
        return None

    with open(livehosts_file, "r") as f:
        live_data = json.load(f)

    live_hosts = live_data.get("live_hosts", [])
    if not live_hosts:
        print(f"[-] No live hosts to analyze")
        return None

    print(f"[*] Loaded {len(live_hosts)} live hosts")
    print(f"[*] Aggregating technology fingerprints...")

    # === Step 2: Aggregate per-host tech data ===
    host_profiles = []
    tech_counter = Counter()

    # Disable urllib3 warnings for cleaner output (we're testing, not auth'ing)
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    for i, host in enumerate(live_hosts, 1):
        url = host.get("url")
        # Start with httpx's tech detection (already in livehosts.json)
        tech_set = set(host.get("tech", []))

        # Add webserver as a tech if it's not empty
        if host.get("webserver"):
            tech_set.add(host["webserver"])

        # Optional enrichment: extra header analysis (slower but catches more)
        if enrich_with_headers and i <= enrich_limit and url:
            print(f"    [{i}/{min(enrich_limit, len(live_hosts))}] Enriching: {url}")
            extra = fingerprint_from_headers(url)
            tech_set.update(extra)

        host_profile = {
            "url": url,
            "host": host.get("host"),
            "status_code": host.get("status_code"),
            "technologies": sorted(tech_set),
            "tech_count": len(tech_set),
        }
        host_profiles.append(host_profile)

        # Count for aggregate summary
        for t in tech_set:
            tech_counter[t] += 1

    # === Step 3: Build target-wide summary ===
    top_tech = tech_counter.most_common(10)

    print(f"\n[+] Detected {len(tech_counter)} unique technologies across all hosts")
    if top_tech:
        top_str = ", ".join(f"{name} ({count})" for name, count in top_tech[:5])
        print(f"[+] Top stacks: {top_str}")

    findings = {
        "target": target,
        "module": "tech",
        "tool": "httpx + custom header analysis",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "hosts_analyzed": len(host_profiles),
        "unique_technologies": len(tech_counter),
        "tech_distribution": [
            {"technology": name, "host_count": count}
            for name, count in tech_counter.most_common()
        ],
        "host_profiles": host_profiles,
    }

    # === Step 4: Save ===
    output_file = os.path.join(target_dir, "tech.json")
    with open(output_file, "w") as f:
        json.dump(findings, f, indent=2)

    print(f"[+] Output saved to: {output_file}")
    return findings


# === Standalone test ===
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 -m modules.tech <target>")
        print("Example: python3 -m modules.tech hackerone.com")
        sys.exit(1)

    target = sys.argv[1]
    output_dir = "output"

    result = aggregate_tech(target, output_dir)

    if result:
        print(f"\n{'='*60}")
        print(f"  Top 10 technologies across {result['hosts_analyzed']} hosts:")
        print(f"{'='*60}")
        for entry in result["tech_distribution"][:10]:
            bar = "█" * min(entry["host_count"], 30)
            print(f"  {entry['technology']:25} {bar} {entry['host_count']}")