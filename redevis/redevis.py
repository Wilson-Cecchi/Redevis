# redevis.py — Ponto de entrada principal
# Autor: Wilson Klein Cecchi

import os
import sys
import argparse
from scanner import run_scan
from history import save_scan, get_last_scan, compare_scans
from report  import generate_report, open_report

ICONS = {
    "router":   "⬡ Router",
    "tv":       "⬡ TV",
    "apple":    "⬡ Apple",
    "computer": "⬡ Computer",
    "server":   "⬡ Server",
    "phone":    "⬡ Phone",
    "unknown":  "⬡ Unknown",
}


def print_banner():
    print("""
\033[36m╔═══════════════════════════════════════╗
║         R E D E V I S  v1.0           ║
║    Network Scanner · Wilson Cecchi    ║
╚═══════════════════════════════════════╝\033[0m
""")


def print_devices(devices: list):
    if not devices:
        print("\033[33m[!]\033[0m Nenhum dispositivo encontrado.")
        return

    print(f"\n\033[36m{'IP':<18} {'HOSTNAME':<25} {'FABRICANTE':<25} {'OS':<20} {'LATÊNCIA'}\033[0m")
    print("─" * 100)
    for d in devices:
        ports   = ", ".join([str(p["port"]) for p in d["ports"]]) or "—"
        icon    = ICONS.get(d.get("device_type", "unknown"), "⬡")
        print(
            f"\033[97m{d['ip']:<18}\033[0m "
            f"{d['hostname']:<25} "
            f"\033[36m{d['vendor']:<25}\033[0m "
            f"\033[90m{d['os']:<20}\033[0m "
            f"\033[33m{d['latency']}\033[0m"
        )


def main():
    parser = argparse.ArgumentParser(description="Redevis — Network Scanner")
    parser.add_argument("--range",      type=str,  help="Range de rede (ex: 192.168.1.0/24)")
    parser.add_argument("--no-browser", action="store_true", help="Não abre o relatório no navegador")
    args = parser.parse_args()

    print_banner()

    if os.geteuid() != 0:
        print("\033[31m[✗]\033[0m Redevis precisa de permissão root.")
        print("    Execute com: \033[97msudo python3 redevis.py\033[0m")
        sys.exit(1)

    print("\033[36m[→]\033[0m Iniciando scan...\n")
    scan = run_scan(network=args.range)

    print(f"\n\033[36m[✓]\033[0m {scan['total']} dispositivo(s) encontrado(s)\n")
    print_devices(scan["devices"])

    previous = get_last_scan()
    diff     = None
    if previous:
        diff = compare_scans(scan, previous)
        if diff["new"]:
            print(f"\n\033[36m[▲]\033[0m {len(diff['new'])} novo(s) dispositivo(s):")
            for d in diff["new"]:
                print(f"    + {d['ip']} ({d['hostname']})")
        if diff["removed"]:
            print(f"\n\033[33m[▼]\033[0m {len(diff['removed'])} dispositivo(s) saíram:")
            for d in diff["removed"]:
                print(f"    - {d['ip']} ({d['hostname']})")

    save_scan(scan)
    print(f"\n\033[36m[✓]\033[0m Scan salvo no histórico.")

    print("\033[36m[→]\033[0m Gerando relatório HTML...")
    filepath = generate_report(scan, diff)
    print(f"\033[36m[✓]\033[0m Relatório: \033[97m{filepath}\033[0m")

    if not args.no_browser:
        os.system(f"sudo -u {os.environ.get('SUDO_USER', 'wilson')} xdg-open '{filepath}'")
        print("\033[36m[✓]\033[0m Relatório aberto no navegador!\n")


if __name__ == "__main__":
    main()