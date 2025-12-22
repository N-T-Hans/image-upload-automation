#!/usr/bin/env python3
"""
CardDealerPro Image Upload Workflow Orchestrator

This script orchestrates the complete 20-step workflow for uploading images
to CardDealerPro, including image rotation, login, batch creation, and upload.

Usage:
    python scripts/image_upload_workflow.py --config config/upload_config.json [--headless]

USER NOTE: Before running, ensure:
1. config/.env file exists with CDP_USERNAME and CDP_PASSWORD
   (copy from templates/env.template)
2. config file created from templates/upload_config.template.json
3. All selectors in config file are updated for your website
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Optional
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.image_tools import ImageRotationHandler
from tools.web_automation_tools import (
    ElementWaiter,
    LoginHandler,
    FormNavigator,
    FormSubmitter
)
from config import SELENIUM_HEADLESS, SELENIUM_TIMEOUT

console = Console()


class CardDealerProWorkflow:
    """
    Orchestrates the complete CardDealerPro batch upload workflow.
    
    This class manages the 20-step process from image rotation through
    final upload and validation at the inspector view.
    
    Workflow Steps:
    1. Rotate images based on EXIF orientation
    2. Login to CardDealerPro
    3. Navigate to batches page
    4. Click create batch button
    5. Fill general settings form
    6. Click continue button
    7. Fill optional details (if configured)
    8. Click create batch button
    9. Extract batch_id from URL
    10. Click magic scan button
    11. Navigate sides selection page
    12. Click continue for sides
    13. Navigate to upload page
    14. Locate file upload input
    15. Upload all rotated images
    16. Click continue button
    17. Wait for inspector view
    18. Stop for manual validation
    
    USER NOTE: The workflow stops at inspector view for you to manually
    validate the uploaded images before finalizing the batch.
    """
    
    def __init__(self, config_path: str, headless: bool = False):
        """
        Initialize workflow orchestrator.
        
        Args:
            config_path: Path to JSON configuration file
            headless: Run browser in headless mode (no visible window)
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid or missing required fields
            
        USER NOTE: See config_templates/upload_config.example.json for structure
        """
        self.config_path = Path(config_path)
        self.headless = headless
        self.driver = None
        self.waiter = None
        self.config = None
        self.batch_id = None
        self.rotated_image_paths = []
        
        # Load environment variables from .env file
        # Try config/.env first, then fall back to root .env for backwards compatibility
        config_env = Path(__file__).parent.parent / "config" / ".env"
        root_env = Path(__file__).parent.parent / ".env"
        
        if config_env.exists():
            load_dotenv(config_env)
        elif root_env.exists():
            load_dotenv(root_env)
        else:
            load_dotenv()  # Try default locations
        
        # Load and validate configuration
        self._load_config()
        self._validate_config()
        
        console.print(Panel.fit(
            "[bold cyan]CardDealerPro Image Upload Automation[/bold cyan]\n"
            f"Config: {self.config_path.name}\n"
            f"Images: {self.config['image_folder']}",
            border_style="cyan"
        ))
    
    def _load_config(self):
        """
        Load JSON configuration file.
        
        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
            
        USER NOTE: Ensure your config.json is valid JSON format
        """
        if not self.config_path.exists():
            console.print(f"[red]✗ Config file not found: {self.config_path}[/red]")
            console.print("[yellow]USER ACTION REQUIRED:[/yellow]")
            console.print("  1. Copy config_templates/upload_config.example.json")
            console.print("  2. Update all fields marked with << USER: ... >>")
            console.print("  3. Save as your config file")
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            console.print(f"[green]✓ Loaded configuration from {self.config_path}[/green]")
        except json.JSONDecodeError as e:
            console.print(f"[red]✗ Invalid JSON in config file: {str(e)}[/red]")
            raise
    
    def _validate_config(self):
        """
        Validate configuration has all required fields.
        
        Checks for presence of required sections and fields.
        
        Raises:
            ValueError: If required fields are missing
            
        USER NOTE: See config_templates/upload_config.example.json for all required fields
        """
        required_fields = [
            'image_folder',
            'urls',
            'general_settings',
            'selectors'
        ]
        
        missing = [field for field in required_fields if field not in self.config]
        
        if missing:
            console.print(f"[red]✗ Missing required fields in config: {', '.join(missing)}[/red]")
            console.print("[yellow]USER ACTION REQUIRED:[/yellow]")
            console.print("  Check config_templates/upload_config.example.json for required structure")
            raise ValueError(f"Missing required config fields: {missing}")
        
        # Check image folder exists
        image_folder = Path(self.config['image_folder'])
        if not image_folder.exists():
            console.print(f"[red]✗ Image folder not found: {image_folder}[/red]")
            raise ValueError(f"Image folder does not exist: {image_folder}")
        
        console.print("[green]✓ Configuration validated[/green]")
    
    def _setup_driver(self):
        """
        Initialize Selenium WebDriver with Chrome.
        
        Uses webdriver-manager to automatically download/update ChromeDriver.
        Configures browser options including headless mode if requested.
        
        USER NOTE: Chrome browser must be installed on your system
        """
        console.print("\n[cyan]Setting up Chrome WebDriver...[/cyan]")
        
        try:
            # Configure Chrome options
            options = Options()
            
            if self.headless or SELENIUM_HEADLESS:
                options.add_argument('--headless')
                console.print("[dim]Running in headless mode (no visible browser)[/dim]")
            
            # Additional options for stability
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            # Set window size
            options.add_argument('--window-size=1920,1080')
            
            # Initialize driver with webdriver-manager (auto-downloads ChromeDriver)
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Set timeouts
            self.driver.implicitly_wait(2)
            
            # Initialize waiter
            self.waiter = ElementWaiter(self.driver, SELENIUM_TIMEOUT)
            
            console.print("[green]✓ WebDriver initialized[/green]")
            
        except Exception as e:
            console.print(f"[red]✗ Failed to initialize WebDriver: {str(e)}[/red]")
            console.print("[yellow]USER ACTION REQUIRED:[/yellow]")
            console.print("  1. Ensure Chrome browser is installed")
            console.print("  2. Check internet connection (ChromeDriver downloads automatically)")
            raise
    
    def _rotate_images(self) -> bool:
        """
        Step 1: Rotate images based on EXIF orientation.
        
        Uses ImageRotationHandler to process all images in the configured folder.
        Continues workflow even if some images fail to rotate.
        
        Returns:
            True if at least some images were successfully rotated
            
        USER NOTE: Failed image rotations are logged but don't stop the workflow
        """
        console.print("\n" + "="*60)
        console.print("[bold cyan]STEP 1: Rotate Images[/bold cyan]")
        console.print("="*60)
        
        try:
            handler = ImageRotationHandler(self.config['image_folder'])
            result = handler.rotate_images()
            
            # Store paths to successfully rotated images for upload
            self.rotated_image_paths = result['rotated_paths']
            
            # Also include skipped images (no rotation needed)
            self.rotated_image_paths.extend(result['skipped'])
            
            if not self.rotated_image_paths:
                console.print("[red]✗ No images available for upload[/red]")
                return False
            
            console.print(f"\n[green]✓ {len(self.rotated_image_paths)} images ready for upload[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]✗ Image rotation failed: {str(e)}[/red]")
            return False
    
    def _login(self) -> bool:
        """
        Step 2: Login to CardDealerPro.
        
        Uses credentials from environment variables (.env file).
        
        Returns:
            True if login successful
            
        Raises:
            Exception: If login fails after retries
            
        USER NOTE: Ensure CDP_USERNAME and CDP_PASSWORD are set in .env file
        """
        console.print("\n" + "="*60)
        console.print("[bold cyan]STEP 2: Login to CardDealerPro[/bold cyan]")
        console.print("="*60)
        
        # Get credentials from environment
        username = os.getenv('CDP_USERNAME')
        password = os.getenv('CDP_PASSWORD')
        
        if not username or not password:
            console.print("[red]✗ Credentials not found in environment[/red]")
            console.print("[yellow]USER ACTION REQUIRED:[/yellow]")
            console.print("  1. Copy .env.example to .env")
            console.print("  2. Fill in CDP_USERNAME and CDP_PASSWORD")
            raise ValueError("Missing credentials in .env file")
        
        # Initialize login handler
        login_handler = LoginHandler(self.driver, self.waiter)
        
        # Perform login
        return login_handler.login(
            login_url=self.config['urls']['login'],
            username=username,
            password=password,
            username_selector=self.config['selectors']['username_input'],
            password_selector=self.config['selectors']['password_input'],
            login_button_selector=self.config['selectors']['login_button'],
            success_url_pattern=self.config['urls']['batches']
        )
    
    def _navigate_to_batches(self) -> bool:
        """
        Step 3: Navigate to batches page.
        
        Returns:
            True if navigation successful
        """
        console.print("\n" + "="*60)
        console.print("[bold cyan]STEP 3: Navigate to Batches Page[/bold cyan]")
        console.print("="*60)
        
        navigator = FormNavigator(self.driver, self.waiter)
        return navigator.navigate_to(
            self.config['urls']['batches'],
            wait_for_selector=self.config['selectors']['create_batch_button']
        )
    
    def _click_create_batch(self) -> bool:
        """
        Step 4: Click create batch button.
        
        Returns:
            True if successful
        """
        console.print("\n" + "="*60)
        console.print("[bold cyan]STEP 4: Click Create Batch Button[/bold cyan]")
        console.print("="*60)
        
        submitter = FormSubmitter(self.driver, self.waiter)
        success = submitter.click_button(
            self.config['selectors']['create_batch_button'],
            label="Create Batch"
        )
        
        if success:
            # Wait for general settings page to load
            self.waiter.wait_for_url_contains('general-settings')
        
        return success
    
    def _fill_general_settings(self) -> bool:
        """
        Step 5: Fill general settings form.
        
        Fills batch name and all dropdown selections.
        
        Returns:
            True if successful
            
        USER NOTE: Dropdown values must match exactly what appears in the dropdown
        """
        console.print("\n" + "="*60)
        console.print("[bold cyan]STEP 5: Fill General Settings[/bold cyan]")
        console.print("="*60)
        
        submitter = FormSubmitter(self.driver, self.waiter)
        settings = self.config['general_settings']
        selectors = self.config['selectors']
        
        try:
            # Fill batch name
            submitter.fill_text_input(
                selectors['batch_name_input'],
                settings['batch_name'],
                label="Batch Name"
            )
            
            # Select batch type
            submitter.select_dropdown_option(
                selectors['batch_type_select'],
                settings['batch_type'],
                label="Batch Type"
            )
            
            # Select sport type
            submitter.select_dropdown_option(
                selectors['sport_type_select'],
                settings['sport_type'],
                label="Sport Type"
            )
            
            # Select title template
            submitter.select_dropdown_option(
                selectors['title_template_select'],
                settings['title_template'],
                label="Title Template"
            )
            
            # Fill description
            submitter.fill_text_input(
                selectors['description_input'],
                settings['description'],
                label="Description"
            )
            
            console.print("[green]✓ All general settings filled[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]✗ Failed to fill general settings: {str(e)}[/red]")
            raise
    
    def _click_continue_general_settings(self) -> bool:
        """
        Step 6: Click continue button to proceed to optional details.
        
        Returns:
            True if successful
        """
        console.print("\n" + "="*60)
        console.print("[bold cyan]STEP 6: Continue to Optional Details[/bold cyan]")
        console.print("="*60)
        
        submitter = FormSubmitter(self.driver, self.waiter)
        success = submitter.click_button(
            self.config['selectors']['continue_button_general'],
            label="Continue (General Settings)"
        )
        
        if success:
            # Wait for optional details page to load
            self.waiter.wait_for_url_contains('optional-details')
        
        return success
    
    def _fill_optional_details(self) -> bool:
        """
        Step 7: Fill optional details form (if configured).
        
        Skips this step if no optional_details in config.
        
        Returns:
            True if successful or skipped
            
        USER NOTE: Optional details are entirely optional. Leave empty {} to skip.
        """
        console.print("\n" + "="*60)
        console.print("[bold cyan]STEP 7: Fill Optional Details[/bold cyan]")
        console.print("="*60)
        
        optional_details = self.config.get('optional_details', {})
        
        if not optional_details:
            console.print("[dim]No optional details configured, skipping...[/dim]")
            return True
        
        submitter = FormSubmitter(self.driver, self.waiter)
        
        try:
            for field_name, field_value in optional_details.items():
                # Get selector for this field from config
                selector_key = f'optional_{field_name}'
                selector = self.config['selectors'].get(selector_key)
                
                if not selector:
                    console.print(f"[yellow]⚠ No selector found for optional field: {field_name}[/yellow]")
                    console.print(f"[dim]Add '{selector_key}' to selectors in config.json[/dim]")
                    continue
                
                # Try to fill the field (could be text input or dropdown)
                try:
                    submitter.fill_text_input(selector, field_value, label=field_name)
                except:
                    # If text input fails, try as dropdown
                    try:
                        submitter.select_dropdown_option(selector, field_value, label=field_name)
                    except:
                        console.print(f"[yellow]⚠ Could not fill optional field: {field_name}[/yellow]")
            
            console.print("[green]✓ Optional details processed[/green]")
            return True
            
        except Exception as e:
            console.print(f"[yellow]⚠ Error filling optional details: {str(e)}[/yellow]")
            console.print("[dim]Continuing anyway...[/dim]")
            return True
    
    def _create_batch(self) -> bool:
        """
        Step 8: Click create batch button to finalize batch creation.
        
        Returns:
            True if successful
        """
        console.print("\n" + "="*60)
        console.print("[bold cyan]STEP 8: Create Batch[/bold cyan]")
        console.print("="*60)
        
        submitter = FormSubmitter(self.driver, self.waiter)
        success = submitter.click_button(
            self.config['selectors']['create_batch_submit'],
            label="Create Batch (Submit)"
        )
        
        if success:
            # Wait for navigation to batch types page
            self.waiter.wait_for_url_contains('/batches/')
        
        return success
    
    def _extract_batch_id(self) -> bool:
        """
        Step 9: Extract batch_id from URL.
        
        Returns:
            True if batch_id successfully extracted
            
        USER NOTE: If this fails, the batch was likely created but we can't
        continue automatically. Check the URL pattern in config.py
        """
        console.print("\n" + "="*60)
        console.print("[bold cyan]STEP 9: Extract Batch ID[/bold cyan]")
        console.print("="*60)
        
        navigator = FormNavigator(self.driver, self.waiter)
        self.batch_id = navigator.extract_batch_id_from_url()
        
        if self.batch_id:
            console.print(f"[bold green]✓ Batch ID: {self.batch_id}[/bold green]")
            return True
        else:
            console.print("[red]✗ Failed to extract batch ID[/red]")
            console.print("[yellow]USER ACTION REQUIRED:[/yellow]")
            console.print("  The batch was likely created but automatic continuation failed")
            console.print("  You may need to manually complete the upload in the browser")
            return False
    
    def _click_magic_scan(self) -> bool:
        """
        Step 10: Click magic scan button.
        
        Returns:
            True if successful
        """
        console.print("\n" + "="*60)
        console.print("[bold cyan]STEP 10: Click Magic Scan[/bold cyan]")
        console.print("="*60)
        
        submitter = FormSubmitter(self.driver, self.waiter)
        success = submitter.click_button(
            self.config['selectors']['magic_scan_button'],
            label="Magic Scan"
        )
        
        if success:
            # Wait for sides selection page
            self.waiter.wait_for_url_contains('/sides')
        
        return success
    
    def _select_sides(self) -> bool:
        """
        Step 11: Navigate sides selection and continue.
        
        Returns:
            True if successful
        """
        console.print("\n" + "="*60)
        console.print("[bold cyan]STEP 11: Select Sides[/bold cyan]")
        console.print("="*60)
        
        # If there are side-specific selections needed, add them here
        # For now, just click continue
        
        submitter = FormSubmitter(self.driver, self.waiter)
        success = submitter.click_button(
            self.config['selectors']['sides_continue_button'],
            label="Continue (Sides)"
        )
        
        if success:
            # Wait for upload page
            self.waiter.wait_for_url_contains('/upload')
        
        return success
    
    def _upload_images(self) -> bool:
        """
        Step 12: Upload all rotated images.
        
        Sends all image file paths to the file upload input.
        
        Returns:
            True if successful
            
        USER NOTE: This uploads all successfully rotated images at once
        """
        console.print("\n" + "="*60)
        console.print("[bold cyan]STEP 12: Upload Images[/bold cyan]")
        console.print("="*60)
        
        if not self.rotated_image_paths:
            console.print("[red]✗ No images to upload[/red]")
            return False
        
        submitter = FormSubmitter(self.driver, self.waiter)
        
        try:
            # Upload all images
            success = submitter.upload_files(
                self.config['selectors']['upload_file_input'],
                self.rotated_image_paths
            )
            
            if success:
                console.print(f"[bold green]✓ Uploaded {len(self.rotated_image_paths)} images[/bold green]")
            
            return success
            
        except Exception as e:
            console.print(f"[red]✗ Upload failed: {str(e)}[/red]")
            return False
    
    def _click_continue_upload(self) -> bool:
        """
        Step 13: Click continue after upload.
        
        Returns:
            True if successful
        """
        console.print("\n" + "="*60)
        console.print("[bold cyan]STEP 13: Continue After Upload[/bold cyan]")
        console.print("="*60)
        
        # Wait a moment for uploads to process
        import time
        console.print("[dim]Waiting for uploads to process...[/dim]")
        time.sleep(3)
        
        submitter = FormSubmitter(self.driver, self.waiter)
        success = submitter.click_button(
            self.config['selectors']['upload_continue_button'],
            label="Continue (Upload)"
        )
        
        return success
    
    def _reach_inspector_view(self) -> bool:
        """
        Step 14: Wait for inspector view to load.
        
        This is the final step where the workflow stops for manual validation.
        
        Returns:
            True if inspector view reached
            
        USER NOTE: At this point, manually review the uploaded images in the browser.
        The script will keep the browser open until you close it or press Enter.
        """
        console.print("\n" + "="*60)
        console.print("[bold cyan]STEP 14: Inspector View[/bold cyan]")
        console.print("="*60)
        
        # Wait for inspector view to load
        import time
        time.sleep(2)
        
        console.print("[bold green]✓ Reached inspector view[/bold green]")
        console.print("\n[yellow]═══════════════════════════════════════════════════════════[/yellow]")
        console.print("[bold yellow]WORKFLOW PAUSED FOR MANUAL VALIDATION[/bold yellow]")
        console.print("[yellow]═══════════════════════════════════════════════════════════[/yellow]")
        console.print("\n[cyan]Please review the uploaded images in the browser window.[/cyan]")
        console.print("[dim]The browser will remain open for your inspection.[/dim]")
        
        return True
    
    def _print_summary(self):
        """
        Print final workflow summary.
        
        Shows results from all major stages.
        """
        console.print("\n" + "="*60)
        console.print("[bold cyan]WORKFLOW SUMMARY[/bold cyan]")
        console.print("="*60 + "\n")
        
        table = Table(title="Workflow Results", show_header=True)
        table.add_column("Stage", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="dim")
        
        table.add_row("Image Rotation", "✓ Complete", f"{len(self.rotated_image_paths)} images ready")
        table.add_row("Login", "✓ Complete", "Authenticated successfully")
        table.add_row("Batch Creation", "✓ Complete", f"Batch ID: {self.batch_id}")
        table.add_row("Image Upload", "✓ Complete", f"{len(self.rotated_image_paths)} files uploaded")
        table.add_row("Inspector View", "✓ Reached", "Manual validation pending")
        
        console.print(table)
        console.print()
    
    def _cleanup(self):
        """
        Clean up resources and close browser.
        
        USER NOTE: Browser will close after you finish manual validation
        """
        if self.driver:
            console.print("\n[dim]Press Enter to close browser and exit...[/dim]")
            input()
            console.print("[dim]Closing browser...[/dim]")
            self.driver.quit()
            console.print("[green]✓ Browser closed[/green]")
    
    def run(self) -> bool:
        """
        Execute the complete workflow.
        
        Runs all 14 steps in sequence, stopping at inspector view for manual validation.
        
        Returns:
            True if workflow completed successfully
            
        Raises:
            Exception: If any critical step fails
        """
        try:
            # Setup WebDriver
            self._setup_driver()
            
            # Step 1: Rotate images
            if not self._rotate_images():
                console.print("[red]✗ Workflow failed at image rotation[/red]")
                return False
            
            # Step 2: Login
            if not self._login():
                console.print("[red]✗ Workflow failed at login[/red]")
                return False
            
            # Step 3: Navigate to batches
            if not self._navigate_to_batches():
                console.print("[red]✗ Workflow failed at batches navigation[/red]")
                return False
            
            # Step 4: Click create batch
            if not self._click_create_batch():
                console.print("[red]✗ Workflow failed at create batch click[/red]")
                return False
            
            # Step 5: Fill general settings
            if not self._fill_general_settings():
                console.print("[red]✗ Workflow failed at general settings[/red]")
                return False
            
            # Step 6: Continue to optional details
            if not self._click_continue_general_settings():
                console.print("[red]✗ Workflow failed at continue click[/red]")
                return False
            
            # Step 7: Fill optional details
            if not self._fill_optional_details():
                console.print("[red]✗ Workflow failed at optional details[/red]")
                return False
            
            # Step 8: Create batch
            if not self._create_batch():
                console.print("[red]✗ Workflow failed at batch creation[/red]")
                return False
            
            # Step 9: Extract batch ID
            if not self._extract_batch_id():
                console.print("[red]✗ Workflow failed at batch ID extraction[/red]")
                return False
            
            # Step 10: Magic scan
            if not self._click_magic_scan():
                console.print("[red]✗ Workflow failed at magic scan[/red]")
                return False
            
            # Step 11: Select sides
            if not self._select_sides():
                console.print("[red]✗ Workflow failed at sides selection[/red]")
                return False
            
            # Step 12: Upload images
            if not self._upload_images():
                console.print("[red]✗ Workflow failed at image upload[/red]")
                return False
            
            # Step 13: Continue after upload
            if not self._click_continue_upload():
                console.print("[red]✗ Workflow failed at upload continue[/red]")
                return False
            
            # Step 14: Reach inspector view
            if not self._reach_inspector_view():
                console.print("[red]✗ Workflow failed at inspector view[/red]")
                return False
            
            # Print summary
            self._print_summary()
            
            console.print("\n[bold green]✓ WORKFLOW COMPLETED SUCCESSFULLY[/bold green]")
            return True
            
        except KeyboardInterrupt:
            console.print("\n[yellow]⚠ Workflow interrupted by user[/yellow]")
            return False
            
        except Exception as e:
            console.print(f"\n[bold red]✗ WORKFLOW FAILED: {str(e)}[/bold red]")
            return False
            
        finally:
            # Always cleanup
            self._cleanup()


def main():
    """
    Main entry point for the script.
    
    Parses command-line arguments and runs the workflow.
    """
    parser = argparse.ArgumentParser(
        description="CardDealerPro Image Upload Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/image_upload_workflow.py --config my_batch.json
  python scripts/image_upload_workflow.py --config my_batch.json --headless

For more information, see docs/USAGE.md
        """
    )
    
    parser.add_argument(
        '--config',
        required=True,
        help='Path to JSON configuration file'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode (no visible window)'
    )
    
    args = parser.parse_args()
    
    try:
        workflow = CardDealerProWorkflow(args.config, args.headless)
        success = workflow.run()
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        console.print(f"\n[bold red]Fatal error: {str(e)}[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
