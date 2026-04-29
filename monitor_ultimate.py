import socket
import threading
import time
import csv
import sys
import os
import subprocess
import re
import ipaddress
from datetime import datetime
import msvcrt

KNOWN_DOMAINS_REGEX = re.compile(r'(?i)(microsoft|windows|azure|msedge|trafficmanager|google|1e100|googleapis|bing|live|office|skype|msn|azureedge)')
KNOWN_CIDR_BLOCKS = [
    ipaddress.ip_network('20.0.0.0/8'), ipaddress.ip_network('52.0.0.0/8'), ipaddress.ip_network('13.64.0.0/11'),
    ipaddress.ip_network('40.74.0.0/15'), ipaddress.ip_network('104.40.0.0/13'), ipaddress.ip_network('137.116.0.0/16'),
    ipaddress.ip_network('204.79.197.0/24'), ipaddress.ip_network('8.8.4.0/24'), ipaddress.ip_network('8.8.8.0/24'),
    ipaddress.ip_network('34.0.0.0/8'), ipaddress.ip_network('35.0.0.0/8'), ipaddress.ip_network('74.125.0.0/16'),
    ipaddress.ip_network('142.250.0.0/15'), ipaddress.ip_network('172.217.0.0/16'), ipaddress.ip_network('216.58.192.0/19'),
]

# Trackers
tracked_ips = {}
recent_traffic = {} # Time Machine Buffer
lock = threading.Lock()

def is_known_cloud_ip(ip_str):
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        for net in KNOWN_CIDR_BLOCKS:
            if ip_obj in net: return True
        return False
    except ValueError: return False

def is_private_ip(ip):
    if ip.startswith('127.') or ip == '::1': return True
    if ip.startswith('192.168.') or ip.startswith('10.'): return True
    parts = ip.split('.')
    if len(parts) == 4 and parts[0] == '172' and 16 <= int(parts[1]) <= 31: return True
    return False

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]
    except Exception: return socket.gethostbyname(socket.gethostname())
    finally: s.close()

# THREAD 1: Sysmon Listener (Kernel Level Sub-Second Detection)
def sysmon_listener():
    # Call the PowerShell script that tails Sysmon Event ID 3
    proc = subprocess.Popen(['powershell', '-ExecutionPolicy', 'Bypass', '-File', 'sysmon_tail.ps1'], stdout=subprocess.PIPE, text=True)
    
    for line in proc.stdout:
        line = line.strip()
        if not line: continue
        try:
            pid, ip, host = line.split(',', 2)
            if is_private_ip(ip) or is_known_cloud_ip(ip): continue
            
            # If no hostname was in Sysmon, resolve it manually
            if not host:
                try: host, _, _ = socket.gethostbyaddr(ip)
                except Exception: host = "UNKNOWN_OR_NO_PTR"
                
            if not KNOWN_DOMAINS_REGEX.search(host):
                with lock:
                    if ip not in tracked_ips:
                        tracked_ips[ip] = {'pid': pid, 'host': host, 'rx_p': 0, 'tx_p': 0, 'rx_b': 0, 'tx_b': 0}
                        
                        # Time Machine: Instantly grab buffered packets that flew by a few milliseconds ago
                        if ip in recent_traffic:
                            tracked_ips[ip]['rx_p'] += recent_traffic[ip]['rx_p']
                            tracked_ips[ip]['tx_p'] += recent_traffic[ip]['tx_p']
                            tracked_ips[ip]['rx_b'] += recent_traffic[ip]['rx_b']
                            tracked_ips[ip]['tx_b'] += recent_traffic[ip]['tx_b']
        except Exception:
            pass

# THREAD 2: Raw Sniffer + Time Machine Buffer
def packet_sniffer():
    HOST = get_local_ip()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
        s.bind((HOST, 0))
        s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        s.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
    except OSError as e:
        print(f'Error binding raw socket: {e}.')
        return

    while True:
        try:
            packet, addr = s.recvfrom(65535)
            src_ip = socket.inet_ntoa(packet[12:16])
            dst_ip = socket.inet_ntoa(packet[16:20])
            pkt_length = len(packet)
            
            with lock:
                # Update Permanent Tracker
                if src_ip in tracked_ips:
                    tracked_ips[src_ip]['rx_p'] += 1
                    tracked_ips[src_ip]['rx_b'] += pkt_length
                else:
                    # Update Time Machine Buffer (for incoming)
                    if src_ip not in recent_traffic: recent_traffic[src_ip] = {'rx_p':0, 'tx_p':0, 'rx_b':0, 'tx_b':0, 'ts':0}
                    recent_traffic[src_ip]['rx_p'] += 1
                    recent_traffic[src_ip]['rx_b'] += pkt_length
                    recent_traffic[src_ip]['ts'] = time.time()
                    
                if dst_ip in tracked_ips:
                    tracked_ips[dst_ip]['tx_p'] += 1
                    tracked_ips[dst_ip]['tx_b'] += pkt_length
                else:
                    # Update Time Machine Buffer (for outgoing)
                    if dst_ip not in recent_traffic: recent_traffic[dst_ip] = {'rx_p':0, 'tx_p':0, 'rx_b':0, 'tx_b':0, 'ts':0}
                    recent_traffic[dst_ip]['tx_p'] += 1
                    recent_traffic[dst_ip]['tx_b'] += pkt_length
                    recent_traffic[dst_ip]['ts'] = time.time()
        except Exception:
            pass

# THREAD 3: Buffer Cleanup (Prevents memory leak from tracking ALL internet traffic)
def buffer_cleanup():
    while True:
        time.sleep(5)
        now = time.time()
        with lock:
            # Delete buffered IPs older than 10 seconds
            stale = [ip for ip, data in recent_traffic.items() if now - data['ts'] > 10]
            for ip in stale:
                del recent_traffic[ip]

def format_bytes(b):
    if b < 1024: return f"{b} B"
    elif b < 1048576: return f"{b/1024:.1f} KB"
    else: return f"{b/1048576:.1f} MB"

# MAIN: Dashboard
def main():
    if sys.stdout.encoding != 'utf-8': sys.stdout.reconfigure(encoding='utf-8')
    csv_file = "ultimate_autopilot_stats.csv"
    
    if not os.path.exists(csv_file):
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'PID', 'RemoteIP', 'Host', 'RxPackets', 'TxPackets', 'RxBytes', 'TxBytes'])
            
    threading.Thread(target=sysmon_listener, daemon=True).start()
    threading.Thread(target=packet_sniffer, daemon=True).start()
    threading.Thread(target=buffer_cleanup, daemon=True).start()
    
    SAVE_INTERVAL = 3600 # 1 hour
    last_save_time = time.time()
    
    try:
        while True:
            # Check for 'S' key press without blocking the loop
            manual_save = False
            for _ in range(20):
                if msvcrt.kbhit():
                    key = msvcrt.getch().decode('utf-8', errors='ignore').lower()
                    if key == 's':
                        manual_save = True
                        while msvcrt.kbhit(): msvcrt.getch() # clear buffer
                        break
                time.sleep(0.1)
                
            now = time.time()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            with lock:
                # Save to disk if 1 hour has passed OR user pressed 'S'
                if manual_save or (now - last_save_time >= SAVE_INTERVAL):
                    if tracked_ips:
                        with open(csv_file, 'a', newline='') as f:
                            writer = csv.writer(f)
                            for ip, data in tracked_ips.items():
                                writer.writerow([timestamp, data['pid'], ip, data['host'], data['rx_p'], data['tx_p'], data['rx_b'], data['tx_b']])
                    last_save_time = now
                    just_saved = True
                else:
                    just_saved = False
                    
                os.system('cls')
                print("===============================================================================")
                print("   [ULTIMATE AUTO-PILOT] Sysmon Kernel Discovery + Buffered Packet Sniffer")
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
                
                time_until_save = int(SAVE_INTERVAL - (now - last_save_time))
                print(f"\nNext background save in: {time_until_save} seconds.")
                print(f"Log File: {csv_file}")
                
                if just_saved and manual_save:
                    print("\n--> [SUCCESS] Data manually saved to disk! <--")
                    
                print("\nPress [S] to force save now. Press [Ctrl+C] to exit.")
    except KeyboardInterrupt:
        print("\nStopping Ultimate Auto-Pilot...")

if __name__ == '__main__':
    main()