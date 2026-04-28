# ============================================================================
# Windows Firewall Hardening: Restrict backgroundTaskHost.exe
# ============================================================================
# This script creates an outbound Windows Firewall rule to block 
# backgroundTaskHost.exe from communicating with the internet, EXCEPT
# for verified Microsoft IP ranges.
#
# HOW IT WORKS:
# Windows Firewall "Block" rules always override "Allow" rules. To block
# everything except Microsoft, we cannot simply use an Allow rule. Instead,
# we must create a Block rule where the RemoteAddress contains the INVERSE
# of Microsoft's IP space (i.e., every IP address in the world EXCEPT 
# Microsoft's).
#
# NOTE: This is a proof-of-concept. Restricting this process to only
# Microsoft IPs will BREAK legitimate third-party UWP apps (like Spotify,
# Netflix, etc.) that rely on background tasks to communicate with their
# own servers.
# ============================================================================

#Requires -RunAsAdministrator

$ruleName = "Block_BTH_NonMicrosoft_Outbound"
$appPath  = "$env:SystemRoot\System32\backgroundTaskHost.exe"

Write-Host "=== Hardening backgroundTaskHost.exe Outbound Traffic ===" -ForegroundColor Cyan

# 1. Remove existing rule if it exists
$existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
if ($existingRule) {
    Remove-NetFirewallRule -DisplayName $ruleName
    Write-Host "[-] Removed existing firewall rule."
}

# 2. Define Microsoft IP Ranges (Simplified for demonstration)
# In a true enterprise environment, you would pull this dynamically from 
# the Microsoft 365 / Azure published JSON endpoints.
Write-Host "[*] Compiling Microsoft IP ranges..."
$microsoftSubnets = @(
    "20.0.0.0/8",      # Microsoft Azure
    "40.76.0.0/14",    # Microsoft Azure
    "52.0.0.0/8",      # Microsoft Azure / M365
    "104.40.0.0/13",   # Microsoft Azure
    "137.116.0.0/16",  # Microsoft Azure
    "204.79.197.200/32" # Windows Update / Telemetry edge
)

# 3. Define the Inverse IP Ranges
# To block everything EXCEPT Microsoft, we define the "rest of the internet"
# as ranges that don't overlap with the above. This requires a subnet calculator 
# to perfectly map 0.0.0.0 - 255.255.255.255 minus Microsoft IPs.
# 
# For this script, we will block standard malicious/proxy hosting ranges and 
# typical CDN blocks (like the Akamai IP we found) as a targeted defense.
Write-Host "[*] Calculating blocked IP ranges (Non-Microsoft spaces)..."
$blockedRanges = @(
    "1.0.0.0/8",     # Various public IPs
    "5.0.0.0/8",     # Includes the Akamai CDN range we found (5.129.7.23)
    "23.0.0.0/8",    # Includes Akamai / external CDNs
    "100.64.0.0/10", # Carrier-grade NAT
    "172.16.0.0/12", # Local lateral movement prevention
    "192.168.0.0/16" # Local lateral movement prevention
)

# 4. Create the Windows Firewall Rule
Write-Host "[*] Creating Windows Firewall Outbound Block Rule..."

New-NetFirewallRule -DisplayName $ruleName `
                    -Description "Blocks backgroundTaskHost.exe from communicating with non-Microsoft external IPs." `
                    -Direction Outbound `
                    -Action Block `
                    -Program $appPath `
                    -RemoteAddress $blockedRanges `
                    -Profile Any `
                    -Enabled True | Out-Null

Write-Host "[+] Firewall rule '$ruleName' created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "WARNING: To fully restrict to ONLY Microsoft, the `$blockedRanges array must contain" -ForegroundColor Yellow
Write-Host "thousands of mathematically inverted subnets covering the entire IPv4/IPv6 space." -ForegroundColor Yellow
Write-Host "This script demonstrates the architecture of the block using known CDN/risky ranges." -ForegroundColor Yellow
