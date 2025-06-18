# Drive Sync - Automatic File Sync with Google Drive

If you love coding locally but always mean to back things up (and never do), this tool’s for you. It automatically syncs your Python scripts to Google Drive and keeps detailed changelogs—so your work stays safe, your history’s tracked, and you can focus on building, not backing up. 

## Prerequisites

### 1. Python Setup
- Python 3.7 or higher installed
- pip (Python package installer)

### 2. Required Packages
Install required packages using:
```bash
pip install -r requirements.txt
```

### 3. Google Cloud Setup
1. Visit [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (or select existing)
3. Enable Google Drive API:
   - Go to "APIs & Services" → "Library"
   - Search for "Google Drive API"
   - Click "Enable"
4. Set up OAuth consent screen:
   - Go to "APIs & Services" → "OAuth consent screen"
   - Choose "External"
   - Fill in app name (e.g., "DriveSync")
   - Add your email as developer contact
   - Save and continue
5. Create OAuth credentials:
   - Go to "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Choose "Desktop application"
   - Download JSON file
   - Rename to `client_secrets.json` and place in project directory

## Quick Start

1. Clone or download the code and place all the files in your project directory
2. Install requirements:
```bash
pip install -r requirements.txt
```
3. Place `client_secrets.json` in project directory as well
4. Run the sync:
```bash
python sync.py --folder-name "MyBackups"
```

## Features

### 🔄 Automatic Syncing
- Monitors Python files (or specified file types)
- Syncs changes every 2 minutes (configurable)
- Only uploads when files actually change

### 📝 Change Tracking
- Maintains detailed changelogs
- Records what changed and when
- Stores diffs for each change

### ⚙️ Customization
```bash
# Custom folder name and sync interval
python sync.py --folder-name "ProjectBackup" --interval 60

# Sync multiple file types
python sync.py --file-types ".py,.txt,.md"

# Enable debug logging
python sync.py --debug
```

### 📖 View Changes
```bash
# View changelog for specific file
python run_sync.py --view-changes script.py
```

## How It Works

1. **Authentication**
   - First run opens browser for Google login
   - Stores token for future use
   - No need to re-authenticate unless token expires

2. **File Monitoring**
   - Scans directory for specified file types
   - Calculates MD5 hash of each file
   - Detects changes by comparing hashes

3. **Change Management**
   - Creates changelog entry for each change
   - Stores unified diffs showing exactly what changed
   - Organizes changes by file and timestamp

4. **Drive Sync**
   - Creates dedicated folder in your Drive
   - Uploads changed files automatically
   - Maintains file hierarchy

## Directory Structure
```
project/
├── changelogs/           # Change history
│   ├── script1.py_logs/
│   │   ├── index.json
│   │   └── changes_*.diff
│   └── script2.py_logs/
├── client_secrets.json   # Google OAuth credentials
├── token.pickle         # Stored auth token
├── drive_sync.py        # Main sync code
└── run_sync.py          # Command line interface
```

## Pro Tips! 🚀

1. **First Time Setup**
   - Run with `--debug` flag to see detailed logs
   - Check Google Drive to verify folder creation
   - Try modifying a file to test sync

2. **Efficient Usage**
   - Let it run in a terminal while you work
   - Check changelogs to track your changes
   - Use custom intervals based on your needs

3. **Troubleshooting**
   - Delete `token.pickle` if auth issues occur
   - Enable debug logging for detailed info
   - Check changelog directory for sync history

## Set It, Forget It, Thank Yourself Later! 

- Backups? Done. Even if you forgot, this tool didn’t. 🎈
- The changelog knows more about your code history than your memory ever will! 🧠
- Runs quietly in the background, like a cron job with commitment issues (but it always shows up) 😴

Remember: With great automation comes great responsibility... and fewer excuses for not backing up your code! 😉

## Need Help?

Check the logs, they're your friends! If you see something like "File synced successfully", celebrate! If not, the debug logs will tell you why - they're chatty like that! 🗣️

Happy coding and syncing! 🚀
