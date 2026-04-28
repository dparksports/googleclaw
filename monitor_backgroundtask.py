"""
backgroundTaskHost.exe Live Network Monitor
Monitors send/receive activity for PID 8452 -> 23.7.129.5:443
Uses process I/O counters + TCP connection state (no admin required)
"""
import subprocess
import time
import csv
import sys
import os
import json
from datetime import datetime

# Force UTF-8 output to avoid cp1252 encoding errors
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

TARGET_IP = '23.7.129.5'
TARGET_PID = 8452
CSV_FILE = 'packet_stats_backgroundtaskhost.csv'
POLL_INTERVAL = 1.0  # seconds


def run_ps(command):
    """Run a PowerShell command and return stripped stdout."""
    result = subprocess.run(
        ['powershell', '-NoProfile', '-Command', command],
        capture_output=True, text=True, timeout=10
    )
    return result.stdout.strip()


def get_process_io(pid):
    """Get the process I/O read/write byte counters via CIM."""
    cmd = (
        f'$p = Get-CimInstance Win32_Process -Filter "ProcessId={pid}" -ErrorAction SilentlyContinue; '
        f'if ($p) {{ '
        f'  $io = (Get-Process -Id {pid} -ErrorAction SilentlyContinue); '
        f'  [PSCustomObject]@{{ '
        f'    ReadBytes  = $io.IO.ReadTransferCount; '
        f'    WriteBytes = $io.IO.WriteTransferCount; '
        f'    ReadOps    = $io.IO.ReadOperationCount; '
        f'    WriteOps   = $io.IO.WriteOperationCount; '
        f'    OtherBytes = $io.IO.OtherTransferCount; '
        f'    OtherOps   = $io.IO.OtherOperationCount; '
        f'    WS_MB      = [math]::Round($io.WorkingSet64/1MB,2); '
        f'    Threads    = $io.Threads.Count; '
        f'    Alive      = $true '
        f'  }} | ConvertTo-Json '
        f'}} else {{ '
        f'  [PSCustomObject]@{{ Alive=$false }} | ConvertTo-Json '
        f'}}'
    )
    raw = run_ps(cmd)
    if raw:
        return json.loads(raw)
    return None


def get_tcp_connections(remote_ip):
    """Get TCP connection details to the target IP."""
    cmd = (
        f'Get-NetTCPConnection -RemoteAddress "{remote_ip}" -ErrorAction SilentlyContinue | '
        f'Select-Object LocalPort, RemotePort, State, OwningProcess | ConvertTo-Json'
    )
    raw = run_ps(cmd)
    if raw:
        data = json.loads(raw)
        if isinstance(data, dict):
            data = [data]
        return data
    return []


def format_bytes(b):
    """Format byte count with human-readable suffix."""
    if b < 1024:
        return f"{b} B"
    elif b < 1024 * 1024:
        return f"{b / 1024:.1f} KB"
    else:
        return f"{b / (1024 * 1024):.1f} MB"


def main():
    print()
    print("+===================================================================+")
    print("|   backgroundTaskHost.exe  --  Live Network Monitor                |")
    print(f"|   PID: {TARGET_PID}  ->  {TARGET_IP}:443 (Akamai CDN)               |")
    print("|   Mode: Process I/O counters (no admin required)                  |")
    print("|   Press Ctrl+C to stop                                            |")
    print("+===================================================================+")
    print()

    # Initial snapshot
    print("  Taking initial I/O snapshot...", end="", flush=True)
    prev_io = get_process_io(TARGET_PID)
    if not prev_io or not prev_io.get('Alive'):
        print(f"\n  ERROR: PID {TARGET_PID} not found. Check if backgroundTaskHost.exe is still running.")
        sys.exit(1)
    print(" OK")

    # Check TCP connection
    conns = get_tcp_connections(TARGET_IP)
    if conns:
        for c in conns:
            print(f"  TCP: :{c['LocalPort']} -> {TARGET_IP}:{c['RemotePort']}  [{c['State']}]  PID={c['OwningProcess']}")
    else:
        print(f"  WARNING: No active TCP connection to {TARGET_IP} found")
    print()

    # Column headers
    hdr = (f"  {'Time':<20s}"
           f"  {'d_Read':>10s}"
           f"  {'d_Write':>10s}"
           f"  {'d_RdOps':>8s}"
           f"  {'d_WrOps':>8s}"
           f"  {'Tot Read':>12s}"
           f"  {'Tot Write':>12s}"
           f"  {'Mem':>7s}"
           f"  {'Thr':>4s}")
    print(hdr)
    print(f"  {'-' * 20}"
          f"  {'-' * 10}"
          f"  {'-' * 10}"
          f"  {'-' * 8}"
          f"  {'-' * 8}"
          f"  {'-' * 12}"
          f"  {'-' * 12}"
          f"  {'-' * 7}"
          f"  {'-' * 4}")

    # CSV setup
    with open(CSV_FILE, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Timestamp', 'TargetIP', 'PID',
            'DeltaReadBytes', 'DeltaWriteBytes', 'DeltaReadOps', 'DeltaWriteOps',
            'TotalReadBytes', 'TotalWriteBytes', 'TotalReadOps', 'TotalWriteOps',
            'WorkingSetMB', 'Threads', 'TCPState'
        ])

        silent_count = 0
        try:
            while True:
                time.sleep(POLL_INTERVAL)
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # Get current I/O
                cur_io = get_process_io(TARGET_PID)
                if not cur_io or not cur_io.get('Alive'):
                    print(f"  {timestamp}  *** PROCESS {TARGET_PID} TERMINATED ***")
                    break

                # Compute deltas
                d_read = cur_io['ReadBytes'] - prev_io['ReadBytes']
                d_write = cur_io['WriteBytes'] - prev_io['WriteBytes']
                d_rdops = cur_io['ReadOps'] - prev_io['ReadOps']
                d_wrops = cur_io['WriteOps'] - prev_io['WriteOps']

                # Check TCP state periodically (every 10s to reduce overhead)
                tcp_state = ""
                if silent_count % 10 == 0:
                    conns = get_tcp_connections(TARGET_IP)
                    if conns:
                        tcp_state = conns[0].get('State', '?')
                    else:
                        tcp_state = "GONE"

                # Print line
                if d_read > 0 or d_write > 0:
                    silent_count = 0
                    marker = " <->" if d_read > 0 and d_write > 0 else (" <<" if d_read > 0 else " >>")
                    print(f"  {timestamp}"
                          f"  {format_bytes(d_read):>10s}"
                          f"  {format_bytes(d_write):>10s}"
                          f"  {d_rdops:>8d}"
                          f"  {d_wrops:>8d}"
                          f"  {format_bytes(cur_io['ReadBytes']):>12s}"
                          f"  {format_bytes(cur_io['WriteBytes']):>12s}"
                          f"  {cur_io['WS_MB']:>6.1f}M"
                          f"  {cur_io['Threads']:>4d}"
                          f"{marker}")
                else:
                    silent_count += 1
                    if silent_count % 30 == 0:
                        state_str = f"  [{tcp_state}]" if tcp_state else ""
                        print(f"  {timestamp}"
                              f"  {'.':>10s}"
                              f"  {'.':>10s}"
                              f"  {'.':>8s}"
                              f"  {'.':>8s}"
                              f"  {format_bytes(cur_io['ReadBytes']):>12s}"
                              f"  {format_bytes(cur_io['WriteBytes']):>12s}"
                              f"  {cur_io['WS_MB']:>6.1f}M"
                              f"  {cur_io['Threads']:>4d}"
                              f"  [quiet {silent_count}s]{state_str}")

                # Write CSV
                writer.writerow([
                    timestamp, TARGET_IP, TARGET_PID,
                    d_read, d_write, d_rdops, d_wrops,
                    cur_io['ReadBytes'], cur_io['WriteBytes'],
                    cur_io['ReadOps'], cur_io['WriteOps'],
                    cur_io['WS_MB'], cur_io['Threads'], tcp_state
                ])
                f.flush()

                prev_io = cur_io

        except KeyboardInterrupt:
            print()
            print()
            print("  === Monitor Stopped ===")
            print(f"  Total Read:  {format_bytes(cur_io['ReadBytes'])}")
            print(f"  Total Write: {format_bytes(cur_io['WriteBytes'])}")
            print(f"  CSV saved:   {CSV_FILE}")
            print()


if __name__ == '__main__':
    main()
