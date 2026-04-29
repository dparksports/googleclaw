$ErrorActionPreference = "Stop"

$sysmonConfigPath = ".\sysmon_svchost_config.xml"
$sysmonConfig = @"
<Sysmon schemaversion="4.90">
  <HashAlgorithms>SHA256</HashAlgorithms>
  <EventFiltering>
    <NetworkConnect onmatch="include">
      <Image condition="end with">svchost.exe</Image>
    </NetworkConnect>
  </EventFiltering>
</Sysmon>
"@

if (-not (Test-Path $sysmonConfigPath)) { Set-Content -Path $sysmonConfigPath -Value $sysmonConfig }

$sysmonService = Get-Service -Name "Sysmon64" -ErrorAction SilentlyContinue
if (-not $sysmonService) {
    Write-Host "[*] Microsoft Sysmon is required for Ultimate Mode. Downloading..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri "https://download.sysinternals.com/files/Sysmon.zip" -OutFile ".\Sysmon.zip"
    Expand-Archive -Path ".\Sysmon.zip" -DestinationPath ".\Sysmon" -Force
    
    Write-Host "[*] Installing Sysmon invisibly..." -ForegroundColor Cyan
    Start-Process -FilePath ".\Sysmon\Sysmon64.exe" -ArgumentList "-i $sysmonConfigPath -accepteula" -Wait -NoNewWindow
} else {
    Write-Host "[*] Ensuring Sysmon rules are active..." -ForegroundColor Cyan
    Start-Process -FilePath "sysmon64.exe" -ArgumentList "-c $sysmonConfigPath" -Wait -NoNewWindow
}

Write-Host "[+] Sysmon Kernel Driver is Active. Starting Ultimate Auto-Pilot..." -ForegroundColor Green
Start-Sleep -Seconds 2
