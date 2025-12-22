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
IMAGE_SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.webp', '.heic']

# EXIF orientation tag values and their meanings
# Reference: https://exiftool.org/TagNames/EXIF.html
EXIF_ORIENTATION_TAG = 274
EXIF_ORIENTATION_CODES = {
    1: "Normal",
    2: "Mirrored horizontally",
    3: "Rotated 180°",
    4: "Mirrored vertically",
    5: "Mirrored horizontally and rotated 270° CW",
    6: "Rotated 90° CW",
    7: "Mirrored horizontally and rotated 90° CW",
    8: "Rotated 270° CW"
}

# =============================================================================
# SELENIUM WEBDRIVER SETTINGS
# =============================================================================

# Browser to use for automation
# USER NOTE: Currently only 'chrome' is supported
SELENIUM_WEBDRIVER = 'chrome'

# Run browser in headless mode (no visible window)
# USER NOTE: Set to True for production runs, False for debugging
SELENIUM_HEADLESS = False

# Maximum time to wait for elements to appear (seconds)
# USER NOTE: Increase if you have slow internet or the website is slow
SELENIUM_TIMEOUT = 30

# Maximum number of login attempts before giving up
# USER NOTE: Increase if experiencing intermittent login issues
MAX_LOGIN_RETRIES = 3

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

# =============================================================================
# VALIDATION SETTINGS
# =============================================================================

# Tolerance for image count mismatch (0 = exact match required)
# USER NOTE: Keep at 0 unless you want to allow some upload failures
IMAGE_COUNT_TOLERANCE = 0

# =============================================================================
# LOGGING AND OUTPUT
# =============================================================================

# Directory for log files (relative to project root)
LOG_DIR = 'logs'

# Directory name for rotated images (created in image folder)
ROTATED_IMAGES_DIR = 'rotated_images'
