"""
Web automation tools for CardDealerPro batch upload workflow.

This module provides Selenium-based utilities for browser automation including
element waiting, login handling, form navigation, and form submission.

USER NOTE: These classes handle the browser automation. You'll need to provide
CSS selectors in your config.json file. See docs/SELECTOR_GUIDE.md for help.
"""

import os
import re
import time
from typing import Optional, List
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException
)
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from rich.console import Console

# Import configuration constants
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    SELENIUM_TIMEOUT,
    SELENIUM_HEADLESS,
    MAX_LOGIN_RETRIES,
    BATCH_ID_REGEX,
    BATCH_ID_FALLBACK_SELECTORS
)

console = Console()


class ElementWaiter:
    """
    Centralized explicit wait patterns for Selenium WebDriver.
    
    Provides reusable wait conditions for common scenarios like element visibility,
    clickability, URL changes, etc. Uses WebDriverWait for robust element detection.
    
    USER NOTE: If you experience timeout errors, increase SELENIUM_TIMEOUT in config.py
    """
    
    def __init__(self, driver: webdriver.Chrome, timeout: int = SELENIUM_TIMEOUT):
        """
        Initialize element waiter.
        
        Args:
            driver: Selenium WebDriver instance
            timeout: Maximum time to wait for conditions (seconds)
        """
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)
    
    def wait_for_element_visible(self, selector: str, by: By = By.CSS_SELECTOR) -> object:
        """
        Wait for element to be visible on page.
        
        Args:
            selector: CSS selector or XPath expression
            by: Locator strategy (default: CSS_SELECTOR)
            
        Returns:
            WebElement when visible
            
        Raises:
            TimeoutException: If element doesn't appear within timeout
            
        USER NOTE: If this fails, verify the selector is correct using browser DevTools
        """
        try:
            element = self.wait.until(
                EC.visibility_of_element_located((by, selector))
            )
            return element
        except TimeoutException:
            console.print(f"[red]✗ Timeout waiting for element: {selector}[/red]")
            raise
    
    def wait_for_element_clickable(self, selector: str, by: By = By.CSS_SELECTOR) -> object:
        """
        Wait for element to be clickable (visible and enabled).
        
        Args:
            selector: CSS selector or XPath expression
            by: Locator strategy (default: CSS_SELECTOR)
            
        Returns:
            WebElement when clickable
            
        Raises:
            TimeoutException: If element doesn't become clickable within timeout
        """
        try:
            element = self.wait.until(
                EC.element_to_be_clickable((by, selector))
            )
            return element
        except TimeoutException:
            console.print(f"[red]✗ Timeout waiting for clickable element: {selector}[/red]")
            raise
    
    def wait_for_url_contains(self, url_fragment: str) -> bool:
        """
        Wait for URL to contain specific text.
        
        Useful for verifying page navigation after form submission.
        
        Args:
            url_fragment: Text that should appear in URL
            
        Returns:
            True when URL contains fragment
            
        Raises:
            TimeoutException: If URL doesn't change within timeout
        """
        try:
            self.wait.until(EC.url_contains(url_fragment))
            return True
        except TimeoutException:
            current_url = self.driver.current_url
            console.print(f"[red]✗ Timeout waiting for URL containing '{url_fragment}'[/red]")
            console.print(f"[dim]Current URL: {current_url}[/dim]")
            raise
    
    def wait_for_url_matches(self, pattern: str) -> bool:
        """
        Wait for URL to match regex pattern.
        
        Args:
            pattern: Regular expression pattern
            
        Returns:
            True when URL matches pattern
            
        Raises:
            TimeoutException: If URL doesn't match within timeout
        """
        try:
            self.wait.until(EC.url_matches(pattern))
            return True
        except TimeoutException:
            current_url = self.driver.current_url
            console.print(f"[red]✗ Timeout waiting for URL matching pattern: {pattern}[/red]")
            console.print(f"[dim]Current URL: {current_url}[/dim]")
            raise
    
    def wait_for_element_stale(self, element: object) -> bool:
        """
        Wait for element to become stale (removed from DOM).
        
        Useful after form submissions or page transitions.
        
        Args:
            element: WebElement to check for staleness
            
        Returns:
            True when element is stale
        """
        try:
            self.wait.until(EC.staleness_of(element))
            return True
        except TimeoutException:
            console.print("[yellow]⚠ Element did not become stale[/yellow]")
            return False


class LoginHandler:
    """
    Handles authentication to CardDealerPro.
    
    Manages login form interaction and verification of successful authentication.
    Credentials are loaded from environment variables for security.
    
    USER NOTE: Ensure CDP_USERNAME and CDP_PASSWORD are set in your .env file
    """
    
    def __init__(self, driver: webdriver.Chrome, waiter: ElementWaiter):
        """
        Initialize login handler.
        
        Args:
            driver: Selenium WebDriver instance
            waiter: ElementWaiter instance for waiting patterns
        """
        self.driver = driver
        self.waiter = waiter
    
    def login(
        self,
        login_url: str,
        username: str,
        password: str,
        username_selector: str,
        password_selector: str,
        login_button_selector: str,
        success_url_pattern: str
    ) -> bool:
        """
        Perform login to CardDealerPro.
        
        Process:
        1. Navigate to login URL
        2. Wait for login form to appear
        3. Fill username and password
        4. Click login button
        5. Verify redirect to expected URL
        
        Args:
            login_url: URL of login page
            username: Username from environment
            password: Password from environment
            username_selector: CSS selector for username input
            password_selector: CSS selector for password input
            login_button_selector: CSS selector for login button
            success_url_pattern: URL fragment expected after successful login
            
        Returns:
            True if login successful, False otherwise
            
        Raises:
            Exception: If login fails after MAX_LOGIN_RETRIES attempts
            
        USER NOTE: If login fails, verify selectors are correct in your config.json
        """
        for attempt in range(1, MAX_LOGIN_RETRIES + 1):
            try:
                console.print(f"\n[cyan]Attempting login (attempt {attempt}/{MAX_LOGIN_RETRIES})...[/cyan]")
                
                # Navigate to login page
                console.print(f"[dim]Navigating to: {login_url}[/dim]")
                self.driver.get(login_url)
                
                # Wait for and fill username
                console.print("[dim]Waiting for username field...[/dim]")
                username_field = self.waiter.wait_for_element_visible(username_selector)
                username_field.clear()
                username_field.send_keys(username)
                console.print("[green]✓ Username entered[/green]")
                
                # Wait for and fill password
                console.print("[dim]Waiting for password field...[/dim]")
                password_field = self.waiter.wait_for_element_visible(password_selector)
                password_field.clear()
                password_field.send_keys(password)
                console.print("[green]✓ Password entered[/green]")
                
                # Click login button
                console.print("[dim]Clicking login button...[/dim]")
                login_button = self.waiter.wait_for_element_clickable(login_button_selector)
                login_button.click()
                
                # Wait for URL to change (indicates login processed)
                console.print("[dim]Waiting for redirect...[/dim]")
                self.waiter.wait_for_url_contains(success_url_pattern)
                
                # Verify we're on the expected page
                current_url = self.driver.current_url
                if success_url_pattern in current_url:
                    console.print(f"[bold green]✓ Login successful![/bold green]")
                    console.print(f"[dim]Current URL: {current_url}[/dim]")
                    return True
                else:
                    console.print(f"[yellow]⚠ Login completed but URL unexpected[/yellow]")
                    console.print(f"[dim]Expected pattern: {success_url_pattern}[/dim]")
                    console.print(f"[dim]Current URL: {current_url}[/dim]")
                    # Continue anyway - might still be valid
                    return True
                    
            except TimeoutException:
                console.print(f"[red]✗ Login attempt {attempt} timed out[/red]")
                if attempt < MAX_LOGIN_RETRIES:
                    console.print("[yellow]Retrying...[/yellow]")
                    time.sleep(2)  # Brief pause before retry
                continue
            
            except Exception as e:
                console.print(f"[red]✗ Login error: {str(e)}[/red]")
                if attempt < MAX_LOGIN_RETRIES:
                    console.print("[yellow]Retrying...[/yellow]")
                    time.sleep(2)
                continue
        
        # All attempts failed
        console.print(f"[bold red]✗ Login failed after {MAX_LOGIN_RETRIES} attempts[/bold red]")
        console.print("[yellow]USER ACTION REQUIRED:[/yellow]")
        console.print("  1. Verify credentials in .env file are correct")
        console.print("  2. Verify login selectors in config.json are correct")
        console.print("  3. Check if website requires CAPTCHA or 2FA")
        raise Exception("Login failed after maximum retries")


class FormNavigator:
    """
    Handles navigation between CardDealerPro pages.
    
    Provides URL navigation with wait for page load, and batch_id extraction
    from URLs during the workflow.
    
    USER NOTE: This class handles page transitions in the 20-step workflow
    """
    
    def __init__(self, driver: webdriver.Chrome, waiter: ElementWaiter):
        """
        Initialize form navigator.
        
        Args:
            driver: Selenium WebDriver instance
            waiter: ElementWaiter instance for waiting patterns
        """
        self.driver = driver
        self.waiter = waiter
    
    def navigate_to(self, url: str, wait_for_selector: Optional[str] = None) -> bool:
        """
        Navigate to URL and wait for page to load.
        
        Args:
            url: Target URL to navigate to
            wait_for_selector: Optional CSS selector to wait for after navigation
            
        Returns:
            True if navigation successful
            
        Raises:
            TimeoutException: If page doesn't load within timeout
        """
        try:
            console.print(f"[cyan]Navigating to: {url}[/cyan]")
            self.driver.get(url)
            
            # Wait for page to be ready
            time.sleep(1)  # Brief pause for page initialization
            
            # If specific element selector provided, wait for it
            if wait_for_selector:
                console.print(f"[dim]Waiting for element: {wait_for_selector}[/dim]")
                self.waiter.wait_for_element_visible(wait_for_selector)
            
            console.print(f"[green]✓ Page loaded[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]✗ Navigation failed: {str(e)}[/red]")
            raise
    
    def extract_batch_id_from_url(self) -> Optional[str]:
        """
        Extract batch_id from current URL using regex.
        
        Attempts to parse batch_id from URL patterns like:
        /batches/{batch_id}/add/types
        
        If regex fails, tries fallback selectors from page DOM.
        
        Returns:
            batch_id string if found, None otherwise
            
        USER NOTE: If extraction fails, check BATCH_ID_REGEX in config.py
        or add more fallback selectors to BATCH_ID_FALLBACK_SELECTORS
        """
        current_url = self.driver.current_url
        console.print(f"[cyan]Extracting batch_id from URL...[/cyan]")
        console.print(f"[dim]Current URL: {current_url}[/dim]")
        
        # Try regex extraction from URL
        match = re.search(BATCH_ID_REGEX, current_url)
        if match:
            batch_id = match.group(1)
            console.print(f"[green]✓ Extracted batch_id from URL: {batch_id}[/green]")
            return batch_id
        
        # Regex failed - try fallback selectors
        console.print("[yellow]⚠ Could not extract batch_id from URL with regex[/yellow]")
        console.print("[dim]Trying fallback DOM selectors...[/dim]")
        
        for selector in BATCH_ID_FALLBACK_SELECTORS:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                batch_id = element.get_attribute('value') or element.text
                if batch_id:
                    console.print(f"[green]✓ Extracted batch_id from DOM ({selector}): {batch_id}[/green]")
                    return batch_id
            except NoSuchElementException:
                continue
        
        # All methods failed
        console.print("[red]✗ Failed to extract batch_id[/red]")
        console.print("[yellow]USER ACTION REQUIRED:[/yellow]")
        console.print(f"  Current URL: {current_url}")
        console.print("  Please check:")
        console.print("    1. BATCH_ID_REGEX pattern in config.py")
        console.print("    2. BATCH_ID_FALLBACK_SELECTORS in config.py")
        console.print("    3. Manually inspect the page to find where batch_id is located")
        
        return None


class FormSubmitter:
    """
    Handles form field filling and submission.
    
    Provides methods for interacting with text inputs, dropdowns, file uploads,
    and buttons with retry logic for stale elements.
    
    USER NOTE: This class fills out the CardDealerPro forms based on your config
    """
    
    def __init__(self, driver: webdriver.Chrome, waiter: ElementWaiter):
        """
        Initialize form submitter.
        
        Args:
            driver: Selenium WebDriver instance
            waiter: ElementWaiter instance for waiting patterns
        """
        self.driver = driver
        self.waiter = waiter
    
    def fill_text_input(self, selector: str, value: str, label: str = "field") -> bool:
        """
        Fill a text input field.
        
        Clears existing value before entering new text.
        
        Args:
            selector: CSS selector for input element
            value: Text value to enter
            label: Human-readable field name for logging
            
        Returns:
            True if successful
            
        Raises:
            TimeoutException: If element not found
        """
        try:
            console.print(f"[dim]Filling {label}...[/dim]")
            element = self.waiter.wait_for_element_visible(selector)
            element.clear()  # Clear any existing value
            element.send_keys(value)
            console.print(f"[green]✓ Filled {label}: {value}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]✗ Failed to fill {label}: {str(e)}[/red]")
            raise
    
    def select_dropdown_option(self, selector: str, value: str, label: str = "dropdown") -> bool:
        """
        Select option from dropdown by visible text.
        
        Uses Selenium's Select class to interact with <select> elements.
        
        Args:
            selector: CSS selector for select element
            value: Visible text of option to select
            label: Human-readable field name for logging
            
        Returns:
            True if successful
            
        Raises:
            TimeoutException: If element not found
            NoSuchElementException: If option value not found
            
        USER NOTE: The value must match the visible text in the dropdown exactly
        """
        try:
            console.print(f"[dim]Selecting {label}...[/dim]")
            element = self.waiter.wait_for_element_visible(selector)
            select = Select(element)
            
            # Try selecting by visible text
            select.select_by_visible_text(value)
            console.print(f"[green]✓ Selected {label}: {value}[/green]")
            return True
            
        except NoSuchElementException:
            # Try selecting by value attribute as fallback
            try:
                select.select_by_value(value)
                console.print(f"[green]✓ Selected {label}: {value} (by value)[/green]")
                return True
            except:
                console.print(f"[red]✗ Option '{value}' not found in {label}[/red]")
                console.print("[yellow]USER ACTION REQUIRED:[/yellow]")
                console.print(f"  Check that '{value}' exists in the dropdown options")
                raise
        except Exception as e:
            console.print(f"[red]✗ Failed to select {label}: {str(e)}[/red]")
            raise
    
    def upload_files(self, selector: str, file_paths: List[str]) -> bool:
        """
        Upload multiple files to file input element.
        
        Sends newline-separated file paths to file input. This works for
        <input type="file" multiple> elements.
        
        Args:
            selector: CSS selector for file input element
            file_paths: List of absolute paths to files
            
        Returns:
            True if successful
            
        Raises:
            TimeoutException: If element not found
            
        USER NOTE: File paths must be absolute. The file input must accept multiple files.
        """
        try:
            console.print(f"[cyan]Uploading {len(file_paths)} files...[/cyan]")
            
            # Wait for file input (note: file inputs are often hidden)
            element = self.waiter.wait_for_element_visible(selector)
            
            # Join all file paths with newline (for multiple file upload)
            files_string = "\n".join(file_paths)
            
            # Send file paths to input
            element.send_keys(files_string)
            
            console.print(f"[green]✓ Uploaded {len(file_paths)} files[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]✗ Failed to upload files: {str(e)}[/red]")
            console.print("[yellow]USER ACTION REQUIRED:[/yellow]")
            console.print("  1. Verify file input selector is correct")
            console.print("  2. Check that all file paths are absolute and exist")
            console.print("  3. Ensure file input accepts multiple files")
            raise
    
    def click_button(self, selector: str, label: str = "button", max_retries: int = 3) -> bool:
        """
        Click a button with retry logic for stale elements.
        
        Retries if element becomes stale (common after dynamic page updates).
        
        Args:
            selector: CSS selector for button element
            label: Human-readable button name for logging
            max_retries: Maximum number of click attempts
            
        Returns:
            True if successful
            
        Raises:
            Exception: If all retry attempts fail
        """
        for attempt in range(1, max_retries + 1):
            try:
                console.print(f"[dim]Clicking {label}...[/dim]")
                
                # Wait for element to be clickable
                element = self.waiter.wait_for_element_clickable(selector)
                
                # Scroll element into view (helps with click interception issues)
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(0.5)  # Brief pause after scroll
                
                # Attempt click
                element.click()
                
                console.print(f"[green]✓ Clicked {label}[/green]")
                return True
                
            except StaleElementReferenceException:
                if attempt < max_retries:
                    console.print(f"[yellow]⚠ Element became stale, retrying ({attempt}/{max_retries})...[/yellow]")
                    time.sleep(1)
                    continue
                else:
                    console.print(f"[red]✗ Element stale after {max_retries} attempts[/red]")
                    raise
                    
            except ElementClickInterceptedException:
                if attempt < max_retries:
                    console.print(f"[yellow]⚠ Click intercepted, retrying ({attempt}/{max_retries})...[/yellow]")
                    time.sleep(1)
                    continue
                else:
                    console.print(f"[red]✗ Click intercepted after {max_retries} attempts[/red]")
                    console.print("[yellow]USER ACTION REQUIRED:[/yellow]")
                    console.print("  Another element may be covering the button")
                    console.print("  Check for modals, popups, or overlays")
                    raise
                    
            except Exception as e:
                console.print(f"[red]✗ Failed to click {label}: {str(e)}[/red]")
                raise
        
        return False


# Example usage (for testing individual components)
if __name__ == "__main__":
    console.print("[yellow]This module provides utilities for the main workflow script[/yellow]")
    console.print("[dim]Import these classes in image_upload_workflow.py[/dim]")
