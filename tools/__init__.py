"""
CardDealerPro Image Upload Automation Tools

This package contains utility modules for web automation.
"""

from .web_automation_tools import (
    ElementWaiter,
    LoginHandler,
    FormNavigator,
    FormSubmitter
)

__all__ = [
    'ElementWaiter',
    'LoginHandler',
    'FormNavigator',
    'FormSubmitter'
]

__version__ = '1.0.0'
