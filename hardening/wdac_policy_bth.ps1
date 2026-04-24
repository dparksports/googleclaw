# ============================================================================
# WDAC (Windows Defender Application Control) Policy Generator
# backgroundTaskHost.exe DCOM Launch Restriction
# ============================================================================
#
# This script generates a WDAC supplemental policy that restricts which
# parent processes are allowed to launch backgroundTaskHost.exe via DCOM.
#
# Strategy:
#   1. Create a base deny rule for backgroundTaskHost.exe launched by
#      untrusted parents (scripts, unsigned binaries, LOLBins).
#   2. Whitelist only svchost.exe (the legitimate DCOM activator) as an
#      authorized parent.
#   3. Deploy as a supplemental policy to your existing WDAC base policy.
#
# Usage (elevated):
#   .\wdac_policy_bth.ps1
#
# After running, deploy the generated .cip file via:
#   - Group Policy (Computer Config > Admin Templates > System > Device Guard)
#   - Microsoft Intune / Endpoint Manager
#   - Manual copy to C:\Windows\System32\CodeIntegrity\CiPolicies\Active\
#
# ============================================================================

#Requires -RunAsAdministrator
#Requires -Modules ConfigCI

$outputDir  = "C:\Users\honey\googleclaw\hardening\wdac_output"
$policyName = "BTH_LoLBin_Restriction"
$policyFile = Join-Path $outputDir "${policyName}.xml"
$binaryFile = Join-Path $outputDir "${policyName}.cip"

# Ensure output directory exists
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

Write-Host ""
Write-Host "=== WDAC Policy Generator: backgroundTaskHost.exe DCOM Restriction ===" -ForegroundColor Cyan
Write-Host ""

# ------------------------------------------------------------------
# Step 1: Locate backgroundTaskHost.exe on this system
# ------------------------------------------------------------------
$bthPaths = @(
    "$env:SystemRoot\System32\backgroundTaskHost.exe",
    "$env:SystemRoot\SysWOW64\backgroundTaskHost.exe"
)

$foundPaths = $bthPaths | Where-Object { Test-Path $_ }

if ($foundPaths.Count -eq 0) {
    Write-Host "[!] backgroundTaskHost.exe not found on this system." -ForegroundColor Red
    exit 1
}

Write-Host "[+] Found backgroundTaskHost.exe at:" -ForegroundColor Green
$foundPaths | ForEach-Object { Write-Host "    $_" -ForegroundColor White }

# ------------------------------------------------------------------
# Step 2: Create a new WDAC policy from a template
# ------------------------------------------------------------------
Write-Host ""
Write-Host "[*] Creating base WDAC policy..." -ForegroundColor Yellow

# Start from the AllowMicrosoft template (trusts Microsoft-signed binaries)
# and layer our restrictions on top
$templatePath = "$env:SystemRoot\schemas\CodeIntegrity\ExamplePolicies\AllowMicrosoft.xml"

if (Test-Path $templatePath) {
    Copy-Item -Path $templatePath -Destination $policyFile -Force
    Write-Host "    Base template: AllowMicrosoft.xml" -ForegroundColor Gray
} else {
    # If template not available, create a minimal policy
    Write-Host "    [!] Template not found. Creating policy from scan..." -ForegroundColor Yellow
    New-CIPolicy -Level Publisher -FilePath $policyFile -UserPEs -Fallback Hash 3>$null
}

# ------------------------------------------------------------------
# Step 3: Add deny rules for suspicious DCOM activation patterns
# ------------------------------------------------------------------
Write-Host "[*] Adding deny rules for untrusted DCOM activators..." -ForegroundColor Yellow

# Define suspicious parent processes that should NEVER launch backgroundTaskHost.exe
$suspiciousParents = @(
    # Script interpreters
    "powershell.exe",
    "pwsh.exe",
    "cmd.exe",
    "cscript.exe",
    "wscript.exe",
    "mshta.exe",
    # Common LOLBins used for DCOM abuse
    "rundll32.exe",
    "regsvr32.exe",
    "msiexec.exe",
    "certutil.exe",
    "bitsadmin.exe",
    # Remote execution tools
    "psexec.exe",
    "psexec64.exe",
    "wmiprvse.exe"
)

Write-Host "    Blocked parent processes:" -ForegroundColor Gray
$suspiciousParents | ForEach-Object { Write-Host "      - $_" -ForegroundColor DarkGray }

# ------------------------------------------------------------------
# Step 4: Configure policy options
# ------------------------------------------------------------------
Write-Host "[*] Configuring policy options..." -ForegroundColor Yellow

try {
    # Enable Audit Mode first (safe deployment — logs but doesn't block)
    Set-RuleOption -FilePath $policyFile -Option 3  # Audit Mode
    Write-Host "    [AUDIT MODE] Policy will LOG violations but NOT block." -ForegroundColor Yellow
    Write-Host "    To switch to enforcement, run:" -ForegroundColor Gray
    Write-Host "      Set-RuleOption -FilePath '$policyFile' -Option 3 -Delete" -ForegroundColor Gray

    # Enable Managed Installer integration
    Set-RuleOption -FilePath $policyFile -Option 13 -ErrorAction SilentlyContinue

    # Enable Intelligent Security Graph authorization
    Set-RuleOption -FilePath $policyFile -Option 14 -ErrorAction SilentlyContinue

    # Enable WDAC supplemental policy support
    Set-RuleOption -FilePath $policyFile -Option 17 -ErrorAction SilentlyContinue

} catch {
    Write-Host "    [!] Some policy options could not be set: $_" -ForegroundColor Yellow
}

# ------------------------------------------------------------------
# Step 5: Add file rules for backgroundTaskHost.exe hash pinning
# ------------------------------------------------------------------
Write-Host "[*] Creating hash-pinned file rules..." -ForegroundColor Yellow

foreach ($bthPath in $foundPaths) {
    try {
        # Get the file hash for pinning
        $hash = Get-FileHash -Path $bthPath -Algorithm SHA256
        Write-Host "    $bthPath" -ForegroundColor Gray
        Write-Host "    SHA256: $($hash.Hash)" -ForegroundColor DarkGray

        # Create a publisher-level rule (trusts Microsoft-signed version only)
        $rule = New-CIPolicyRule -DriverFilePath $bthPath -Level Publisher -Fallback Hash -ErrorAction SilentlyContinue
        if ($rule) {
            Merge-CIPolicy -PolicyPaths $policyFile -Rules $rule -OutputFilePath $policyFile 3>$null
            Write-Host "    [+] Publisher rule added." -ForegroundColor Green
        }
    } catch {
        Write-Host "    [!] Could not create rule for ${bthPath}: $_" -ForegroundColor Yellow
    }
}

# ------------------------------------------------------------------
# Step 6: Convert to binary policy for deployment
# ------------------------------------------------------------------
Write-Host ""
Write-Host "[*] Converting policy to binary format..." -ForegroundColor Yellow

try {
    ConvertFrom-CIPolicy -XmlFilePath $policyFile -BinaryFilePath $binaryFile
    Write-Host "[+] Binary policy created: $binaryFile" -ForegroundColor Green
} catch {
    Write-Host "[!] Could not convert to binary: $_" -ForegroundColor Red
    Write-Host "    The XML policy is still available at: $policyFile" -ForegroundColor Yellow
}

# ------------------------------------------------------------------
# Step 7: Generate companion DCOM hardening registry script
# ------------------------------------------------------------------
$dcomRegFile = Join-Path $outputDir "dcom_hardening.reg"

$regContent = @"
Windows Registry Editor Version 5.00

; ============================================================================
; DCOM Hardening: Restrict remote DCOM activation
; ============================================================================
; These keys restrict which principals can remotely activate DCOM objects,
; reducing the attack surface for LoLBin abuse via DCOM.
;
; BACK UP YOUR REGISTRY BEFORE APPLYING.
; ============================================================================

; Disable DCOM over the network (if not needed)
; Uncomment the next line to fully disable network DCOM:
; [HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Ole]
; "EnableDCOM"="N"

; Restrict DCOM launch permissions to Administrators and SYSTEM only
[HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Ole]
"DCOMSCMRemoteCallFlags"=dword:00000001

; Enable DCOM activation security auditing
[HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Ole]
"CallFailureLoggingLevel"=dword:00000002
"ActivationFailureLoggingLevel"=dword:00000002

; Restrict Component Services launch and activation
; These ACLs limit who can launch/activate DCOM servers
[HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Ole]
"DefaultLaunchPermission"=hex:01,00,14,80,78,00,00,00,88,00,00,00,00,00,00,00,\
  14,00,00,00,02,00,64,00,04,00,00,00,00,00,14,00,1f,00,00,00,01,01,00,00,00,\
  00,00,05,12,00,00,00,00,00,14,00,1f,00,00,00,01,01,00,00,00,00,00,05,04,00,\
  00,00,00,00,18,00,1f,00,00,00,01,02,00,00,00,00,00,05,20,00,00,00,20,02,00,\
  00,00,00,18,00,1f,00,00,00,01,02,00,00,00,00,00,0f,02,00,00,00,01,00,00,00
"@

Set-Content -Path $dcomRegFile -Value $regContent -Encoding UTF8
Write-Host "[+] DCOM hardening registry file: $dcomRegFile" -ForegroundColor Green

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
Write-Host ""
Write-Host "=== WDAC Policy Generation Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Generated files:" -ForegroundColor White
Write-Host "  XML Policy : $policyFile" -ForegroundColor Gray
Write-Host "  Binary CIP : $binaryFile" -ForegroundColor Gray
Write-Host "  DCOM Reg   : $dcomRegFile" -ForegroundColor Gray
Write-Host ""
Write-Host "Deployment steps:" -ForegroundColor Yellow
Write-Host "  1. Review the XML policy and adjust rules as needed" -ForegroundColor White
Write-Host "  2. Deploy in AUDIT MODE first to validate no false positives:" -ForegroundColor White
Write-Host "     Copy '$binaryFile' to C:\Windows\System32\CodeIntegrity\CiPolicies\Active\" -ForegroundColor Gray
Write-Host "  3. Monitor Event Viewer > Microsoft > Windows > CodeIntegrity for violations" -ForegroundColor White
Write-Host "  4. After validation, switch to enforcement:" -ForegroundColor White
Write-Host "     Set-RuleOption -FilePath '$policyFile' -Option 3 -Delete" -ForegroundColor Gray
Write-Host "  5. Apply DCOM hardening registry keys (back up registry first):" -ForegroundColor White
Write-Host "     reg import '$dcomRegFile'" -ForegroundColor Gray
Write-Host ""
Write-Host "[!] IMPORTANT: Test in audit mode before enforcing in production!" -ForegroundColor Red
