#!/usr/bin/env python3
"""
Safe local network scanner for your own Wi-Fi/LAN.

What it does:
- Detects your local IPv4 subnet from the default interface
- Pings hosts on that subnet
- Reports responsive IPs
- Optionally resolves hostnames

This is intended only for networks you own or are authorized to administer.
"""

from __future__ import annotations

import ipaddress
import platform
import socket
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed


def get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


def get_network(local_ip: str) -> ipaddress.IPv4Network:
    # Simple /24 default for typical home networks
    return ipaddress.ip_network(f"{local_ip}/24", strict=False)


def ping_host(ip: str, timeout_ms: int = 700) -> bool:
    system = platform.system().lower()
    if system == "windows":
        cmd = ["ping", "-n", "1", "-w", str(timeout_ms), ip]
    elif system == "darwin":
        timeout_s = max(1, round(timeout_ms / 1000))
        cmd = ["ping", "-c", "1", "-W", str(timeout_s), ip]
    else:
        timeout_s = max(1, round(timeout_ms / 1000))
        cmd = ["ping", "-c", "1", "-W", str(timeout_s), ip]

    result = subprocess.run(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def reverse_dns(ip: str) -> str | None:
    try:
        name, _, _ = socket.gethostbyaddr(ip)
        return name
    except Exception:
        return None


def scan(network: ipaddress.IPv4Network, max_workers: int = 64) -> list[tuple[str, str | None]]:
    results: list[tuple[str, str | None]] = []
    hosts = [str(ip) for ip in network.hosts()]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(ping_host, ip): ip for ip in hosts}
        for future in as_completed(future_map):
            ip = future_map[future]
            try:
                if future.result():
                    results.append((ip, reverse_dns(ip)))
            except Exception:
                pass

    return sorted(results, key=lambda x: tuple(int(part) for part in x[0].split(".")))


def main() -> int:
    try:
        local_ip = get_local_ip()
        network = get_network(local_ip)
    except Exception as e:
        print(f"Failed to determine local network: {e}", file=sys.stderr)
        return 1

    print(f"Local IP: {local_ip}")
    print(f"Scanning network: {network}")
    print("Please use this only on networks you own or are authorized to administer.\n")

    results = scan(network)

    if not results:
        print("No responsive hosts found.")
        return 0

    print("Responsive hosts:")
    for ip, name in results:
        if name:
            print(f"- {ip:15} {name}")
        else:
            print(f"- {ip:15}")

    print(f"\nFound {len(results)} responsive host(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
