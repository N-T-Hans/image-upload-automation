# Template Files Setup Guide

This guide explains how to use the template files in this project to get started quickly.

## Overview

This project includes template files that you need to copy and customize. **Never edit the template files directly** - always make a copy first.

---

## Step 1: Setup Credentials File

### What it's for
The `config/.env` file stores your CardDealerPro login credentials securely.

### How to create it

**Option A: Copy and Rename (Recommended)**
```bash
# In the project root directory
cp templates/env.template config/.env
```

**Option B: Manual Creation**
1. Create a new file named `.env` in the `config/` folder
2. Copy the contents from `templates/env.template`
3. Save as `config/.env`

### How to fill it out

Open the `config/.env` file and replace the placeholder values:

```bash
# Before (from template)
CDP_USERNAME=your_username_here
CDP_PASSWORD=your_password_here

# After (your actual credentials)
CDP_USERNAME=john.doe@example.com
CDP_PASSWORD=MySecurePassword123
```

### Important Notes
- The entire `config/` folder is in `.gitignore` and will NOT be committed to version control
- Keep this file secure - it contains your login credentials
- Do not share this file or commit it to Git
- The `config/` folder keeps all your working files organized in one place

---

## Step 2: Setup Configuration File

### What it's for
The configuration JSON file defines:
- What images to upload
- Form field values (batch name, type, sport, etc.)
- CSS selectors for form elements
- Workflow settings

### How to create it

**Option A: Copy and Rename (Recommended)**
```bash
# Create your first config file
cp templates/upload_config.template.json config/upload_config.json
```

**Option B: Manual Creation**
1. Create a new file in the `config/` folder (e.g., `config/baseball_batch_1.json`)
2. Copy the entire contents from `templates/upload_config.template.json`
3. Save in the `config/` folder

### How to fill it out

The template has sections marked with `<< USER: REPLACE >>` that you must fill in:

#### Required: Image Folder
```json
"image_folder": "/Users/yourname/Desktop/card_images"
```

#### Required: Batch Settings
```json
"general_settings": {
  "batch_name": "2024 Baseball Cards - Set 1",
  "batch_type": "Raw",
  "sport_type": "Baseball",
  "title_template": "Standard",
  "description": "Vintage baseball cards from 1990s"
}
```

#### Required: CSS Selectors
You must find these using Chrome DevTools (see `docs/SELECTOR_GUIDE.md`):

```json
"selectors": {
  "username_input": "#user_email",
  "password_input": "#user_password",
  "login_button": "button[type='submit']",
  "create_batch_button": "a.btn-primary[href*='new']",
  // ... and 20+ more selectors
}
```

**See `docs/SELECTOR_GUIDE.md` for detailed instructions on finding selectors.**

#### Optional: Additional Details
```json
"optional_details": {
  "field1": "value1",
  "field2": "value2"
}
```
Remove this section if not needed.

### Configuration Examples

**Minimal Config** (fastest setup):
```json
{
  "image_folder": "/path/to/images",
  "urls": { "login": "...", "batches": "...", "general_settings": "..." },
  "general_settings": { "batch_name": "Test", "batch_type": "Raw", "sport_type": "Baseball" },
  "selectors": { /* all required selectors */ }
}
```

**Full Config** (with all options):
```json
{
  "image_folder": "/path/to/images",
  "urls": { /* all URLs */ },
  "general_settings": { /* all settings */ },
  "optional_details": { /* custom fields */ },
  "selectors": { /* all selectors */ },
  "workflow": { "stop_after": "inspector_view", "validate_upload_count": true }
}
```

---

## Step 3: Using Your Configuration

Once you've created your config file, run the workflow:

```bash
python scripts/image_upload_workflow.py --config config/upload_config.json
```

### Multiple Configurations

You can create multiple configuration files for different batches in the `config/` folder:

```
config/
├── .env                              # One .env for all configs
├── .gitkeep                          # Keeps folder in git
├── baseball_batch1.json             # First batch
├── baseball_batch2.json             # Second batch
├── basketball_cards.json            # Different sport
└── vintage_collection.json          # Different collection
```

Run different batches:
```bash
python scripts/image_upload_workflow.py --config config/baseball_batch1.json
python scripts/image_upload_workflow.py --config config/basketball_cards.json
```

---

## Quick Reference

### Files You Need to Create

| Template File | Your File | Location | Purpose |
|--------------|-----------|----------|---------||
| `templates/env.template` | `.env` | `config/` folder | Credentials |
| `templates/upload_config.template.json` | `*.json` | `config/` folder | Batch config |

### Quick Setup Commands

```bash
# 1. Setup environment
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt

# 2. Create credentials file
cp templates/env.template config/.env
# Edit config/.env with your credentials

# 3. Create config file
cp templates/upload_config.template.json config/upload_config.json
# Edit config/upload_config.json with your batch details and selectors

# 4. Test in pieces
python tests/test_image_rotation.py /path/to/images
python tests/test_login_navigation.py --config config/upload_config.json
python tests/test_upload_config.py --config config/upload_config.json

# 5. Run full workflow
python scripts/image_upload_workflow.py --config config/upload_config.json
```

---

## Troubleshooting

### "File not found" errors

**Problem**: `FileNotFoundError: [Errno 2] No such file or directory: '.env'`

**Solution**: You need to create the `.env` file:
```bash
cp .env.example .env
```

### "Invalid JSON" errors

**Problem**: `json.decoder.JSONDecodeError: Expecting value`

**Solution**: Check your JSON syntax:
- All strings must use double quotes `"`
- No trailing commas
- Properly nested brackets
- Use a JSON validator: https://jsonlint.com

### Missing template markers

**Problem**: Still see `<< USER: REPLACE >>` in error messages

**Solution**: You forgot to replace a required field:
1. Search your config file for `<< USER`
2. Replace all occurrences with actual values
3. Remove the `<< USER: REPLACE >>` marker text

### Credentials not loading

**Problem**: "Credentials not found in .env file"

**Solutions**:
1. Ensure `.env` file exists in project root
2. Check file is named exactly `.env` (not `.env.txt`)
3. Verify environment variables are set:
   ```bash
   cat .env
   ```
4. Restart terminal if you just created `.env`

---

## Best Practices

### DO:
✓ Copy template files before editing  
✓ Use descriptive config file names (`baseball_2024_batch1.json`)  
✓ Keep `.env` file secure and private  
✓ Test with small batches first  
✓ Document your selectors in config comments  

### DON'T:
✗ Edit template files directly  
✗ Commit `.env` file to version control  
✗ Share config files with credentials  
✗ Use production batches for testing  
✗ Delete template files  

---

## Next Steps

After setting up your files:

1. **Test individual components** with test scripts (see `docs/USAGE.md`)
2. **Find CSS selectors** using Chrome DevTools (see `docs/SELECTOR_GUIDE.md`)
3. **Run a small test batch** (5-10 images) to verify everything works
4. **Review console output** at each step for errors
5. **Proceed to full batches** once testing passes

Need help? See:
- `docs/QUICKSTART.md` - Getting started guide
- `docs/SELECTOR_GUIDE.md` - How to find CSS selectors
- `docs/USAGE.md` - Detailed usage instructions
- `QUICK_REFERENCE.md` - One-page cheat sheet
