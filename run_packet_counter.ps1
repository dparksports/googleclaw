$ErrorActionPreference = "Stop"
$csvFile = "targeted_packet_stats.csv"

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "   Targeted Packet Counter (pktmon)" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "Because this tool works at the network card level, it cannot filter by process (svchost)."
Write-Host "Instead, you can target the specific suspicious IP you found in Standard Mode.`n"

$targetIp = Read-Host "Enter the specific IP to monitor (or press Enter to monitor ALL traffic)"

# 1. Initialize CSV
if (-not (Test-Path $csvFile)) {
    "Timestamp,Target_IP,Packets_Sent,Packets_Received" | Out-File -FilePath $csvFile -Encoding utf-8
}

Write-Host "`n[*] Initializing Windows Packet Monitor (pktmon)..." -ForegroundColor Cyan

# 2. Reset pktmon and set filters
pktmon stop 2>$null
pktmon filter remove 2>$null

if ([string]::IsNullOrWhiteSpace($targetIp)) {
    $targetIp = "ALL_TRAFFIC"
    Write-Host "[*] No IP entered. Filtering for ALL TCP/UDP traffic..." -ForegroundColor Yellow
    pktmon filter add -t TCP UDP | Out-Null
} else {
    Write-Host "[*] Filtering strictly for IP: $targetIp" -ForegroundColor Yellow
    pktmon filter add -i $targetIp | Out-Null
}

Write-Host "[*] Starting live capture (Circular 10MB limit to save disk space)..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop.`n"

# -s 10: Limits the file size to 10MB circular to prevent disk exhaustion
pktmon start -c --pkt-size 0 -s 10 --file-name "temp_capture.etl" | Out-Null

try {
    while ($true) {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        
        $rawCounters = pktmon counters
        
        $rxPackets = 0
        $txPackets = 0
        
        foreach ($line in $rawCounters) {
            if ($line -match "Packets:\s+(\d+)\s+\(Rx\),\s+(\d+)\s+\(Tx\)") {
                $rxPackets += [int]$Matches[1]
                $txPackets += [int]$Matches[2]
            }
        }

        cls
        echo "===================================================="
        echo "   LIVE PACKET COUNTER"
        echo "===================================================="
        echo "Time:   $timestamp"
        echo "Target: $targetIp"
        echo "----------------------------------------------------"
        echo "Packets Received (Rx): $rxPackets"
        echo "Packets Sent     (Tx): $txPackets"
        echo "----------------------------------------------------"
        echo "Log File: $csvFile"
        echo "Press Ctrl+C to exit back to menu."
        echo "===================================================="
        
        "$timestamp,$targetIp,$txPackets,$rxPackets" | Out-File -FilePath $csvFile -Append -Encoding utf-8
        
        Start-Sleep -Seconds 2
    }
}
finally {
    pktmon stop | Out-Null
    Write-Host "`n[*] Stopped Packet Monitor. Cleaning up..." -ForegroundColor Yellow
}