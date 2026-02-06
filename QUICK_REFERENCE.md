# CardDealerPro Image Upload Automation - Quick Reference

## 🚀 Quick Start

### 1. Create Virtual Environment (Recommended)
```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```
You'll see `(venv)` in your prompt when active.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Credentials
```bash
cp templates/env.template config/.env
```
Edit `config/.env`:
```bash
CDP_USERNAME=your_email@example.com
CDP_PASSWORD=your_password
```

### 4. Configure Settings
```bash
cp templates/upload_config.template.json config/upload_config.json
```

**Required edits in `config/upload_config.json`:**
- `default_images_path`: Base folder where image folders are stored
- `general_settings.batch_type`: Must match dropdown text exactly
- `general_settings.sport_type`: Must match dropdown text exactly
- `selectors`: See [SELECTOR_GUIDE.md](docs/SELECTOR_GUIDE.md)

### 5. Organize Images
```
/base/path/
  ├── Test1/
  │   ├── card-001-front.jpg
  │   └── card-001-back.jpg
  └── A3/
      ├── card-002-front.jpg
      └── card-002-back.jpg
```
Files must contain "front" or "back" in filename for auto-rotation.

### 6. Run Workflow
```bash
# Single folder (uses default config path)
python3 scripts/image_upload_workflow.py --folder Test1

# Multiple folders (single login, shared browser session)
python3 scripts/image_upload_workflow.py --folder A3 B5 C2

# Headless (no browser window)
python3 scripts/image_upload_workflow.py --folder Test1 --headless
```

### 7. When Finished (Deactivate Virtual Environment)
```bash
deactivate
```
This returns you to your system Python. Reactivate anytime with `source venv/bin/activate` (macOS/Linux) or `venv\Scripts\activate` (Windows).

## 📁 Key Files

```
config/
  ├── .env                    # Credentials (YOU CREATE)
  └── upload_config.json      # Settings & selectors (YOU CREATE)
scripts/
  ├── image_upload_workflow.py   # Main workflow
  └── rotate_images.py           # Standalone rotation (optional)
tests/
  └── test_scan_sides.py          # Test without upload
docs/
  ├── QUICKSTART.md              # Full setup guide
  └── SELECTOR_GUIDE.md          # Finding CSS selectors
```

## 🎯 Commands

⚠️ **Note**: Activate virtual environment first: `source venv/bin/activate`

```bash
# Standard run (default config path)
python3 scripts/image_upload_workflow.py --folder Test1

# Headless mode (no browser window)
python3 scripts/image_upload_workflow.py --folder Test1 --headless

# Use full path instead of folder name
python3 scripts/image_upload_workflow.py --folder /full/path/to/images

# Test without upload
python3 tests/test_scan_sides.py --config config/upload_config.json

# Rotate images only (optional)
python3 scripts/rotate_images.py /path/to/folder
```

## 🚀 Shell Shortcuts (Optional)

Add these to your `~/.zshrc` for quick access:

```bash
# Quick run aliases
alias yolo='python3 ~/Repos/image-upload-automation/scripts/image_upload_workflow.py --config ~/Repos/image-upload-automation/config/upload_config.json --folder'
alias yolo-headless='python3 ~/Repos/image-upload-automation/scripts/image_upload_workflow.py --config ~/Repos/image-upload-automation/config/upload_config.json --folder --headless'

# Function to run in new iTerm2 tab with custom title
cdp() {
    if [ -z "$1" ]; then
        echo "Usage: cdp <folder_name> [folder_name2 ...]"
        echo "Example: cdp A3"
        echo "Example: cdp A3 B4 C5"
        return 1
    fi
    
    # Build tab title from all folder names
    tab_title="$*"
    
    # AppleScript to open new iTerm2 tab with custom title
    osascript <<EOF
        tell application "iTerm2"
            tell current window
                create tab with default profile
                tell current session of current tab
                    set name to "$tab_title"
                    write text "cd ~/Repos/image-upload-automation"
                    write text "python3 scripts/image_upload_workflow.py --config config/upload_config.json --folder $*"
                end tell
            end tell
        end tell
EOF
}
```

**Usage:**
```bash
yolo A3                    # Run with visible browser
yolo-headless A3          # Run in headless mode
cdp A3                    # Open new iTerm2 tab and run
cdp A3 B4 C5              # Multiple folders in new tab
```

**After adding to ~/.zshrc, reload:**
```bash
source ~/.zshrc
```

## 📋 Workflow Steps (13)

1. Rotate Images (front→8, back→6)
2. Login (username → continue → password)
3. Navigate to General Settings
4. Fill General Settings (batch name auto-set from folder)
5. Continue to Optional Details
6. Fill Optional Details
7. Create Batch
8. Extract Batch ID
9. Click Magic Scan
10. Select Sides
11. Upload Images
12. Continue After Upload
13. Inspector View ⏸️ (stops here)

## ⚠️ Common Issues

| Issue | Solution |
|-------|----------|
| Credentials missing | Create config/.env file |
| Element not found | Verify selectors in DevTools |
| Upload timeout | Increase SELENIUM_TIMEOUT in config.py |

## 🔧 Customization

**Edit config.py:**
```python
SELENIUM_TIMEOUT = 60      # Default: 30
MAX_LOGIN_RETRIES = 5      # Default: 3
```

## 🧩 New Configurable Fields

- **Title Template**: `general_settings.title_template` + selector `title_template_select` (set `_type: "custom"` if needed)
- **Description Template**: `general_settings.description_template` + selector `description_template_select` (set `_type: "custom"`)
- **Optional Condition**: `optional_details.condition` + selector `optional_condition` (set `_type: "custom"`)
- **Optional Sale Price**: `optional_details.sale_price` + selector `optional_sale_price`

See [docs/SELECTOR_GUIDE.md](docs/SELECTOR_GUIDE.md) for Headless UI (custom dropdown) selectors.

## 📚 Documentation

- [QUICKSTART.md](docs/QUICKSTART.md) - Full setup guide
- [SELECTOR_GUIDE.md](docs/SELECTOR_GUIDE.md) - Finding CSS selectors
- [USAGE.md](docs/USAGE.md) - Detailed usage & troubleshooting
