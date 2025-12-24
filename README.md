# CardDealerPro Image Upload Automation

A Python-based Selenium automation script that rotates images based on filename patterns and automates the multi-step batch upload process for CardDealerPro.

## Features

- **Automatic Image Rotation**: Inline step rotates files with "front" → EXIF orientation 8, "back" → orientation 6
- **Complete Batch Automation**: Orchestrates login → settings → batch creation → upload → inspector
- **Multi-Folder Runs**: Queue multiple folders in one run with a shared session
- **Config Defaults**: Uses `config/upload_config.json` by default (no `--config` required)
- **Rich Console Output**: Clear step logs plus per-step timing
- **Summary Metrics**: Batch summary shows Images, Total Time, Status, Step, and Error
- **Safe Credential Storage**: Uses `config/.env` for credentials

## Quick Start

1. **Prerequisites**: Python 3.8+, Chrome browser
2. **Virtual Environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```
3. **Install**: `pip install -r requirements.txt`
4. **Configure**: 
   ```bash
   cp templates/env.template config/.env
   cp templates/upload_config.template.json config/upload_config.json
   # Edit config/.env with your credentials
   # Edit config/upload_config.json with your settings and selectors
   ```
5. **Run**: 
   ```bash
   # Single folder (uses default config path):
   python3 scripts/image_upload_workflow.py --folder Test1

   # Multiple folders in one session (single login):
   python3 scripts/image_upload_workflow.py --folder A3 B5 C2

   # Headless mode (no browser window):
   python3 scripts/image_upload_workflow.py --folder Test1 --headless

   # Using a full absolute path instead of folder name:
   python3 scripts/image_upload_workflow.py --folder /path/to/images
   ```

For detailed setup, see [docs/QUICKSTART.md](docs/QUICKSTART.md)

## Image Rotation

Images are automatically rotated in Step 1 of the workflow, in-place, using EXIF orientation:
- Files with "front" in the filename → orientation 8 (270° CW)
- Files with "back" in the filename → orientation 6 (90° CW)
- Files without front/back are left unchanged
Errors are logged but do not stop the workflow.

### Standalone Rotation (optional)

If you want to pre-rotate images without running the full workflow, use the standalone tool:

```zsh
python3 scripts/rotate_images.py /path/to/folder
```

Notes:
- The main workflow already performs rotation; this is for one-off checks or pre-processing.
- Rotation is applied in-place by updating the EXIF orientation.

## Testing

Test the workflow up to sides selection (without full upload):

```bash
python3 tests/test_scan_sides.py --config config/upload_config.json
```

## Documentation

- [QUICKSTART.md](docs/QUICKSTART.md) - First-time setup guide
- [USAGE.md](docs/USAGE.md) - Command reference and workflow details
- [SELECTOR_GUIDE.md](docs/SELECTOR_GUIDE.md) - How to find CSS selectors for form elements
- [TEMPLATE_SETUP.md](docs/TEMPLATE_SETUP.md) - Using the `config/.env` and `config/upload_config.json` templates

## Workflow Overview

1. Rotate Images
2. Login
3. Navigate to General Settings
4. Fill General Settings (batch name auto-set from folder)
5. Continue to Optional Details
6. Fill Optional Details (optional fields)
7. Create Batch
8. Extract Batch ID
9. Click Magic Scan
10. Select Sides
11. Upload Images
12. Continue After Upload
13. Inspector View (pause for manual validation)

## Configuration

The workflow uses `--folder` parameter to:
- Set the image source folder
- Automatically set batch_name to the folder name
- Override config file settings

Set `default_images_path` in your config to use just folder names:
```json
{
   "default_images_path": "/Users/username/Downloads/CardTest",
   ...
}
```

Then run with:
```bash
python3 scripts/image_upload_workflow.py --folder A3
```

## Batch Summary

At the end of a run (or after multiple folders), a summary table shows:
- Images: Count of files discovered
- Time: Total elapsed across steps
- Status: Success or Failed
- Step: Last step executed (useful on failure)
- Error: Error message if any

## Headless Mode

Run without visible browser for faster execution:
```bash
python3 scripts/image_upload_workflow.py --folder Test1 --headless
```

## Project Structure

```
image-upload-automation/
├── tools/                       # Core automation modules
│   └── web_automation_tools.py  # Selenium utilities
├── scripts/                     # Executable scripts
│   ├── image_upload_workflow.py # Main workflow orchestrator
│   └── rotate_images.py         # Standalone rotation tool (optional)
├── tests/                       # Component test scripts
│   └── test_scan_sides.py       # Test sides selection/navigation
├── templates/                   # Template files (copy to config/)
│   ├── env.template             # Credentials template
│   └── upload_config.template.json # Config template
├── config/                      # Your working configs (gitignored)
│   ├── .env                     # Your credentials (create from template)
│   └── upload_config.json       # Your batch config (create from template)
├── docs/                        # Documentation
├── config.py                    # Global constants
└── requirements.txt             # Python dependencies
```

## Support

See [docs/USAGE.md](docs/USAGE.md) for troubleshooting common issues.

## Future Enhancements

See [docs/FUTURE_ENHANCEMENTS.md](docs/FUTURE_ENHANCEMENTS.md) for planned features.
