# Template Files

This folder contains template files that you should copy to create your working configuration files.

## Template Files

| Template File | Copy To | Purpose |
|--------------|---------|---------|
| `env.template` | `config/.env` | CardDealerPro login credentials |
| `upload_config.template.json` | `config/upload_config.json` | Batch upload configuration |

## Quick Setup

```bash
# Create your working files from templates
cp templates/env.template config/.env
cp templates/upload_config.template.json config/upload_config.json

# Edit the files with your actual values
nano config/.env
nano config/upload_config.json
```

## Multiple Configurations

You can create multiple config files for different batches:

```bash
cp templates/upload_config.template.json config/baseball_batch1.json
cp templates/upload_config.template.json config/basketball_cards.json
cp templates/upload_config.template.json config/vintage_collection.json
```

Then run with:
```bash
python scripts/image_upload_workflow.py --config config/baseball_batch1.json
```

## Important Notes

- **Never edit template files directly** - always copy them first
- The `config/` folder is in `.gitignore` and will not be committed
- Keep your credentials secure in `config/.env`
- See `docs/TEMPLATE_SETUP.md` for detailed setup instructions

## Template File Contents

### env.template
Contains placeholder credentials for CardDealerPro login.

### upload_config.template.json
Contains all configuration options including:
- Image folder path
- URL endpoints
- Batch settings (name, type, sport, etc.)
- CSS selectors for form elements
- Workflow options

Replace all `<< USER: REPLACE >>` markers with your actual values.
