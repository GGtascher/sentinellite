#!/usr/bin/env python3
"""Send safe, fictional events that exercise SentinelLite's V0.1 detections."""
import argparse
import json
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta


def build_events() -> list[dict | str]:
    base = datetime.now(UTC) - timedelta(minutes=3)
    stamp = lambda seconds: (base + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")
    events: list[dict | str] = []
    for index in range(5):
        events.append({"EventID": 4625, "timestamp": stamp(index * 10), "Computer": "win-lab-01", "user": "alice", "src_ip": "10.20.30.40", "message": "Fictional failed interactive logon"})
    events.append({"EventID": 4624, "timestamp": stamp(60), "Computer": "win-lab-01", "user": "alice", "src_ip": "10.20.30.40", "message": "Fictional successful interactive logon"})
    events.append({"EventID": 1, "timestamp": stamp(90), "Computer": "win-lab-01", "user": "alice", "Image": r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe", "CommandLine": "powershell.exe -NoProfile -EncodedCommand U0FGRV9ERU1P", "ParentImage": "explorer.exe"})
    for port in range(20, 30):
        events.append(f"timestamp={stamp(100 + port)} src_ip=192.168.50.25 dst_ip=192.168.50.10 dst_port={port} protocol=tcp action=blocked severity=medium")
    for index in range(8):
        events.append(f'203.0.113.55 - - [15/Aug/2026:14:{index:02d}:01 +0000] "POST /login HTTP/1.1" 401 382')
    events.extend([
        "Aug 15 14:31:11 linux-lab sshd[1234]: Failed password for root from 198.51.100.8 port 55422 ssh2",
        "Aug 15 14:31:21 linux-lab sshd[1235]: Accepted publickey for student from 192.168.10.5 port 55423 ssh2",
        {"timestamp": stamp(120), "level": "info", "host": "app-lab", "message": "Application health check completed", "event_type": "application_health"},
        "sensor::zephyr / node=alpha / signal nominal / observer 10.10.9.7",
    ])
    return events


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", default="http://localhost:8000/api/v1", help="SentinelLite API base URL")
    args = parser.parse_args()
    payload = json.dumps({"events": build_events(), "source_type": "demo"}).encode()
    request = urllib.request.Request(f"{args.api_url.rstrip('/')}/ingest/batch", data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response)
    except urllib.error.URLError as exc:
        print(f"Demo ingestion failed: {exc}")
        return 1
    print(json.dumps(result, indent=2))
    print("Demo complete. Open http://localhost:3000 to investigate the generated alerts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

