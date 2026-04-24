# 🛑 Web Components Lockdown Guide

> **Who is this for?** Anyone managing a Windows PC who wants to enforce a strict security lockdown on built-in Windows web components (like the Search bar and the Widgets board) to prevent them from downloading content from external Content Delivery Networks (CDNs).

---

## 📖 What Are We Doing?

Windows uses a hidden web browser engine called **`msedgewebview2.exe`** to display web content inside normal apps. For example, when you use the Windows 11 **Widgets** board or type in the **Start Menu Search**, Windows uses this engine to fetch images, news, and Javascript from large internet hubs known as CDNs (Content Delivery Networks) like Akamai and Amazon.

While this is normal behavior, strict security environments may want to completely block these background processes from talking to CDNs to ensure zero external data is fetched by the Windows interface.

We have created a script that places a **"Firewall Block Rule"** specifically on these two programs:
1. `msedgewebview2.exe` (The web engine)
2. `Widgets.exe` (The Windows 11 Widgets board)

### ⚠️ IMPORTANT WARNING 
**If you apply this block, your Windows Search and Widgets board will look broken.** Because they can no longer download images or styling from the internet, you will likely see blank boxes, missing icons, or text-only results when you use them. This is the expected trade-off for this level of strict security.

---

## ✅ Step 1 — Apply the Lockdown (3 Minutes)

This step tells Windows Firewall to instantly cut off access to Amazon and Akamai CDNs for these specific programs.

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
   .\firewall_webview2_restrict.ps1
   ```

4. **Read the results**
   - You should see green messages saying: 
     `[+] Firewall rule 'Block_CDN_Outbound_msedgewebview2.exe' created successfully!`
     `[+] Firewall rule 'Block_CDN_Outbound_Widgets.exe' created successfully!`

The lockdown is now active!

---

## 🔍 Step 2 — Verify It Worked (Optional)

If you want to visually confirm the rules are active:

1. Press the **Start** button, type **Windows Defender Firewall**, and press **Enter**.
2. On the left side of the window, click **Advanced settings**.
3. In the new window that opens, click **Outbound Rules** on the top left.
4. Look down the list in the middle for rules starting with:
   - **Block_CDN_Outbound_msedgewebview2.exe_...**
   - **Block_CDN_Outbound_Widgets.exe_...**
5. They will have a red "NO" symbol (🚫) next to them, which means they are actively blocking traffic.

---

## 🗑️ How to Remove the Protection (Restore Functionality)

If you decide that having a broken-looking Search Menu or Widgets board is too annoying, you can instantly restore them to normal by removing the firewall rules.

**To remove them:**
1. Open PowerShell as Administrator (same as Step 1).
2. Copy, paste, and run this command:
   ```powershell
   Get-NetFirewallRule -DisplayName "Block_CDN_Outbound_*" | Remove-NetFirewallRule
   ```
3. The rules are deleted, and your Windows interface will immediately be able to download images and news again.

---

## 💡 Troubleshooting

### "Running scripts is disabled on this system"
If you get a red error saying scripts are disabled when trying to run step 1, run this command first:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Then try running the `.\firewall_webview2_restrict.ps1` script again.

### "Access is denied"
You forgot to run PowerShell as an Administrator. Close the blue window, click Start, search for PowerShell, and explicitly choose **Run as administrator**.
