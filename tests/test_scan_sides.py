#!/usr/bin/env python3
"""
Test up to selecting sides on the "Select Cards To Scan" screen.

Runs: Login → Navigate to General Settings → Fill basic fields → Continue →
Create Batch → Magic Scan → Select Card Type radio (if provided) → Click Sides tile.
Stops after selecting the sides option (does NOT proceed to upload).

Usage:
    python tests/test_scan_sides.py --config config/upload_config.json [--headless]
"""

import os
import sys
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

from tools.web_automation_tools import ElementWaiter, LoginHandler, FormNavigator, FormSubmitter
from config import SELENIUM_TIMEOUT, SELENIUM_HEADLESS

console = Console()


def run_scan_sides(config_path: str, headless: bool = False) -> bool:
    console.print(Panel.fit(
        "[bold cyan]Scan Sides Selection Test[/bold cyan]\n"
        f"Config: {config_path}",
        border_style="cyan"
    ))

    # Load environment
    config_env = Path(__file__).parent.parent / "config" / ".env"
    root_env = Path(__file__).parent.parent / ".env"
    if config_env.exists():
        load_dotenv(config_env, override=True)
    elif root_env.exists():
        load_dotenv(root_env, override=True)
    else:
        load_dotenv()

    # Read config
    with open(config_path, "r") as f:
        config = json.load(f)

    # Setup WebDriver
    options = Options()
    if headless or SELENIUM_HEADLESS:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(2)
    waiter = ElementWaiter(driver, SELENIUM_TIMEOUT)

    try:
        # Step A: Login
        username = os.getenv("CDP_USERNAME")
        password = os.getenv("CDP_PASSWORD")
        login_handler = LoginHandler(driver, waiter)

        console.print("\n[bold cyan]Login[/bold cyan]")
        login_success = login_handler.login(
            login_url=config['urls']['login'],
            username=username,
            password=password,
            username_selector=config['selectors']['username_input'],
            password_selector=config['selectors']['password_input'],
            login_button_selector=config['selectors']['login_button'],
            success_url_pattern=config['urls']['inventory'],
            continue_button_selector=config['selectors'].get('continue_button')
        )
        if not login_success:
            console.print("[red]✗ Login failed[/red]")
            return False

        # Step B: Navigate directly to General Settings
        console.print("\n[bold cyan]Navigate to General Settings[/bold cyan]")
        navigator = FormNavigator(driver, waiter)
        wait_selector = (
            config['selectors'].get('batch_name_input')
            or config['selectors'].get('batch_type_select')
            or config['selectors'].get('sport_type_select')
        )
        navigator.navigate_to(config['urls']['general_settings'], wait_for_selector=wait_selector)

        # Step C: Fill minimal General Settings
        console.print("\n[bold cyan]Fill General Settings[/bold cyan]")
        submitter = FormSubmitter(driver, waiter)
        settings = config.get('general_settings', {})
        selectors = config.get('selectors', {})

        # Batch name
        if selectors.get('batch_name_input') and settings.get('batch_name'):
            submitter.fill_text_input(selectors['batch_name_input'], settings['batch_name'], label="Batch Name")
        # Batch type
        if selectors.get('batch_type_select') and settings.get('batch_type'):
            if selectors.get('batch_type_select_type') == 'custom':
                submitter.select_custom_dropdown_option(selectors['batch_type_select'], settings['batch_type'], label="Batch Type")
            else:
                submitter.select_dropdown_option(selectors['batch_type_select'], settings['batch_type'], label="Batch Type")
        # Sport/Game type
        if selectors.get('sport_type_select') and settings.get('sport_type'):
            if selectors.get('sport_type_select_type') == 'custom':
                submitter.select_custom_dropdown_option(selectors['sport_type_select'], settings['sport_type'], label="Sport Type")
            else:
                submitter.select_dropdown_option(selectors['sport_type_select'], settings['sport_type'], label="Sport Type")

        # Continue to Optional Details
        console.print("\n[bold cyan]Continue to Optional Details[/bold cyan]")
        submitter.click_button(selectors['continue_button_general'], label="Continue (General Settings)")
        waiter.wait_for_url_contains('optional-details')

        # Step D: Create Batch (submit)
        console.print("\n[bold cyan]Create Batch[/bold cyan]")
        submitter.click_button(selectors['create_batch_submit'], label="Create Batch (Submit)")
        waiter.wait_for_url_contains('/batches')

        # Step E: Magic Scan
        console.print("\n[bold cyan]Magic Scan[/bold cyan]")
        submitter.click_button(selectors['magic_scan_button'], label="Magic Scan")
        waiter.wait_for_url_contains('/sides')

        # Step F: Select Card Type + Sides tile
        console.print("\n[bold cyan]Select Card Type and Sides[/bold cyan]")
        # Card type radio (optional)
        if selectors.get('scan_card_type_radio'):
            try:
                submitter.click_button(selectors['scan_card_type_radio'], label=f"Card Type ({config.get('scan_options', {}).get('card_type', '')})")
            except Exception:
                console.print("[yellow]⚠ Could not click Card Type radio; continuing[/yellow]")

        # Prefer clicking the sides tile via XPath; fallback to dropdown
        if selectors.get('scan_sides_option'):
            submitter.click_button(selectors['scan_sides_option'], label=f"Sides ({config.get('scan_options', {}).get('sides', '')})")
            console.print("[green]✓ Sides tile clicked[/green]")
        elif selectors.get('scan_sides_select') and config.get('scan_options', {}).get('sides'):
            val = config['scan_options']['sides']
            if selectors.get('scan_sides_select_type') == 'custom':
                submitter.select_custom_dropdown_option(selectors['scan_sides_select'], val, label="Sides")
            else:
                submitter.select_dropdown_option(selectors['scan_sides_select'], val, label="Sides")
            console.print("[green]✓ Sides selected via dropdown[/green]")
        else:
            console.print("[yellow]⚠ No sides selector configured[/yellow]")

        console.print("\n[bold green]✓ Test completed: sides option selected[/bold green]")
        console.print("\n[dim]Keeping browser open for 30 seconds...[/dim]")
        import time
        time.sleep(30)
        return True

    except Exception as e:
        console.print(f"\n[bold red]✗ TEST FAILED: {str(e)}[/bold red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        return False

    finally:
        console.print("\n[dim]Closing browser...[/dim]")
        driver.quit()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run up to sides selection screen")
    parser.add_argument('--config', required=True, help='Path to JSON configuration file')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    args = parser.parse_args()

    ok = run_scan_sides(args.config, args.headless)
    sys.exit(0 if ok else 1)
