"""
Global configuration constants for CardDealerPro image upload automation.

USER NOTE: These constants can be customized to match your specific needs.
Most users won't need to modify these defaults unless experiencing issues.
"""

# =============================================================================
# IMAGE PROCESSING SETTINGS
# =============================================================================

# Supported image formats for upload
# USER NOTE: Add or remove formats based on CardDealerPro's requirements
IMAGE_SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp']

# EXIF orientation tag
EXIF_ORIENTATION_TAG = 274

# =============================================================================
# SELENIUM WEBDRIVER SETTINGS
# =============================================================================

# Browser to use for automation
# USER NOTE: Brave browser is used by default to avoid Chrome navigation issues
# To switch back to Chrome, comment out BRAVE_BROWSER_PATH in image_upload_workflow.py
SELENIUM_WEBDRIVER = 'brave'

# Run browser in headless mode (no visible window)
# USER NOTE: Set to True for production runs, False for debugging
SELENIUM_HEADLESS = False

# Maximum time to wait for elements to appear (seconds)
# USER NOTE: Increase if you have slow internet or the website is slow
SELENIUM_TIMEOUT = 15

# Maximum number of login attempts before giving up
# USER NOTE: Increase if experiencing intermittent login issues
MAX_LOGIN_RETRIES = 1

# =============================================================================
# BATCH ID EXTRACTION
# =============================================================================

# Regex pattern to extract batch_id from URL
# USER NOTE: Update this if CardDealerPro changes their URL structure
# Current format: /batches/{batch_id}/add/types
BATCH_ID_REGEX = r'/batches/([^/]+)/add'

# Fallback CSS selectors to try if URL regex fails
# USER NOTE: Add more selectors if you discover additional ways to find batch_id
BATCH_ID_FALLBACK_SELECTORS = [
    'input[name="batch_id"]',
    '[data-batch-id]',
    '.batch-info [data-id]',
    '#batch_id'
]
