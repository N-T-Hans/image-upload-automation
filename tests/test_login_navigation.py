#!/usr/bin/env python3
"""
Test script for login and navigation functionality.

Tests the login process and basic navigation independently from the full workflow.
Use this to verify your credentials and selectors work before attempting uploads.

Usage:
    python tests/test_login_navigation.py --config path/to/test_config.json
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
    FormNavigator
)
from config import SELENIUM_TIMEOUT, SELENIUM_HEADLESS

console = Console()


def test_login_navigation(config_path: str, headless: bool = False):
    """
    Test login and navigation functionality.
    
    Args:
        config_path: Path to configuration file
        headless: Run in headless mode
    """
    console.print(Panel.fit(
        "[bold cyan]Login & Navigation Test[/bold cyan]\n"
        f"Config: {config_path}",
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
    
    try:
        # Load config
        console.print("\n[cyan]Step 1: Load Configuration[/cyan]")
        with open(config_path, 'r') as f:
            config = json.load(f)
        console.print("[green]✓ Configuration loaded[/green]")
        
        # Get credentials
        username = os.getenv('CDP_USERNAME')
        password = os.getenv('CDP_PASSWORD')
        
        if not username or not password:
            console.print("[red]✗ Credentials not found in .env file[/red]")
            console.print("[yellow]Action Required:[/yellow]")
            console.print("  1. Ensure .env file exists in project root")
            console.print("  2. Set CDP_USERNAME and CDP_PASSWORD")
            return False
        
        console.print(f"[green]✓ Credentials loaded (username: {username})[/green]")
        
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
        
        # Test selectors exist in config
        console.print("\n[cyan]Step 3: Validate Selectors in Config[/cyan]")
        required_selectors = [
            'username_input',
            'password_input',
            'login_button',
            'create_batch_button'
        ]
        
        missing = [s for s in required_selectors if s not in config.get('selectors', {})]
        if missing:
            console.print(f"[red]✗ Missing selectors: {', '.join(missing)}[/red]")
            console.print("[yellow]Action Required:[/yellow]")
            console.print("  Update config file with all required selectors")
            return False
        
        console.print("[green]✓ All required selectors present[/green]")
        
        # Test login
        console.print("\n[cyan]Step 4: Test Login[/cyan]")
        login_handler = LoginHandler(driver, waiter)
        
        success = login_handler.login(
            login_url=config['urls']['login'],
            username=username,
            password=password,
            username_selector=config['selectors']['username_input'],
            password_selector=config['selectors']['password_input'],
            login_button_selector=config['selectors']['login_button'],
            success_url_pattern=config['urls']['batches']
        )
        
        if not success:
            console.print("[red]✗ Login failed[/red]")
            console.print("[yellow]Action Required:[/yellow]")
            console.print("  1. Verify credentials are correct")
            console.print("  2. Check login selectors in config")
            console.print("  3. Manually test login in browser")
            return False
        
        console.print("[green]✓ Login successful[/green]")
        
        # Test navigation to batches page
        console.print("\n[cyan]Step 5: Test Navigation to Batches Page[/cyan]")
        navigator = FormNavigator(driver, waiter)
        
        nav_success = navigator.navigate_to(
            config['urls']['batches'],
            wait_for_selector=config['selectors']['create_batch_button']
        )
        
        if not nav_success:
            console.print("[red]✗ Navigation failed[/red]")
            console.print("[yellow]Action Required:[/yellow]")
            console.print("  1. Verify batches URL is correct")
            console.print("  2. Check create_batch_button selector")
            return False
        
        console.print("[green]✓ Navigation successful[/green]")
        console.print(f"[dim]Current URL: {driver.current_url}[/dim]")
        
        # Test that create batch button is visible
        console.print("\n[cyan]Step 6: Verify Create Batch Button[/cyan]")
        try:
            element = waiter.wait_for_element_visible(
                config['selectors']['create_batch_button']
            )
            console.print("[green]✓ Create batch button found and visible[/green]")
        except Exception as e:
            console.print("[red]✗ Create batch button not found[/red]")
            console.print(f"[dim]Error: {str(e)}[/dim]")
            console.print("[yellow]Action Required:[/yellow]")
            console.print("  1. Update create_batch_button selector in config")
            console.print("  2. Use browser DevTools to find correct selector")
            return False
        
        # Summary
        console.print("\n" + "="*60)
        console.print("[bold green]✓ ALL TESTS PASSED[/bold green]")
        console.print("="*60 + "\n")
        
        table = Table(title="Test Results", show_header=True)
        table.add_column("Test", style="cyan")
        table.add_column("Status", style="green")
        
        table.add_row("Configuration Loading", "✓ Pass")
        table.add_row("Credentials Loaded", "✓ Pass")
        table.add_row("WebDriver Setup", "✓ Pass")
        table.add_row("Selector Validation", "✓ Pass")
        table.add_row("Login Process", "✓ Pass")
        table.add_row("Batches Navigation", "✓ Pass")
        table.add_row("Create Button Found", "✓ Pass")
        
        console.print(table)
        
        # Next steps
        console.print("\n[cyan]Next Steps:[/cyan]")
        console.print("  1. Browser will stay open for 10 seconds for inspection")
        console.print("  2. Verify you're on the correct page")
        console.print("  3. If everything looks good, proceed to upload test")
        console.print("     Run: python tests/test_upload_config.py")
        
        # Keep browser open briefly
        console.print("\n[dim]Keeping browser open for inspection...[/dim]")
        import time
        time.sleep(10)
        
        return True
        
    except Exception as e:
        console.print(f"\n[bold red]✗ TEST FAILED WITH ERROR:[/bold red]")
        console.print(f"[red]{str(e)}[/red]")
        console.print("\n[yellow]Troubleshooting:[/yellow]")
        console.print("  • Verify config file path is correct")
        console.print("  • Check .env file exists with credentials")
        console.print("  • Ensure all selectors are correct")
        console.print("  • Try running without --headless to see what's happening")
        return False
        
    finally:
        if driver:
            console.print("\n[dim]Closing browser...[/dim]")
            driver.quit()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test login and navigation functionality",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/test_login_navigation.py --config my_batch.json
  python tests/test_login_navigation.py --config test_config.json --headless

This test will:
  1. Load your configuration
  2. Load credentials from .env
  3. Initialize WebDriver
  4. Attempt login
  5. Navigate to batches page
  6. Verify page elements

Note: Browser will stay open for 10 seconds for inspection.
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
    
    args = parser.parse_args()
    
    success = test_login_navigation(args.config, args.headless)
    sys.exit(0 if success else 1)
