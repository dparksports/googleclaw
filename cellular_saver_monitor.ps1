$log = 'C:\Users\honey\googleclaw\process_monitor.log'
Add-Content -Path $log -Value "--- $(Get-Date) Monitor Started ---"
try {
    $reg = 'HKLM:\SOFTWARE\Policies\Microsoft\Dsh'
    if (-not (Test-Path $reg)) { New-Item -Path $reg -Force -ErrorAction SilentlyContinue | Out-Null }
    Set-ItemProperty -Path $reg -Name 'AllowNewsAndInterests' -Value 0 -Type DWord -Force -ErrorAction SilentlyContinue
} catch {}
Stop-Process -Name 'Widgets' -Force -ErrorAction SilentlyContinue
$s = @{}
while($true) {
    $procs = Get-CimInstance Win32_Process -Filter "Name='Widgets.exe' OR Name='msedgewebview2.exe' OR Name='backgroundTaskHost.exe'"
    foreach($i in $procs) {
        if($i.Name -eq 'Widgets.exe') {
            Stop-Process -Id $i.ProcessId -Force -ErrorAction SilentlyContinue
            Add-Content -Path $log -Value "$(Get-Date) - KILLED Widgets.exe PID $($i.ProcessId)"
        } elseif (-not $s.ContainsKey($i.ProcessId)) {
            $s[$i.ProcessId] = $true
            Add-Content -Path $log -Value "$(Get-Date) - RUNNING $($i.Name) PID $($i.ProcessId) - Cmd: $($i.CommandLine)"
        }
    }
    Start-Sleep -Seconds 15
}