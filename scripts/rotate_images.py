#!/usr/bin/env python3
"""
Rotate images based on filename patterns.

This script rotates images in a folder based on whether "front" or "back" 
appears in the filename:
- Files with "front" in name → orientation 8 (270° CW)
- Files with "back" in name → orientation 6 (90° CW)

Usage:
    python scripts/rotate_images.py <folder_path>
    python scripts/rotate_images.py /Users/username/Downloads/CardTest/A3
"""

import sys
import argparse
from pathlib import Path
from PIL import Image
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

console = Console()

# EXIF orientation tag
ORIENTATION_TAG = 0x0112

# Orientation values
ORIENTATION_CODES = {
    1: "Normal",
    2: "Mirrored",
    3: "Rotated 180°",
    4: "Mirrored and rotated 180°",
    5: "Mirrored and rotated 90° CCW",
    6: "Rotated 90° CW",
    7: "Mirrored and rotated 90° CW",
    8: "Rotated 270° CW"
}


def set_exif_orientation(image_path: Path, orientation: int) -> bool:
    """
    Set EXIF orientation on an image.
    
    Args:
        image_path: Path to image file
        orientation: EXIF orientation value (1-8)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        img = Image.open(image_path)
        
        # Get existing EXIF data or create new
        exif = img.getexif()
        
        # Set orientation
        exif[ORIENTATION_TAG] = orientation
        
        # Save with new EXIF data
        img.save(image_path, exif=exif, quality=95)
        
        return True
        
    except Exception as e:
        console.print(f"[red]Error processing {image_path.name}: {e}[/red]")
        return False


def rotate_images(folder_path: Path) -> dict:
    """
    Rotate images in folder based on filename patterns.
    
    Args:
        folder_path: Path to folder containing images
    
    Returns:
        Dictionary with processing statistics
    """
    if not folder_path.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")
    
    if not folder_path.is_dir():
        raise ValueError(f"Not a directory: {folder_path}")
    
    # Supported image formats
    supported_formats = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'}
    
    # Find all image files
    image_files = [
        f for f in folder_path.iterdir() 
        if f.is_file() and f.suffix.lower() in supported_formats
    ]
    
    if not image_files:
        console.print(f"[yellow]No image files found in {folder_path}[/yellow]")
        return {'total': 0, 'front': 0, 'back': 0, 'skipped': 0, 'errors': 0}
    
    stats = {
        'total': len(image_files),
        'front': 0,
        'back': 0,
        'skipped': 0,
        'errors': 0
    }
    
    console.print(f"\n[cyan]Processing {stats['total']} images in {folder_path.name}[/cyan]\n")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        
        task = progress.add_task("Rotating images...", total=stats['total'])
        
        for image_file in image_files:
            filename_lower = image_file.name.lower()
            
            # Determine orientation based on filename
            if 'front' in filename_lower:
                orientation = 8  # 270° CW
                stats['front'] += 1
                label = "front → orientation 8"
            elif 'back' in filename_lower:
                orientation = 6  # 90° CW
                stats['back'] += 1
                label = "back → orientation 6"
            else:
                # Skip files without front/back in name
                stats['skipped'] += 1
                progress.advance(task)
                continue
            
            # Set orientation
            success = set_exif_orientation(image_file, orientation)
            
            if success:
                progress.console.print(f"[green]✓[/green] {image_file.name} ({label})")
            else:
                stats['errors'] += 1
            
            progress.advance(task)
    
    return stats


def print_summary(stats: dict):
    """Print summary table of processing results."""
    table = Table(title="Processing Summary", show_header=True)
    table.add_column("Metric", style="cyan", justify="left")
    table.add_column("Count", style="bold", justify="right")
    
    table.add_row("Total images found", str(stats['total']))
    table.add_row("Front images rotated", f"[green]{stats['front']}[/green]")
    table.add_row("Back images rotated", f"[green]{stats['back']}[/green]")
    table.add_row("Skipped (no front/back)", f"[yellow]{stats['skipped']}[/yellow]")
    table.add_row("Errors", f"[red]{stats['errors']}[/red]")
    
    console.print()
    console.print(table)
    console.print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Rotate images based on filename patterns",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/rotate_images.py A3
  python scripts/rotate_images.py /Users/username/Downloads/CardTest/A3
  
Rules:
  - Files with "front" in name → orientation 8 (270° CW)
  - Files with "back" in name → orientation 6 (90° CW)
  - Other files are skipped
        """
    )
    
    parser.add_argument(
        'folder',
        help='Path to folder containing images'
    )
    
    args = parser.parse_args()
    
    try:
        folder_path = Path(args.folder)
        
        console.print(f"\n[bold cyan]Image Rotation Tool[/bold cyan]")
        console.print(f"[cyan]Target: {folder_path.resolve()}[/cyan]")
        
        stats = rotate_images(folder_path)
        print_summary(stats)
        
        if stats['errors'] > 0:
            console.print(f"[yellow]⚠ Completed with {stats['errors']} errors[/yellow]")
            sys.exit(1)
        else:
            console.print("[bold green]✓ All images processed successfully[/bold green]\n")
            sys.exit(0)
        
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
