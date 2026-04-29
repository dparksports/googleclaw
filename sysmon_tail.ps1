$ErrorActionPreference = "SilentlyContinue"

$lastRecordId = 0
$latestEvent = Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" -MaxEvents 1
if ($latestEvent) { $lastRecordId = $latestEvent.RecordId }

while ($true) {
    $events = Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" | Where-Object { $_.RecordId -gt $lastRecordId }
    
    if ($events) {
        $events = $events | Sort-Object RecordId
        foreach ($evt in $events) {
            $lastRecordId = $evt.RecordId
            if ($evt.Id -eq 3) {
                $xml = [xml]$evt.ToXml()
                $eventData = @{}
                $xml.Event.EventData.Data | ForEach-Object { $eventData[$_.Name] = $_.'#text' }
                
                $pid = $eventData["ProcessId"]
                $ip = $eventData["DestinationIp"]
                $hostName = $eventData["DestinationHostname"]
                
                # Output format: PID,IP,Hostname
                Write-Output "$pid,$ip,$hostName"
            }
        }
    }
    Start-Sleep -Milliseconds 100
}