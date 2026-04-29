$ErrorActionPreference = "Stop"

# 1. Define the safe, lightweight XML config for Sysmon
$sysmonConfigPath = ".\sysmon_svchost_config.xml"
$sysmonConfig = @"
<Sysmon schemaversion="4.90">
  <HashAlgorithms>SHA256</HashAlgorithms>
  <EventFiltering>
    <!-- Log network connections for svchost only -->
    <NetworkConnect onmatch="include">
      <Image condition="end with">svchost.exe</Image>
    </NetworkConnect>
  </EventFiltering>
</Sysmon>
"@

if (-not (Test-Path $sysmonConfigPath)) {
    Set-Content -Path $sysmonConfigPath -Value $sysmonConfig
}

# 2. Check if Sysmon is installed. If not, download and install it.
$sysmonService = Get-Service -Name "Sysmon64" -ErrorAction SilentlyContinue
if (-not $sysmonService) {
    Write-Host "[*] Microsoft Sysmon is not installed. Downloading from Sysinternals..." -ForegroundColor Cyan
    $sysmonZip = ".\Sysmon.zip"
    Invoke-WebRequest -Uri "https://download.sysinternals.com/files/Sysmon.zip" -OutFile $sysmonZip
    Expand-Archive -Path $sysmonZip -DestinationPath ".\Sysmon" -Force
    
    Write-Host "[*] Installing Sysmon with targeted svchost rules..." -ForegroundColor Cyan
    Start-Process -FilePath ".\Sysmon\Sysmon64.exe" -ArgumentList "-i $sysmonConfigPath -accepteula" -Wait -NoNewWindow
    Write-Host "[+] Sysmon installed successfully." -ForegroundColor Green
} else {
    Write-Host "[*] Sysmon is already installed. Ensuring correct configuration..." -ForegroundColor Cyan
    Start-Process -FilePath "sysmon64.exe" -ArgumentList "-c $sysmonConfigPath" -Wait -NoNewWindow
}

# 3. Read the Sysmon Event log in real-time
Write-Host "`n[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Starting Advanced Sysmon Tracking..." -ForegroundColor Green
Write-Host "Monitoring for ANY svchost network activity. Press Ctrl+C to stop.`n"

# We will start reading from the newest event onwards
$lastRecordId = 0
$latestEvent = Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" -MaxEvents 1 -ErrorAction SilentlyContinue
if ($latestEvent) { $lastRecordId = $latestEvent.RecordId }

while ($true) {
    # Fetch new events
    $events = Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" -ErrorAction SilentlyContinue | Where-Object { $_.RecordId -gt $lastRecordId }
    
    if ($events) {
        $events = $events | Sort-Object RecordId
        foreach ($evt in $events) {
            $lastRecordId = $evt.RecordId
            # Event ID 3 is Network Connection
            if ($evt.Id -eq 3) {
                # Convert the XML event data to an object
                $xml = [xml]$evt.ToXml()
                $eventData = @{}
                $xml.Event.EventData.Data | ForEach-Object { $eventData[$_.Name] = $_.'#text' }
                
                $processId = $eventData["ProcessId"]
                $destIp = $eventData["DestinationIp"]
                $destPort = $eventData["DestinationPort"]
                $destHost = $eventData["DestinationHostname"]
                
                # Basic exclusion for loopback/local
                if ($destIp -notmatch "^127\." -and $destIp -notmatch "^192\.168\." -and $destIp -ne "::1") {
                    Write-Host "[EVENT] Connection Detected:" -ForegroundColor Yellow
                    Write-Host "  Time:   $($evt.TimeCreated)"
                    Write-Host "  PID:    $processId"
                    Write-Host "  Dest:   $destIp : $destPort"
                    Write-Host "  Host:   $destHost`n"
                }
            }
        }
    }
    Start-Sleep -Milliseconds 500
}