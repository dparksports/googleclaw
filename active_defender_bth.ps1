# ============================================================================
# Active Defense: Rogue backgroundTaskHost.exe Sweep
# ============================================================================
# Scans all running 'backgroundTaskHost.exe' processes, extracts the App ID
# from the -ServerName command-line argument, and cross-references it against
# the system's registered UWP packages. If an App ID is completely absent
# (indicating Defense Evasion / Masquerading via LoLBin), the script
# terminates the malicious process and logs the event.
#
# Usage (elevated):  .\active_defender_bth.ps1
# ============================================================================

#Requires -RunAsAdministrator

$logFile = "C:\Users\honey\googleclaw\rogue_bth_terminations.log"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $entry = "[$timestamp] $Message"
    Write-Host $entry
    Add-Content -Path $logFile -Value $entry
}

# ------------------------------------------------------------------
# 1. Build a hash-set of every registered UWP / AppX server name
#    so look-ups are O(1).
# ------------------------------------------------------------------
Write-Host ""
Write-Host "=== Executing Active Defense Sweep for Rogue backgroundTaskHost.exe ===" -ForegroundColor Cyan
Write-Host ""

Write-Log "INFO  | Building registered UWP package index..."

$registeredAppIds = @{}

# Source 1: Enumerate all AppX packages for all users
try {
    $packages = Get-AppxPackage -AllUsers -ErrorAction SilentlyContinue
    foreach ($pkg in $packages) {
        # Store the PackageFamilyName - this is the base used in ServerName args
        if ($pkg.PackageFamilyName) {
            $registeredAppIds[$pkg.PackageFamilyName] = $true
        }
        # Also store the full PackageFullName
        if ($pkg.PackageFullName) {
            $registeredAppIds[$pkg.PackageFullName] = $true
        }
    }
} catch {
    Write-Log "WARN  | Could not enumerate AppX packages: $_"
}

# Source 2: Scan HKCU and HKLM Software\Classes for registered AppId entries
$registryPaths = @(
    "HKCU:\Software\Classes\AppID",
    "HKLM:\Software\Classes\AppID",
    "HKCU:\Software\Classes\CLSID",
    "HKLM:\Software\Classes\CLSID"
)

foreach ($regPath in $registryPaths) {
    if (Test-Path $regPath) {
        try {
            $keys = Get-ChildItem -Path $regPath -ErrorAction SilentlyContinue
            foreach ($key in $keys) {
                $registeredAppIds[$key.PSChildName] = $true
            }
        } catch {
            Write-Log "WARN  | Could not read registry path ${regPath}: $_"
        }
    }
}

# Source 3: Scan activation entries under PackageRepository
$activationPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModel\PackageRepository\Packages"
if (Test-Path $activationPath) {
    try {
        $keys = Get-ChildItem -Path $activationPath -ErrorAction SilentlyContinue
        foreach ($key in $keys) {
            $registeredAppIds[$key.PSChildName] = $true
        }
    } catch {
        Write-Log "WARN  | Could not read PackageRepository: $_"
    }
}

$totalRegistered = $registeredAppIds.Count
Write-Log "INFO  | Indexed $totalRegistered registered App IDs / CLSIDs / PackageFamilyNames."

# ------------------------------------------------------------------
# 2. Enumerate every running backgroundTaskHost.exe and validate
# ------------------------------------------------------------------
Write-Log "INFO  | Scanning running backgroundTaskHost.exe processes..."

$processes = Get-CimInstance Win32_Process -Filter "Name = 'backgroundTaskHost.exe'" -ErrorAction SilentlyContinue
$rogueFound = $false
$scannedCount = 0
$terminatedCount = 0

if (-not $processes -or $processes.Count -eq 0) {
    Write-Log "INFO  | No backgroundTaskHost.exe processes are currently running. System is clean."
} else {
    foreach ($proc in $processes) {
        $scannedCount++
        $procPid = $proc.ProcessId
        $cmdLine = $proc.CommandLine
        $parentPid = $proc.ParentProcessId

        Write-Log "SCAN  | PID=$procPid  CommandLine=[$cmdLine]"

        # Extract the -ServerName argument value
        $serverName = $null
        if ($cmdLine -match '-ServerName[:=]\s*"?([^\s"]+)"?') {
            $serverName = $Matches[1]
        } elseif ($cmdLine -match '-ServerName\s+"?([^\s"]+)"?') {
            $serverName = $Matches[1]
        }

        if (-not $serverName) {
            Write-Log "WARN  | PID=$procPid  No -ServerName argument found in command line. Flagging as suspicious."
            $rogueFound = $true
            continue
        }

        # Cross-reference against our registered index
        # The ServerName usually looks like: PackageFamilyName!AppClassName
        # We check the full value, the part before '!', and partial matches
        $isRegistered = $false

        # Direct match
        if ($registeredAppIds.ContainsKey($serverName)) {
            $isRegistered = $true
        }

        # Check the PackageFamilyName portion (before the '!')
        if (-not $isRegistered -and $serverName -match '^([^!]+)!') {
            $familyName = $Matches[1]
            if ($registeredAppIds.ContainsKey($familyName)) {
                $isRegistered = $true
            }
        }

        # Partial substring match against all known package family names
        if (-not $isRegistered) {
            foreach ($knownId in $registeredAppIds.Keys) {
                if ($serverName -like "*$knownId*" -or $knownId -like "*$serverName*") {
                    $isRegistered = $true
                    break
                }
            }
        }

        if ($isRegistered) {
            Write-Log "OK    | PID=$procPid  ServerName=[$serverName] is REGISTERED. Legitimate process."
        } else {
            $rogueFound = $true
            $terminatedCount++

            Write-Log "ALERT | ============================================================"
            Write-Log "ALERT | ROGUE PROCESS DETECTED - Defense Evasion / Masquerading"
            Write-Log "ALERT | PID         : $procPid"
            Write-Log "ALERT | Parent PID  : $parentPid"
            Write-Log "ALERT | ServerName  : $serverName"
            Write-Log "ALERT | CommandLine : $cmdLine"
            Write-Log "ALERT | ============================================================"

            # Attempt to gather parent process info for forensic logging
            try {
                $parentProc = Get-CimInstance Win32_Process -Filter "ProcessId = $parentPid" -ErrorAction SilentlyContinue
                if ($parentProc) {
                    Write-Log "ALERT | Parent Name : $($parentProc.Name)"
                    Write-Log "ALERT | Parent Cmd  : $($parentProc.CommandLine)"
                }
            } catch {
                Write-Log "WARN  | Could not retrieve parent process info for PID $parentPid"
            }

            # Capture network connections from this process before termination
            try {
                $netConns = Get-NetTCPConnection -OwningProcess $procPid -ErrorAction SilentlyContinue
                if ($netConns) {
                    foreach ($conn in $netConns) {
                        $netMsg = 'ALERT | Network     : {0}:{1} -> {2}:{3} [{4}]' -f $conn.LocalAddress, $conn.LocalPort, $conn.RemoteAddress, $conn.RemotePort, $conn.State
                        Write-Log $netMsg
                    }
                }
            } catch {
                Write-Log "WARN  | Could not capture network connections for PID $procPid"
            }

            # Terminate the rogue process
            try {
                Stop-Process -Id $procPid -Force -ErrorAction Stop
                Write-Log "KILL  | PID=$procPid successfully terminated."
            } catch {
                Write-Log "ERROR | Failed to terminate PID=${procPid}: $_"
            }
        }
    }
}

# ------------------------------------------------------------------
# 3. Summary
# ------------------------------------------------------------------
Write-Host ""
Write-Host "=== Active Defense Sweep Complete ===" -ForegroundColor Cyan
Write-Log "INFO  | Scan Summary: $scannedCount process(es) scanned, $terminatedCount rogue process(es) terminated."

if ($rogueFound) {
    Write-Host ""
    Write-Host "[!] ROGUE PROCESSES WERE DETECTED. Review the log for details:" -ForegroundColor Red
    Write-Host "    $logFile" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Recommended next steps:" -ForegroundColor Yellow
    Write-Host "  1. Run a full anti-malware scan (Windows Defender / EDR)" -ForegroundColor White
    Write-Host "  2. Review network logs for connections to external IPs from backgroundTaskHost.exe" -ForegroundColor White
    Write-Host "  3. Check Sysmon / Event Viewer for Event ID 1 (Process Creation) correlations" -ForegroundColor White
    Write-Host "  4. Investigate the parent process chain for the initial infection vector" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "[OK] All backgroundTaskHost.exe processes are legitimate. No threats detected." -ForegroundColor Green
}

Write-Host ""
Write-Host "Log file: $logFile" -ForegroundColor Gray
