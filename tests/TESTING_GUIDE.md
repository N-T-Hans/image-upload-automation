# Component Testing Guide

This guide explains how to test the image upload automation system in pieces before running the full workflow.

## Why Test in Pieces?

Testing components individually helps you:
- Identify configuration issues early
- Verify each part works before combining them
- Debug problems more easily
- Build confidence in your setup

---

## Test Sequence

Follow this sequence to systematically verify each component:

### 1. Image Rotation Test (5 minutes)

**Purpose**: Verify EXIF-based image rotation works correctly

**Command**:
```bash
python tests/test_image_rotation.py /path/to/your/images
```

**What it tests**:
- Reads EXIF orientation metadata from images
- Rotates images as needed
- Creates rotated copies for JPEGs
- Shows detailed results with counts

**Success criteria**:
- Script completes without errors
- Console shows "TEST PASSED"
- Rotated images created in `rotated_images/` subfolder (for JPEGs)
- Image counts match expected numbers

**If it fails**:
- Verify folder path is correct
- Check folder contains supported image formats (.jpg, .png, .webp, .heic)
- Ensure read/write permissions on folder

**Example output**:
```
✓ Handler initialized successfully
✓ TEST PASSED
  50 images ready for upload
```

---

### 2. Login & Navigation Test (2 minutes)

**Purpose**: Verify credentials and basic navigation work

**Command**:
```bash
python tests/test_login_navigation.py --config config/upload_config.json
```

**What it tests**:
- Loads configuration file
- Reads credentials from .env
- Initializes Chrome WebDriver
- Logs into CardDealerPro
- Navigates to batches page
- Finds the "Create Batch" button

**Success criteria**:
- All 7 tests show "✓ Pass"
- Browser opens and logs in successfully
- Batches page loads
- Browser stays open for 10 seconds for inspection

**If it fails**:
- Check `config/.env` file exists with correct credentials
- Verify login selectors in config are correct
- Try running without `--headless` flag to see what's happening
- Manually test login in browser to confirm credentials work

**Example output**:
```
✓ Configuration loaded
✓ Credentials loaded (username: john@example.com)
✓ WebDriver initialized
✓ Login successful
✓ Navigation successful
✓ ALL TESTS PASSED
```

---

### 3. Upload Configuration Test (5 minutes)

**Purpose**: Verify all form selectors are correct

**Command**:
```bash
python tests/test_upload_config.py --config config/upload_config.json
```

**What it tests**:
- All general settings form selectors
- Optional details selectors (if configured)
- Verifies selectors are configured for upload pages
- Tests dropdown options
- Attempts to fill test values (in dry-run mode)

**Success criteria**:
- All configured selectors show "✓ Found and Tested"
- 100% pass rate for testable selectors
- No "NOT FOUND" errors
- Browser stays open for 15 seconds for inspection

**If it fails**:
- Update incorrect selectors using Chrome DevTools (see `docs/SELECTOR_GUIDE.md`)
- Test selectors in browser console: `document.querySelector('your-selector')`
- Ensure you're on the correct page when finding selectors

**Example output**:
```
✓ batch_name_input (text input) - found
✓ batch_type_select (dropdown) - found
✓ sport_type_select (dropdown) - found
...
✓ All configured selectors working!
Pass Rate: 100% (15/15 selectors working)
```

---

## Advanced Testing

### Dry Run Mode (Default)

The upload config test runs in "dry run" mode by default, which:
- Tests selectors without submitting forms
- Safe to run multiple times
- Doesn't create actual batches

### No Dry Run Mode (⚠️ Use with Caution)

To actually submit forms and test the full flow:

```bash
python tests/test_upload_config.py --config config/upload_config.json --no-dry-run
```

**Warning**: This will create actual batch entries on CardDealerPro!

---

## Headless Mode

Run tests without opening a visible browser window:

```bash
python tests/test_login_navigation.py --config config/upload_config.json --headless
python tests/test_upload_config.py --config config/upload_config.json --headless
```

**Note**: Image rotation test doesn't use a browser, so no headless option needed.

---

## After All Tests Pass

Once all three tests pass successfully:

1. **Review your configuration** one final time
2. **Prepare a small test batch** (5-10 images)
3. **Run the full workflow**:
   ```bash
   python scripts/image_upload_workflow.py --config config/upload_config.json
   ```
4. **Monitor the console output** for each step
5. **Manually verify** images at the inspector view
6. **Scale to larger batches** once confident

---

## Troubleshooting Tips

### Test 1 Fails (Image Rotation)
- Problem: "No images found"
- Solution: Verify folder path and file extensions

### Test 2 Fails (Login)
- Problem: "Login failed"
- Solutions:
  - Check `config/.env` has correct credentials
  - Verify `username_input`, `password_input`, `login_button` selectors
  - Try manual login in browser to confirm credentials

### Test 3 Fails (Upload Config)
- Problem: "Element not found"
- Solutions:
  - Use Chrome DevTools to find correct selector (F12 → Inspect)
  - Update selector in config.json
  - Test selector in browser console
  - See `docs/SELECTOR_GUIDE.md` for detailed instructions

### All Tests Pass But Full Workflow Fails
- Some elements only appear during actual workflow
- Run full workflow with small batch to identify issue
- Check `docs/USAGE.md` for workflow-specific troubleshooting

---

## Quick Reference

| Test | Time | Purpose | Command |
|------|------|---------|---------|
| Image Rotation | 5 min | Verify EXIF rotation | `python tests/test_image_rotation.py /path` |
| Login & Nav | 2 min | Verify credentials | `python tests/test_login_navigation.py --config X` |
| Upload Config | 5 min | Verify selectors | `python tests/test_upload_config.py --config X` |

**Total testing time**: ~12 minutes

**Recommended frequency**: Run tests after any configuration change

---

## Next Steps

- ✅ All tests passed? → Run full workflow with small batch
- ❌ Tests failing? → See troubleshooting sections above
- 📚 Need more help? → See `docs/QUICKSTART.md`, `docs/SELECTOR_GUIDE.md`, `docs/USAGE.md`
