# 🔒 LockBox2

![Alpha](https://img.shields.io/badge/Alpha-Project-4D6BFE?style=for-the-badge&logo=github&logoColor=white)
![Arch Linux](https://img.shields.io/badge/Arch_Linux-Derivatives_✓_Tested-1793D1?style=for-the-badge&logo=archlinux&logoColor=white)

**Open‑source secure password manager**  
A local desktop application built with Python + PyQt6 and AES‑256 encryption.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🔐 **Encryption** | Master password + PBKDF2 + Fernet (AES‑256) |
| 📋 **Entry management** | Title, username, password, URL, notes, creation/modification dates |
| 🎲 **Password generator** | Configurable length, character sets, exclude similar characters |
| 🔍 **Search** | Instant filter by title, username, URL |
| 📤 **Export / Import** | JSON, CSV, XML (with or without encryption) |
| 🔢 **TOTP (2FA)** | ⚠️ Under development – unstable, use with caution |
| ⏰ **Auto‑lock** | Inactivity timer (configurable) |
| 🔄 **Master password change** | Automatic re‑encryption of all data |
| 🖥️ **System tray** | Minimise to background |
| 💾 **Backup** | Automatic on every change (last 10 copies, can be disabled) |

---

## 🚀 Quick Start

1. **Check Python version** (3.10+ required):
```
   python3 --version
```

2. **Clone the repository**:

```
git clone https://github.com/Shavermushka/LockBox2.git
cd LockBox2
```
3. **Create a virtual environment**:

```
python3 -m venv venv
```
4. **Activate it**:

- Linux / macOS: `source venv/bin/activate`
- Windows (cmd): `venv\Scripts\activate.bat`
- Windows (PowerShell): `venv\Scripts\Activate.ps1`
5. **Install dependencies**:

```
pip install -r requirements.txt
```
6. **Run the application**:

```
python main.py
```

> **On first launch** you will be prompted to create a master password – **remember it!** Recovery is impossible.

---

## 📁 Project Structure

```
LockBox2/
├── main.py                 # entry point
├── requirements.txt        # dependencies
├── README.md               # this file (Russian)
├── README.en.md            # English version
├── .gitignore
└── src/
    ├── app.py              # initialisation and event loop
    ├── crypto.py           # encryption / decryption
    ├── database.py         # SQLite (CRUD, encryption)
    ├── models.py           # dataclass for entries
    ├── password_generator.py
    ├── totp.py             # TOTP (in development)
    ├── main_window.py      # main window
    ├── password_dialog.py  # add/edit dialog
    ├── login_dialog.py     # master password input
    ├── settings_dialog.py  # settings
    ├── export_import.py    # import/export
    ├── tray_icon.py        # system tray
    └── resources/
        ├── styles/         # themes (dark.qss, light.qss)
        └── icons/          # (optional)
```

---

## 🖥️ Interface & Controls

- **➕ Add** – new entry (or `Ctrl+N`).
- **✏️ Edit** – double‑click a row.
- **🗑️ Delete** – select an entry and click the button (or `Delete`).
- **🔍 Search** – the search bar filters by title, username, URL.
- **📋 Copy** – right‑click on an entry to copy username, password, or TOTP code (if working).
- **🎲 Password generator** – available in the edit dialog.

---

## ⚙️ Settings

- **Auto‑lock**: inactivity timeout in seconds (0 to disable).
- **Backups**: stored in `~/.lockbox_pro/backups/` (can be disabled).

---

## ❓ FAQ

**What if I forget the master password?**
Nothing. Data cannot be recovered – this is intentional for your security.

**Can I import from KeePass?**
Yes, via exporting from KeePass to CSV/JSON and importing into LockBox2.

**Is it safe to store TOTP secrets alongside passwords?**
Theoretically yes, but **TOTP is currently under development and may not work correctly**. It is recommended to use a separate authenticator app for now.

---

## 📄 License

**GNU General Public License v3.0** – the program remains free and open‑source. See the `LICENSE` file for details.

---

## 💬 Feedback

If you find a bug or have an idea for improvement, please create an issue or contact me directly.
Enjoy using LockBox2! 🚀

