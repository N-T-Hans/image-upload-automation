# CardDealerPro Image Upload Automation

A Python-based Selenium automation script that handles EXIF image rotation and automates the multi-step batch upload process for CardDealerPro.

## Features

- **Automatic Image Rotation**: Reads EXIF orientation data and rotates images correctly
- **Batch Upload Automation**: Automates the 20-step workflow on carddealerpro.com
- **Rich Console Output**: Clear progress bars and status updates for each stage
- **Configurable**: JSON-based configuration for different batch types and settings
- **Safe Credential Storage**: Uses `.env` file for secure credential management

## Quick Start

1. **Prerequisites**: Python 3.8+, Chrome browser
2. **Install**: See [docs/QUICKSTART.md](docs/QUICKSTART.md) for detailed setup
3. **Configure**: Copy templates to `config/` folder and fill in your values
   ```bash
   cp templates/env.template config/.env
   cp templates/upload_config.template.json config/upload_config.json
   ```
4. **Test Components**: Run individual test scripts before full workflow
5. **Run**: `python scripts/image_upload_workflow.py --config config/upload_config.json`

For help with template files, see [templates/README.md](templates/README.md) or [docs/TEMPLATE_SETUP.md](docs/TEMPLATE_SETUP.md).

## Testing

Test individual components before running the full workflow:

```bash
# Test image rotation
python tests/test_image_rotation.py /path/to/images

# Test login and navigation
python tests/test_login_navigation.py --config my_batch.json

# Test form selectors
python tests/test_upload_config.py --config my_batch.json
```

**See [TESTING_GUIDE.md](TESTING_GUIDE.md) for detailed testing instructions and troubleshooting.**

## Documentation

- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Component testing guide
- [QUICKSTART.md](docs/QUICKSTART.md) - First-time setup guide
- [TEMPLATE_SETUP.md](docs/TEMPLATE_SETUP.md) - How to use template files (.env and config)
- [SELECTOR_GUIDE.md](docs/SELECTOR_GUIDE.md) - How to find CSS selectors for form elements
- [USAGE.md](docs/USAGE.md) - Command reference and workflow details
- [DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md) - Implementation roadmap

## Project Structure

```
image-upload-automation/
├── tools/                      # Core automation modules
│   ├── image_tools.py         # Image rotation handler
│   └── web_automation_tools.py # Selenium utilities
├── scripts/                    # Executable scripts
│   └── image_upload_workflow.py # Main workflow orchestrator
├── tests/                      # Component test scripts
│   ├── test_image_rotation.py # Test image rotation
│   ├── test_login_navigation.py # Test login/navigation
│   └── test_upload_config.py  # Test form selectors
├── templates/                  # Template files (copy to config/)
│   ├── env.template           # Credentials template
│   ├── upload_config.template.json # Config template
│   └── README.md              # Template usage guide
├── config/                     # Your working configs (gitignored)
│   ├── .env                   # Your credentials (create from template)
│   └── *.json                 # Your batch configs (create from template)
├── docs/                       # Documentation
├── config.py                   # Global constants
└── requirements.txt           # Python dependencies
```

## Workflow Overview

1. Rotate images based on EXIF orientation
2. Login to CardDealerPro
3. Navigate to batches page
4. Create new batch with general settings
5. Fill optional details (if configured)
6. Submit batch creation
7. Select magic scan mode
8. Choose sides (front and back)
9. Upload all images
10. Reach inspector view for manual validation

## Support

See [docs/USAGE.md](docs/USAGE.md) for troubleshooting common issues.

## Future Enhancements

See [docs/FUTURE_ENHANCEMENTS.md](docs/FUTURE_ENHANCEMENTS.md) for planned features.
