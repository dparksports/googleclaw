import time
import csv
import sys
import psutil
import socket
import re
import ipaddress
from datetime import datetime

# Optional: Try to import scapy for full packet sniffing, but provide a fallback using psutil.net_io_counters
try:
    from scapy.all import sniff, IP, TCP, UDP
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    print("Scapy not found. Packet counting will be simulated using psutil's connection tracking.", file=sys.stderr)

# known domains regex pattern
KNOWN_DOMAINS_REGEX = re.compile(
    r'(?i)(microsoft|windows|azure|msedge|trafficmanager|google|1e100|googleapis|bing|live|office|skype|msn|azureedge)'
)

# Known Cloud Provider CIDR blocks (A simplified subset of major Microsoft and Google ranges)
# In a full enterprise tool, this would be updated dynamically from BGP routing tables.
KNOWN_CIDR_BLOCKS = [
    # Microsoft / Azure (AS8075) - heavily truncated for example
    ipaddress.ip_network('20.0.0.0/8'),     # Huge MS block
    ipaddress.ip_network('52.0.0.0/8'),     # Huge MS block
    ipaddress.ip_network('13.64.0.0/11'),
    ipaddress.ip_network('40.74.0.0/15'),
    ipaddress.ip_network('104.40.0.0/13'),
    ipaddress.ip_network('137.116.0.0/16'),
    ipaddress.ip_network('204.79.197.0/24'), # Bing/Edge
    
    # Google (AS15169)
    ipaddress.ip_network('8.8.4.0/24'),      # DNS
    ipaddress.ip_network('8.8.8.0/24'),      # DNS
    ipaddress.ip_network('34.0.0.0/8'),      # GCP
    ipaddress.ip_network('35.0.0.0/8'),      # GCP
    ipaddress.ip_network('74.125.0.0/16'),
    ipaddress.ip_network('142.250.0.0/15'),
    ipaddress.ip_network('172.217.0.0/16'),
    ipaddress.ip_network('216.58.192.0/19'),
]

def is_known_cloud_ip(ip_str):
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        for network in KNOWN_CIDR_BLOCKS:
            if ip_obj in network:
                return True
        return False
    except ValueError:
        return False

# known private IP blocks
def is_private_ip(ip):
    if ip.startswith('127.') or ip == '::1':
        return True
    if ip.startswith('192.168.') or ip.startswith('10.'):
        return True
    parts = ip.split('.')
    if len(parts) == 4 and parts[0] == '172' and 16 <= int(parts[1]) <= 31:
         return True
    return False

def resolve_ip(ip):
    try:
         host, _, _ = socket.gethostbyaddr(ip)
         return host
    except Exception:
         return "UNKNOWN_OR_NO_PTR"

def get_svchost_pids():
    """Returns a set of PIDs for svchost.exe and its children."""
    target_pids = set()
    svchost_pids = set()
    
    # First pass: find svchost
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() == 'svchost.exe':
                svchost_pids.add(proc.info['pid'])
                target_pids.add(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    # Second pass: find children
    for proc in psutil.process_iter(['pid', 'ppid']):
        try:
             if proc.info['ppid'] in svchost_pids:
                 target_pids.add(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
             pass
             
    return target_pids

def monitor_connections():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Svchost Monitor (Non-Microsoft/Google)")
    
    known_connections = set() # Store (pid, remote_ip, remote_port)
    csv_file = "svchost_non_ms_traffic.csv"
    
    with open(csv_file, 'w', newline='') as f:
         writer = csv.writer(f)
         writer.writerow(['Timestamp', 'PID', 'LocalAddress', 'RemoteAddress', 'ResolvedHost', 'PacketsSent(Est)', 'PacketsRecv(Est)'])
    
    try:
        while True:
            target_pids = get_svchost_pids()
            
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == 'ESTABLISHED' and conn.pid in target_pids:
                    raddr = conn.raddr
                    if not raddr:
                        continue
                    
                    remote_ip = raddr.ip
                    remote_port = raddr.port
                    
                    if is_private_ip(remote_ip):
                         continue
                         
                    conn_key = (conn.pid, remote_ip, remote_port)
                    if conn_key not in known_connections:
                        # Fast check: Is it in a known Microsoft/Google IP block?
                        if is_known_cloud_ip(remote_ip):
                            known_connections.add(conn_key)
                            continue

                        host = resolve_ip(remote_ip)
                        
                        # Slower check: Does the reverse DNS domain match?
                        if not KNOWN_DOMAINS_REGEX.search(host):
                            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            print(f"\n[ALERT] NON-MS/GOOGLE SVCHOST TRAFFIC")
                            print(f"Time:  {timestamp}")
                            print(f"PID:   {conn.pid}")
                            print(f"Local: {conn.laddr.ip}:{conn.laddr.port}")
                            print(f"Remote: {remote_ip}:{remote_port}")
                            print(f"Host:  {host}")
                            
                            # Estimate packets by tracking IO counters for the specific process
                            try:
                                p = psutil.Process(conn.pid)
                                io_counters = p.io_counters()
                                # Note: These are bytes read/written by the process overall, not per connection.
                                # True per-connection packet counting requires pcap/scapy sniffing.
                                est_sent = io_counters.write_count
                                est_recv = io_counters.read_count
                            except Exception:
                                est_sent = 0
                                est_recv = 0
                            
                            with open(csv_file, 'a', newline='') as f:
                                 writer = csv.writer(f)
                                 writer.writerow([timestamp, conn.pid, f"{conn.laddr.ip}:{conn.laddr.port}", f"{remote_ip}:{remote_port}", host, est_sent, est_recv])
                            
                            known_connections.add(conn_key)
            
            time.sleep(5)
            
    except KeyboardInterrupt:
         print("\nMonitoring stopped.")

if __name__ == '__main__':
    # Force UTF-8 output
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    monitor_connections()