$ip = '52.110.4.23'
Write-Host "Monitoring connections to $ip (Press Ctrl+C to stop)..."
while ($true) {
    $timestamp = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    $conns = netstat -ano | Select-String $ip
    if ($conns) {
        Write-Host "--- $timestamp ---"
        $conns | ForEach-Object { Write-Host $_.Line.Trim() }
    } else {
        Write-Host "[$timestamp] No active connections."
    }
    Start-Sleep -Seconds 1
}
