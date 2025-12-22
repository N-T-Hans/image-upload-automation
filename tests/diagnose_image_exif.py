#!/usr/bin/env python3
"""
Image EXIF Diagnostic Tool

This script analyzes images to show their EXIF orientation data and actual dimensions.
Use this to understand why images might not be rotating as expected.

Usage:
    python tests/diagnose_image_exif.py /path/to/images
"""

import sys
import os
from pathlib import Path
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def diagnose_images(folder_path: str):
    """
    Analyze all images in folder and display EXIF orientation data.
    """
    folder = Path(folder_path).resolve()
    
    if not folder.exists():
        console.print(f"[red]Folder not found: {folder}[/red]")
        return
    
    console.print(Panel.fit(
        f"[bold cyan]Image EXIF Diagnostics[/bold cyan]\n{folder}",
        border_style="cyan"
    ))
    
    # Supported formats
    supported_formats = ['.jpg', '.jpeg', '.png', '.webp', '.heic']
    image_files = [
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in supported_formats
    ]
    
    if not image_files:
        console.print("[yellow]No supported images found[/yellow]")
        return
    
    console.print(f"\n[cyan]Found {len(image_files)} images[/cyan]\n")
    
    # Create results table
    table = Table(title="Image Analysis", show_header=True, header_style="bold cyan")
    table.add_column("File", style="white", width=30)
    table.add_column("Size (WxH)", style="cyan", width=12)
    table.add_column("EXIF Orient", style="yellow", width=12)
    table.add_column("Status", style="green", width=40)
    
    orientation_names = {
        1: "Normal",
        2: "Flip H",
        3: "Rotate 180°",
        4: "Flip V",
        5: "Flip H + 270°",
        6: "Rotate 90° CW",
        7: "Flip H + 90°",
        8: "Rotate 270° CW"
    }
    
    for img_path in sorted(image_files):
        try:
            with Image.open(img_path) as img:
                width, height = img.size
                size_str = f"{width}x{height}"
                
                # Try to get EXIF orientation
                orientation = 1  # Default
                has_exif = False
                
                try:
                    exif = img._getexif()
                    if exif is not None:
                        has_exif = True
                        orientation = exif.get(274, 1)  # 274 is orientation tag
                except (AttributeError, KeyError, IndexError):
                    pass
                
                orient_str = f"{orientation} ({orientation_names.get(orientation, 'Unknown')})"
                
                # Determine status
                if not has_exif:
                    status = "[yellow]No EXIF data found[/yellow]"
                elif orientation == 1:
                    status = "[dim]No rotation needed (EXIF=1)[/dim]"
                else:
                    status = f"[green]Needs rotation: {orientation_names.get(orientation)}[/green]"
                
                table.add_row(
                    img_path.name[:28] + "..." if len(img_path.name) > 28 else img_path.name,
                    size_str,
                    orient_str,
                    status
                )
        
        except Exception as e:
            table.add_row(
                img_path.name,
                "ERROR",
                "ERROR",
                f"[red]Failed: {str(e)}[/red]"
            )
    
    console.print(table)
    
    # Summary and recommendations
    console.print("\n" + "="*80)
    console.print("[bold cyan]Understanding the Results:[/bold cyan]\n")
    
    console.print("[yellow]EXIF Orientation = 1[/yellow]")
    console.print("  • Image is marked as 'normal' orientation in metadata")
    console.print("  • But actual pixel data might still be rotated!")
    console.print("  • Common when editors rotate visually but don't update EXIF\n")
    
    console.print("[yellow]No EXIF data found[/yellow]")
    console.print("  • Image has no orientation metadata")
    console.print("  • Script cannot auto-rotate these images")
    console.print("  • You must manually ensure correct orientation\n")
    
    console.print("[green]EXIF Orientation != 1[/green]")
    console.print("  • Image will be rotated by the script")
    console.print("  • This is what you want to see!\n")
    
    console.print("="*80)
    console.print("[bold cyan]Solutions:[/bold cyan]\n")
    
    console.print("[cyan]Problem:[/cyan] All images show EXIF=1 but display rotated")
    console.print("[cyan]Solution:[/cyan] Your editor changed pixels but not EXIF metadata")
    console.print("  → Option 1: Use 'exiftool' to add rotation EXIF tags")
    console.print("  → Option 2: Re-export images with 'Save for Web' or similar")
    console.print("  → Option 3: Use an editor that properly writes EXIF (Adobe Bridge, etc.)\n")
    
    console.print("[cyan]Problem:[/cyan] Images have no EXIF data at all")
    console.print("[cyan]Solution:[/cyan] Metadata was stripped by an editor/compressor")
    console.print("  → Manually rotate images to correct orientation before uploading")
    console.print("  → Use tools that preserve EXIF (avoid web-based compressors)\n")
    
    console.print("[cyan]Problem:[/cyan] All images show EXIF=1 but are visually rotated")
    console.print("[cyan]Solution:[/cyan] Use the --force-exif flag to apply EXIF to pixels")
    console.print("  → Run: python tests/test_image_rotation.py test_images/ --force-exif")
    console.print("  → This applies any EXIF rotation to the actual pixel data\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Diagnose image EXIF orientation data",
        epilog="Use this to understand why images aren't rotating as expected"
    )
    
    parser.add_argument(
        'folder',
        nargs='?',
        help='Path to folder containing images'
    )
    
    args = parser.parse_args()
    
    if not args.folder:
        console.print("[yellow]Usage:[/yellow] python tests/diagnose_image_exif.py /path/to/images")
        sys.exit(1)
    
    diagnose_images(args.folder)
