import socket
import threading
import time
import csv
import sys
import os
import psutil
import re
import ipaddress
from datetime import datetime
import msvcrt

# Known domains and CIDR blocks to filter out Microsoft/Google
KNOWN_DOMAINS_REGEX = re.compile(r'(?i)(microsoft|windows|azure|msedge|trafficmanager|google|1e100|googleapis|bing|live|office|skype|msn|azureedge)')
KNOWN_CIDR_BLOCKS = [
    ipaddress.ip_network('20.0.0.0/8'),
    ipaddress.ip_network('52.0.0.0/8'),
    ipaddress.ip_network('13.64.0.0/11'),
    ipaddress.ip_network('40.74.0.0/15'),
    ipaddress.ip_network('104.40.0.0/13'),
    ipaddress.ip_network('137.116.0.0/16'),
    ipaddress.ip_network('204.79.197.0/24'),
    ipaddress.ip_network('8.8.4.0/24'),
    ipaddress.ip_network('8.8.8.0/24'),
    ipaddress.ip_network('34.0.0.0/8'),
    ipaddress.ip_network('35.0.0.0/8'),
    ipaddress.ip_network('74.125.0.0/16'),
    ipaddress.ip_network('142.250.0.0/15'),
    ipaddress.ip_network('172.217.0.0/16'),
    ipaddress.ip_network('216.58.192.0/19'),
]

# Global dictionary to store dynamically discovered IPs
# Format: { '1.2.3.4': {'pid': 1234, 'host': '...', 'rx_p': 0, 'tx_p': 0, 'rx_b': 0, 'tx_b': 0} }
tracked_ips = {}
tracked_ips_lock = threading.Lock()

def is_known_cloud_ip(ip_str):
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        for network in KNOWN_CIDR_BLOCKS:
            if ip_obj in network:
                return True
        return False
    except ValueError:
        return False

def is_private_ip(ip):
    if ip.startswith('127.') or ip == '::1': return True
    if ip.startswith('192.168.') or ip.startswith('10.'): return True
    parts = ip.split('.')
    if len(parts) == 4 and parts[0] == '172' and 16 <= int(parts[1]) <= 31: return True
    return False

def resolve_ip(ip):
    try:
        host, _, _ = socket.gethostbyaddr(ip)
        return host
    except Exception:
        return "UNKNOWN_OR_NO_PTR"

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't even have to be reachable
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]
    except Exception:
        return socket.gethostbyname(socket.gethostname())
    finally:
        s.close()

# THREAD 1: Dynamically hunt for new svchost connections
def connection_poller():
    while True:
        svchost_pids = set()
        target_pids = set()
        
        # 1. Find all svchost processes and their children
        for proc in psutil.process_iter(['pid', 'name', 'ppid']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == 'svchost.exe':
                    svchost_pids.add(proc.info['pid'])
                    target_pids.add(proc.info['pid'])
            except Exception:
                pass
        
        for proc in psutil.process_iter(['pid', 'ppid']):
            try:
                if proc.info['ppid'] in svchost_pids:
                    target_pids.add(proc.info['pid'])
            except Exception:
                pass
                
        # 2. Check their active connections
        for conn in psutil.net_connections(kind='inet'):
            if conn.status == 'ESTABLISHED' and conn.pid in target_pids:
                if not conn.raddr: continue
                remote_ip = conn.raddr.ip
                
                if is_private_ip(remote_ip): continue
                
                with tracked_ips_lock:
                    # If it's a completely new IP, evaluate it
                    if remote_ip not in tracked_ips:
                        if is_known_cloud_ip(remote_ip): continue
                        host = resolve_ip(remote_ip)
                        if not KNOWN_DOMAINS_REGEX.search(host):
                            # It's suspicious/external. Add it to the tracking list!
                            tracked_ips[remote_ip] = {
                                'pid': conn.pid,
                                'host': host,
                                'rx_p': 0, 'tx_p': 0, 'rx_b': 0, 'tx_b': 0
                            }
        time.sleep(3)

# THREAD 2: Raw packet sniffing (No setup or extra tools required)
def packet_sniffer():
    HOST = get_local_ip()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
        s.bind((HOST, 0))
        # Include IP headers
        s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        # Receive all packages
        s.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
    except OSError as e:
        print(f'Error binding raw socket: {e}. Ensure you are running as Administrator.')
        return

    while True:
        try:
            packet, addr = s.recvfrom(65535)
            # Extract IP addresses from the IP Header (bytes 12-15 = Src, 16-19 = Dst)
            src_ip = socket.inet_ntoa(packet[12:16])
            dst_ip = socket.inet_ntoa(packet[16:20])
            pkt_length = len(packet)
            
            with tracked_ips_lock:
                # Instantly count the packet if it matches any dynamically discovered IP
                if src_ip in tracked_ips:
                    tracked_ips[src_ip]['rx_p'] += 1
                    tracked_ips[src_ip]['rx_b'] += pkt_length
                if dst_ip in tracked_ips:
                    tracked_ips[dst_ip]['tx_p'] += 1
                    tracked_ips[dst_ip]['tx_b'] += pkt_length
        except Exception:
            pass

def format_bytes(b):
    if b < 1024: return f"{b} B"
    elif b < 1048576: return f"{b/1024:.1f} KB"
    else: return f"{b/1048576:.1f} MB"

# MAIN THREAD: Dashboard
def main():
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    csv_file = "autopilot_svchost_stats.csv"
    if not os.path.exists(csv_file):
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'PID', 'RemoteIP', 'Host', 'RxPackets', 'TxPackets', 'RxBytes', 'TxBytes'])
            
    # Start the automated workers
    threading.Thread(target=connection_poller, daemon=True).start()
    threading.Thread(target=packet_sniffer, daemon=True).start()
    
    SAVE_INTERVAL = 3600 # 1 hour
    last_save_time = time.time()
    
    try:
        while True:
            time.sleep(2)
            now = time.time()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            with tracked_ips_lock:
                os.system('cls')
                print("===============================================================================")
                print("   [AUTO-PILOT] Svchost Discovery + Live Packet Counting")
                print("===============================================================================")
                print(f"Time: {timestamp}")
                print(f"Tracking {len(tracked_ips)} external connection(s) in RAM. Saving to disk every 1 hour.\n")
                
                if not tracked_ips:
                    print("No non-Microsoft svchost connections detected yet. Waiting...")
                else:
                    print(f"{'PID':<6} | {'Remote IP':<15} | {'Host':<20} | {'Rx Pkts':<8} | {'Tx Pkts':<8} | {'Rx Bytes':<10} | {'Tx Bytes':<10}")
                    print("-" * 96)
                    
                    for ip, data in tracked_ips.items():
                        host_short = data['host'][:18] + '..' if len(data['host']) > 20 else data['host']
                        print(f"{data['pid']:<6} | {ip:<15} | {host_short:<20} | {data['rx_p']:<8} | {data['tx_p']:<8} | {format_bytes(data['rx_b']):<10} | {format_bytes(data['tx_b']):<10}")
                
                # Periodic Save
                if now - last_save_time >= SAVE_INTERVAL:
                    if tracked_ips:
                        with open(csv_file, 'a', newline='') as f:
                            writer = csv.writer(f)
                            for ip, data in tracked_ips.items():
                                writer.writerow([timestamp, data['pid'], ip, data['host'], data['rx_p'], data['tx_p'], data['rx_b'], data['tx_b']])
                    last_save_time = now
                        
                time_until_save = int(SAVE_INTERVAL - (now - last_save_time))
                print(f"\nNext background save in: {time_until_save} seconds.")
                print(f"Log File: {csv_file}")
                print("Press Ctrl+C to exit back to menu.")
    except KeyboardInterrupt:
        print("\nStopping Auto-Pilot...")

if __name__ == '__main__':
    main()