# Future Enhancements

Planned features and improvements for future development.

## Overview

This document tracks features that were considered during initial development but deferred to future releases. These enhancements would improve usability, reliability, and functionality.

---

## High Priority Features

### 1. Workflow Resume Capability

**Problem:** If workflow fails mid-execution (e.g., after batch creation), user must start over or manually complete the upload.

**Proposed Solution:**

Add `--resume-batch-id` flag to continue from a specific step:

```bash
python scripts/image_upload_workflow.py \
  --config my_batch.json \
  --resume-batch-id ABC123 \
  --resume-step upload
```

**Implementation Details:**
- Save workflow state to temporary file after each major step
- Detect interrupted workflows and offer resume option
- Skip completed steps (rotation, login, batch creation)
- Resume from specified step with batch_id

**Benefits:**
- Saves time on failed runs
- Reduces frustration with network issues
- Allows manual intervention mid-workflow

**Effort:** Medium (2-3 days)

**Status:** 🔴 Not Started

---

### 2. Automatic Retry Logic

**Problem:** Transient failures (network glitches, slow page loads) cause entire workflow to fail.

**Proposed Solution:**

Implement configurable retry logic for all critical operations:

```python
# config.py additions
RETRY_ATTEMPTS = {
    'login': 3,
    'navigation': 2,
    'form_submission': 2,
    'upload': 3
}

RETRY_DELAY = 2  # seconds between retries
RETRY_BACKOFF = 1.5  # exponential backoff multiplier
```

**Implementation Details:**
- Decorator pattern for automatic retries
- Exponential backoff between attempts
- Different retry counts per operation type
- Log each retry attempt

**Benefits:**
- More resilient to transient failures
- Reduces manual re-runs
- Better user experience

**Effort:** Medium (2-3 days)

**Status:** 🔴 Not Started

---

### 3. Better Batch ID Extraction

**Problem:** Current regex and fallback selectors may not work if URL structure changes.

**Proposed Solution:**

Multiple extraction strategies with priority order:

1. **URL regex** (fastest, current method)
2. **API call** - Check if API endpoint returns batch_id
3. **JavaScript extraction** - Execute JS to find batch_id in page state
4. **Breadcrumb parsing** - Extract from navigation breadcrumbs
5. **User prompt** - Ask user to manually enter batch_id

**Implementation Details:**
```python
class ImprovedBatchIdExtractor:
    def extract(self):
        strategies = [
            self._from_url_regex,
            self._from_api,
            self._from_javascript,
            self._from_breadcrumbs,
            self._from_user_input
        ]
        
        for strategy in strategies:
            batch_id = strategy()
            if batch_id:
                return batch_id
        
        raise Exception("Could not extract batch_id")
```

**Benefits:**
- More robust to website changes
- Fallback options increase reliability
- User can always provide batch_id manually

**Effort:** Small (1-2 days)

**Status:** 🔴 Not Started

---

## Medium Priority Features

### 4. Interactive Field Discovery Helper

**Problem:** Users struggle to find CSS selectors for form fields.

**Proposed Solution:**

Add discovery mode that helps identify selectors:

```bash
python scripts/discover_selectors.py --url https://carddealerpro.com/login
```

**Features:**
- Opens browser and navigates to URL
- Allows user to click elements
- Displays selector options for each element
- Tests selectors automatically
- Generates config.json with found selectors

**Implementation Details:**
- Uses Selenium to open browser
- JavaScript injection to highlight hovered elements
- Multiple selector strategies (ID, name, class, attributes)
- Validation that selector is unique
- Export to JSON config format

**Benefits:**
- Dramatically easier for non-technical users
- Reduces setup time from 30 minutes to 5 minutes
- Fewer incorrect selectors

**Effort:** Large (5-7 days)

**Status:** 🔴 Not Started

---

### 5. Batch State Persistence

**Problem:** No record of completed batches or workflow history.

**Proposed Solution:**

Save workflow state to SQLite database:

```python
# Database schema
batches = {
    'id': 'ABC123',
    'config_file': 'my_batch.json',
    'started_at': '2024-12-20 10:30:00',
    'completed_at': '2024-12-20 10:45:00',
    'status': 'completed',  # pending, completed, failed
    'images_uploaded': 45,
    'error_message': None
}
```

**Features:**
- Track all workflow runs
- Query batch history
- Resume interrupted batches
- Generate usage reports

**Implementation Details:**
- SQLite database in project directory
- Models for batches, steps, errors
- CLI commands to query history
- Auto-cleanup of old records

**Benefits:**
- Track what's been uploaded
- Audit trail for batches
- Easy to find failed batches
- Resume capability (ties to #1)

**Effort:** Medium (3-4 days)

**Status:** 🔴 Not Started

---

### 6. Upload Validation

**Problem:** Workflow assumes upload succeeded but doesn't verify image count.

**Proposed Solution:**

Validate uploads at inspector view:

```python
def validate_upload(self):
    """
    Verify uploaded image count matches expected count.
    
    Strategies:
    1. Parse count from text element (e.g., "45 images")
    2. Count image thumbnails in DOM
    3. Check for error messages
    """
    expected = len(self.rotated_image_paths)
    
    # Try text element
    count_text = self.get_element_text('image_count_display')
    actual = self.parse_count(count_text)
    
    # Fall back to counting thumbnails
    if actual is None:
        thumbnails = self.find_elements('image_thumbnail')
        actual = len(thumbnails)
    
    if actual != expected:
        self.handle_mismatch(expected, actual)
```

**Features:**
- Configurable validation strategies
- Tolerance for minor mismatches (±1)
- Detailed mismatch reporting
- Option to retry upload
- Screenshot capture for failed validations

**Benefits:**
- Catch upload failures automatically
- Confidence in upload success
- Early detection of issues

**Effort:** Small (1-2 days)

**Status:** 🔴 Not Started (depends on selector configuration)

---

## Low Priority Features

### 7. GUI Interface

**Problem:** Command-line interface not friendly for all users.

**Proposed Solution:**

Desktop GUI application using PyQt or Tkinter:

**Features:**
- Visual config editor (no JSON editing)
- Interactive selector picker
- Live workflow progress visualization
- Batch history browser
- Settings manager

**Benefits:**
- Accessible to non-technical users
- Visual feedback more intuitive
- Easier to manage multiple configs

**Effort:** Very Large (2-3 weeks)

**Status:** 🔴 Not Started

---

### 8. Scheduled Batch Runs

**Problem:** Need to manually trigger each batch upload.

**Proposed Solution:**

Add scheduling capability:

```bash
python scripts/schedule_batch.py \
  --config my_batch.json \
  --time "2024-12-21 02:00:00" \
  --repeat weekly
```

**Features:**
- Schedule batch uploads
- Recurring schedules (daily, weekly, monthly)
- Email notifications on completion/failure
- Queue management

**Implementation:**
- Uses `schedule` library or cron jobs
- Daemon process for scheduled runs
- Log file for unattended runs

**Benefits:**
- Run during off-peak hours
- Automated workflow
- No manual intervention needed

**Effort:** Medium (3-4 days)

**Status:** 🔴 Not Started

---

### 9. Multi-Browser Support

**Problem:** Only works with Chrome.

**Proposed Solution:**

Support Firefox, Edge, Safari:

```python
# config.py
SELENIUM_WEBDRIVER = 'chrome'  # or 'firefox', 'edge', 'safari'
```

**Implementation:**
- Abstract WebDriver initialization
- Browser-specific selectors if needed
- Test on each browser

**Benefits:**
- Works if Chrome unavailable
- User preference flexibility

**Effort:** Small (1-2 days)

**Status:** 🔴 Not Started

---

### 10. Headless Mode Improvements

**Problem:** Headless mode has limitations for debugging.

**Proposed Solution:**

Enhanced headless mode:

- Automatic screenshot capture at each step
- Video recording of workflow
- DOM snapshots for debugging
- Better error reporting

**Benefits:**
- Debugging without visible browser
- Production logs more useful
- CI/CD integration possible

**Effort:** Small (1-2 days)

**Status:** 🔴 Not Started

---

## Stretch Goals

### 11. API Integration

**Problem:** Web scraping is fragile; API would be more reliable.

**Proposed Solution:**

If CardDealerPro provides an API:

- Replace Selenium with API calls
- Much faster execution
- More reliable
- No browser needed

**Status:** ⏸️ Waiting on API availability

---

### 12. Machine Learning for Element Detection

**Problem:** CSS selectors break when website changes.

**Proposed Solution:**

Train ML model to identify form elements:

- Computer vision to find fields
- Natural language to match field labels
- Auto-update selectors when website changes

**Benefits:**
- Self-healing selectors
- No manual updates needed

**Effort:** Very Large (1-2 months)

**Status:** 🔴 Research phase

---

### 13. Mobile App

**Problem:** Desktop-only solution.

**Proposed Solution:**

iOS/Android app for batch uploads:

- Take photos with phone camera
- Upload directly from mobile
- Push notifications on completion

**Effort:** Very Large (2-3 months)

**Status:** 🔴 Not Started

---

## Implementation Priority

Based on user impact and development effort:

### Phase 7 (Next Release)
1. Automatic Retry Logic (#2)
2. Better Batch ID Extraction (#3)
3. Upload Validation (#6)

### Phase 8 (Future)
4. Workflow Resume Capability (#1)
5. Interactive Field Discovery (#4)
6. Batch State Persistence (#5)

### Phase 9 (Long-term)
7. Headless Mode Improvements (#10)
8. Multi-Browser Support (#9)
9. GUI Interface (#7)

### Phase 10 (Stretch Goals)
10. Scheduled Batch Runs (#8)
11. API Integration (#11) - if available

---

## Feature Request Process

Have an idea for improvement?

1. **Check this document** - May already be planned
2. **Create an issue** with:
   - Clear description of problem
   - Proposed solution
   - Use cases
   - Impact on existing users
3. **Discuss feasibility** before implementation
4. **Document decision** here

---

## Declined Features

Features considered but decided against:

### Automatic Batch Finalization

**Reason:** User explicitly requested manual validation step. Auto-finalization risks publishing incorrect batches.

### CAPTCHA Solving

**Reason:** Ethically questionable, may violate terms of service. User should handle CAPTCHA manually.

### Parallel Batch Processing

**Reason:** Website likely rate-limits; parallel uploads could trigger blocking. Sequential is safer.

---

## Version Roadmap

### v1.0 (Current)
- ✅ Core workflow automation
- ✅ Image rotation
- ✅ Manual validation
- ✅ Basic error handling
- ✅ Configuration system
- ✅ Documentation

### v1.1 (Next)
- 🔵 Automatic retry logic
- 🔵 Better batch ID extraction
- 🔵 Upload validation

### v1.2 (Future)
- 🔵 Workflow resume
- 🔵 Interactive field discovery
- 🔵 Batch history

### v2.0 (Long-term)
- 🔵 GUI interface
- 🔵 Scheduled runs
- 🔵 Multi-browser support

---

**Last Updated:** December 2025  
**Next Review:** Q1 2026

**Legend:**
- 🔴 Not Started
- 🔵 Planned
- 🟡 In Progress
- 🟢 Complete
- ⏸️ On Hold
