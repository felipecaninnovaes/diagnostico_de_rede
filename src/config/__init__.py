"""__init__.py para config."""

from .config_manager import (
    ConfigManager,
    TestSettings,
    ReportSettings,
    UISettings,
    NetworkSettings,
    ISPDetectionSettings,
)

__all__ = [
    "ConfigManager",
    "TestSettings",
    "ReportSettings", 
    "UISettings",
    "NetworkSettings",
    "ISPDetectionSettings",
]
