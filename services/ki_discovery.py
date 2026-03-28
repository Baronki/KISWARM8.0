#!/usr/bin/env python3
import subprocess
import json
import time
import os
import datetime
import socket
from pathlib import Path

LOG_DIR = Path("/opt/kiswarm/logs")
SCAN_DIR = Path("/opt/kiswarm/scans")
LOG_DIR.mkdir(parents=True, exist_ok=True)
SCAN_DIR.mkdir(parents=True, exist_ok=True)

def log(msg):
    ts = datetime.datetime.now().isoformat()
    entry = f"[{ts}] {msg}"
    print(entry)
    with open(LOG_DIR / "discovery.log", "a") as f:
        f.write(entry + "\n")

def run_cmd(cmd, timeout=300):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def ki_port_scan(target):
    ki_ports = "5000,5001,5002,5009,5010,5011,5012,5013,5014,5015,5016,5017,5199,5555,5556,8000,8080,11434"
    cmd = f"timeout 120 nmap -Pn -sT -p {ki_ports} --open {target} 2>/dev/null"
    ret, out, err = run_cmd(cmd, 180)
    return out

def broadcast_discovery():
    log("Broadcast discovery on 255.255.255.255")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        msg = json.dumps({"type": "KISWARM_DISCOVERY", "version": "8.0"}).encode()
        for port in [5000, 5009, 5017, 5556, 8080]:
            try:
                sock.sendto(msg, ("255.255.255.255", port))
            except:
                pass
        sock.close()
        log("Broadcast packets sent")
    except Exception as e:
        log(f"Broadcast error: {e}")

def dcom_investigation():
    log("DCOM/SCADA investigation ports 135,445,593")
    cmd = "timeout 60 nmap -Pn -sT -p 135,139,445,593 10.8.3.0/24 2>/dev/null"
    ret, out, err = run_cmd(cmd, 120)
    log(f"DCOM: {out[:500]}")
    return out

def main():
    log("=" * 40)
    log("KI DISCOVERY CYCLE START")
    log("=" * 40)
    broadcast_discovery()
    dcom_investigation()
    
    ranges = ["3.0.0.0/8", "13.0.0.0/8", "52.0.0.0/8", "35.0.0.0/8", "95.111.0.0/16"]
    for r in ranges:
        log(f"Scanning: {r}")
        result = ki_port_scan(r)
        if "open" in result.lower():
            log(f"FOUND in {r}")
        time.sleep(10)
    
    log("Cycle done. Sleep 1h.")
    time.sleep(3600)

if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            log(f"Error: {e}")
            time.sleep(300)
