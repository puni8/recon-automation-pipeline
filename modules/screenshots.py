import subprocess
import json
import os
import re
from datetime import datetime
from urllib.parse import urlparse


def safe_filename_from_url(url):
    """
    Convert a URL into a safe filename component.
    Example: https://api.example.com → api_example_com
    gowitness names its own files internally, but we use this for cross-referencing.
    """
    parsed = urlparse(url)
    host = parsed.hostname or "unknown"
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", host)


def capture_screenshot(url, screenshot_dir, timeout=60):
    """
    Capture a single screenshot via gowitness.
    Returns the path to the screenshot file if successful, None otherwise.
    """
    try:
        result = subprocess.run(
            [
                "gowitness", "scan", "single",
                "--url", url,
                "--screenshot-path", screenshot_dir,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return None, "timeout"
    except FileNotFoundError:
        return None, "gowitness not found"

    if result.returncode != 0:
        # gowitness sometimes returns non-zero for sites that fail to load fully
        # but may still have produced a partial screenshot
        return None, f"exit code {result.returncode}"

    # Find the most recently created file in the screenshot dir
    # gowitness names files based on URL hash + timestamp
    try:
        files = [
            os.path.join(screenshot_dir, f)
            for f in os.listdir(screenshot_dir)
            if f.endswith((".jpeg", ".jpg", ".png"))
        ]
        if not files:
            return None, "no file produced"
        latest = max(files, key=os.path.getmtime)
        return latest, "ok"
    except OSError:
        return None, "directory read failed"


def capture_all_screenshots(target, output_dir, max_hosts=20, per_host_timeout=60):
    """
    Capture screenshots for every live host of a target.
    """
    target_dir = os.path.join(output_dir, target)
    livehosts_file = os.path.join(target_dir, "livehosts.json")
    screenshot_dir = os.path.join(target_dir, "screenshots")

    # === Load upstream data ===
    if not os.path.exists(livehosts_file):
        print(f"[-] {livehosts_file} not found. Run livehosts module first.")
        return None

    with open(livehosts_file, "r") as f:
        live_data = json.load(f)

    live_hosts = live_data.get("live_hosts", [])
    if not live_hosts:
        print(f"[-] No live hosts to screenshot")
        return None

    # Cap to keep runtime reasonable
    hosts_to_capture = live_hosts[:max_hosts]
    print(f"[*] Loaded {len(live_hosts)} live hosts")
    print(f"[*] Capturing screenshots (limit: {max_hosts})...")

    # Ensure screenshot dir exists
    os.makedirs(screenshot_dir, exist_ok=True)

    # === Capture each one ===
    results = []
    success_count = 0

    for i, host in enumerate(hosts_to_capture, 1):
        url = host.get("url")
        if not url:
            continue

        print(f"    [{i}/{len(hosts_to_capture)}] Capturing {url} ...", end=" ", flush=True)
        screenshot_path, status = capture_screenshot(url, screenshot_dir, per_host_timeout)

        if screenshot_path:
            # Store path RELATIVE to target_dir so the report can reference it portably
            relative_path = os.path.relpath(screenshot_path, target_dir)
            results.append({
                "url": url,
                "host": host.get("host"),
                "status_code": host.get("status_code"),
                "title": host.get("title", ""),
                "screenshot_path": relative_path,
                "captured": True,
            })
            success_count += 1
            print("[+] saved")
        else:
            results.append({
                "url": url,
                "host": host.get("host"),
                "status_code": host.get("status_code"),
                "title": host.get("title", ""),
                "screenshot_path": None,
                "captured": False,
                "error": status,
            })
            print(f"[-] failed ({status})")

    # === Build findings ===
    findings = {
        "target": target,
        "module": "screenshots",
        "tool": "gowitness",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "hosts_attempted": len(hosts_to_capture),
        "hosts_captured": success_count,
        "screenshot_dir": "screenshots",  # relative to target_dir
        "results": results,
    }

    # === Save JSON manifest ===
    output_file = os.path.join(target_dir, "screenshots.json")
    with open(output_file, "w") as f:
        json.dump(findings, f, indent=2)

    print(f"\n[+] Captured {success_count}/{len(hosts_to_capture)} screenshots")
    print(f"[+] Output saved to: {output_file}")
    print(f"[+] Screenshot directory: {screenshot_dir}")
    return findings


# === Standalone test ===
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 -m modules.screenshots <target> [max_hosts]")
        print("Example: python3 -m modules.screenshots hackerone.com 10")
        sys.exit(1)

    target = sys.argv[1]
    max_hosts = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    output_dir = "output"

    result = capture_all_screenshots(target, output_dir, max_hosts=max_hosts)

    if result and result["hosts_captured"]:
        print(f"\n{'='*60}")
        print(f"  Screenshot summary")
        print(f"{'='*60}")
        print(f"  Success: {result['hosts_captured']} / {result['hosts_attempted']}")
        print(f"  Saved to: output/{target}/screenshots/")
        print(f"  Open one: xdg-open output/{target}/screenshots/")