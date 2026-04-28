# ============================================================================
# Incident Response Sweep: Post-Detection Triage
# ============================================================================
# This script performs automated post-detection triage for the rogue
# backgroundTaskHost.exe incident.
#
# 1. Traces the Infection Vector (Event Logs)
# 2. Extracts Network Indicators (Sysmon / DNS Cache)
# 3. Initiates a Windows Defender Quick Scan
# ============================================================================

$reportFile = "C:\Users\honey\googleclaw\incident_triage_report.txt"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

function Write-Report {
    param([string]$Message)
    Write-Host $Message
    Add-Content -Path $reportFile -Value $Message
}

Write-Report "======================================================================"
Write-Report "INCIDENT TRIAGE REPORT - $timestamp"
Write-Report "======================================================================"
Write-Report ""

# ----------------------------------------------------------------------------
# STEP 1: Trace Infection Vector
# ----------------------------------------------------------------------------
Write-Report "[*] STEP 1: Tracing Infection Vector (Parent Process Chain)..."

# The rogue PID was 6952, parent was 1424 (svchost.exe)
$roguePid = 6952
$parentPid = 1424

Write-Report "    Querying Security Event Log (4688) for rogue processes..."

try {
    # We look back 24 hours
    $startTime = (Get-Date).AddHours(-24)
    
    # Query Process Creation events
    $events = Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4688; StartTime=$startTime} -ErrorAction SilentlyContinue | 
              Where-Object { $_.Properties[5].Value -match "backgroundTaskHost.exe|svchost.exe" -and ($_.Properties[4].Value -match "1424" -or $_.Properties[4].Value -match "6952") }
              
    if ($events) {
        foreach ($event in $events) {
            $time = $event.TimeCreated
            $procName = $event.Properties[5].Value
            $procId = [Convert]::ToInt32($event.Properties[4].Value, 16)
            $parentProcId = [Convert]::ToInt32($event.Properties[1].Value, 16)
            $cmdLine = $event.Properties[8].Value
            
            Write-Report "    [+] Match Found: $time | PID: $procId | Parent PID: $parentProcId | Process: $procName"
            Write-Report "        CmdLine: $cmdLine"
        }
    } else {
        Write-Report "    [-] No direct Security 4688 events found for PID 1424 or 6952."
    }
} catch {
    Write-Report "    [!] Error querying Security logs: $_"
}

# ----------------------------------------------------------------------------
# STEP 2: Review Network Connections
# ----------------------------------------------------------------------------
Write-Report ""
Write-Report "[*] STEP 2: Reviewing Network Connections and DNS..."

Write-Report "    Checking active DNS cache for suspicious domains..."
try {
    $dnsCache = Get-DnsClientCache | Where-Object { $_.Entry -notmatch "microsoft.com|windows.com|local" }
    if ($dnsCache) {
        foreach ($entry in $dnsCache) {
            Write-Report "    [+] DNS Cache Entry: $($entry.Entry) -> $($entry.Data)"
        }
    } else {
         Write-Report "    [-] No highly anomalous DNS entries found in cache."
    }
} catch {
    Write-Report "    [!] Error querying DNS cache: $_"
}

Write-Report "    Checking Windows Firewall logs (pfirewall.log) for dropped connections..."
$firewallLog = "$env:SystemRoot\System32\LogFiles\Firewall\pfirewall.log"
if (Test-Path $firewallLog) {
    try {
        $recentDrops = Select-String -Path $firewallLog -Pattern "DROP" | Select-Object -Last 10
        foreach ($drop in $recentDrops) {
            Write-Report "    [+] FW DROP: $($drop.Line)"
        }
    } catch {
        Write-Report "    [!] Error reading firewall log: $_"
    }
} else {
    Write-Report "    [-] Firewall log not found at expected path."
}

# ----------------------------------------------------------------------------
# STEP 3: Anti-Malware Scan
# ----------------------------------------------------------------------------
Write-Report ""
Write-Report "[*] STEP 3: Initiating Anti-Malware Scan (Windows Defender)..."

try {
    $defenderPath = "$env:ProgramFiles\Windows Defender\MpCmdRun.exe"
    if (Test-Path $defenderPath) {
        Write-Report "    Starting Quick Scan..."
        
        # Start the scan process. Wait for it to complete. 
        # ScanType 1 = Quick Scan. ScanType 2 = Full Scan. (Quick scan used for immediate triage)
        $scanProcess = Start-Process -FilePath $defenderPath -ArgumentList "-Scan -ScanType 1" -Wait -NoNewWindow -PassThru
        
        if ($scanProcess.ExitCode -eq 0) {
            Write-Report "    [+] Quick Scan completed successfully. No immediate threats found."
        } elseif ($scanProcess.ExitCode -eq 2) {
            Write-Report "    [!] Quick Scan detected malware! Please check Defender GUI for remediation details."
        } else {
            Write-Report "    [?] Scan finished with exit code: $($scanProcess.ExitCode)"
        }
        
        # Grab recent Defender detection events (Event ID 1116 = Malware detected)
        $defEvents = Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-Windows Defender/Operational'; ID=1116; StartTime=$startTime} -ErrorAction SilentlyContinue
        if ($defEvents) {
            foreach ($defEv in $defEvents) {
                Write-Report "    [!] DEFENDER ALERT: $($defEv.Message)"
            }
        }
    } else {
        Write-Report "    [-] Windows Defender command-line utility not found."
    }
} catch {
    Write-Report "    [!] Error running Defender scan: $_"
}

Write-Report ""
Write-Report "======================================================================"
Write-Report "TRIAGE COMPLETE"
Write-Report "Report saved to: $reportFile"
Write-Report "======================================================================"
