"""
Image rotation handler for EXIF-based orientation correction.

This module provides functionality to read EXIF orientation metadata from images
and rotate them correctly for upload to CardDealerPro.

USER NOTE: This module automatically handles image rotation based on EXIF data.
No user configuration needed unless you want to modify supported formats in config.py
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple
from PIL import Image, ExifTags
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn

# Import configuration constants
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    IMAGE_SUPPORTED_FORMATS,
    EXIF_ORIENTATION_TAG,
    EXIF_ORIENTATION_CODES,
    ROTATED_IMAGES_DIR
)

console = Console()


class ImageRotationHandler:
    """
    Handles EXIF-based image rotation for batch uploads.
    
    This class processes images in a folder, reads their EXIF orientation data,
    and rotates them correctly. JPEG images are copied to preserve quality,
    while other formats are rotated in-place.
    
    USER NOTE: The handler will create a 'rotated_images' subfolder for JPEG copies.
    Original files are never modified for JPEGs to maintain image quality.
    """
    
    def __init__(self, image_folder: str):
        """
        Initialize the image rotation handler.
        
        Args:
            image_folder: Path to folder containing images to process
            
        Raises:
            ValueError: If folder doesn't exist or contains no valid images
            
        USER NOTE: Ensure your image_folder path is absolute or relative to
        where you run the script from.
        """
        self.image_folder = Path(image_folder).resolve()
        
        # Validate folder exists
        if not self.image_folder.exists():
            raise ValueError(f"Image folder does not exist: {self.image_folder}")
        
        if not self.image_folder.is_dir():
            raise ValueError(f"Path is not a directory: {self.image_folder}")
        
        # Create output directory for rotated JPEG copies
        self.rotated_folder = self.image_folder / ROTATED_IMAGES_DIR
        
        console.print(f"[cyan]Initialized ImageRotationHandler for:[/cyan] {self.image_folder}")
    
    def _is_supported_format(self, file_path: Path) -> bool:
        """
        Check if file has a supported image format.
        
        Args:
            file_path: Path to image file
            
        Returns:
            True if format is supported, False otherwise
        """
        return file_path.suffix.lower() in IMAGE_SUPPORTED_FORMATS
    
    def _read_exif_orientation(self, image: Image.Image) -> int:
        """
        Read EXIF orientation tag from image.
        
        EXIF orientation codes:
        1 = Normal (no rotation needed)
        2 = Mirrored horizontally
        3 = Rotated 180°
        4 = Mirrored vertically
        5 = Mirrored horizontally and rotated 270° CW
        6 = Rotated 90° CW
        7 = Mirrored horizontally and rotated 90° CW
        8 = Rotated 270° CW (or 90° CCW)
        
        Args:
            image: PIL Image object
            
        Returns:
            Orientation code (1-8), or 1 if no EXIF data found
            
        USER NOTE: If images appear rotated incorrectly after upload,
        they may lack EXIF data. Consider manually rotating them first.
        """
        try:
            # Get EXIF data from image
            exif = image._getexif()
            
            if exif is not None:
                # Look for orientation tag (274)
                orientation = exif.get(EXIF_ORIENTATION_TAG, 1)
                return orientation
        except (AttributeError, KeyError, IndexError):
            # No EXIF data available
            pass
        
        # Default: no rotation needed
        return 1
    
    def _apply_rotation(self, image: Image.Image, orientation: int) -> Image.Image:
        """
        Apply rotation transformation based on EXIF orientation code.
        
        Uses PIL's transpose method for lossless rotation when possible.
        
        Args:
            image: PIL Image object to rotate
            orientation: EXIF orientation code (1-8)
            
        Returns:
            Rotated image object
        """
        # Mapping of EXIF orientation codes to PIL transpose operations
        orientation_transforms = {
            1: None,  # Normal - no rotation
            2: Image.FLIP_LEFT_RIGHT,  # Mirrored horizontally
            3: Image.ROTATE_180,  # Rotated 180°
            4: Image.FLIP_TOP_BOTTOM,  # Mirrored vertically
            5: Image.TRANSPOSE,  # Mirrored horizontally + rotated 270° CW
            6: Image.ROTATE_270,  # Rotated 90° CW
            7: Image.TRANSVERSE,  # Mirrored horizontally + rotated 90° CW
            8: Image.ROTATE_90,  # Rotated 270° CW (90° CCW)
        }
        
        transform = orientation_transforms.get(orientation)
        
        if transform is not None:
            return image.transpose(transform)
        
        return image
    
    def _is_jpeg(self, file_path: Path) -> bool:
        """
        Check if file is a JPEG image.
        
        Args:
            file_path: Path to image file
            
        Returns:
            True if JPEG, False otherwise
        """
        return file_path.suffix.lower() in ['.jpg', '.jpeg']
    
    def rotate_images(self) -> Dict:
        """
        Process all images in the folder and rotate them based on EXIF data.
        
        Strategy:
        - JPEG files: Create rotated copies in 'rotated_images' subfolder
        - Other formats: Rotate in-place (overwrites original)
        
        Returns:
            Dictionary containing:
            - rotated_paths: List of paths to successfully rotated images
            - failed: List of {path, error} dicts for failed images
            - skipped: List of paths to images skipped (no rotation needed)
            - summary: {total, success, failed, skipped} counts
            
        USER NOTE: After running, use the images from rotated_paths for upload.
        Original JPEGs remain unchanged in the source folder.
        """
        rotated_paths = []
        failed = []
        skipped = []
        
        # Find all supported image files
        image_files = [
            f for f in self.image_folder.iterdir()
            if f.is_file() and self._is_supported_format(f)
        ]
        
        if not image_files:
            console.print(f"[yellow]⚠ No supported images found in {self.image_folder}[/yellow]")
            return {
                'rotated_paths': [],
                'failed': [],
                'skipped': [],
                'summary': {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0}
            }
        
        console.print(f"\n[cyan]Found {len(image_files)} images to process[/cyan]")
        
        # Process images with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("[cyan]Rotating images...", total=len(image_files))
            
            for img_path in image_files:
                try:
                    # Open image
                    with Image.open(img_path) as img:
                        # Read EXIF orientation
                        orientation = self._read_exif_orientation(img)
                        
                        # Check if rotation is needed
                        if orientation == 1:
                            # No rotation needed
                            skipped.append(str(img_path))
                            progress.update(task, advance=1, description=f"[dim]Skipped: {img_path.name}[/dim]")
                            continue
                        
                        # Apply rotation
                        rotated_img = self._apply_rotation(img, orientation)
                        
                        # Determine output path based on file type
                        if self._is_jpeg(img_path):
                            # JPEG: Save rotated copy to subfolder
                            self.rotated_folder.mkdir(exist_ok=True)
                            output_path = self.rotated_folder / img_path.name
                            
                            # Save with high quality
                            rotated_img.save(output_path, 'JPEG', quality=95, optimize=True)
                            rotated_paths.append(str(output_path))
                            
                            progress.update(
                                task, 
                                advance=1, 
                                description=f"[green]✓ Rotated (copy): {img_path.name}[/green]"
                            )
                        else:
                            # Other formats: Save in-place
                            rotated_img.save(img_path)
                            rotated_paths.append(str(img_path))
                            
                            progress.update(
                                task, 
                                advance=1, 
                                description=f"[green]✓ Rotated (in-place): {img_path.name}[/green]"
                            )
                
                except Exception as e:
                    # Log error and continue with other images
                    failed.append({
                        'path': str(img_path),
                        'error': str(e)
                    })
                    progress.update(task, advance=1, description=f"[red]✗ Failed: {img_path.name}[/red]")
        
        # Print summary
        summary = {
            'total': len(image_files),
            'success': len(rotated_paths),
            'failed': len(failed),
            'skipped': len(skipped)
        }
        
        console.print("\n[bold cyan]Image Rotation Summary:[/bold cyan]")
        console.print(f"  Total images: {summary['total']}")
        console.print(f"  [green]✓ Successfully rotated: {summary['success']}[/green]")
        console.print(f"  [dim]○ Skipped (no rotation needed): {summary['skipped']}[/dim]")
        console.print(f"  [red]✗ Failed: {summary['failed']}[/red]")
        
        if failed:
            console.print("\n[red]Failed images:[/red]")
            for fail in failed:
                console.print(f"  • {Path(fail['path']).name}: {fail['error']}")
        
        return {
            'rotated_paths': rotated_paths,
            'failed': failed,
            'skipped': skipped,
            'summary': summary
        }


# Example usage (for testing)
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Rotate images based on EXIF orientation")
    parser.add_argument("folder", help="Path to folder containing images")
    args = parser.parse_args()
    
    handler = ImageRotationHandler(args.folder)
    result = handler.rotate_images()
    
    print(f"\nRotated images available at:")
    for path in result['rotated_paths']:
        print(f"  - {path}")
