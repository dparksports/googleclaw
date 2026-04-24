# ============================================================================
# Windows Firewall Hardening: Restrict msedgewebview2.exe from CDNs
# ============================================================================
# This script creates an outbound Windows Firewall rule to block 
# msedgewebview2.exe from communicating with specific known CDN IP ranges 
# (Akamai, Amazon CloudFront).
#
# WARNING: Blocking WebView2 from CDNs WILL break web rendering in native 
# Windows apps (Search, Widgets, Teams) as they rely on these CDNs to 
# load CSS, images, and Javascript. Use this only for strict lockdown.
# ============================================================================

#Requires -RunAsAdministrator

$ruleNameBase = "Block_CDN_Outbound"

# Windows Firewall does not accept wildcards like "*\app.exe" for the Program path.
# We must dynamically discover the absolute paths.
$appPaths = @()

Write-Host "=== Hardening msedgewebview2.exe & Widgets.exe Outbound Traffic ===" -ForegroundColor Cyan
Write-Host "[*] Discovering application paths..."

# 1a. Discover WebView2 path
$webViewPath = (Get-ChildItem -Path "C:\Program Files (x86)\Microsoft\EdgeWebView\Application" -Filter "msedgewebview2.exe" -Recurse -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
if ($webViewPath) {
    $appPaths += $webViewPath
    Write-Host "    [+] Found WebView2: $webViewPath"
} else {
    Write-Host "    [-] Could not find msedgewebview2.exe"
}

# 1b. Discover Widgets path
$widgetsPath = (Get-ChildItem -Path "C:\Program Files\WindowsApps" -Filter "Widgets.exe" -Recurse -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
if ($widgetsPath) {
    $appPaths += $widgetsPath
    Write-Host "    [+] Found Widgets: $widgetsPath"
} else {
    Write-Host "    [-] Could not find Widgets.exe"
}

if ($appPaths.Count -eq 0) {
    Write-Host "[!] No applications found. Exiting." -ForegroundColor Red
    exit
}

# 1c. Remove existing rules if they exist
foreach ($app in $appPaths) {
    $appName = ($app -split "\\")[-1]
    $ruleName = "${ruleNameBase}_${appName}"
    $existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
    if ($existingRule) {
        Remove-NetFirewallRule -DisplayName $ruleName
        Write-Host "[-] Removed existing firewall rule: $ruleName"
    }
}

# 2. Define CDN IP Ranges to Block
# CDNs have massive IP spaces. We are targeting the primary blocks used by 
# Akamai and Amazon CloudFront observed in typical telemetry.
Write-Host "[*] Compiling CDN IP ranges (Akamai & Amazon CloudFront)..."
$blockedCDNRanges = @(
    # --- Amazon Web Services / CloudFront ---
    "13.32.0.0/15",    
    "13.224.0.0/14",   
    "13.249.0.0/16",   # Matches 13.249.185.38
    "18.160.0.0/15",
    "18.238.0.0/15",
    "52.46.0.0/18",
    "52.84.0.0/15",
    "52.124.0.0/14",
    "54.230.0.0/15",
    "54.239.128.0/18",
    "99.84.0.0/16",
    "143.204.0.0/16",
    
    # --- Akamai Technologies ---
    "23.0.0.0/8",      # Very broad Akamai/CDN space (Matches 23.61.x.x)
    "96.16.0.0/15",    
    "104.64.0.0/10",   
    "184.24.0.0/13",
    "202.21.128.0/22"
)

# 3. Create the Windows Firewall Rules
Write-Host "[*] Creating Windows Firewall Outbound Block Rules..."

foreach ($app in $appPaths) {
    $appName = (Split-Path $app -Leaf)
    # Add a short hash of the path to the rule name to avoid collisions if multiple versions exist
    $pathHash = ($app.GetHashCode()).ToString("X")
    $ruleName = "${ruleNameBase}_${appName}_${pathHash}"
    
    New-NetFirewallRule -DisplayName $ruleName `
                        -Description "Blocks $appName from communicating with Akamai and AWS CDN ranges." `
                        -Direction Outbound `
                        -Action Block `
                        -Program $app `
                        -RemoteAddress $blockedCDNRanges `
                        -Profile Any `
                        -Enabled True | Out-Null

    Write-Host "[+] Firewall rule '$ruleName' created successfully!" -ForegroundColor Green
}

Write-Host ""
Write-Host "NOTE: To monitor this rule blocking traffic, enable Firewall Dropped logging:" -ForegroundColor Yellow
Write-Host "netsh advfirewall set currentprofile logging droppedconnections enable" -ForegroundColor Yellow
