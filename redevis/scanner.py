# scanner.py — Redevis
import nmap
import socket
import manuf
import subprocess
from zeroconf import Zeroconf, ServiceBrowser
from datetime import datetime
import time


def get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


def get_network_range(ip: str) -> str:
    parts = ip.split(".")
    return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"


def resolve_hostname(ip: str) -> str:
    try:
        return socket.gethostbyaddr(ip)[0]
    except socket.herror:
        return None


def get_mdns_names(timeout: int = 3) -> dict:
    mdns_names = {}

    class MDNSListener:
        def add_service(self, zc, type_, name):
            info = zc.get_service_info(type_, name)
            if info and info.addresses:
                import ipaddress
                for addr in info.addresses:
                    ip = str(ipaddress.ip_address(addr))
                    host = name.replace(f".{type_}", "").replace("._tcp", "").replace("._udp", "")
                    mdns_names[ip] = host
        def remove_service(self, zc, type_, name): pass
        def update_service(self, zc, type_, name): pass

    zc = Zeroconf()
    listener = MDNSListener()
    services = ["_http._tcp.local.", "_ssh._tcp.local.", "_workstation._tcp.local."]
    [ServiceBrowser(zc, s, listener) for s in services]
    time.sleep(timeout)
    zc.close()
    return mdns_names


def get_vendor(mac: str) -> str:
    if not mac or mac == "Unknown":
        return "—"
    try:
        p = manuf.MacParser()
        vendor = p.get_manuf_long(mac)
        if not vendor:
            vendor = p.get_manuf(mac)
        return vendor if vendor else "—"
    except Exception:
        return "—"


def get_ping(ip: str) -> str:
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "1", ip],
            capture_output=True, text=True
        )
        for line in result.stdout.split("\n"):
            if "time=" in line:
                return line.split("time=")[1].split(" ")[0] + " ms"
        return "—"
    except Exception:
        return "—"


def guess_device_type(ports: list, vendor: str, hostname: str) -> str:
    port_nums = [p["port"] for p in ports]
    vendor_l  = vendor.lower()
    host_l    = hostname.lower() if hostname != "—" else ""

    if any(x in host_l for x in ["router", "gateway", "fritz", "huawei"]) or \
       any(x in vendor_l for x in ["huawei", "tp-link", "asus", "netgear", "mikrotik"]):
        return "router"
    if any(x in vendor_l for x in ["samsung", "lg", "sony", "roku", "androidtv"]) or \
       8008 in port_nums or 8009 in port_nums:
        return "tv"
    if any(x in vendor_l for x in ["apple", "iphone", "ipad"]):
        return "apple"
    if any(x in vendor_l for x in ["hewlett", "lenovo", "dell", "acer", "asus"]) or \
       any(x in host_l for x in ["thinkpad", "laptop", "desktop", "pc"]):
        return "computer"
    if any(x in vendor_l for x in ["zimaboard", "zimaos", "icew"]) or \
       any(x in host_l for x in ["zima", "server", "nas"]) or \
       445 in port_nums or 2049 in port_nums:
        return "server"
    if any(x in vendor_l for x in ["qualcomm", "mediatek", "xiaomi", "oppo", "realme"]):
        return "phone"
    if 22 in port_nums or 80 in port_nums or 443 in port_nums:
        return "computer"
    return "unknown"


def scan_network(network: str) -> list:
    nm = nmap.PortScanner()
    print(f"\n\033[36m[→]\033[0m Escaneando {network} ...")
    nm.scan(hosts=network, arguments="-T4 -F --open -O")

    print(f"\033[36m[→]\033[0m Buscando nomes mDNS...")
    mdns_names = get_mdns_names(timeout=3)

    devices = []
    for host in nm.all_hosts():
        if nm[host].state() == "up":
            hostname = resolve_hostname(host)
            if not hostname:
                hostname = mdns_names.get(host, "—")

            mac    = "—"
            vendor = "—"
            if "addresses" in nm[host] and "mac" in nm[host]["addresses"]:
                mac    = nm[host]["addresses"]["mac"]
                vendor = get_vendor(mac)

            ports = []
            for proto in nm[host].all_protocols():
                for port in nm[host][proto].keys():
                    if nm[host][proto][port]["state"] == "open":
                        ports.append({
                            "port": port,
                            "name": nm[host][proto][port]["name"]
                        })

            # OS detection
            os_name = "—"
            if "osmatch" in nm[host] and nm[host]["osmatch"]:
                os_name = nm[host]["osmatch"][0]["name"]

            # Latência
            latency = get_ping(host)

            # Tipo de dispositivo
            device_type = guess_device_type(ports, vendor, hostname)

            devices.append({
                "ip":          host,
                "hostname":    hostname,
                "mac":         mac,
                "vendor":      vendor,
                "os":          os_name,
                "latency":     latency,
                "device_type": device_type,
                "ports":       ports,
                "status":      "up",
            })

    return devices


def run_scan(network: str = None) -> dict:
    local_ip = get_local_ip()
    if not network:
        network = get_network_range(local_ip)

    print(f"\033[36m[✓]\033[0m IP local: \033[97m{local_ip}\033[0m")
    print(f"\033[36m[✓]\033[0m Rede alvo: \033[97m{network}\033[0m")

    devices = scan_network(network)

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "local_ip":  local_ip,
        "network":   network,
        "total":     len(devices),
        "devices":   devices,
    }