# Usage Guide

Complete reference for running the CardDealerPro Image Upload Automation.

## Command Line Interface

### Basic Command

```bash
python scripts/image_upload_workflow.py --config <path-to-config.json>
```

### Command Options

| Option | Required | Description |
|--------|----------|-------------|
| `--config` | Yes | Path to JSON configuration file |
| `--headless` | No | Run browser in headless mode (no visible window) |

### Examples

**Standard run with visible browser:**
```bash
python scripts/image_upload_workflow.py --config my_batch.json
```

**Headless run (background mode):**
```bash
python scripts/image_upload_workflow.py --config my_batch.json --headless
```

**Using absolute path to config:**
```bash
python scripts/image_upload_workflow.py --config /Users/username/configs/batch_01.json
```

## Workflow Stages

The script executes 14 major stages:

### Stage 1: Image Rotation
- Reads EXIF orientation from images
- Rotates JPEGs (creates copies in `rotated_images/`)
- Rotates other formats in-place
- Shows progress bar with file names

**Console Output:**
```
Found 50 images to process
Rotating images... ━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00
✓ Rotated 45/50 images (5 skipped, 0 failed)
```

**What to check:**
- Failed images are logged with error messages
- Verify rotated image count matches expectations

### Stage 2: Login
- Navigates to login URL
- Fills username and password from `.env`
- Clicks login button
- Verifies redirect to batches page

**Console Output:**
```
Attempting login (attempt 1/3)...
✓ Username entered
✓ Password entered
✓ Login successful!
```

**Common issues:**
- **Login fails**: Check credentials in `.env`
- **Timeout**: Increase `SELENIUM_TIMEOUT` in `config.py`
- **Wrong page**: Verify `success_url_pattern` in config

### Stage 3-8: Batch Creation
- Navigates through form pages
- Fills general settings
- Fills optional details (if configured)
- Submits batch creation

**Console Output:**
```
STEP 5: Fill General Settings
✓ Filled Batch Name: 2024 Topps Chrome
✓ Selected Batch Type: Sports Cards
✓ Selected Sport Type: Baseball
...
```

**Common issues:**
- **Element not found**: Selector is wrong, see [SELECTOR_GUIDE.md](SELECTOR_GUIDE.md)
- **Option not found in dropdown**: Value doesn't match exactly
- **Click intercepted**: Another element is covering the button

### Stage 9: Batch ID Extraction
- Extracts batch_id from URL using regex
- Falls back to DOM selectors if regex fails

**Console Output:**
```
Extracting batch_id from URL...
Current URL: https://v2.carddealerpro.com/batches/ABC123/add/types
✓ Extracted batch_id from URL: ABC123
```

**Common issues:**
- **Extraction failed**: URL pattern changed, update `BATCH_ID_REGEX` in `config.py`
- Check console for current URL and adjust regex

### Stage 10-13: Image Upload
- Navigates through magic scan and sides selection
- Uploads all rotated images
- Clicks continue

**Console Output:**
```
STEP 12: Upload Images
Uploading 45 files...
✓ Uploaded 45 files
```

**Common issues:**
- **File input not found**: Selector for hidden input is wrong
- **Upload fails**: Check file paths are absolute
- **Timeout**: Large batches take time, increase timeout

### Stage 14: Inspector View
- Reaches inspector view
- Pauses for manual validation
- Keeps browser open

**Console Output:**
```
═══════════════════════════════════════════════════════════
WORKFLOW PAUSED FOR MANUAL VALIDATION
═══════════════════════════════════════════════════════════

Please review the uploaded images in the browser window.
The browser will remain open for your inspection.

Press Enter to close browser and exit...
```

**What to do:**
1. Review all uploaded images in the inspector view
2. Verify image count matches expectations
3. Check for upload errors or missing images
4. When satisfied, return to terminal and press Enter

## Console Output Interpretation

### Status Symbols

| Symbol | Meaning |
|--------|---------|
| `✓` | Success - step completed |
| `✗` | Error - step failed |
| `⚠` | Warning - non-critical issue |
| `○` | Skipped - no action needed |

### Progress Bars

```
Rotating images... ━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:05
```

Shows:
- Current operation
- Progress percentage
- Estimated time remaining

### Summary Tables

```
Workflow Results
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Stage            ┃ Status     ┃ Details             ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ Image Rotation   │ ✓ Complete │ 45 images ready     │
│ Login            │ ✓ Complete │ Authenticated       │
│ Batch Creation   │ ✓ Complete │ Batch ID: ABC123    │
│ Image Upload     │ ✓ Complete │ 45 files uploaded   │
└──────────────────┴────────────┴─────────────────────┘
```

## Error Messages and Solutions

### Configuration Errors

**Error:** `Config file not found: my_batch.json`
```
Solution:
1. Verify file exists
2. Use absolute path or run from project root
3. Check file name spelling
```

**Error:** `Missing required config fields: ['selectors']`
```
Solution:
1. Copy from config_templates/upload_config.example.json
2. Ensure all required sections exist
3. Validate JSON syntax (use jsonlint.com)
```

**Error:** `Image folder does not exist: /path/to/images`
```
Solution:
1. Verify folder path is correct
2. Use absolute path (not relative)
3. Check folder permissions
```

### Credential Errors

**Error:** `Credentials not found in environment`
```
Solution:
1. Ensure .env file exists in project root
2. Verify CDP_USERNAME and CDP_PASSWORD are set
3. No quotes needed: CDP_USERNAME=myuser
4. Restart script after creating .env
```

### WebDriver Errors

**Error:** `Failed to initialize WebDriver`
```
Solution:
1. Ensure Chrome browser is installed
2. Check internet connection (ChromeDriver downloads automatically)
3. Try updating Chrome to latest version
4. Clear webdriver-manager cache:
   rm -rf ~/.wdm/drivers/
```

### Element Not Found Errors

**Error:** `Timeout waiting for element: input[name="username"]`
```
Solution:
1. Verify selector in browser DevTools
2. Test: document.querySelector('input[name="username"]')
3. Element might load slowly - increase SELENIUM_TIMEOUT
4. Website structure may have changed
5. See SELECTOR_GUIDE.md for finding correct selectors
```

**Error:** `Element became stale after 3 attempts`
```
Solution:
1. This is usually a timing issue
2. Page is updating dynamically
3. Script retries automatically - check if it recovers
4. If persistent, website may have changed
```

### Login Errors

**Error:** `Login failed after 3 attempts`
```
Solution:
1. Verify credentials in .env are correct
2. Try logging in manually to test credentials
3. Check if website requires CAPTCHA
4. Verify login button selector is correct
5. Website may have rate limiting - wait and retry
```

### Upload Errors

**Error:** `Failed to upload files: Element not found`
```
Solution:
1. File input selector is likely wrong
2. Input is often hidden - search for: input[type="file"]
3. Use browser DevTools to find correct selector
4. Try: document.querySelector('input[type="file"]')
```

**Error:** `Upload failed: File not found`
```
Solution:
1. Image rotation may have failed for some files
2. Check image_folder path is correct
3. Verify images exist and are readable
4. Check file permissions
```

## Headless Mode

Running without a visible browser window.

### When to Use Headless

- Production/scheduled runs
- Server environments without display
- Faster execution (slightly)
- Running multiple instances

### When NOT to Use Headless

- First-time setup (need to see what's happening)
- Debugging selector issues
- Troubleshooting login problems
- Manual validation needed

### Headless Limitations

- Cannot visually verify form filling
- Screenshots needed for debugging
- Some websites detect headless mode
- CAPTCHA solving not possible

## Tips and Best Practices

### Before Running

1. **Test selectors in browser** - Don't guess!
2. **Start with small batches** - Test with 5-10 images first
3. **Backup images** - Just in case
4. **Verify credentials** - Test manual login first

### During Execution

1. **Watch the console** - Detailed progress shown
2. **Don't interrupt** - Let it complete or fail cleanly
3. **Note any warnings** - May indicate future issues

### After Completion

1. **Validate in inspector view** - Check all images uploaded
2. **Document any issues** - Help improve future runs
3. **Save working config** - Reuse for similar batches

### For Large Batches

1. **Increase timeout** - Edit `SELENIUM_TIMEOUT` in `config.py`
2. **Test subset first** - Verify all settings work
3. **Monitor progress** - Large uploads take time
4. **Check internet connection** - Stable connection needed

## Troubleshooting Workflow

If something goes wrong:

1. **Read the error message** - They're detailed!
2. **Check the console output** - Shows exactly what step failed
3. **Verify that step manually** - Can you do it in browser?
4. **Check selectors** - Use browser DevTools
5. **Test in console** - `document.querySelector('selector')`
6. **Update config** - Fix selectors and retry
7. **Report persistent issues** - May be website changes

## Performance Notes

### Typical Run Times

| Batch Size | Rotation | Upload | Total |
|------------|----------|--------|-------|
| 10 images  | 5 sec    | 10 sec | ~1 min |
| 50 images  | 20 sec   | 30 sec | ~2 min |
| 100 images | 40 sec   | 60 sec | ~4 min |
| 500 images | 3 min    | 5 min  | ~15 min |

*Times are approximate and depend on image size and internet speed*

### Optimization Tips

1. **Use headless mode** - Slightly faster
2. **Optimize images beforehand** - Smaller files upload faster
3. **Stable internet** - Avoid WiFi if possible
4. **Close other applications** - Free up system resources

## Advanced Usage

### Running Multiple Batches

```bash
# Create multiple configs
configs/batch_01.json
configs/batch_02.json
configs/batch_03.json

# Run sequentially
python scripts/image_upload_workflow.py --config configs/batch_01.json
python scripts/image_upload_workflow.py --config configs/batch_02.json
python scripts/image_upload_workflow.py --config configs/batch_03.json
```

### Testing Image Rotation Only

```bash
# Test rotation without uploading
python tools/image_tools.py /path/to/images
```

### Custom Timeout

Edit `config.py`:
```python
SELENIUM_TIMEOUT = 60  # Increase to 60 seconds for slow connections
```

## Exit Codes

The script returns different exit codes:

| Code | Meaning |
|------|---------|
| 0 | Success - workflow completed |
| 1 | Error - workflow failed |
| 2 | Interrupted - user cancelled (Ctrl+C) |

Use in scripts:
```bash
python scripts/image_upload_workflow.py --config my_batch.json
if [ $? -eq 0 ]; then
    echo "Success!"
else
    echo "Failed!"
fi
```

## Next Steps

- Review [SELECTOR_GUIDE.md](SELECTOR_GUIDE.md) for selector help
- Check [QUICKSTART.md](QUICKSTART.md) for setup issues
- See [FUTURE_ENHANCEMENTS.md](FUTURE_ENHANCEMENTS.md) for planned features

---

**Questions or issues?** Check error messages carefully - they guide you to the solution!
