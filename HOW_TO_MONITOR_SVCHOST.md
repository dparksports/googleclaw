# 🛡️ How to Use the Svchost Network Monitor

This guide will show you how to run the `monitor_svchost_live.py` script. 

**What does this script do?**  
In Windows, `svchost.exe` is a core system process that handles many different background services. Because it does so much, malware sometimes tries to hide inside it. This script acts like a security guard. It watches `svchost.exe` in real-time and alerts you if it tries to talk to any computer on the internet that does **not** belong to Microsoft, Windows, or Google.

---

## Step-by-Step Instructions

We have created a shortcut script to make this as easy as possible. You do not need to open any command lines manually.

### Step 1: Start the Monitor
1. Open the `googleclaw` folder where these files are saved.
2. Find the file named **`Start_Monitor.bat`** (it might just show as `Start_Monitor` with a gear/window icon).
3. **Double-click** it.

### Step 2: Allow Administrator Access
For the script to see all the hidden network traffic, it needs special permissions. 
* When you double-click the file, your screen might dim and a Windows prompt (User Account Control) will appear asking: **"Do you want to allow this app to make changes to your device?"**
* Click **Yes**.

A black terminal window will open and the monitor will begin running automatically.

---

## What to Expect Next

Once the script starts, it will say:  
`[YYYY-MM-DD HH:MM:SS] Starting Svchost Monitor (Non-Microsoft/Google)`

* **If everything is normal:** The screen will stay quiet. This means `svchost.exe` is only talking to normal, safe Microsoft and Google servers.
* **If it detects something suspicious:** You will see a large **[ALERT]** pop up on the screen, showing you exactly when it happened and where the traffic was going.

### The Log File (CSV)
Every time the script finds a suspicious connection, it writes the details into a spreadsheet file named **`svchost_non_ms_traffic.csv`** located in your `googleclaw` folder. 
You can open this file by double-clicking it (it will usually open in Excel or Notepad) to review the history of alerts, including an estimate of how much data was sent and received.

---

## How to Stop the Monitor

When you are done monitoring and want to close the script:
1. Click inside the black monitor window.
2. Hold down the **`Ctrl`** key on your keyboard and press the **`C`** key at the same time (`Ctrl + C`).
3. The script will say "Monitoring stopped." You can then press any key to close the window, or just click the **X** in the top right corner.