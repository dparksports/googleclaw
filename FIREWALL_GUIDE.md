# 🧱 Windows Firewall Guide — Blocking Rogue Background Traffic

> **Who is this for?** Anyone managing a Windows PC who wants to block a specific hacking technique where malware uses normal Windows background tasks to communicate with the internet.

---

## 📖 What Are We Doing?

In our previous steps, we discovered that hackers can disguise their malware as a normal Windows "background task" (a program called `backgroundTaskHost.exe`). Once disguised, the malware tries to secretly connect to the internet to download more viruses or steal data.

To stop this, we are putting a **"Bouncer"** (a Firewall Rule) on your internet connection. 

This bouncer's job is very specific:
*   "If the background task program tries to talk to internal networks (like other computers in your house) — **BLOCK IT.**"
*   "If the background task program tries to talk to known risky internet hubs (like the ones hackers use) — **BLOCK IT.**"

### ⚠️ A Quick Warning About Blocking Everything
You might wonder: *"Why not just block it from talking to the internet entirely?"*

If we block it completely, **legitimate apps** from the Microsoft Store (like Spotify downloading music in the background, or Netflix updating shows) will stop working. Our script uses a "smart block" approach that stops the hackers without breaking your favorite apps.

---

## ✅ Step 1 — Apply the Firewall Rule (3 Minutes)

This step tells Windows Firewall to create our specific "Bouncer".

### What You Need
- Administrator access to your PC

### Instructions

1. **Open PowerShell as Administrator**
   - Click the **Start** button at the bottom of your screen.
   - Type **PowerShell**.
   - Right-click **Windows PowerShell** and select **Run as administrator**.
   - Click **Yes** when Windows asks for permission.

2. **Navigate to the toolkit folder**
   - Copy and paste this exact command, then press **Enter**:
   ```powershell
   cd "C:\Users\honey\googleclaw\hardening"
   ```

3. **Run the script**
   - Copy and paste this command, then press **Enter**:
   ```powershell
   .\firewall_bth_restrict.ps1
   ```

4. **Read the results**
   - You should see a green message that says: `[+] Firewall rule 'Block_BTH_NonMicrosoft_Outbound' created successfully!`

You are done! The protection is now active.

---

## 🔍 Step 2 — Verify It Worked (Optional)

If you want to see the rule with your own eyes in the Windows Firewall settings:

1. Press the **Start** button, type **Windows Defender Firewall**, and press **Enter**.
2. On the left side of the window, click **Advanced settings**.
3. In the new window that opens, click **Outbound Rules** on the top left.
4. Look down the list in the middle for a rule named **Block_BTH_NonMicrosoft_Outbound**.
5. It will have a red "NO" symbol (🚫) next to it, which means it is actively blocking that specific traffic.

---

## 🗑️ How to Remove the Protection (If Needed)

If you ever notice that a specific Windows Store app is having trouble syncing in the background, and you suspect this firewall rule is the cause, you can easily remove it.

**To remove it:**
1. Open PowerShell as Administrator (same as Step 1).
2. Copy, paste, and run this command:
   ```powershell
   Remove-NetFirewallRule -DisplayName "Block_BTH_NonMicrosoft_Outbound"
   ```
3. The rule is instantly deleted, and things return to normal.

---

## 💡 Troubleshooting

### "Running scripts is disabled on this system"
If you get a red error saying scripts are disabled when trying to run step 1, run this command first:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Then try running the `.\firewall_bth_restrict.ps1` script again.

### "Access is denied"
You forgot to run PowerShell as an Administrator. Close the blue window, click Start, search for PowerShell, and explicitly choose **Run as administrator**.
