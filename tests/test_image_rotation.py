#!/usr/bin/env python3
"""
Test script for image rotation functionality.

Tests the ImageRotationHandler class independently from the full workflow.
Use this to verify EXIF rotation is working correctly before running the full workflow.

Usage:
    python tests/test_image_rotation.py /path/to/test/images
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.image_tools import ImageRotationHandler
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def test_image_rotation(image_folder: str):
    """
    Test image rotation with a folder of images.
    
    Args:
        image_folder: Path to folder containing test images
    """
    console.print(Panel.fit(
        "[bold cyan]Image Rotation Test[/bold cyan]\n"
        f"Testing folder: {image_folder}",
        border_style="cyan"
    ))
    
    try:
        # Create handler
        console.print("\n[cyan]Step 1: Initialize ImageRotationHandler[/cyan]")
        handler = ImageRotationHandler(image_folder)
        console.print("[green]✓ Handler initialized successfully[/green]")
        
        # Run rotation
        console.print("\n[cyan]Step 2: Rotate images[/cyan]")
        result = handler.rotate_images()
        
        # Display detailed results
        console.print("\n" + "="*60)
        console.print("[bold cyan]ROTATION TEST RESULTS[/bold cyan]")
        console.print("="*60 + "\n")
        
        # Summary table
        table = Table(title="Summary", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")
        
        table.add_row("Total Images", str(result['summary']['total']))
        table.add_row("Successfully Rotated", str(result['summary']['success']))
        table.add_row("Skipped (No Rotation Needed)", str(result['summary']['skipped']))
        table.add_row("Failed", str(result['summary']['failed']))
        
        console.print(table)
        
        # Rotated images details
        if result['rotated_paths']:
            console.print("\n[bold green]Successfully Rotated Images:[/bold green]")
            for path in result['rotated_paths'][:10]:  # Show first 10
                console.print(f"  ✓ {Path(path).name}")
            if len(result['rotated_paths']) > 10:
                console.print(f"  ... and {len(result['rotated_paths']) - 10} more")
        
        # Skipped images
        if result['skipped']:
            console.print("\n[dim]Skipped Images (No EXIF rotation needed):[/dim]")
            for path in result['skipped'][:5]:  # Show first 5
                console.print(f"  ○ {Path(path).name}")
            if len(result['skipped']) > 5:
                console.print(f"  ... and {len(result['skipped']) - 5} more")
        
        # Failed images
        if result['failed']:
            console.print("\n[bold red]Failed Images:[/bold red]")
            for fail in result['failed']:
                console.print(f"  ✗ {Path(fail['path']).name}: {fail['error']}")
        
        # Output location
        console.print("\n[cyan]Output Locations:[/cyan]")
        console.print(f"  • Original folder: {image_folder}")
        rotated_folder = Path(image_folder) / "rotated_images"
        if rotated_folder.exists():
            console.print(f"  • Rotated JPEGs: {rotated_folder}")
            console.print(f"  • Other formats: Rotated in-place in original folder")
        else:
            console.print(f"  • All images: In-place rotation (no copies created)")
        
        # Test verdict
        console.print("\n" + "="*60)
        if result['summary']['failed'] > 0:
            console.print("[yellow]⚠ TEST PASSED WITH WARNINGS[/yellow]")
            console.print("[dim]Some images failed to rotate. Check errors above.[/dim]")
        elif result['summary']['success'] == 0 and result['summary']['skipped'] == 0:
            console.print("[red]✗ TEST FAILED[/red]")
            console.print("[dim]No images were processed. Check folder path and permissions.[/dim]")
        else:
            console.print("[bold green]✓ TEST PASSED[/bold green]")
            console.print(f"[dim]{result['summary']['success']} images ready for upload[/dim]")
        console.print("="*60)
        
        # Next steps
        console.print("\n[cyan]Next Steps:[/cyan]")
        if result['summary']['success'] > 0 or result['summary']['skipped'] > 0:
            console.print("  1. Check the rotated images visually")
            console.print("  2. Verify orientations are correct")
            console.print("  3. If good, proceed to test login/navigation")
            console.print("     Run: python tests/test_login_navigation.py")
        else:
            console.print("  1. Ensure folder contains supported images (.jpg, .png, etc.)")
            console.print("  2. Check file permissions")
            console.print("  3. Try with a different folder")
        
        return result['summary']['failed'] == 0
        
    except Exception as e:
        console.print(f"\n[bold red]✗ TEST FAILED WITH ERROR:[/bold red]")
        console.print(f"[red]{str(e)}[/red]")
        console.print("\n[yellow]Troubleshooting:[/yellow]")
        console.print("  • Verify folder path is correct")
        console.print("  • Check folder contains images")
        console.print("  • Ensure you have read/write permissions")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test image rotation functionality",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/test_image_rotation.py /Users/username/Desktop/test_images
  python tests/test_image_rotation.py ./sample_images

This test will:
  1. Read EXIF orientation from images
  2. Rotate images as needed
  3. Create copies for JPEGs
  4. Show detailed results
        """
    )
    
    parser.add_argument(
        'folder',
        nargs='?',
        help='Path to folder containing test images'
    )
    
    args = parser.parse_args()
    
    if not args.folder:
        console.print("[yellow]No folder specified. Usage:[/yellow]")
        console.print("  python tests/test_image_rotation.py /path/to/images")
        console.print("\n[dim]Example:[/dim]")
        console.print("  python tests/test_image_rotation.py ~/Desktop/card_images")
        sys.exit(1)
    
    success = test_image_rotation(args.folder)
    sys.exit(0 if success else 1)
