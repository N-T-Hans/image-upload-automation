#!/usr/bin/env python3
"""
Test script for upload configuration and selectors.

Tests form filling and selector accuracy without actually uploading.
Use this to verify all your form selectors work before running the full workflow.

Usage:
    python tests/test_upload_config.py --config path/to/test_config.json
"""

import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from tools.web_automation_tools import (
    ElementWaiter,
    LoginHandler,
    FormNavigator,
    FormSubmitter
)
from config import SELENIUM_TIMEOUT, SELENIUM_HEADLESS

console = Console()


def test_upload_config(config_path: str, headless: bool = False, dry_run: bool = True):
    """
    Test upload configuration and selectors.
    
    Args:
        config_path: Path to configuration file
        headless: Run in headless mode
        dry_run: If True, don't actually submit forms (recommended)
    """
    console.print(Panel.fit(
        "[bold cyan]Upload Configuration Test[/bold cyan]\n"
        f"Config: {config_path}\n"
        f"Dry Run: {'Yes (recommended)' if dry_run else 'No - WILL SUBMIT FORMS!'}",
        border_style="cyan"
    ))
    
    # Load environment
    load_dotenv()
    
    # Try config/.env first, then fall back to root .env
    config_env = Path(__file__).parent.parent / "config" / ".env"
    root_env = Path(__file__).parent.parent / ".env"
    
    if config_env.exists():
        load_dotenv(config_env, override=True)
    elif root_env.exists():
        load_dotenv(root_env, override=True)
    
    driver = None
    test_results = {}
    
    try:
        # Load config
        console.print("\n[cyan]Step 1: Load Configuration[/cyan]")
        with open(config_path, 'r') as f:
            config = json.load(f)
        console.print("[green]✓ Configuration loaded[/green]")
        
        # Setup WebDriver
        console.print("\n[cyan]Step 2: Initialize WebDriver[/cyan]")
        options = Options()
        if headless or SELENIUM_HEADLESS:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(2)
        
        waiter = ElementWaiter(driver, SELENIUM_TIMEOUT)
        console.print("[green]✓ WebDriver initialized[/green]")
        
        # Login first
        console.print("\n[cyan]Step 3: Login (required to access forms)[/cyan]")
        username = os.getenv('CDP_USERNAME')
        password = os.getenv('CDP_PASSWORD')
        
        login_handler = LoginHandler(driver, waiter)
        login_success = login_handler.login(
            login_url=config['urls']['login'],
            username=username,
            password=password,
            username_selector=config['selectors']['username_input'],
            password_selector=config['selectors']['password_input'],
            login_button_selector=config['selectors']['login_button'],
            success_url_pattern=config['urls']['batches']
        )
        
        if not login_success:
            console.print("[red]✗ Login failed - cannot proceed with form tests[/red]")
            return False
        
        test_results['login'] = True
        console.print("[green]✓ Login successful[/green]")
        
        # Navigate and click create batch
        console.print("\n[cyan]Step 4: Navigate and Click Create Batch[/cyan]")
        navigator = FormNavigator(driver, waiter)
        submitter = FormSubmitter(driver, waiter)
        
        navigator.navigate_to(config['urls']['batches'])
        
        if dry_run:
            # Just verify button exists
            try:
                waiter.wait_for_element_visible(config['selectors']['create_batch_button'])
                console.print("[green]✓ Create batch button found[/green]")
                test_results['create_batch_button'] = True
                
                # Navigate directly to general settings for testing
                console.print("[dim]Navigating directly to general settings page for testing...[/dim]")
                driver.get(config['urls']['general_settings'])
                waiter.wait_for_url_contains('general-settings')
            except Exception as e:
                console.print(f"[red]✗ Create batch button not found: {str(e)}[/red]")
                test_results['create_batch_button'] = False
        else:
            # Actually click it
            submitter.click_button(config['selectors']['create_batch_button'], "Create Batch")
            waiter.wait_for_url_contains('general-settings')
            test_results['create_batch_button'] = True
        
        # Test general settings selectors
        console.print("\n[cyan]Step 5: Test General Settings Selectors[/cyan]")
        
        selectors_to_test = {
            'batch_name_input': 'text input',
            'batch_type_select': 'dropdown',
            'sport_type_select': 'dropdown',
            'title_template_select': 'dropdown',
            'description_input': 'text input',
            'continue_button_general': 'button'
        }
        
        for selector_name, element_type in selectors_to_test.items():
            try:
                selector = config['selectors'].get(selector_name)
                if not selector:
                    console.print(f"[yellow]⚠ {selector_name} not in config - skipping[/yellow]")
                    test_results[selector_name] = 'missing'
                    continue
                
                element = waiter.wait_for_element_visible(selector)
                console.print(f"[green]✓ {selector_name} ({element_type}) - found[/green]")
                test_results[selector_name] = True
                
                # Try filling with test data if dry_run
                if dry_run:
                    if element_type == 'text input':
                        element.clear()
                        element.send_keys("TEST_VALUE")
                        console.print(f"[dim]  → Filled with test value[/dim]")
                    elif element_type == 'dropdown':
                        from selenium.webdriver.support.ui import Select
                        select = Select(element)
                        options = [opt.text for opt in select.options if opt.text.strip()]
                        if options:
                            console.print(f"[dim]  → Found {len(options)} options: {', '.join(options[:3])}{'...' if len(options) > 3 else ''}[/dim]")
                
            except Exception as e:
                console.print(f"[red]✗ {selector_name} - NOT FOUND[/red]")
                console.print(f"[dim]  Error: {str(e)}[/dim]")
                test_results[selector_name] = False
        
        # Test optional details selectors if configured
        if config.get('optional_details'):
            console.print("\n[cyan]Step 6: Test Optional Details Selectors[/cyan]")
            
            if not dry_run:
                # Click continue to reach optional details
                submitter.click_button(config['selectors']['continue_button_general'])
                waiter.wait_for_url_contains('optional-details')
            
            for field_name in config['optional_details'].keys():
                selector_key = f'optional_{field_name}'
                selector = config['selectors'].get(selector_key)
                
                if not selector:
                    console.print(f"[yellow]⚠ {selector_key} not in selectors - skipping[/yellow]")
                    continue
                
                try:
                    waiter.wait_for_element_visible(selector)
                    console.print(f"[green]✓ {selector_key} - found[/green]")
                    test_results[selector_key] = True
                except Exception as e:
                    console.print(f"[red]✗ {selector_key} - NOT FOUND[/red]")
                    test_results[selector_key] = False
        else:
            console.print("\n[dim]No optional details configured - skipping[/dim]")
        
        # Test upload page selectors (navigate without creating batch)
        console.print("\n[cyan]Step 7: Test Upload Selectors (Verification Only)[/cyan]")
        
        upload_selectors = {
            'magic_scan_button': 'Magic scan button',
            'sides_continue_button': 'Sides continue button',
            'upload_file_input': 'File upload input',
            'upload_continue_button': 'Upload continue button'
        }
        
        console.print("[dim]Note: Cannot test these without creating an actual batch[/dim]")
        console.print("[dim]Verifying selectors exist in config...[/dim]")
        
        for selector_name, description in upload_selectors.items():
            if selector_name in config['selectors']:
                console.print(f"[green]✓ {selector_name} - configured[/green]")
                test_results[selector_name] = 'configured'
            else:
                console.print(f"[yellow]⚠ {selector_name} - MISSING from config[/yellow]")
                test_results[selector_name] = 'missing'
        
        # Summary
        console.print("\n" + "="*60)
        console.print("[bold cyan]TEST RESULTS SUMMARY[/bold cyan]")
        console.print("="*60 + "\n")
        
        table = Table(title="Selector Test Results", show_header=True)
        table.add_column("Selector", style="cyan")
        table.add_column("Status", style="white")
        
        for selector_name, result in test_results.items():
            if result is True:
                status = "[green]✓ Found and Tested[/green]"
            elif result == 'configured':
                status = "[blue]○ Configured (not tested)[/blue]"
            elif result == 'missing':
                status = "[yellow]⚠ Missing from config[/yellow]"
            else:
                status = "[red]✗ Not Found[/red]"
            
            table.add_row(selector_name, status)
        
        console.print(table)
        
        # Calculate pass rate
        testable = [k for k, v in test_results.items() if v in [True, False]]
        passed = [k for k, v in test_results.items() if v is True]
        
        if testable:
            pass_rate = (len(passed) / len(testable)) * 100
            console.print(f"\n[cyan]Pass Rate: {pass_rate:.1f}% ({len(passed)}/{len(testable)} selectors working)[/cyan]")
        
        # Recommendations
        console.print("\n[cyan]Recommendations:[/cyan]")
        
        failed = [k for k, v in test_results.items() if v is False]
        missing = [k for k, v in test_results.items() if v == 'missing']
        
        if failed:
            console.print("\n[yellow]Fix These Selectors (Not Found):[/yellow]")
            for selector in failed:
                console.print(f"  • {selector}")
                console.print(f"    Update in config: selectors.{selector}")
        
        if missing:
            console.print("\n[yellow]Add These Selectors to Config:[/yellow]")
            for selector in missing:
                console.print(f"  • {selector}")
        
        if not failed and not missing:
            console.print("\n[bold green]✓ All configured selectors working![/bold green]")
            console.print("\n[cyan]Next Steps:[/cyan]")
            console.print("  1. Review browser window (staying open for 15 seconds)")
            console.print("  2. If everything looks good, run full workflow:")
            console.print("     python scripts/image_upload_workflow.py --config your_config.json")
            
            # Keep browser open longer for inspection
            import time
            console.print("\n[dim]Keeping browser open for inspection...[/dim]")
            time.sleep(15)
        
        return len(failed) == 0
        
    except Exception as e:
        console.print(f"\n[bold red]✗ TEST FAILED WITH ERROR:[/bold red]")
        console.print(f"[red]{str(e)}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        return False
        
    finally:
        if driver:
            console.print("\n[dim]Closing browser...[/dim]")
            driver.quit()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test upload configuration and selectors",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/test_upload_config.py --config my_batch.json
  python tests/test_upload_config.py --config test_config.json --no-dry-run

This test will:
  1. Login to CardDealerPro
  2. Navigate to forms
  3. Test all configured selectors
  4. Verify elements exist and are accessible
  5. Report any missing or incorrect selectors

Dry Run Mode (default):
  - Tests selectors without submitting forms
  - Safe to run multiple times
  - Recommended for initial testing

No Dry Run Mode:
  - Actually clicks buttons and submits forms
  - May create test batches
  - Use with caution!
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
        help='Run browser in headless mode'
    )
    
    parser.add_argument(
        '--no-dry-run',
        action='store_true',
        help='Actually submit forms (not recommended for testing)'
    )
    
    args = parser.parse_args()
    
    if args.no_dry_run:
        console.print("[bold yellow]⚠ WARNING: Running without dry-run mode![/bold yellow]")
        console.print("[yellow]This will actually submit forms and may create batches.[/yellow]")
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            console.print("Cancelled.")
            sys.exit(0)
    
    success = test_upload_config(args.config, args.headless, dry_run=not args.no_dry_run)
    sys.exit(0 if success else 1)
