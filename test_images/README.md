# Test Images Folder

This folder is for testing the image rotation functionality before running the full workflow.

## Usage

1. Place sample images here for testing
2. Run the image rotation test:
   ```bash
   python tests/test_image_rotation.py test_images/
   ```

## What to Test

- Different image formats (.jpg, .png, .webp, .heic)
- Images with different EXIF orientations
- Images with no EXIF data
- Small batch of images (5-10) before processing large batches

## Notes

- This folder is gitignored (won't be committed)
- Rotated images will be created in `test_images/rotated_images/` subfolder
- Use this to verify rotation works correctly before uploading to production
