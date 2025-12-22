# Image Rotation Troubleshooting Guide

This guide helps you understand and fix image rotation issues.

## 🔍 Diagnosing Image Rotation Issues

### Step 1: Run the Diagnostic Tool

```bash
python tests/diagnose_image_exif.py test_images/
```

This shows you:
- Image dimensions (width x height)
- EXIF orientation value (1-8)
- Whether EXIF data exists
- Why images might be skipped

---

## 📊 Understanding EXIF Orientation

### EXIF Orientation Values

| Value | Meaning | Action Needed |
|-------|---------|---------------|
| 1 | Normal (0°) | No rotation |
| 3 | Rotated 180° | Rotate 180° |
| 6 | Rotated 90° CW | Rotate 90° CW |
| 8 | Rotated 270° CW (90° CCW) | Rotate 270° CW |

### How Images Get Rotated

**Method 1: EXIF Tag Only** (Common Problem!)
- Many editors (Preview, Photos, etc.) just change EXIF tag
- Image pixels remain unchanged
- Displays correctly in apps that read EXIF
- But appears wrong in apps that ignore EXIF (like some web browsers)

**Method 2: Pixel Rotation + EXIF Update** (Correct Way)
- Image pixels are physically rotated
- EXIF tag is set to 1 (normal)
- Displays correctly everywhere
- This is what you want!

**Method 3: Pixel Rotation Only** (EXIF Stripped)
- Image pixels are rotated
- But EXIF data is removed
- Can't auto-detect rotation
- Manual rotation needed

---

## 🛠️ Common Scenarios & Solutions

### Scenario 1: All Images Show EXIF=1 But Look Rotated

**What happened:**
- Your editor rotated the view but didn't rotate the actual pixels
- Common with macOS Preview, Photos app, or web-based editors

**Solution A: Use Force EXIF Mode** (Easiest)
```bash
python tests/test_image_rotation.py test_images/ --force-exif
```

This applies the EXIF rotation to the actual pixel data.

**Solution B: Use ImageMagick** (Alternative)
```bash
# Install ImageMagick
brew install imagemagick  # macOS
# or: sudo apt-get install imagemagick  # Linux

# Auto-orient images (applies EXIF to pixels)
mogrify -auto-orient test_images/*.jpg

# Then run normal rotation test
python tests/test_image_rotation.py test_images/
```

**Solution C: Use exiftool to Add Proper EXIF**
```bash
# Install exiftool
brew install exiftool  # macOS

# Manually set orientation (example: rotate 90° CW)
exiftool -Orientation=6 test_images/*.jpg

# Then run normal rotation test
python tests/test_image_rotation.py test_images/
```

### Scenario 2: No EXIF Data Found

**What happened:**
- EXIF data was stripped by compression tool, web uploader, or editor
- Common with web-based image editors or aggressive compression

**Solution:**
1. **Prevention**: Use tools that preserve EXIF
   - Adobe Bridge, Lightroom
   - Native camera apps
   - Avoid web-based compressors

2. **Fix existing images**: Manually rotate to correct orientation
   ```bash
   # Use ImageMagick to rotate without EXIF
   mogrify -rotate 90 test_images/*.jpg  # Rotate 90° CW
   mogrify -rotate 180 test_images/*.jpg # Rotate 180°
   mogrify -rotate 270 test_images/*.jpg # Rotate 270° CW
   ```

3. **Or add EXIF manually**:
   ```bash
   exiftool -Orientation=6 test_images/*.jpg  # 6 = 90° CW
   ```

### Scenario 3: Mixed Orientations (Some Work, Some Don't)

**Diagnosis:**
```bash
python tests/diagnose_image_exif.py test_images/
```

Look for images with:
- EXIF=1 but visually rotated → Use --force-exif
- No EXIF → Manually fix or add EXIF
- EXIF != 1 → Should work automatically

**Solution:**
Process in batches:
```bash
# First, fix images with proper EXIF (works automatically)
python tests/test_image_rotation.py test_images/

# Then, manually handle images with no EXIF or EXIF=1
python tests/test_image_rotation.py test_images/ --force-exif
```

---

## 🚀 Workflow Recommendations

### For New Images (Before Rotation Issues)

1. **Use cameras/phones directly** - They set EXIF correctly
2. **Use professional tools** - Adobe Bridge, Lightroom preserve EXIF
3. **Avoid web editors** - They often strip metadata
4. **Test early** - Run diagnostic on small batch first

### For Existing Images (Fixing Issues)

1. **Diagnose first**:
   ```bash
   python tests/diagnose_image_exif.py test_images/
   ```

2. **Choose fix strategy based on results**:
   - **EXIF != 1**: Normal rotation works
   - **EXIF = 1 but rotated**: Use `--force-exif`
   - **No EXIF**: Manual rotation or add EXIF with exiftool

3. **Test rotation**:
   ```bash
   python tests/test_image_rotation.py test_images/
   # or with force flag
   python tests/test_image_rotation.py test_images/ --force-exif
   ```

4. **Verify results**:
   - Check `test_images/rotated_images/` folder
   - Open images to confirm correct orientation
   - If wrong, try different approach

---

## 🔧 Tool Installation

### ImageMagick (Image Processing)

**macOS:**
```bash
brew install imagemagick
```

**Linux:**
```bash
sudo apt-get install imagemagick
```

**Windows:**
Download from: https://imagemagick.org/script/download.php

### exiftool (EXIF Metadata Editor)

**macOS:**
```bash
brew install exiftool
```

**Linux:**
```bash
sudo apt-get install libimage-exiftool-perl
```

**Windows:**
Download from: https://exiftool.org/

---

## 📝 Quick Reference Commands

```bash
# Diagnose EXIF issues
python tests/diagnose_image_exif.py test_images/

# Test rotation (normal mode)
python tests/test_image_rotation.py test_images/

# Test rotation (force EXIF to pixels)
python tests/test_image_rotation.py test_images/ --force-exif

# ImageMagick: Auto-orient (apply EXIF to pixels)
mogrify -auto-orient test_images/*.jpg

# ImageMagick: Manual rotation
mogrify -rotate 90 test_images/*.jpg   # 90° CW
mogrify -rotate 180 test_images/*.jpg  # 180°
mogrify -rotate 270 test_images/*.jpg  # 270° CW

# exiftool: Set EXIF orientation
exiftool -Orientation=6 test_images/*.jpg  # 6 = 90° CW
exiftool -Orientation=3 test_images/*.jpg  # 3 = 180°
exiftool -Orientation=8 test_images/*.jpg  # 8 = 270° CW

# exiftool: View EXIF orientation
exiftool -Orientation test_images/image.jpg
```

---

## ❓ FAQ

**Q: Why does my Mac Preview show images correctly but they're wrong when uploaded?**

A: Preview reads EXIF orientation tags and rotates the display automatically. But if you "rotate" in Preview, it often just changes the EXIF tag without rotating the actual pixels. Use `--force-exif` flag to fix this.

**Q: Can I batch process hundreds of images?**

A: Yes! Both the rotation script and ImageMagick can handle large batches. Process in chunks of 100-200 for progress monitoring.

**Q: Will rotation reduce image quality?**

A: For JPEGs, the script creates new copies at 95% quality. For lossless rotation, use ImageMagick's `-auto-orient` which doesn't re-encode.

**Q: What if --force-exif doesn't work?**

A: This means your images truly have no rotation information. You'll need to manually rotate them using ImageMagick or another tool.

**Q: Should I use --force-exif by default?**

A: No, only use it when images appear rotated despite EXIF=1. For properly tagged images, normal mode is faster and safer.

---

## 🎯 Best Practices

1. ✅ **Always diagnose first** before processing large batches
2. ✅ **Test with 5-10 images** before full batch
3. ✅ **Keep backups** of original images
4. ✅ **Use professional tools** that preserve EXIF
5. ✅ **Check rotated_images/** folder visually before uploading
6. ❌ **Don't use web-based compressors** that strip EXIF
7. ❌ **Don't assume all images need same treatment**
8. ❌ **Don't skip the diagnostic step**

---

## 📞 Still Having Issues?

If images still don't rotate correctly:

1. Share diagnostic output:
   ```bash
   python tests/diagnose_image_exif.py test_images/ > diagnosis.txt
   ```

2. Try manual rotation:
   ```bash
   mogrify -rotate 90 test_images/*.jpg
   ```

3. Check image format is supported (.jpg, .png, .webp, .heic)

4. Verify images open correctly in other applications

5. Consider re-exporting from original source with proper settings
