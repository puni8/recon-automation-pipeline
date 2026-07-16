import json
import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader


# === Configuration ===
TEMPLATE_DIR = "templates"
TEMPLATE_FILE = "recon_report.html.j2"
TESTER_NAME = "Puneeth Gowda"


def load_json_safe(filepath):
    """Load a JSON file, return None if missing or malformed."""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def generate_report(target, output_dir="output", output_file="report.html"):
    """
    Read all module outputs for a target and render the HTML report.
    Gracefully handles missing modules — sections show placeholder text.
    """
    target_dir = os.path.join(output_dir, target)

    print(f"[*] Generating report for: {target}")
    print(f"[*] Reading module outputs from: {target_dir}")

    # === Load all module outputs ===
    subdomains_data = load_json_safe(os.path.join(target_dir, "subdomains.json"))
    livehosts_data  = load_json_safe(os.path.join(target_dir, "livehosts.json"))
    ports_data      = load_json_safe(os.path.join(target_dir, "ports.json"))
    tech_data       = load_json_safe(os.path.join(target_dir, "tech.json"))
    screenshots_data = load_json_safe(os.path.join(target_dir, "screenshots.json"))

    # === Extract key fields ===
    subdomains   = subdomains_data.get("subdomains", []) if subdomains_data else []
    live_hosts   = livehosts_data.get("live_hosts", []) if livehosts_data else []
    port_results = ports_data.get("results", []) if ports_data else []
    tech_dist    = tech_data.get("tech_distribution", []) if tech_data else []
    screenshots  = screenshots_data.get("results", []) if screenshots_data else []

    # Fix screenshot paths to be relative to where report.html will live
    # report.html is in output/<target>/ so paths like "screenshots/file.jpeg" work directly
    report_output_path = os.path.join(target_dir, output_file)

    # === Compute summary stats ===
    total_open_ports = sum(
        len(r.get("open_ports", [])) for r in port_results
    )
    stats = {
        "subdomains": len(subdomains),
        "live_hosts": len(live_hosts),
        "open_ports": total_open_ports,
        "technologies": len(tech_dist),
        "hosts_scanned": ports_data.get("hosts_scanned", 0) if ports_data else 0,
    }

    print(f"[+] Subdomains: {stats['subdomains']}")
    print(f"[+] Live hosts: {stats['live_hosts']}")
    print(f"[+] Open ports: {stats['open_ports']}")
    print(f"[+] Technologies: {stats['technologies']}")

    # === Render template ===
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template(TEMPLATE_FILE)

    html = template.render(
        target=target,
        report_date=datetime.now().strftime("%B %d, %Y"),
        tester=TESTER_NAME,
        stats=stats,
        live_hosts=live_hosts,
        port_results=port_results,
        tech_distribution=tech_dist,
        screenshots=screenshots,
        subdomains=subdomains,
    )

    # === Save report ===
    with open(report_output_path, "w") as f:
        f.write(html)

    size_kb = os.path.getsize(report_output_path) // 1024
    print(f"\n[+] Report saved: {report_output_path} ({size_kb} KB)")
    print(f"[+] Open in browser: file://{os.path.abspath(report_output_path)}")
    return report_output_path


# === Standalone ===
if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "hackerone.com"
    generate_report(target)