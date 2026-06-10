# OliSched — Personal Scheduler

A professional desktop scheduler app built with Python + PyQt6.
Dark theme, animated grass effect, full persistent memory.

---

## Features

- ✅ Three task boards: Planned → In Progress → Completed
- 🔔 Reminders (at time, 5/15/30 min, 1hr, 1 day before)
- 📓 Daily journal / end-of-day notes with auto-save by date
- 🗑 Delete tasks yourself — nothing is auto-deleted
- 💾 All data saved to `~/.olisched_data.json` on your machine
- 🌿 Animated grass effect at the bottom (macOS-inspired)
- 🕐 Live clock in the header

---

## Quick Start (Development)

### 1. Install Python 3.10+
Download from https://www.python.org/downloads/windows/
✔ Check "Add Python to PATH" during install.

### 2. Install dependencies
Open a terminal (Command Prompt or PowerShell) inside this folder:
```
pip install -r requirements.txt
```

### 3. Run
```
python main.py
```

---

## Export as a Windows .exe (Standalone App)

So anyone can double-click and run — no Python needed on their machine.

### Step 1 — Install PyInstaller
```
pip install pyinstaller
```

### Step 2 — Build the .exe
Run this from inside the OliSched folder(where your files are stored):
```
pyinstaller --onefile --windowed --name OliSched main.py
```

- `--onefile`   → single .exe file
- `--windowed`  → no console window behind the app

### Step 3 — Find your app
After building, look in:
```
dist/OliSched.exe
```

That's your portable app. Copy it anywhere — it runs on Windows without Python installed.

---

## Tips

| Action | How |
|---|---|
| Add a task | Click **＋ New Task** top-right |
| Move to In Progress | Click **▶ Working** on the task card |
| Mark complete | Click **✓ Done** — title gets crossed out |
| Revert | Click **↩ Revert** |
| Delete | Click **🗑** (confirms before deleting) |
| Daily notes | Write in the journal box at the bottom, click **Save Note** |
| Data location | `C:\Users\YourName\.olisched_data.json` |

---

## VS Code Workflow

1. Open VS Code
2. **File → Open Folder** → select the `OliSched` folder
3. Open terminal: **Ctrl + `**
4. `pip install -r requirements.txt`
5. `python main.py` to run
6. `pyinstaller --onefile --windowed --name OliSched main.py` to export

---

Made for OliSched — your personal daily command center to track your progress.
