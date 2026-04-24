# ============================================================================
# EDR / SIEM Detection Rules: backgroundTaskHost.exe LoLBin Masquerading
# ============================================================================
# These rules are written in a vendor-agnostic pseudocode format with
# ready-to-use translations for:
#   - Microsoft Sentinel (KQL)
#   - Splunk (SPL)
#   - Elastic / ELK (KQL / Lucene)
#   - Sigma (portable SIEM format)
#
# Deploy the Sigma rules directly, or copy the vendor-specific queries
# into your detection platform.
# ============================================================================

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RULE 1: Unregistered ServerName in backgroundTaskHost.exe
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# MITRE ATT&CK:  T1036.004 - Masquerading: Masquerade Task or Service
#                T1218     - System Binary Proxy Execution
#
# Severity: HIGH
# Description: Detects backgroundTaskHost.exe launched with a -ServerName
#              argument that does not match any known/registered UWP package.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# --- Sigma Rule (portable) ---------------------------------------------------
# Save as: sigma_bth_unregistered_servername.yml

# title: Unregistered ServerName in backgroundTaskHost.exe
# id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
# status: experimental
# description: >
#   Detects backgroundTaskHost.exe processes with -ServerName arguments
#   that do not correspond to any registered UWP AppX package, indicating
#   potential LoLBin masquerading for defense evasion.
# author: Active Defense Team
# date: 2026/04/24
# references:
#   - https://attack.mitre.org/techniques/T1036/004/
#   - https://attack.mitre.org/techniques/T1218/
# tags:
#   - attack.defense_evasion
#   - attack.t1036.004
#   - attack.t1218
# logsource:
#   category: process_creation
#   product: windows
# detection:
#   selection:
#     Image|endswith: '\backgroundTaskHost.exe'
#     CommandLine|contains: '-ServerName'
#   filter_known_packages:
#     CommandLine|contains:
#       - 'Microsoft.'
#       - 'Windows.'
#       - 'MicrosoftWindows.'
#   condition: selection and not filter_known_packages
# falsepositives:
#   - Legitimate third-party UWP apps with non-standard naming
#   - Custom enterprise UWP deployments
# level: high


# --- Microsoft Sentinel (KQL) ------------------------------------------------

# // Rule 1: Unregistered ServerName detection
# DeviceProcessEvents
# | where Timestamp > ago(24h)
# | where FileName =~ "backgroundTaskHost.exe"
# | where ProcessCommandLine has "-ServerName"
# // Exclude known Microsoft packages — expand this list with your
# // registered third-party packages
# | where ProcessCommandLine !contains "Microsoft."
#     and ProcessCommandLine !contains "Windows."
#     and ProcessCommandLine !contains "MicrosoftWindows."
# | extend ServerName = extract(@"-ServerName[:=\s]+""?([^\s""]+)", 1, ProcessCommandLine)
# | project Timestamp, DeviceName, AccountName, ProcessId,
#           ProcessCommandLine, ServerName,
#           InitiatingProcessFileName, InitiatingProcessCommandLine,
#           InitiatingProcessParentFileName
# | sort by Timestamp desc


# --- Splunk (SPL) ------------------------------------------------------------

# index=sysmon sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational"
#   EventCode=1
#   Image="*\\backgroundTaskHost.exe"
#   CommandLine="*-ServerName*"
#   NOT (CommandLine="*Microsoft.*" OR CommandLine="*Windows.*" OR CommandLine="*MicrosoftWindows.*")
# | rex field=CommandLine "-ServerName[:=\s]+\"?(?<ServerName>[^\s\"]+)"
# | table _time, host, user, ProcessId, CommandLine, ServerName,
#          ParentImage, ParentCommandLine
# | sort -_time


# --- Elastic / ELK -----------------------------------------------------------

# GET _search
# {
#   "query": {
#     "bool": {
#       "must": [
#         { "wildcard": { "process.executable": "*\\\\backgroundTaskHost.exe" }},
#         { "match_phrase": { "process.command_line": "-ServerName" }}
#       ],
#       "must_not": [
#         { "wildcard": { "process.command_line": "*Microsoft.*" }},
#         { "wildcard": { "process.command_line": "*Windows.*" }},
#         { "wildcard": { "process.command_line": "*MicrosoftWindows.*" }}
#       ]
#     }
#   }
# }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RULE 2: backgroundTaskHost.exe External Network Connection
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# MITRE ATT&CK:  T1071.001 - Application Layer Protocol: Web Protocols
#                T1105     - Ingress Tool Transfer
#
# Severity: CRITICAL
# Description: backgroundTaskHost.exe connecting to external (non-RFC1918)
#              IPs is highly anomalous. Legitimate UWP background tasks
#              rarely initiate outbound connections to arbitrary endpoints.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# --- Microsoft Sentinel (KQL) ------------------------------------------------

# DeviceNetworkEvents
# | where Timestamp > ago(24h)
# | where InitiatingProcessFileName =~ "backgroundTaskHost.exe"
# | where RemoteIPType == "Public"
# // Exclude known Microsoft telemetry endpoints
# | where RemoteUrl !endswith ".microsoft.com"
#     and RemoteUrl !endswith ".windows.com"
#     and RemoteUrl !endswith ".windowsupdate.com"
#     and RemoteUrl !endswith ".msftconnecttest.com"
# | project Timestamp, DeviceName, RemoteIP, RemotePort, RemoteUrl,
#           InitiatingProcessCommandLine, InitiatingProcessAccountName
# | sort by Timestamp desc


# --- Splunk (SPL) ------------------------------------------------------------

# index=sysmon sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational"
#   EventCode=3
#   Image="*\\backgroundTaskHost.exe"
#   NOT (DestinationIp="10.*" OR DestinationIp="192.168.*" OR DestinationIp="172.16.*"
#        OR DestinationIp="127.0.0.1" OR DestinationIp="::1")
#   NOT (DestinationHostname="*.microsoft.com" OR DestinationHostname="*.windows.com")
# | table _time, host, Image, DestinationIp, DestinationPort,
#          DestinationHostname, User, CommandLine
# | sort -_time


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RULE 3: Suspicious Parent Process for backgroundTaskHost.exe
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# MITRE ATT&CK:  T1059     - Command and Scripting Interpreter
#                T1036.004 - Masquerading: Masquerade Task or Service
#
# Severity: HIGH
# Description: backgroundTaskHost.exe should only be spawned by svchost.exe
#              (via DCOM/WinRT activation). Any other parent is suspicious.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# --- Microsoft Sentinel (KQL) ------------------------------------------------

# DeviceProcessEvents
# | where Timestamp > ago(24h)
# | where FileName =~ "backgroundTaskHost.exe"
# | where InitiatingProcessFileName !~ "svchost.exe"
# | project Timestamp, DeviceName, AccountName,
#           FileName, ProcessCommandLine,
#           InitiatingProcessFileName, InitiatingProcessCommandLine,
#           InitiatingProcessParentFileName
# | sort by Timestamp desc


# --- Splunk (SPL) ------------------------------------------------------------

# index=sysmon sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational"
#   EventCode=1
#   Image="*\\backgroundTaskHost.exe"
#   NOT ParentImage="*\\svchost.exe"
# | table _time, host, user, Image, CommandLine, ParentImage, ParentCommandLine
# | sort -_time


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RULE 4: Unsigned DLL Loaded into backgroundTaskHost.exe
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# MITRE ATT&CK:  T1574.002 - Hijack Execution Flow: DLL Side-Loading
#
# Severity: CRITICAL
# Description: Detects unsigned or non-Microsoft-signed DLLs loaded into
#              backgroundTaskHost.exe, indicating DLL side-loading or injection.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# --- Microsoft Sentinel (KQL) ------------------------------------------------

# DeviceImageLoadEvents
# | where Timestamp > ago(24h)
# | where InitiatingProcessFileName =~ "backgroundTaskHost.exe"
# | where not(SignerType == "Microsoft" or IsTrusted == true)
# | project Timestamp, DeviceName, FileName, FolderPath, SHA256,
#           SignerType, IsTrusted,
#           InitiatingProcessCommandLine
# | sort by Timestamp desc


# --- Splunk (SPL) ------------------------------------------------------------

# index=sysmon sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational"
#   EventCode=7
#   Image="*\\backgroundTaskHost.exe"
#   Signed="false"
# | table _time, host, Image, ImageLoaded, Hashes, Signed, Signature
# | sort -_time
