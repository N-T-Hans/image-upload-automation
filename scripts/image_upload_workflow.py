#!/usr/bin/env python3
"""
CardDealerPro Image Upload Workflow Orchestrator

This script orchestrates the complete workflow for uploading images
to CardDealerPro, including image rotation, login, batch creation, and upload.

Usage:
    python3 scripts/image_upload_workflow.py --config config/upload_config.json --folder Test1
    python3 scripts/image_upload_workflow.py --config config/upload_config.json --folder Test1 --headless

USER NOTE: Before running, ensure:
1. config/.env file exists with CDP_USERNAME and CDP_PASSWORD
2. config/upload_config.json created and configured with selectors
3. default_images_path set in config (or use full path with --folder)
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
    
    This class manages the process from image rotation through
    final upload and validation at the inspector view.
    
    Workflow Steps:
    1. Rotate images (front → orientation 8, back → orientation 6)
    2. Login to CardDealerPro
    3. Navigate to general settings
    4. Fill general settings form
    5. Continue to optional details
    6. Fill optional details
    7. Create batch
    8. Extract batch ID
    9. Select Magic Scan
    10. Select card type and sides
    11. Upload images
    12. Continue after upload
    13. Stop at inspector view for manual validation
    
    USER NOTE: Images with "front" or "back" in filename are automatically rotated.
    The workflow stops at inspector view for manual validation.
    """
    
    def __init__(self, config_path: str, folder_path: Optional[str] = None, headless: bool = False, shared_driver=None, skip_login: bool = False):
        """
        Initialize workflow orchestrator.
        
        Args:
            config_path: Path to JSON configuration file
            folder_path: Path to folder containing images (overrides config and sets batch_name)
            headless: Run browser in headless mode (no visible window)
            shared_driver: Existing WebDriver to reuse (for multi-folder workflows)
            skip_login: Skip login step if already logged in
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid or missing required fields
            
        USER NOTE: See config_templates/upload_config.example.json for structure
        """
        self.config_path = Path(config_path)
        self.folder_path = Path(folder_path) if folder_path else None
        self.headless = headless
        self.driver = shared_driver  # Use shared driver if provided
        self.skip_login = skip_login
        self.waiter = None
        self.config = None
        self.batch_id = None
        self.rotated_image_paths = []
        self.step_timings = {}  # Track time for each step
        self.total_images = 0  # Track number of images in batch
        self.current_step = "Init"  # Track the current/last executed step
        self.last_error = None  # Store the last error message (if any)
        
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
        
        # Override image_folder and batch_name if folder_path provided
        if self.folder_path:
            # If folder_path is relative or just a name, combine with default_images_path
            if not self.folder_path.is_absolute():
                default_base = self.config.get('default_images_path')
                if not default_base:
                    raise ValueError(
                        "Relative folder path provided but 'default_images_path' not set in config. "
                        "Either use absolute path or set 'default_images_path' in your config."
                    )
                self.folder_path = Path(default_base) / self.folder_path
                console.print(f"[cyan]→ Using base path: {default_base}[/cyan]")
            
            if not self.folder_path.exists():
                raise FileNotFoundError(f"Folder not found: {self.folder_path}")
            if not self.folder_path.is_dir():
                raise ValueError(f"Not a directory: {self.folder_path}")
            
            # Set image_folder to absolute path
            self.config['image_folder'] = str(self.folder_path.resolve())
            
            # Set batch_name to folder name
            folder_name = self.folder_path.name
            if 'general_settings' not in self.config:
                self.config['general_settings'] = {}
            self.config['general_settings']['batch_name'] = folder_name
            
            console.print(f"[cyan]→ Using folder: {folder_name}[/cyan]")
            console.print(f"[cyan]→ Batch name set to: {folder_name}[/cyan]")
        
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
        # Skip setup if driver already provided (shared driver from multi-folder)
        if self.driver:
            console.print("\n[cyan]Using existing WebDriver session...[/cyan]")
            # Reinitialize waiter with existing driver
            self.waiter = ElementWaiter(self.driver, SELENIUM_TIMEOUT)
            console.print("[green]✓ WebDriver ready[/green]")
            return
        
        console.print("\n[cyan]Setting up Brave WebDriver...[/cyan]")
        
        try:
            # Configure Chrome options (works with Brave since it's Chromium-based)
            options = Options()
            options.binary_location = '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
            
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
        Step 1: Rotate images based on filename patterns.
        
        Rotates images with "front" in name to orientation 8 (270° CW)
        and images with "back" in name to orientation 6 (90° CW).
        
        Returns:
            True if folder exists and has images
        """
        console.print("\n" + "="*60)
        console.print("[bold cyan]STEP 1: Rotate Images[/bold cyan]")
        console.print("="*60)
        import time
        # Track current step for summary/error reporting
        self.current_step = "Rotate Images"
        
        try:
            from pathlib import Path
            from PIL import Image
            start_time = time.time()
            
            
            image_folder = Path(self.config['image_folder'])
            
            if not image_folder.exists():
                console.print(f"[red]✗ Image folder not found: {image_folder}[/red]")
                self.last_error = f"Image folder not found: {image_folder}"
                return False
            
            # Find image files
            supported_formats = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'}
            image_files = [
                f for f in image_folder.iterdir()
                if f.is_file() and f.suffix.lower() in supported_formats
            ]
            
            if not image_files:
                console.print(f"[red]✗ No image files found in {image_folder}[/red]")
                self.last_error = f"No image files found in {image_folder}"
                return False
            
            # Rotation statistics
            stats = {'front': 0, 'back': 0, 'skipped': 0, 'errors': 0}
            
            console.print(f"[cyan]Processing {len(image_files)} images...[/cyan]")
            
            # EXIF orientation tag
            ORIENTATION_TAG = 0x0112
            
            for image_file in image_files:
                filename_lower = image_file.name.lower()
                
                # Determine orientation based on filename
                if 'front' in filename_lower:
                    orientation = 8  # 270° CW
                    stats['front'] += 1
                elif 'back' in filename_lower:
                    orientation = 6  # 90° CW
                    stats['back'] += 1
                else:
                    # Skip files without front/back in name
                    stats['skipped'] += 1
                    continue
                
                # Set EXIF orientation
                try:
                    img = Image.open(image_file)
                    exif = img.getexif()
                    exif[ORIENTATION_TAG] = orientation
                    img.save(image_file, exif=exif, quality=95)
                except Exception as e:
                    console.print(f"[red]✗ Error: {image_file.name} - {e}[/red]")
                    stats['errors'] += 1
            
            # Store image paths for upload
            self.rotated_image_paths = [str(f) for f in image_files]
            
            # Save timing and image count
            elapsed = time.time() - start_time
            self.step_timings['Rotate Images'] = elapsed
            self.total_images = len(image_files)
            
            # Summary
            console.print(f"\n[green]✓ Processed {len(image_files)} images[/green]")
            console.print(f"  Front: {stats['front']} | Back: {stats['back']} | Skipped: {stats['skipped']} | Errors: {stats['errors']}")
            console.print(f"[dim]Time: {elapsed:.1f}s[/dim]")
            
            if stats['errors'] > 0:
                console.print(f"[yellow]⚠ {stats['errors']} images had errors but workflow will continue[/yellow]")
            
            return True
            
        except Exception as e:
            console.print(f"[red]✗ Image rotation failed: {str(e)}[/red]")
            self.last_error = f"Rotate Images failed: {str(e)}"
            return False
    
    def _track_step_time(self, step_name: str, step_func):
        """Helper to track execution time for a step."""
        import time
        # Track current step for summary/error reporting
        self.current_step = step_name
        start_time = time.time()
        try:
            result = step_func()
            elapsed = time.time() - start_time
            self.step_timings[step_name] = elapsed
            console.print(f"[dim]Time: {elapsed:.1f}s[/dim]")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            self.step_timings[step_name] = elapsed
            # Record error for summary and re-raise to be handled upstream
            self.last_error = f"{step_name} error: {str(e)}"
            raise
    
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
            success_url_pattern=self.config['urls']['inventory'],
            continue_button_selector=self.config['selectors'].get('continue_button')
        )
    
    def _navigate_to_batches(self) -> bool:
        """
        Step 3: Navigate to General Settings page directly.
        
        Returns:
            True if navigation successful
        """
        console.print("\n" + "="*60)
        console.print("[bold cyan]STEP 3: Navigate to General Settings[/bold cyan]")
        console.print("="*60)
        
        navigator = FormNavigator(self.driver, self.waiter)
        # Prefer navigating directly to general settings
        wait_selector = (
            self.config['selectors'].get('batch_name_input')
            or self.config['selectors'].get('batch_type_select')
            or self.config['selectors'].get('sport_type_select')
        )
        return navigator.navigate_to(
            self.config['urls']['general_settings'],
            wait_for_selector=wait_selector
        )
    
    def _fill_general_settings(self) -> bool:
        """
        Step 4: Fill general settings form.
        
        Fills batch name and all dropdown selections.
        
        Returns:
            True if successful
            
        USER NOTE: Dropdown values must match exactly what appears in the dropdown
        """
        console.print("\n" + "="*60)
        console.print("[bold cyan]STEP 4: Fill General Settings[/bold cyan]")
        console.print("="*60)
        
        submitter = FormSubmitter(self.driver, self.waiter)
        settings = self.config['general_settings']
        selectors = self.config['selectors']
        
        try:
            # Fill batch name (if both selector and value provided)
            if selectors.get('batch_name_input') and settings.get('batch_name'):
                submitter.fill_text_input(
                    selectors['batch_name_input'],
                    settings['batch_name'],
                    label="Batch Name"
                )
            else:
                console.print("[dim]Skipping Batch Name (missing selector or value)[/dim]")
            
            # Select batch type - check if it's a custom dropdown
            if selectors.get('batch_type_select') and settings.get('batch_type'):
                if selectors.get('batch_type_select_type') == 'custom':
                    submitter.select_custom_dropdown_option(
                        selectors['batch_type_select'],
                        settings['batch_type'],
                        label="Batch Type"
                    )
                else:
                    submitter.select_dropdown_option(
                        selectors['batch_type_select'],
                        settings['batch_type'],
                        label="Batch Type"
                    )
            else:
                console.print("[dim]Skipping Batch Type (missing selector or value)[/dim]")
            
            # Select sport type (Game)
            if selectors.get('sport_type_select') and settings.get('sport_type'):
                if selectors.get('sport_type_select_type') == 'custom':
                    submitter.select_custom_dropdown_option(
                        selectors['sport_type_select'],
                        settings['sport_type'],
                        label="Sport Type"
                    )
                else:
                    submitter.select_dropdown_option(
                        selectors['sport_type_select'],
                        settings['sport_type'],
                        label="Sport Type"
                    )
            else:
                console.print("[dim]Skipping Sport/Game Type (missing selector or value)[/dim]")
            
            # Select title template (optional)
            if selectors.get('title_template_select') and settings.get('title_template'):
                if selectors.get('title_template_select_type') == 'custom':
                    submitter.select_custom_dropdown_option(
                        selectors['title_template_select'],
                        settings['title_template'],
                        label="Title Template"
                    )
                else:
                    submitter.select_dropdown_option(
                        selectors['title_template_select'],
                        settings['title_template'],
                        label="Title Template"
                    )
            else:
                console.print("[dim]Skipping Title Template (missing selector or value)[/dim]")
            
            # Select description template (optional)
            if selectors.get('description_template_select') and settings.get('description_template'):
                if selectors.get('description_template_select_type') == 'custom':
                    submitter.select_custom_dropdown_option(
                        selectors['description_template_select'],
                        settings['description_template'],
                        label="Description Template"
                    )
                else:
                    submitter.select_dropdown_option(
                        selectors['description_template_select'],
                        settings['description_template'],
                        label="Description Template"
                    )
            else:
                console.print("[dim]Skipping Description Template (missing selector or value)[/dim]")
            
            # Fill description (optional)
            if selectors.get('description_input') and settings.get('description'):
                submitter.fill_text_input(
                    selectors['description_input'],
                    settings['description'],
                    label="Description"
                )
            else:
                console.print("[dim]Skipping Description (missing selector or value)[/dim]")
            
            console.print("[green]✓ All general settings filled[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]✗ Failed to fill general settings: {str(e)}[/red]")
            raise
    
    def _click_continue_general_settings(self) -> bool:
        """
        Step 5: Click continue button to proceed to optional details.
        
        Returns:
            True if successful
        """
        console.print("\n" + "="*60)
        console.print("[bold cyan]STEP 5: Continue to Optional Details[/bold cyan]")
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
        Step 6: Fill optional details form (if configured).
        
        Skips this step if no optional_details in config.
        
        Returns:
            True if successful or skipped
            
        USER NOTE: Optional details are entirely optional. Leave empty {} to skip.
        """
        console.print("\n" + "="*60)
        console.print("[bold cyan]STEP 6: Fill Optional Details[/bold cyan]")
        console.print("="*60)
        
        optional_details = self.config.get('optional_details', {})
        
        if not optional_details:
            console.print("[dim]No optional details configured, skipping...[/dim]")
            return True
        
        submitter = FormSubmitter(self.driver, self.waiter)
        
        try:
            for field_name, field_value in optional_details.items():
                # Skip comment fields
                if field_name.startswith('_'):
                    continue
                
                # Get selector for this field from config
                selector_key = f'optional_{field_name}'
                selector = self.config['selectors'].get(selector_key)
                
                if not selector:
                    console.print(f"[yellow]⚠ No selector found for optional field: {field_name}[/yellow]")
                    console.print(f"[dim]Add '{selector_key}' to selectors in config.json[/dim]")
                    continue
                
                # Check if this is a custom dropdown
                selector_type_key = f'{selector_key}_type'
                is_custom = self.config['selectors'].get(selector_type_key) == 'custom'
                
                # Try to fill the field based on type
                try:
                    if is_custom:
                        # Custom dropdown (Headless UI)
                        submitter.select_custom_dropdown_option(selector, field_value, label=field_name)
                    else:
                        # Try text input first
                        submitter.fill_text_input(selector, field_value, label=field_name)
                except Exception:
                    # If text input fails, try as native <select> dropdown
                    try:
                        submitter.select_dropdown_option(selector, field_value, label=field_name)
                    except Exception:
                        submitter.select_dropdown_option(selector, field_value, label=field_name)
                    except Exception:
                        # As a final fallback, try clicking the element (for radio/checkbox/toggles)
                        try:
                            submitter.click_button(selector, label=field_name)
                        except Exception:
                            console.print(f"[yellow]⚠ Could not set optional field: {field_name}[/yellow]")
            
            console.print("[green]✓ Optional details processed[/green]")
            return True
            
        except Exception as e:
            console.print(f"[yellow]⚠ Error filling optional details: {str(e)}[/yellow]")
            console.print("[dim]Continuing anyway...[/dim]")
            return True
    
    def _create_batch(self) -> bool:
        """
        Step 7: Click create batch button to finalize batch creation.
        
        Returns:
            True if successful
        """
        console.print("\n" + "="*60)
        console.print("[bold cyan]STEP 7: Create Batch[/bold cyan]")
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
        Step 8: Extract batch_id from URL.
        
        Returns:
            True if batch_id successfully extracted
            
        USER NOTE: If this fails, the batch was likely created but we can't
        continue automatically. Check the URL pattern in config.py
        """
        console.print("\n" + "="*60)
        console.print("[bold cyan]STEP 8: Extract Batch ID[/bold cyan]")
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
        Step 9: Click magic scan button.
        
        Returns:
            True if successful
        """
        console.print("\n" + "="*60)
        console.print("[bold cyan]STEP 9: Click Magic Scan[/bold cyan]")
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
        Step 10: Navigate sides selection and continue.
        
        Returns:
            True if successful
        """
        console.print("\n" + "="*60)
        console.print("[bold cyan]STEP 10: Select Sides[/bold cyan]")
        console.print("="*60)
        
        submitter = FormSubmitter(self.driver, self.waiter)
        selectors = self.config.get('selectors', {})
        scan_options = self.config.get('scan_options', {})
        
        # 11.a Select card type (radio) if provided
        card_type_selector = selectors.get('scan_card_type_radio')
        if card_type_selector:
            try:
                label = f"Card Type ({scan_options.get('card_type', '')})".strip()
                submitter.click_button(card_type_selector, label=label or "Card Type")
            except Exception:
                console.print("[yellow]⚠ Could not set Card Type radio; continuing[/yellow]")
        
        # 11.b Select sides via clickable tile (preferred) or dropdown fallback
        sides_value = scan_options.get('sides')
        sides_option_selector = selectors.get('scan_sides_option')
        if sides_option_selector:
            try:
                label = f"Sides ({sides_value})" if sides_value else "Sides"
                submitter.click_button(sides_option_selector, label=label)
            except Exception:
                console.print("[yellow]⚠ Could not click Sides option tile; trying dropdown if available[/yellow]")
                # Fall through to dropdown path
        else:
            sides_selector = selectors.get('scan_sides_select')
            if sides_selector and sides_value:
                try:
                    if selectors.get('scan_sides_select_type') == 'custom':
                        submitter.select_custom_dropdown_option(sides_selector, sides_value, label="Sides")
                    else:
                        submitter.select_dropdown_option(sides_selector, sides_value, label="Sides")
                except Exception:
                    console.print("[yellow]⚠ Could not set Sides selection; continuing[/yellow]")
        
        console.print("[green]✓ Sides selection completed[/green]")
        
        # Wait for upload page to load
        import time
        console.print("[dim]Waiting for upload page...[/dim]")
        time.sleep(2)
        
        # Wait for upload page URL
        try:
            self.waiter.wait_for_url_contains('/add/upload')
        except Exception:
            # If URL doesn't change, try waiting for upload input directly
            console.print("[dim]Upload page URL not detected, checking for upload input...[/dim]")
        
        return True
    
    def _upload_images(self) -> bool:
        """
        Step 11: Upload all rotated images.
        
        Sends all image file paths to the file upload input.
        
        Returns:
            True if successful
            
        USER NOTE: This uploads all successfully rotated images at once
        """
        console.print("\n" + "="*60)
        console.print("[bold cyan]STEP 11: Upload Images[/bold cyan]")
        console.print("="*60)
        
        if not self.rotated_image_paths:
            console.print("[red]✗ No images to upload[/red]")
            return False
        
        submitter = FormSubmitter(self.driver, self.waiter)
        
        try:
            # Wait for upload page to be ready
            import time
            console.print("[dim]Ensuring upload page is ready...[/dim]")
            time.sleep(2)
            
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
        Step 12: Click continue after upload.
        
        Waits for all uploads to complete and button to become clickable.
        
        Returns:
            True if successful
        """
        console.print("\n" + "="*60)
        console.print("[bold cyan]STEP 12: Continue After Upload[/bold cyan]")
        console.print("="*60)
        
        # Wait for uploads to process and button to become available
        import time
        console.print("[dim]Waiting for uploads to complete...[/dim]")
        
        # Wait for the button to be clickable (uploads are done)
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support import expected_conditions as EC
            
            button_selector = self.config['selectors']['upload_continue_button']
            
            # Wait up to 60 seconds for button to be clickable
            console.print("[dim]Waiting for continue button to be enabled...[/dim]")
            button = self.waiter.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, button_selector))
            )
            
            # Extra safety wait
            time.sleep(2)
            
            submitter = FormSubmitter(self.driver, self.waiter)
            success = submitter.click_button(
                button_selector,
                label="Continue (Upload)"
            )
            
            return success
            
        except Exception as e:
            console.print(f"[red]✗ Failed to click continue button: {str(e)}[/red]")
            return False
    
    def _reach_inspector_view(self) -> bool:
        """
        Step 13: Wait for inspector view to load.
        
        This is the final step where the workflow stops for manual validation.
        
        Returns:
            True if inspector view reached
            
        USER NOTE: At this point, manually review the uploaded images in the browser.
        The script will keep the browser open until you close it or press Enter.
        """
        console.print("\n" + "="*60)
        console.print("[bold cyan]STEP 13: Inspector View[/bold cyan]")
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
    
    def _cleanup(self, wait_for_user=True):
        """
        Clean up resources and close browser.
        
        Args:
            wait_for_user: If True, wait for user input before closing browser
        
        USER NOTE: Browser will close after you finish manual validation
        """
        if self.driver:
            if wait_for_user:
                console.print("\n[dim]Press Enter to close browser and exit...[/dim]")
                input()
            console.print("[dim]Closing browser...[/dim]")
            self.driver.quit()
            console.print("[green]✓ Browser closed[/green]")
    
    def run(self, keep_browser_open=False) -> bool:
        """
        Execute the complete workflow.
        
        Runs all 13 steps in sequence, stopping at inspector view for manual validation.
        
        Args:
            keep_browser_open: If True, skip cleanup (for multi-folder workflows)
        
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
                if not self.last_error:
                    self.last_error = "Rotate Images returned False"
                return False
            
            # Step 2: Login (skip if already logged in)
            if not self.skip_login:
                if not self._track_step_time('Login', self._login):
                    console.print("[red]✗ Workflow failed at login[/red]")
                    if not self.last_error:
                        self.last_error = "Login returned False"
                    return False
            else:
                console.print("\n[dim]Skipping login (already authenticated)[/dim]")
            
            # Step 3: Navigate to batches
            if not self._track_step_time('Navigate', self._navigate_to_batches):
                console.print("[red]✗ Workflow failed at batches navigation[/red]")
                if not self.last_error:
                    self.last_error = "Navigate returned False"
                return False
            
            # Step 4: Fill general settings
            if not self._track_step_time('Fill General Settings', self._fill_general_settings):
                console.print("[red]✗ Workflow failed at general settings[/red]")
                if not self.last_error:
                    self.last_error = "Fill General Settings returned False"
                return False
            
            # Step 5: Continue to optional details
            if not self._track_step_time('Continue General', self._click_continue_general_settings):
                console.print("[red]✗ Workflow failed at continue click[/red]")
                if not self.last_error:
                    self.last_error = "Continue General returned False"
                return False
            
            # Step 6: Fill optional details
            if not self._track_step_time('Fill Optional Details', self._fill_optional_details):
                console.print("[red]✗ Workflow failed at optional details[/red]")
                if not self.last_error:
                    self.last_error = "Fill Optional Details returned False"
                return False
            
            # Step 7: Create batch
            if not self._track_step_time('Create Batch Submit', self._create_batch):
                console.print("[red]✗ Workflow failed at batch creation[/red]")
                if not self.last_error:
                    self.last_error = "Create Batch Submit returned False"
                return False
            
            # Step 8: Extract batch ID
            if not self._track_step_time('Extract Batch ID', self._extract_batch_id):
                console.print("[red]✗ Workflow failed at batch ID extraction[/red]")
                if not self.last_error:
                    self.last_error = "Extract Batch ID returned False"
                return False
            
            # Step 9: Magic scan
            if not self._track_step_time('Magic Scan', self._click_magic_scan):
                console.print("[red]✗ Workflow failed at magic scan[/red]")
                if not self.last_error:
                    self.last_error = "Magic Scan returned False"
                return False
            
            # Step 10: Select sides
            if not self._track_step_time('Select Sides', self._select_sides):
                console.print("[red]✗ Workflow failed at sides selection[/red]")
                if not self.last_error:
                    self.last_error = "Select Sides returned False"
                return False
            
            # Step 11: Upload images
            if not self._track_step_time('Upload Images', self._upload_images):
                console.print("[red]✗ Workflow failed at image upload[/red]")
                if not self.last_error:
                    self.last_error = "Upload Images returned False"
                return False
            
            # Step 12: Continue after upload
            if not self._track_step_time('Upload Continue', self._click_continue_upload):
                console.print("[red]✗ Workflow failed at upload continue[/red]")
                if not self.last_error:
                    self.last_error = "Upload Continue returned False"
                return False
            
            # Step 13: Reach inspector view
            if not self._track_step_time('Inspector View', self._reach_inspector_view):
                console.print("[red]✗ Workflow failed at inspector view[/red]")
                if not self.last_error:
                    self.last_error = "Inspector View returned False"
                return False
            
            # Print summary
            self._print_summary()
            
            console.print("\n[bold green]✓ WORKFLOW COMPLETED SUCCESSFULLY[/bold green]")
            return True
            
        except KeyboardInterrupt:
            console.print("\n[yellow]⚠ Workflow interrupted by user[/yellow]")
            return False
            
        except Exception as e:
            # Ensure last_error and current_step are recorded
            if not self.last_error:
                self.last_error = str(e)
            console.print(f"\n[bold red]✗ WORKFLOW FAILED: {str(e)}[/bold red]")
            return False
            
        finally:
            # Cleanup unless told to keep browser open for next folder
            if not keep_browser_open:
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
  # Single folder (uses default config)
  python scripts/image_upload_workflow.py --folder A3
  
  # Multiple folders
  python scripts/image_upload_workflow.py --folder A3 B5 C2
  
  # With custom config
  python scripts/image_upload_workflow.py --config my_config.json --folder A3
  
  # With headless mode
  python scripts/image_upload_workflow.py --folder A3 B5 --headless
  
  # Full paths
  python scripts/image_upload_workflow.py --folder /path/A3 /path/B5

For more information, see docs/USAGE.md
        """
    )
    
    parser.add_argument(
        '--config',
        default='config/upload_config.json',
        help='Path to JSON configuration file (default: config/upload_config.json)'
    )
    
    parser.add_argument(
        '--folder',
        nargs='+',
        help='One or more folder names or paths. Examples: --folder A3 B5 C2 OR --folder /full/path/A3 /full/path/B5'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode (no visible window)'
    )
    
    args = parser.parse_args()
    
    # Ensure at least one folder is provided
    if not args.folder:
        console.print("[red]Error: --folder argument is required[/red]")
        console.print("Example: python scripts/image_upload_workflow.py --config config.json --folder A3")
        sys.exit(1)
    
    folders = args.folder
    total_folders = len(folders)
    results = []  # Track results: {folder, status, step, error, images, time}
    shared_driver = None  # Shared WebDriver across all folders
    
    console.print(f"\n[bold cyan]Starting batch workflow for {total_folders} folder(s)[/bold cyan]\n")
    
    try:
        for idx, folder in enumerate(folders, 1):
            console.print("\n" + "="*70)
            console.print(f"[bold magenta]PROCESSING FOLDER {idx}/{total_folders}: {folder}[/bold magenta]")
            console.print("="*70 + "\n")
            workflow = None
            
            try:
                # First folder: create new workflow with new driver
                # Subsequent folders: reuse driver and skip login
                if idx == 1:
                    workflow = CardDealerProWorkflow(args.config, folder, args.headless)
                else:
                    workflow = CardDealerProWorkflow(args.config, folder, args.headless, 
                                                    shared_driver=shared_driver, skip_login=True)
                
                # For multi-folder: keep browser open between batches
                keep_open = idx < total_folders
                success = workflow.run(keep_browser_open=keep_open)
                
                # Save driver reference for next folder
                if idx == 1:
                    shared_driver = workflow.driver
                
                if success:
                    results.append({
                        "folder": folder, 
                        "status": "success", 
                        "step": "Complete", 
                        "error": None,
                        "images": workflow.total_images,
                        "time": sum(workflow.step_timings.values())
                    })
                    console.print(f"\n[bold green]✓ Folder {idx}/{total_folders} completed: {folder}[/bold green]")
                else:
                    results.append({
                        "folder": folder, 
                        "status": "failed", 
                        "step": getattr(workflow, 'current_step', 'Unknown'), 
                        "error": getattr(workflow, 'last_error', 'Workflow returned False'),
                        "images": workflow.total_images if hasattr(workflow, 'total_images') else 0,
                        "time": sum(workflow.step_timings.values()) if hasattr(workflow, 'step_timings') else 0
                    })
                    console.print(f"\n[bold red]✗ Folder {idx}/{total_folders} failed: {folder}[/bold red]")
                    
            except Exception as e:
                error_msg = str(e)
                # Prefer step/error recorded by workflow, fall back to parsing
                step = getattr(workflow, 'current_step', 'Unknown')
                error_value = getattr(workflow, 'last_error', error_msg)
                
                results.append({
                    "folder": folder, 
                    "status": "error", 
                    "step": step, 
                    "error": error_value,
                    "images": workflow.total_images if hasattr(workflow, 'total_images') else 0,
                    "time": sum(workflow.step_timings.values()) if hasattr(workflow, 'step_timings') else 0
                })
                console.print(f"\n[bold red]✗ Error processing folder {folder}: {error_msg}[/bold red]")
                
                # Save driver reference even if failed (for next folder)
                if idx == 1 and workflow.driver:
                    shared_driver = workflow.driver
            
            # Small pause between batches (except after last one)
            if idx < total_folders:
                console.print("\n[dim]Pausing 3 seconds before next folder...[/dim]")
                import time
                time.sleep(3)
    
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Workflow interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Fatal error: {str(e)}[/bold red]")
    finally:
        # ALWAYS show summary, even if interrupted or errored
        console.print("\n" + "="*70)
        console.print("[bold cyan]BATCH WORKFLOW SUMMARY[/bold cyan]")
        console.print("="*70)
        
        from rich.table import Table
        summary_table = Table(show_header=True, header_style="bold cyan")
        summary_table.add_column("#", style="dim", width=4)
        summary_table.add_column("Folder", style="cyan", width=15)
        summary_table.add_column("Images", style="magenta", width=8, justify="right")
        summary_table.add_column("Time", style="blue", width=10, justify="right")
        summary_table.add_column("Status", width=12)
        summary_table.add_column("Step", style="yellow", width=20)
        summary_table.add_column("Error", style="dim")
        
        successful = 0
        failed = 0
        
        for idx, result in enumerate(results, 1):
            if result["status"] == "success":
                status_text = "[green]✓ Success[/green]"
                successful += 1
                error_text = ""
            else:
                status_text = "[red]✗ Failed[/red]"
                failed += 1
                error_text = result["error"] or "Unknown error"
            
            step_text = result.get("step", "Unknown")
            images = result.get("images", 0)
            time_taken = result.get("time", 0)
            time_str = f"{time_taken:.1f}s" if time_taken > 0 else "-"
            
            summary_table.add_row(str(idx), result["folder"], str(images), time_str, status_text, step_text, error_text)
        
        console.print(summary_table)
        console.print()
        console.print(f"Total: {total_folders} | [green]Success: {successful}[/green] | [red]Failed: {failed}[/red]")
        console.print("="*70)
        
        # Rainbow text for fun
        rainbow_text = "Nick was here"
        colors = ["red", "yellow", "green", "cyan", "blue", "magenta"]
        rainbow_output = ""
        for i, char in enumerate(rainbow_text):
            color = colors[i % len(colors)]
            rainbow_output += f"[{color}]{char}[/{color}]"
        console.print(f"\n{rainbow_output}\n")
        
        sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
