# SmokeScreen v1.0.2

**SmokeScreen** is a lightweight, dark-themed utility console designed to protect your privacy instantly. It acts as a configurable "Panic Button" that allows you to completely conceal a target application (e.g., a game or private window) and instantly bring up or launch a cover application (e.g., a document or browser) with a single keystroke.

---

>[!IMPORTANT]
>Windows defender might flag this as a virus, because it uses cartain python packages that are commonly found in keyloggers. This piece of software is not harmfull and i do not claim responsibility if you downloaded this from anywhere else than from this github page!

## 🚀 Features

* **Instant Concealment:** Completely hides the target application window, removing it from both the desktop and the Windows taskbar.
* **Smart Cover Swapping:** Automatically launches or switches focus to a predefined cover application (such as work or study materials) when the panic trigger is pulled.
* **Secret Recovery:** Safely restores the hidden application precisely to its original state using a hidden, customizable global hotkey sequence.
* **System Tray Stealth Mode:** Minimizes itself completely into the system tray, running invisibly in the background so the utility tool itself remains unnoticeable.
* **Dynamic Process Detection:** Scans actively running system processes to quickly let you map applications via dropdown selectors without needing to manually find file paths.

> [!TIP]
> Place the exe in a directory, because it creates a file to save the settings!

---

## 🛠️ Controls & Hotkeys

| Action | Key / Combination | Description |
| :--- | :--- | :--- |
| **Panic Trigger** | `Pause` | Instantly hides your target application and switches to/opens the cover app. |
| **Secret Recovery** | `Ctrl + Shift + U` | Restores the hidden target application back to the foreground and taskbar. |
| **Minimize to Tray** | *UI Button* | Hides the SmokeScreen console interface safely into the Windows System Tray. |

---

## 📋 Prerequisites

SmokeScreen is built for **Windows OS** and relies on native Win32 APIs for window manipulation. 

### Python Dependencies
If running from source, ensure you have Python 3.8+ installed along with the following packages:
```bash
pip install customtkinter keyboard pillow pystray psutil pywin32
