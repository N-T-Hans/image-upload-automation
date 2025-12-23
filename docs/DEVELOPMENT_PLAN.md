# Development Plan

Implementation roadmap and development guidelines for the CardDealerPro Image Upload Automation project.

## Project Overview

A Python-based Selenium automation tool for batch uploading images to CardDealerPro with automatic EXIF-based rotation.

**Core Technologies:**
- Python 3.8+
- Selenium WebDriver
- Pillow (PIL) for image processing
- Rich for console output
- python-dotenv for configuration

## Implementation Phases

### Phase 1: Project Foundation ✅ COMPLETE

**Objective:** Set up project structure and core configuration

**Tasks:**
- [x] Create directory structure (tools/, scripts/, config_templates/, docs/)
- [x] Define `.gitignore` (exclude .env, credentials, rotated images)
- [x] Create `requirements.txt` with pinned versions
- [x] Create `.env.example` template
- [x] Define global constants in `config.py`
- [x] Write `README.md` with project overview
- script selects them in finder, manually rotate (command +r 3 times on front, command +r 1 time on back)
- use folder name as batch name when creating a new batch
- csv modification - export does not allow duplicate card. Dylan has to manually create a concat with the name/sku then match the front/back photos with the generated row, and the manually generated row



**Deliverables:**
- Clean project structure
- Dependency management
- Configuration framework

**Testing:**
- Verify virtual environment creation
- Test `pip install -r requirements.txt`
- Validate `.env.example` template

---

### Phase 2: Image Processing Module ✅ COMPLETE

**Objective:** Implement EXIF-based image rotation

**Tasks:**
- [x] Create `tools/image_tools.py`
- [x] Implement `ImageRotationHandler` class
- [x] EXIF orientation tag reading (tag 274)
- [x] Rotation logic for codes 1-8
- [x] In-place rotation for non-JPEG
- [x] Copy-based rotation for JPEG (quality preservation)
- [x] Progress bar with Rich
- [x] Error handling per image
- [x] Summary statistics

**Key Features:**
- Supports .jpg, .jpeg, .png, .webp, .heic
- Creates `rotated_images/` subfolder for JPEG copies
- Continues on partial failures
- Detailed logging

**Testing:**
```bash
# Test with sample images
python tools/image_tools.py test_images/

# Verify:
# - Rotated images created correctly
# - Original JPEGs untouched
# - Progress bar displays
# - Summary accurate
```

**Success Criteria:**
- [ ] Correctly rotates images with EXIF orientation 3, 6, 8
- [ ] Creates copies for JPEGs
- [ ] Handles missing EXIF gracefully
- [ ] Reports failures without crashing

---

### Phase 3: Web Automation Utilities ✅ COMPLETE

**Objective:** Build reusable Selenium automation classes

**Tasks:**
- [x] Create `tools/web_automation_tools.py`
- [x] Implement `ElementWaiter` class
  - [x] Explicit wait patterns
  - [x] Visibility, clickability, URL change waits
  - [x] Timeout handling
- [x] Implement `LoginHandler` class
  - [x] Credential loading from env
  - [x] Form filling
  - [x] URL verification
  - [x] Retry logic (up to 3 attempts)
- [x] Implement `FormNavigator` class
  - [x] URL navigation
  - [x] Page load detection
  - [x] Batch ID extraction (regex + fallback)
- [x] Implement `FormSubmitter` class
  - [x] Text input filling
  - [x] Dropdown selection
  - [x] File upload (multiple files)
  - [x] Button clicking with retry
  - [x] Stale element handling

**Key Design Decisions:**
- Explicit waits (not implicit) for reliability
- Rich console output for user feedback
- Detailed error messages with action items
- Retry logic for transient failures

**Testing:**
```python
# Individual class testing
from tools.web_automation_tools import ElementWaiter, LoginHandler

# Test with live website (manual)
# Verify each method works independently
```

**Success Criteria:**
- [ ] Can reliably wait for elements
- [ ] Handles stale elements gracefully
- [ ] Login succeeds with valid credentials
- [ ] Batch ID extraction works for current URL pattern

---

### Phase 4: Workflow Orchestrator ✅ COMPLETE

**Objective:** Implement end-to-end workflow automation

**Tasks:**
- [x] Create `scripts/image_upload_workflow.py`
- [x] Implement `CardDealerProWorkflow` class
- [x] Configuration loading and validation
- [x] WebDriver setup with webdriver-manager
- [x] Sequential workflow execution
  - [x] Step 1: Image rotation
  - [x] Step 2: Login
  - [x] Steps 3-8: Batch creation and form filling
  - [x] Step 9: Batch ID extraction
  - [x] Steps 10-13: Image upload
  - [x] Step 14: Inspector view (stop point)
- [x] Rich console output
  - [x] Progress tracking
  - [x] Status panels
  - [x] Summary table
- [x] Error handling
  - [x] Graceful failures
  - [x] Cleanup in finally block
- [x] CLI argument parsing

**Key Features:**
- Stops at inspector view for manual validation
- Continues on partial image rotation failures
- Exits with error code on critical failures
- Keeps browser open for inspection

**Testing:**
```bash
# End-to-end test (requires valid credentials and config)
python scripts/image_upload_workflow.py --config test_batch.json

# Verify:
# - All 14 stages execute
# - Browser automation works
# - Images upload successfully
# - Stops at inspector view
```

**Success Criteria:**
- [ ] Complete workflow executes without intervention
- [ ] Images upload correctly
- [ ] Console output is clear and helpful
- [ ] Manual validation workflow works

---

### Phase 5: Configuration Templates ✅ COMPLETE

**Objective:** Create user-friendly configuration templates

**Tasks:**
- [x] Create `config_templates/upload_config.example.json`
- [x] Add inline comments for all fields
- [x] Mark all user-configurable fields clearly
- [x] Provide examples for each field type
- [x] Document selector discovery process
- [x] Include optional fields section

**Key Features:**
- Clear `<< USER: ... >>` markers
- Inline documentation
- Example values
- Comments explaining each field

**Testing:**
```bash
# Validate JSON syntax
python -m json.tool config_templates/upload_config.example.json

# Verify all fields are documented
# Check that examples are clear
```

**Success Criteria:**
- [ ] All required fields documented
- [ ] Examples are realistic
- [ ] New users can understand without external docs

---

### Phase 6: Documentation ✅ COMPLETE

**Objective:** Create comprehensive user documentation

**Tasks:**
- [x] Create `docs/QUICKSTART.md`
  - [x] Prerequisites
  - [x] Installation steps
  - [x] First run guide
  - [x] Common issues
- [x] Create `docs/SELECTOR_GUIDE.md`
  - [x] What are CSS selectors
  - [x] Chrome DevTools tutorial
  - [x] Step-by-step selector discovery
  - [x] Testing selectors
  - [x] Common patterns
- [x] Create `docs/USAGE.md`
  - [x] Command reference
  - [x] Workflow stages explanation
  - [x] Error messages reference
  - [x] Troubleshooting guide
- [x] Create `docs/DEVELOPMENT_PLAN.md` (this file)
- [x] Create `docs/FUTURE_ENHANCEMENTS.md`

**Success Criteria:**
- [ ] New user can set up without help
- [ ] Selector guide is clear and actionable
- [ ] Error messages are documented
- [ ] Troubleshooting covers common issues

---

## Testing Strategy

### Unit Testing (Future)

Not currently implemented, but recommended:

```python
# tests/test_image_tools.py
def test_exif_rotation():
    """Test EXIF orientation detection and rotation"""
    
# tests/test_web_automation.py
def test_element_waiter():
    """Test explicit wait patterns"""
```

### Integration Testing

**Manual testing required:**

1. **Image Rotation Module**
   - Test with images of each EXIF orientation (1-8)
   - Test with missing EXIF data
   - Test with various formats (.jpg, .png, .webp)
   - Verify JPEG quality preservation

2. **Web Automation**
   - Test login with valid credentials
   - Test login failure scenarios
   - Test form filling with various field types
   - Test file upload with different counts

3. **End-to-End Workflow**
   - Complete workflow with small batch (5 images)
   - Complete workflow with medium batch (50 images)
   - Test with different batch types/settings
   - Test optional details (filled and empty)

### Test Data Requirements

- Sample images with different EXIF orientations
- Test CardDealerPro account (not production)
- Multiple batch configurations
- Known-good CSS selectors

---

## Common Development Issues

### Issue: Selectors Stop Working

**Cause:** Website HTML structure changed

**Solution:**
1. Inspect website with DevTools
2. Find new selectors
3. Update `config_templates/upload_config.example.json`
4. Document changes
5. Update `BATCH_ID_REGEX` if URL pattern changed

### Issue: Login Fails Intermittently

**Cause:** 
- Rate limiting
- CAPTCHA introduced
- Session conflicts

**Solution:**
1. Add exponential backoff to retry logic
2. Implement CAPTCHA detection
3. Clear cookies between runs
4. Add delay after failed attempts

### Issue: File Upload Times Out

**Cause:**
- Large batch size
- Slow internet
- Timeout too short

**Solution:**
1. Increase `SELENIUM_TIMEOUT` in `config.py`
2. Add progress monitoring during upload
3. Consider chunking large batches
4. Add retry logic for upload stage

### Issue: Stale Element Errors

**Cause:** Page updates dynamically after form interaction

**Solution:**
- Already implemented: retry logic in `FormSubmitter.click_button()`
- If persistent: add longer waits after button clicks
- Check if page structure changed

---

## Code Style Guidelines

### Python Style

- Follow PEP 8
- Use type hints where helpful
- Docstrings for all classes and public methods
- Inline comments for complex logic
- `snake_case` for functions/variables
- `PascalCase` for classes

### Documentation Style

- Clear and concise
- Step-by-step instructions
- Examples for everything
- Troubleshooting sections
- Visual aids where helpful

### Error Messages

**Template:**
```python
console.print("[red]✗ {what_failed}: {error}[/red]")
console.print("[yellow]USER ACTION REQUIRED:[/yellow]")
console.print("  1. {first_thing_to_check}")
console.print("  2. {second_thing_to_check}")
console.print("  3. {where_to_find_help}")
```

---

## Maintenance Plan

### Regular Maintenance

**Monthly:**
- Check if website structure changed
- Test with latest Chrome version
- Update dependencies if security issues
- Review and close GitHub issues

**Quarterly:**
- Test full workflow end-to-end
- Update documentation if needed
- Review error logs for patterns
- Consider new feature requests

### Version Updates

**When updating dependencies:**
```bash
# Test thoroughly before updating
pip install --upgrade selenium
pip install --upgrade Pillow
# ... run full test suite
```

**Breaking changes to watch:**
- Selenium API changes (v4.x to v5.x)
- Pillow API changes
- Chrome WebDriver protocol changes

---

## Contributing Guidelines

### Adding New Features

1. **Plan first** - Document in this file
2. **Implement** - Follow code style
3. **Test** - Manual testing required
4. **Document** - Update relevant docs
5. **Commit** - Clear commit messages

### Modifying Existing Code

1. **Understand impact** - What might break?
2. **Test before and after** - Verify no regressions
3. **Update docs** - Keep documentation current
4. **Consider users** - Will this break existing configs?

---

## Project Metrics

### Current Status

- **Lines of Code:** ~2000
- **Modules:** 3 (image_tools, web_automation_tools, workflow)
- **Documentation Pages:** 5
- **Configuration Complexity:** Medium (requires manual selector discovery)

### Success Metrics

- **Setup Time:** <30 minutes for new users
- **Workflow Success Rate:** >90% with valid selectors
- **Time Savings:** ~15 minutes per batch vs manual upload
- **User Satisfaction:** Clear error messages, good documentation

---

## Future Development

See [FUTURE_ENHANCEMENTS.md](FUTURE_ENHANCEMENTS.md) for planned features and stretch goals.

### Priority Queue

1. **High Priority:**
   - Workflow resume capability
   - Automatic retry logic
   - Better batch ID extraction

2. **Medium Priority:**
   - Interactive field discovery
   - Batch state persistence
   - Upload validation

3. **Low Priority:**
   - GUI interface
   - Scheduled runs
   - Multi-browser support

---

## Questions and Decisions Log

### Q: Why not use a headless browser by default?

**A:** Users need to visually verify the workflow, especially at inspector view. Headless mode available via `--headless` flag.

### Q: Why stop at inspector view?

**A:** Manual validation is critical for ensuring uploads are correct. Automatic finalization risks publishing incorrect batches.

### Q: Why not auto-retry failed uploads?

**A:** User requested clear failure reporting without retries. Failed batches must be manually deleted and re-run.

### Q: Why store credentials in .env instead of config.json?

**A:** Security best practice. .env is gitignored, config.json might be committed.

### Q: Why use CSS selectors instead of XPath?

**A:** CSS selectors are more readable, faster, and easier for users to understand. XPath can be used if needed.

---

**Last Updated:** December 2025
**Project Status:** ✅ Complete - Ready for use
**Next Milestone:** User testing and feedback collection
