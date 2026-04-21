import os
from pathlib import Path

# Application Configuration
APP_NAME = "ADB Manager Pro"
APP_VERSION = "1.0.0"

# Paths
BASE_DIR = Path(__file__).parent
TOOLS_DIR = BASE_DIR / "tools"
LOGS_DIR = BASE_DIR / "logs"
CONFIG_DIR = BASE_DIR / "config"

# Create directories
for directory in [TOOLS_DIR, LOGS_DIR, CONFIG_DIR]:
    directory.mkdir(exist_ok=True)

# Platform detection
import platform
PLATFORM = platform.system()
IS_WINDOWS = PLATFORM == "Windows"
IS_MAC = PLATFORM == "Darwin"
IS_LINUX = PLATFORM == "Linux"

# Tool URLs
ADB_DOWNLOAD_BASE = "https://dl.google.com/android/repository"
ADB_VERSION = "35.0.0"

if IS_WINDOWS:
    ADB_FILENAME = "platform-tools-latest-windows.zip"
    ADB_EXTRACT_DIR = "platform-tools"
elif IS_MAC:
    ADB_FILENAME = "platform-tools-latest-darwin.zip"
    ADB_EXTRACT_DIR = "platform-tools"
else:  # Linux
    ADB_FILENAME = "platform-tools-latest-linux.zip"
    ADB_EXTRACT_DIR = "platform-tools"

# ADB and Fastboot executable names
ADB_EXE = "adb.exe" if IS_WINDOWS else "adb"
FASTBOOT_EXE = "fastboot.exe" if IS_WINDOWS else "fastboot"

# UI Constants
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
REFRESH_INTERVAL = 2000  # milliseconds
