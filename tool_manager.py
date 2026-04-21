import os
import sys
import shutil
import subprocess
import urllib.request
import zipfile
import logging
from pathlib import Path
from config import TOOLS_DIR, ADB_EXE, FASTBOOT_EXE, ADB_FILENAME, ADB_DOWNLOAD_BASE, IS_WINDOWS

logger = logging.getLogger(__name__)

class ToolManager:
    """Manages downloading and locating ADB/Fastboot tools"""
    
    def __init__(self):
        self.tools_dir = TOOLS_DIR
        self.adb_path = None
        self.fastboot_path = None
        self._locate_tools()
    
    def _locate_tools(self):
        """Locate ADB and Fastboot executables"""
        # Check in tools directory
        local_adb = self.tools_dir / "platform-tools" / ADB_EXE
        local_fastboot = self.tools_dir / "platform-tools" / FASTBOOT_EXE
        
        if local_adb.exists():
            self.adb_path = str(local_adb)
        else:
            # Try to find in system PATH
            system_adb = shutil.which("adb")
            if system_adb:
                self.adb_path = system_adb
        
        if local_fastboot.exists():
            self.fastboot_path = str(local_fastboot)
        else:
            system_fastboot = shutil.which("fastboot")
            if system_fastboot:
                self.fastboot_path = system_fastboot
    
    def download_tools(self, progress_callback=None):
        """Download ADB and Fastboot tools"""
        try:
            url = f"{ADB_DOWNLOAD_BASE}/{ADB_FILENAME}"
            zip_path = self.tools_dir / ADB_FILENAME
            extract_path = self.tools_dir / "platform-tools"
            
            logger.info(f"Downloading from {url}")
            
            if not zip_path.exists():
                urllib.request.urlretrieve(url, zip_path, 
                    lambda blocks, block_size, total: progress_callback(
                        min(100, int(blocks * block_size / total * 100)) if progress_callback else 0
                    ))
            
            # Extract
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.tools_dir)
            
            # Clean up zip
            zip_path.unlink()
            
            self._locate_tools()
            return True, "Tools downloaded successfully"
        except Exception as e:
            error_msg = f"Failed to download tools: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def is_tools_available(self):
        """Check if tools are available"""
        return self.adb_path is not None and self.fastboot_path is not None
    
    def get_adb_path(self):
        """Get ADB executable path"""
        return self.adb_path
    
    def get_fastboot_path(self):
        """Get Fastboot executable path"""
        return self.fastboot_path
