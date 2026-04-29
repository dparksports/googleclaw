import socket
import struct
import time
import csv
import sys
from datetime import datetime

IP_TARGET = sys.argv[1] if len(sys.argv) > 1 else '52.110.4.23'
CSV_FILE = f'packet_stats_{IP_TARGET.replace(".", "_")}.csv'
DURATION = 9999999

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]
    except Exception:
        return socket.gethostbyname(socket.gethostname())
    finally:
        s.close()

def main():
    HOST = get_local_ip()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
        s.bind((HOST, 0))
        s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        s.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
    except OSError as e:
        print(f'Error binding socket: {e}')
        sys.exit(1)

    print(f'Monitoring traffic to/from {IP_TARGET}...')
    
    with open(CSV_FILE, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Timestamp', 'TargetIP', 'RxPackets', 'TxPackets', 'RxBytes', 'TxBytes'])
        
        start_time = time.time()
        next_tick = start_time + 1.0
        rx_pkts, tx_pkts, rx_bytes, tx_bytes = 0, 0, 0, 0
        s.settimeout(0.1)
        
        while time.time() - start_time < DURATION:
            try:
                packet, addr = s.recvfrom(65535)
                iph = struct.unpack('!BBHHHBBH4s4s', packet[0:20])
                src_ip = socket.inet_ntoa(iph[8])
                dst_ip = socket.inet_ntoa(iph[9])
                pkt_length = len(packet)
                
                if src_ip == IP_TARGET:
                    rx_pkts += 1
                    rx_bytes += pkt_length
                elif dst_ip == IP_TARGET:
                    tx_pkts += 1
                    tx_bytes += pkt_length
            except socket.timeout: pass
            except Exception: pass
            
            current_time = time.time()
            if current_time >= next_tick:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                writer.writerow([timestamp, IP_TARGET, rx_pkts, tx_pkts, rx_bytes, tx_bytes])
                f.flush()
                rx_pkts, tx_pkts, rx_bytes, tx_bytes = 0, 0, 0, 0
                next_tick += 1.0

if __name__ == '__main__':
    main()