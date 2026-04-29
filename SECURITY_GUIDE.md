# 🛡️ Security Defense Guide — Protecting Against Rogue Background Tasks

> **Who is this for?** Anyone managing a Windows PC who wants to protect against
> a specific type of cyberattack where hackers disguise malicious activity as a
> normal Windows background task.

---

## 📖 What Is This Threat?

Windows runs small programs called **background tasks** to handle things like
updating Live Tiles, syncing email, or refreshing notifications. Each one has a
unique **App ID** — think of it like a license plate for the program.

**The attack:** A hacker can trick Windows into running the background task
program (`backgroundTaskHost.exe`) with a **fake license plate** (a made-up
App ID). Because the program is a trusted part of Windows, antivirus software
may not flag it. The hacker then uses this trusted program to secretly
download malware or communicate with their server.

**Our defense tools detect and stop this by checking every "license plate"
against the official registry.** If one doesn't match, it's fake — and we
shut it down.

---

## 🗂️ What's In the Toolkit

| File | What It Does | Difficulty |
|------|-------------|------------|
| `Start_Monitor.bat` | **Svchost Network Monitor Suite** — An interactive toolkit containing Auto-Pilot and Sysmon modes to track sub-second rogue connections. ([See Guide](HOW_TO_MONITOR_SVCHOST.md)) | ⭐ Easy |
| `active_defender_bth.ps1` | **Instant scan** — checks your PC right now and kills any fake processes | ⭐ Easy |
| `hardening/sysmon_bth_config.xml` | **Monitoring** — watches for future attacks 24/7 | ⭐⭐ Medium |
| `hardening/edr_siem_rules_bth.ps1` | **Enterprise alerts** — detection rules for corporate security platforms | ⭐⭐⭐ Advanced |
| `hardening/wdac_policy_bth.ps1` | **Prevention** — blocks attacks before they happen | ⭐⭐⭐ Advanced |

> **Home users:** Focus on Steps 1 and 2 below. Steps 3 and 4 are for IT
> professionals managing company networks.

---

## ✅ Step 1 — Run the Instant Scan (5 minutes)

This checks your computer right now for any fake background tasks.

### What You Need
- Windows 10 or 11
- Administrator access to your PC

### Instructions

1. **Open PowerShell as Administrator**
   - Click the **Start** button
   - Type **PowerShell**
   - Right-click **Windows PowerShell** and select **Run as administrator**
   - Click **Yes** when Windows asks for permission

2. **Navigate to the toolkit folder**
   - Copy and paste this command, then press **Enter**:
   ```powershell
   cd "C:\Users\honey\googleclaw"
   ```

3. **Run the scan**
   - Copy and paste this command, then press **Enter**:
   ```powershell
   .\active_defender_bth.ps1
   ```

4. **Read the results**

   You will see one of two outcomes:

   - ✅ **Green message** — `"All backgroundTaskHost.exe processes are legitimate."` — Your PC is clean. No action needed.

   - 🔴 **Red message** — `"ROGUE PROCESSES WERE DETECTED"` — A suspicious process was found and terminated. Follow the recommended next steps shown on screen.

### Understanding the Log File

The scan creates a log at `C:\Users\honey\googleclaw\rogue_bth_terminations.log`.
Open it with Notepad to review. Here's what each label means:

| Label | Meaning |
|-------|---------|
| `INFO` | Normal status update |
| `SCAN` | A process being checked |
| `OK` | Process is legitimate — no action needed |
| `ALERT` | ⚠️ Suspicious process detected |
| `KILL` | Malicious process was terminated |
| `ERROR` | Something went wrong (check the message) |

### How Often Should I Run This?

- **After a security concern:** Run immediately
- **Weekly:** Good practice for personal computers
- **Want it automatic?** See the "Schedule Automatic Scans" section below

---

## ✅ Step 2 — Install 24/7 Monitoring with Sysmon (15 minutes)

**Sysmon** is a free Microsoft tool that quietly watches your PC for suspicious
activity. Our configuration file tells it exactly what to look for.

### What You Need
- Administrator access
- Internet connection (to download Sysmon once)

### Instructions

1. **Download Sysmon**
   - Open your web browser
   - Go to: `https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon`
   - Click the **Download Sysmon** link
   - Extract the downloaded `.zip` file to a folder you'll remember
     (for example, `C:\Tools\Sysmon`)

2. **Open PowerShell as Administrator** (same as Step 1)

3. **Install Sysmon with our security configuration**
   - Copy and paste this command (update the Sysmon path if you extracted
     it somewhere different):
   ```powershell
   C:\Tools\Sysmon\Sysmon64.exe -accepteula -i "C:\Users\honey\googleclaw\hardening\sysmon_bth_config.xml"
   ```
   - Press **Enter**
   - You should see: `Sysmon64 installed.`

4. **Verify it's running**
   ```powershell
   Get-Service Sysmon64
   ```
   - You should see `Status: Running`

### What Sysmon Watches For

| Event | What It Catches |
|-------|----------------|
| Process Creation | Any `backgroundTaskHost.exe` launch, with full details |
| Network Connections | The process connecting to the internet (shouldn't happen normally) |
| DLL Loading | Unsigned code being injected into the process |
| DNS Lookups | The process trying to contact a hacker's server by name |
| Process Tampering | Other programs trying to inject code into background tasks |

### Where to See Sysmon Alerts

1. Press **Win + R**, type `eventvwr.msc`, press **Enter**
2. In the left panel, navigate to:
   **Applications and Services Logs** → **Microsoft** → **Windows** → **Sysmon** → **Operational**
3. Look for entries mentioning `backgroundTaskHost.exe`

> **Tip:** If you see a network connection from `backgroundTaskHost.exe` to an
> IP address that isn't Microsoft's, that's suspicious. Take a screenshot and
> consult your IT department or a security professional.

### How to Update the Configuration Later

If you receive an updated `sysmon_bth_config.xml` file:
```powershell
C:\Tools\Sysmon\Sysmon64.exe -c "C:\Users\honey\googleclaw\hardening\sysmon_bth_config.xml"
```

### How to Uninstall Sysmon

If you ever need to remove it:
```powershell
C:\Tools\Sysmon\Sysmon64.exe -u
```

---

## ✅ Step 3 — Enterprise Alert Rules (IT Professionals)

> **This step is for IT professionals** who manage a corporate SIEM (Security
> Information and Event Management) system like Microsoft Sentinel, Splunk, or
> Elastic.

The file `hardening/edr_siem_rules_bth.ps1` contains **4 detection rules**
with copy-paste queries for major platforms:

### Rule Summary

| # | Rule | Severity | What It Detects |
|---|------|----------|-----------------|
| 1 | Unregistered ServerName | 🟠 High | Fake App IDs in command-line arguments |
| 2 | External Network Connection | 🔴 Critical | backgroundTaskHost.exe connecting to the internet |
| 3 | Suspicious Parent Process | 🟠 High | Process spawned by something other than `svchost.exe` |
| 4 | Unsigned DLL Loading | 🔴 Critical | Untrusted code injected into the process |

### How to Deploy

1. **Open** `hardening/edr_siem_rules_bth.ps1` in any text editor

2. **Find your platform** — each rule has sections for:
   - **Microsoft Sentinel** — Copy the KQL query
   - **Splunk** — Copy the SPL query
   - **Elastic/ELK** — Copy the JSON query
   - **Sigma** — Use the YAML for any platform via Sigma converters

3. **Create a new detection rule** in your platform and paste the query

4. **Set the alert action** to:
   - Send email to the security team
   - Create a ticket in your incident management system
   - Optionally: auto-isolate the affected endpoint

### Testing the Rules

After deployment, verify the rules are working:

1. Check that your SIEM is receiving Sysmon events (Event ID 1 and 3)
2. Review the rule output for the past 24 hours — you should see some
   legitimate `backgroundTaskHost.exe` events being correctly filtered out
3. If you see too many false positives, add your organization's custom UWP
   packages to the whitelist in each rule

---

## ✅ Step 4 — Block Attacks Before They Happen (IT Professionals)

> **⚠️ WARNING:** This step modifies Windows system policies. Incorrect
> configuration can prevent legitimate programs from running. **Always test
> in audit mode first.** Only proceed if you are comfortable with Windows
> Defender Application Control (WDAC).

### What This Does

The WDAC policy prevents untrusted programs (scripts, hacking tools) from
being able to launch `backgroundTaskHost.exe` in the first place. Think of it
as a bouncer at the door — only approved programs get in.

### Blocked Parent Programs

The policy blocks these programs from launching background tasks:

| Program | Why It's Blocked |
|---------|-----------------|
| `powershell.exe` / `pwsh.exe` | Script interpreters commonly abused by attackers |
| `cmd.exe` | Command prompt — same reason |
| `cscript.exe` / `wscript.exe` | Windows Script Host — used in malware droppers |
| `mshta.exe` | HTML Application host — common attack vector |
| `rundll32.exe` | DLL execution — frequently abused |
| `regsvr32.exe` | COM registration — known LOLBin |
| `certutil.exe` | Certificate tool — used to download payloads |
| `psexec.exe` | Remote execution tool |

### Instructions

1. **Open PowerShell as Administrator**

2. **Run the policy generator**
   ```powershell
   cd "C:\Users\honey\googleclaw\hardening"
   .\wdac_policy_bth.ps1
   ```

3. **The script generates three files in** `hardening/wdac_output/`:

   | File | Purpose |
   |------|---------|
   | `BTH_LoLBin_Restriction.xml` | Human-readable policy (review this) |
   | `BTH_LoLBin_Restriction.cip` | Binary policy for deployment |
   | `dcom_hardening.reg` | Registry tweaks to harden DCOM |

4. **Deploy in AUDIT MODE** (logs violations but doesn't block anything)
   ```powershell
   Copy-Item ".\wdac_output\BTH_LoLBin_Restriction.cip" `
     "C:\Windows\System32\CodeIntegrity\CiPolicies\Active\" -Force
   ```
   Then **restart your computer**.

5. **Monitor for 1–2 weeks**
   - Open Event Viewer
   - Go to: **Applications and Services Logs** → **Microsoft** → **Windows** → **CodeIntegrity** → **Operational**
   - Look for audit events — these show what *would have been blocked*
   - If you see legitimate programs being flagged, add them to the whitelist
     in the XML policy before switching to enforcement

6. **Switch to enforcement** (only after successful audit period)
   ```powershell
   Set-RuleOption -FilePath ".\wdac_output\BTH_LoLBin_Restriction.xml" -Option 3 -Delete
   ConvertFrom-CIPolicy -XmlFilePath ".\wdac_output\BTH_LoLBin_Restriction.xml" `
     -BinaryFilePath ".\wdac_output\BTH_LoLBin_Restriction.cip"
   Copy-Item ".\wdac_output\BTH_LoLBin_Restriction.cip" `
     "C:\Windows\System32\CodeIntegrity\CiPolicies\Active\" -Force
   ```
   Restart your computer.

7. **Apply DCOM hardening** (optional, adds extra protection)
   - **Back up your registry first:**
     ```powershell
     reg export "HKLM\SOFTWARE\Microsoft\Ole" "C:\Users\honey\googleclaw\hardening\ole_backup.reg"
     ```
   - Apply the hardening:
     ```powershell
     reg import ".\wdac_output\dcom_hardening.reg"
     ```

---

## ⏰ Schedule Automatic Scans (Optional)

You can set Windows to automatically run the defense scan on a schedule.

### Using Task Scheduler (Graphical)

1. Press **Win + R**, type `taskschd.msc`, press **Enter**
2. Click **Create Basic Task** in the right panel
3. **Name:** `Active Defense - BTH Scan`
4. **Trigger:** Choose **Daily** or **Weekly** (recommended: daily)
5. **Action:** Choose **Start a program**
6. **Program:** `powershell.exe`
7. **Arguments:** `-ExecutionPolicy Bypass -File "C:\Users\honey\googleclaw\active_defender_bth.ps1"`
8. Check **Open the Properties dialog** and click **Finish**
9. In Properties, check **Run with highest privileges**
10. Click **OK**

### Using PowerShell (Quick)

```powershell
$action  = New-ScheduledTaskAction -Execute "powershell.exe" `
  -Argument '-ExecutionPolicy Bypass -File "C:\Users\honey\googleclaw\active_defender_bth.ps1"'

$trigger = New-ScheduledTaskTrigger -Daily -At "3:00AM"

$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
  -DontStopOnIdleEnd -AllowStartIfOnBatteries

Register-ScheduledTask -TaskName "ActiveDefense_BTH_Scan" `
  -Action $action -Trigger $trigger -Settings $settings `
  -RunLevel Highest -User "SYSTEM" `
  -Description "Daily scan for rogue backgroundTaskHost.exe processes"
```

---

## 🔍 Troubleshooting

### "Running scripts is disabled on this system"

Run this command first, then try again:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "Access is denied"

You need to run PowerShell **as Administrator**. Right-click PowerShell
and select **Run as administrator**.

### "Sysmon64 is not recognized"

You need to provide the full path to `Sysmon64.exe`. For example:
```powershell
C:\Tools\Sysmon\Sysmon64.exe -i "C:\Users\honey\googleclaw\hardening\sysmon_bth_config.xml"
```

### "Get-AppxPackage is not recognized"

This can happen on older Windows versions or Server Core installations.
The scan will still work but may not be able to validate all App IDs.
Consider updating to Windows 10 version 1903 or later.

### The scan found a rogue process — what do I do?

1. **Don't panic** — the script already terminated the malicious process
2. **Run a full antivirus scan** — Open Windows Security → Virus & threat
   protection → Scan options → Full scan
3. **Check the log file** — Open `rogue_bth_terminations.log` and note the
   IP addresses in the `Network` lines
4. **Change your passwords** — Especially if the rogue process was running
   for a long time
5. **Contact your IT department** if you're on a corporate network

---

## 📚 Glossary

| Term | Simple Definition |
|------|-------------------|
| **backgroundTaskHost.exe** | A Windows program that runs small tasks in the background (email sync, notifications, etc.) |
| **LOLBin** | "Living off the Land Binary" — a legitimate Windows program that hackers abuse for malicious purposes |
| **DCOM** | A Windows technology that lets programs talk to each other — hackers exploit it to launch trusted programs with fake arguments |
| **App ID / ServerName** | A unique identifier for a background task — like a license plate for a program |
| **UWP** | "Universal Windows Platform" — the framework for modern Windows apps (from the Microsoft Store) |
| **Sysmon** | A free Microsoft monitoring tool that records detailed system activity |
| **SIEM** | "Security Information and Event Management" — enterprise software that collects and analyzes security alerts |
| **WDAC** | "Windows Defender Application Control" — a Windows feature that controls which programs are allowed to run |
| **Masquerading** | A hacker technique where malicious activity is disguised as something legitimate |
| **C2 / Command & Control** | The server a hacker uses to send commands to malware on your computer |
| **Payload** | The malicious software a hacker wants to install on your computer |

---

## 📁 File Reference

```
googleclaw/
├── active_defender_bth.ps1           ← Run this for an instant scan
├── rogue_bth_terminations.log        ← Scan results (created after first run)
├── SECURITY_GUIDE.md                 ← This file
└── hardening/
    ├── sysmon_bth_config.xml         ← Sysmon monitoring configuration
    ├── edr_siem_rules_bth.ps1        ← Enterprise detection rules
    └── wdac_policy_bth.ps1           ← Application control policy generator
        └── wdac_output/              ← (created when you run the WDAC script)
            ├── BTH_LoLBin_Restriction.xml
            ├── BTH_LoLBin_Restriction.cip
            └── dcom_hardening.reg
```

---

> **Last updated:** April 2026
> **Questions?** Open an issue on the repository or contact your IT security team.
