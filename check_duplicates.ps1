$csvFile = "all_mp4_scanned.csv"
if (!(Test-Path $csvFile)) {
    Write-Host "Error: $csvFile not found in the current directory."
    return
}

$csvData = Import-Csv -Path $csvFile
if ($null -eq $csvData) {
    Write-Host "The CSV file is empty or could not be parsed."
    return
}

# Identify header names dynamically for Hash and Path
$headers = $csvData[0].psobject.properties.name
$hashKey = $headers | Where-Object { $_ -match "hash" } | Select-Object -First 1
$pathKey = $headers | Where-Object { $_ -match "path" } | Select-Object -First 1

if (!$hashKey -or !$pathKey) {
    Write-Host "Required columns (Hash and Path) not detected in CSV headers."
    return
}

# Group data by Hash
$duplicates = $csvData | Group-Object -Property $hashKey | Where-Object { $_.Count -gt 1 }

if ($duplicates.Count -eq 0) {
    Write-Host "No duplicate hash values found."
    return
}

Write-Host "Found $($duplicates.Count) duplicate hash groups:`n"

foreach ($group in $duplicates) {
    Write-Host "--------------------------------------------------"
    Write-Host "Hash: $($group.Name)"
    $fileNames = @()
    
    foreach ($row in $group.Group) {
        $rawPath = $row.$pathKey.Trim('"').Trim()
        if (Test-Path $rawPath) {
            $item = Get-Item $rawPath
            Write-Host "  - Full Path: $($item.FullName)"
            Write-Host "    Size:      $($item.Length) bytes"
            Write-Host "    Filename:  $($item.Name)"
            $fileNames += $item.Name
        } else {
            Write-Host "  - Path Not Found: $rawPath"
        }
    }
    
    # Check for identical filenames within the hash group
    if ($fileNames.Count -gt 1 -and ($fileNames | Select-Object -Unique).Count -eq 1) {
        Write-Host "  [!] NOTICE: All filenames for this hash are IDENTICAL."
    } elseif ($fileNames.Count -gt 1) {
        Write-Host "  [ ] Note: Filenames for this hash differ."
    }
}
Write-Host "`nAnalysis complete."