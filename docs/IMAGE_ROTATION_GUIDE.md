# Image Rotation Guide

This project performs image rotation inline as the first step of the workflow. Rotation is based on filename patterns and is applied by setting the EXIF Orientation tag.

## How It Works

- Files with "front" in the filename → EXIF Orientation `8` (270° clockwise)
- Files with "back" in the filename → EXIF Orientation `6` (90° clockwise)
- Files without either substring are left unchanged

Rotation is applied in-place using Pillow by updating EXIF tag `0x0112` (Orientation). No copies are created.

## Supported Formats

The workflow scans the batch folder and processes common formats:
- `.jpg`, `.jpeg`, `.png`, `.tiff`, `.tif`, `.bmp`

Files not matching these extensions are ignored.

## Output and Metrics

During rotation, the console shows:
- Total files discovered
- Counts for Front, Back, Skipped, and Errors
- Elapsed time for the rotation step

Errors on individual files are logged but do not stop the workflow.

## File Naming Tips

- Ensure each card image filename contains either `front` or `back` (case-insensitive):
	- `card-001-front.jpg`
	- `card-001-back.jpg`
- Files without these tokens will be skipped for rotation (still uploaded if present).

## Troubleshooting

- "No image files found": Verify the folder path and supported extensions
- "Image folder not found": Check `default_images_path` and `--folder` argument
- An image repeatedly errors: Try opening and re-saving the image; verify write permissions

## Advanced Notes

- Rotation updates EXIF metadata rather than rasterizing a transformed copy. Many modern pipelines respect EXIF orientation.
- If a downstream tool ignores EXIF orientation, consider pre-rotating the pixels externally before running the workflow.

## Standalone Tool (Optional)

You can run rotation without the full workflow:

```zsh
python3 scripts/rotate_images.py /path/to/folder
```

This will print a summary table with counts for Front, Back, Skipped, and Errors.

