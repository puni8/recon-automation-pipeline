import argparse
import json
import os
import sys
import time

from modules.subdomains import enumerate_subdomains
from modules.livehosts import detect_live_hosts
from modules.ports import scan_all_live_hosts
from modules.tech import aggregate_tech
from modules.screenshots import capture_all_screenshots
from report import generate_report


# === ASCII Banner ===
BANNER = r"""
 ____                          ____  _            _ _
|  _ \ ___  ___ ___  _ __    |  _ \(_)_ __   ___| (_)_ __   ___
| |_) / _ \/ __/ _ \| '_ \   | |_) | | '_ \ / _ \ | | '_ \ / _ \
|  _ <  __/ (_| (_) | | | |  |  __/| | |_) |  __/ | | | | |  __/
|_| \_\___|\___\___/|_| |_|  |_|   |_| .__/ \___|_|_|_| |_|\___|
                                       |_|
     Recon Automation Pipeline v1.0  |  by Puneeth Gowda
     Modules: subdomains → livehosts → ports → tech → screenshots → report
"""


def print_phase(num, title):
    """Print a clearly-marked phase header."""
    print(f"\n{'='*60}")
    print(f"  PHASE {num}: {title}")
    print(f"{'='*60}")


def save_json(data, filepath):
    """Helper to save intermediate JSON to disk."""
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def main():
    # === CLI Arguments ===
    parser = argparse.ArgumentParser(
        description="Recon Automation Pipeline — automated attack surface mapping",
        epilog="Example: python3 main.py --target hackerone.com"
    )
    parser.add_argument(
        "--target", required=True,
        help="Target root domain (e.g., hackerone.com)"
    )
    parser.add_argument(
        "--output", default="output",
        help="Base output directory (default: output)"
    )
    parser.add_argument(
        "--report", default="report.html",
        help="Output report filename (default: report.html)"
    )
    parser.add_argument(
        "--max-hosts", type=int, default=10,
        help="Max hosts for port scanning + screenshots (default: 10)"
    )
    parser.add_argument(
        "--no-banner", action="store_true",
        help="Suppress ASCII banner"
    )
    args = parser.parse_args()

    # === Banner ===
    if not args.no_banner:
        print(BANNER)

    print(f"[*] Target:  {args.target}")
    print(f"[*] Output:  {args.output}/{args.target}/")
    print(f"[*] Report:  {args.output}/{args.target}/{args.report}")

    start_time = time.time()
    output_dir = args.output
    target = args.target

    # Ensure output dir exists
    os.makedirs(os.path.join(output_dir, target), exist_ok=True)

    # === Phase 1: Subdomain Enumeration ===
    print_phase(1, "SUBDOMAIN ENUMERATION")
    sub_result = enumerate_subdomains(target, output_dir)
    if not sub_result:
        print("[-] Subdomain enumeration failed. Exiting.")
        sys.exit(1)
    print(f"[+] Phase 1 complete: {sub_result['count']} subdomains")

    # === Phase 2: Live Host Detection ===
    print_phase(2, "LIVE HOST DETECTION")
    live_result = detect_live_hosts(target, output_dir)
    if not live_result:
        print("[-] Live host detection failed. Exiting.")
        sys.exit(1)
    print(f"[+] Phase 2 complete: {live_result['live_count']} live hosts")

    # === Phase 3: Port Scanning ===
    print_phase(3, "PORT SCANNING")
    port_result = scan_all_live_hosts(
        target, output_dir, max_hosts=args.max_hosts
    )
    if port_result:
        print(f"[+] Phase 3 complete: {port_result['total_open_ports']} open ports")
    else:
        print("[!] Port scanning skipped or failed — continuing")

    # === Phase 4: Tech Fingerprinting ===
    print_phase(4, "TECH FINGERPRINTING")
    tech_result = aggregate_tech(target, output_dir)
    if tech_result:
        print(f"[+] Phase 4 complete: {tech_result['unique_technologies']} technologies")
    else:
        print("[!] Tech fingerprinting skipped or failed — continuing")

    # === Phase 5: Screenshots ===
    print_phase(5, "SCREENSHOT CAPTURE")
    shot_result = capture_all_screenshots(
        target, output_dir, max_hosts=args.max_hosts
    )
    if shot_result:
        print(f"[+] Phase 5 complete: {shot_result['hosts_captured']} screenshots")
    else:
        print("[!] Screenshot capture skipped or failed — continuing")

    # === Phase 6: Report Generation ===
    print_phase(6, "REPORT GENERATION")
    report_path = generate_report(target, output_dir, args.report)

    # === Final Summary ===
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"  PIPELINE COMPLETE")
    print(f"{'='*60}")
    print(f"  Target:     {target}")
    print(f"  Subdomains: {sub_result['count']}")
    print(f"  Live hosts: {live_result['live_count']}")
    print(f"  Time:       {elapsed:.1f} seconds")
    print(f"  Report:     {report_path}")
    print(f"\n  Open: firefox {report_path}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()