# CardDealerPro Image Upload Automation - Quick Reference

## 🚀 Quick Start (5 Minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up credentials
cp templates/env.template config/.env
# Edit config/.env with your username/password

# 3. Create config
cp templates/upload_config.template.json config/upload_config.json
# Edit config/upload_config.json with your batch details and selectors

# 4. Test components (recommended)
python tests/test_image_rotation.py /path/to/images
python tests/test_login_navigation.py --config config/upload_config.json
python tests/test_upload_config.py --config config/upload_config.json

# 5. Run full workflow
python scripts/image_upload_workflow.py --config config/upload_config.json
```

**Need help with templates?** See `templates/README.md` or `docs/TEMPLATE_SETUP.md`

## 📁 Project Structure

```
image-upload-automation/
├── config.py                          # Global settings
├── requirements.txt                   # Python dependencies
├── README.md                         # Project overview
│
├── templates/                        # Template files (copy to config/)
│   ├── env.template                 # Credentials template
│   ├── upload_config.template.json  # Config template
│   └── README.md                    # Template usage guide
│
├── config/                           # Your working configs (gitignored)
│   ├── .env                         # Your credentials (CREATE THIS!)
│   └── upload_config.json           # Your batch config (CREATE THIS!)
│
├── tools/                            # Automation modules
│   ├── image_tools.py               # EXIF rotation handler
│   └── web_automation_tools.py      # Selenium utilities
│
├── scripts/                          # Executable scripts
│   └── image_upload_workflow.py     # Main workflow orchestrator
│
├── tests/                            # Component test scripts
│   ├── test_image_rotation.py       # Test image rotation
│   ├── test_login_navigation.py     # Test login/navigation
│   └── test_upload_config.py        # Test form selectors
│
└── docs/                             # Documentation
    ├── QUICKSTART.md                # Setup guide
    ├── TEMPLATE_SETUP.md            # Template files guide
    ├── SELECTOR_GUIDE.md            # Finding CSS selectors
    ├── USAGE.md                     # Command reference
    ├── DEVELOPMENT_PLAN.md          # Implementation details
    └── FUTURE_ENHANCEMENTS.md       # Planned features
```

## 🔑 Essential Files You Need to Create

### 1. config/.env file
```bash
# Copy from template
cp templates/env.template config/.env

# Then edit with your values:
CDP_USERNAME=your_username
CDP_PASSWORD=your_password
```

### 2. config/upload_config.json (from template)
```bash
# Copy from template
cp templates/upload_config.template.json config/upload_config.json
```
- Replace all `<< USER: ... >>` markers
- See [SELECTOR_GUIDE.md](docs/SELECTOR_GUIDE.md) for finding selectors

## 📋 Workflow Steps

1. ✓ **Rotate images** - EXIF-based correction
2. ✓ **Login** - Authenticate with credentials
3. ✓ **Navigate** - Go to batches page
4. ✓ **Create batch** - Click create button
5. ✓ **Fill settings** - Batch name, type, sport, etc.
6. ✓ **Continue** - Navigate to optional details
7. ✓ **Optional fields** - Fill if configured
8. ✓ **Submit batch** - Create the batch
9. ✓ **Extract ID** - Get batch_id from URL
10. ✓ **Magic scan** - Click magic scan button
11. ✓ **Select sides** - Choose front/back
12. ✓ **Upload images** - Send all files
13. ✓ **Continue** - Proceed after upload
14. ⏸️ **Inspector view** - STOP for manual validation

## 🎯 Common Commands

```bash
# Standard run
python scripts/image_upload_workflow.py --config config/upload_config.json

# Headless mode (no browser window)
python scripts/image_upload_workflow.py --config config/upload_config.json --headless

# Test individual components
python tests/test_image_rotation.py /path/to/images
python tests/test_login_navigation.py --config config/upload_config.json
python tests/test_upload_config.py --config config/upload_config.json

# Multiple batch configs
python scripts/image_upload_workflow.py --config config/baseball_batch1.json
python scripts/image_upload_workflow.py --config config/basketball_cards.json
```

## 🔍 Finding CSS Selectors (Quick Method)

1. Open Chrome → Go to carddealerpro.com
2. Right-click element → "Inspect"
3. In DevTools, right-click HTML → Copy → Copy selector
4. Test in Console: `document.querySelector('your-selector')`
5. Paste into config.json

**Detailed guide:** [docs/SELECTOR_GUIDE.md](docs/SELECTOR_GUIDE.md)

## ⚠️ Common Issues

| Issue | Solution |
|-------|----------|
| Config not found | Use absolute path or run from project root |
| Credentials missing | Create .env file with CDP_USERNAME/CDP_PASSWORD |
| Element not found | Verify selector in browser DevTools |
| Login fails | Check credentials, verify selectors |
| Upload timeout | Increase SELENIUM_TIMEOUT in config.py |

**Full troubleshooting:** [docs/USAGE.md](docs/USAGE.md)

## 📊 Console Output Symbols

| Symbol | Meaning |
|--------|---------|
| ✓ | Success |
| ✗ | Error |
| ⚠ | Warning |
| ○ | Skipped |

## 🛠️ Configuration Quick Reference

### Required Config Sections

```json
{
  "image_folder": "/absolute/path/to/images",
  
  "urls": {
    "login": "https://carddealerpro.com/login",
    "batches": "https://v2.carddealerpro.com/upload/batches?status=open"
  },
  
  "general_settings": {
    "batch_name": "Your Batch Name",
    "batch_type": "Sports Cards",
    "sport_type": "Baseball",
    "title_template": "Template Name",
    "description": "Batch description"
  },
  
  "optional_details": {},
  
  "selectors": {
    "username_input": "input[name='username']",
    "password_input": "input[type='password']",
    "login_button": "button[type='submit']",
    "create_batch_button": ".create-batch-btn",
    "batch_name_input": "#batch-name",
    // ... 20+ more selectors
  }
}
```

## 🔧 Customization

### Increase Timeout (Slow Internet)
Edit `config.py`:
```python
SELENIUM_TIMEOUT = 60  # Default: 30
```

### Change Supported Image Formats
Edit `config.py`:
```python
IMAGE_SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.webp', '.heic']
```

### Change Max Login Retries
Edit `config.py`:
```python
MAX_LOGIN_RETRIES = 5  # Default: 3
```

## 📚 Documentation Index

- **[README.md](README.md)** - Project overview
- **[docs/QUICKSTART.md](docs/QUICKSTART.md)** - Setup guide (START HERE!)
- **[docs/SELECTOR_GUIDE.md](docs/SELECTOR_GUIDE.md)** - Find CSS selectors
- **[docs/USAGE.md](docs/USAGE.md)** - Commands and troubleshooting
- **[docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md)** - Implementation details
- **[docs/FUTURE_ENHANCEMENTS.md](docs/FUTURE_ENHANCEMENTS.md)** - Planned features

## 🎓 Learning Path

1. Read [QUICKSTART.md](docs/QUICKSTART.md) - 10 minutes
2. Follow setup steps - 15 minutes
3. Read [SELECTOR_GUIDE.md](docs/SELECTOR_GUIDE.md) - 15 minutes
4. Find and test selectors - 30 minutes
5. Run first batch (small test) - 5 minutes
6. Validate and iterate - 10 minutes

**Total setup time: ~60-90 minutes**

## 💡 Pro Tips

1. **Always test with small batches first** (5-10 images)
2. **Keep working configs** for different batch types
3. **Document your selectors** in case website changes
4. **Use headless mode for production** runs
5. **Check console output** - it's very detailed!
6. **Validate at inspector view** before finalizing

## 🆘 Getting Help

1. Check error message - they're detailed!
2. Review [USAGE.md](docs/USAGE.md) troubleshooting section
3. Verify selectors with [SELECTOR_GUIDE.md](docs/SELECTOR_GUIDE.md)
4. Check if website structure changed

## 📝 Version Info

- **Current Version:** 1.0.0
- **Python Required:** 3.8+
- **Chrome Required:** Latest stable

## 🔄 Update Process

```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Test after update
python scripts/image_upload_workflow.py --config test_batch.json
```

---

**Ready to start?** → [docs/QUICKSTART.md](docs/QUICKSTART.md)

**Need help?** → [docs/USAGE.md](docs/USAGE.md)

**Finding selectors?** → [docs/SELECTOR_GUIDE.md](docs/SELECTOR_GUIDE.md)
