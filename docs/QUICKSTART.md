# Quick Start Guide

Get started with CardDealerPro Image Upload Automation in minutes.

## Prerequisites

Before you begin, ensure you have:

- **Python 3.8 or higher** - [Download Python](https://www.python.org/downloads/)
- **Google Chrome browser** - [Download Chrome](https://www.google.com/chrome/)
- **CardDealerPro account** with valid login credentials
- **Image folder** containing the images you want to upload

## Installation Steps

### 1. Download or Clone the Project

If you have the project files, navigate to the project directory:

```bash
cd /path/to/image-upload-automation
```

### 2. Create Python Virtual Environment

This isolates the project dependencies from your system Python.

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt when the virtual environment is active.

### 3. Install Dependencies

With the virtual environment activated:

```bash
pip install -r requirements.txt
```

This installs:
- Selenium (browser automation)
- Pillow (image processing)
- webdriver-manager (automatic ChromeDriver management)
- python-dotenv (environment variable management)
- rich (beautiful console output)

### 4. Set Up Credentials

Create your credentials file from the template:

```bash
# Copy the template file
cp templates/env.template config/.env

# Edit with your credentials
nano config/.env  # or use any text editor
```

**Edit `config/.env` to contain:**
```
CDP_USERNAME=your_actual_username
CDP_PASSWORD=your_actual_password
```

⚠️ **IMPORTANT**: The entire `config/` folder is in `.gitignore` and will not be committed!

📚 **For detailed template setup help**, see `templates/README.md` or `docs/TEMPLATE_SETUP.md` for step-by-step guidance.

### 5. Create Your Configuration File

The configuration file tells the script what to upload and where to find form elements.

```bash
# Copy the template config
cp templates/upload_config.template.json config/upload_config.json

# Edit with your settings
nano config/upload_config.json  # or use any text editor
```

**You MUST replace all fields marked with `<< USER: ... >>`**

#### Essential Fields to Update:

1. **image_folder** - Absolute path to your images
   ```json
   "image_folder": "/Users/yourname/Desktop/card_images"
   ```

2. **general_settings** - Batch details
   ```json
   "general_settings": {
     "batch_name": "2024 Topps Chrome Baseball",
     "batch_type": "Sports Cards",
     "sport_type": "Baseball",
     "title_template": "Standard Template",
     "description": "Mint condition cards"
   }
   ```

3. **selectors** - CSS selectors for form elements
   
   This is the most critical part! See [SELECTOR_GUIDE.md](SELECTOR_GUIDE.md) for detailed instructions on finding selectors.

### 6. Find CSS Selectors

Before running the script, you need to find CSS selectors for all form elements.

**Quick method:**

1. Open Chrome and go to carddealerpro.com
2. Log in manually
3. Right-click on a form field → "Inspect"
4. In DevTools, right-click the highlighted HTML element → Copy → Copy selector
5. Paste into your config file

**Detailed guide:** See [SELECTOR_GUIDE.md](SELECTOR_GUIDE.md)

### 7. Test Your Configuration

Before uploading a large batch, test with a few images:

```bash
python scripts/image_upload_workflow.py --config my_batch.json
```

The script will:
1. ✓ Rotate images based on EXIF data
2. ✓ Login to CardDealerPro
3. ✓ Navigate through the workflow
4. ✓ Upload images
5. ⏸️ Stop at inspector view for your validation

### 8. Manual Validation

When the workflow reaches the inspector view:

1. **Browser stays open** - Don't close it!
2. **Review uploaded images** in the inspector view
3. **Verify all images appear correctly**
4. Press **Enter** in the terminal when done
5. Browser closes automatically

## Common First-Run Issues

### "Config file not found"
- Ensure you created `my_batch.json` from the example
- Use absolute path or run from project root

### "Credentials not found"
- Ensure `.env` file exists in project root
- Check `CDP_USERNAME` and `CDP_PASSWORD` are set
- No quotes needed around values in `.env`

### "Element not found" / Timeout errors
- Your CSS selectors are likely incorrect
- Verify selectors in browser DevTools
- See [SELECTOR_GUIDE.md](SELECTOR_GUIDE.md) for help

### "ChromeDriver" errors
- Ensure Chrome browser is installed
- Check internet connection (ChromeDriver downloads automatically)
- Try running with `--headless` flag for debugging

### Login fails
- Verify credentials in `.env` are correct
- Check if website requires CAPTCHA or 2FA
- Try logging in manually first to verify credentials

## Command Reference

### Basic Usage
```bash
python scripts/image_upload_workflow.py --config my_batch.json
```

### Headless Mode (No Browser Window)
```bash
python scripts/image_upload_workflow.py --config my_batch.json --headless
```

### Test Image Rotation Only
```bash
python tools/image_tools.py /path/to/image/folder
```

## Next Steps

Once you have a successful test run:

1. **Save your working config** for future batches
2. **Document your selectors** in case the website changes
3. **Read [USAGE.md](USAGE.md)** for advanced features
4. **Check [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md)** for future enhancements

## Getting Help

If you encounter issues:

1. Check error messages in the console (they're detailed!)
2. Review [USAGE.md](USAGE.md) for troubleshooting
3. Verify selectors using [SELECTOR_GUIDE.md](SELECTOR_GUIDE.md)
4. Check that website structure hasn't changed

## Directory Structure

After setup, your project should look like:

```
image-upload-automation/
├── .env                    # Your credentials (don't commit!)
├── my_batch.json          # Your config (don't commit!)
├── config_templates/      # Example configs
├── docs/                  # Documentation
├── scripts/               # Main workflow script
├── tools/                 # Automation utilities
└── venv/                  # Virtual environment
```

## Deactivating Virtual Environment

When you're done:

```bash
deactivate
```

---

**Ready to start?** Run your first batch:

```bash
python scripts/image_upload_workflow.py --config my_batch.json
```
