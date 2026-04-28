import time
import csv
from datetime import datetime
try:
    from scapy.all import sniff, IP
except ImportError:
    print("Scapy is required. Install it using: pip install scapy")
    exit(1)

TARGET_IP = "52.110.4.23"
CSV_FILE = "packet_stats_52_110_4_23.csv"

def main():
    # Initialize CSV file with headers
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Target_IP", "Packets_Sent", "Packets_Received"])

    print(f"Monitoring packets for {TARGET_IP} every second. Press Ctrl+C to stop.")

    while True:
        try:
            # Sniff packets specifically for the target IP for a 1-second interval
            packets = sniff(filter=f"host {TARGET_IP}", timeout=1)
            
            sent = 0
            received = 0
            
            for pkt in packets:
                if IP in pkt:
                    if pkt[IP].dst == TARGET_IP:
                        sent += 1
                    elif pkt[IP].src == TARGET_IP:
                        received += 1

            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Append to CSV
            with open(CSV_FILE, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([timestamp, TARGET_IP, sent, received])
            
            print(f"[{timestamp}] Sent: {sent} | Received: {received}")

        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
            break
        except Exception as e:
            print(f"Error during sniffing: {e}\nNote: Npcap is required on Windows for sniffing. Download from https://npcap.com/")
            break

if __name__ == '__main__':
    main()
