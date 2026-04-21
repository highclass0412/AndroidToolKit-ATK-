import subprocess
import logging
import re
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)

class Device:
    """Represents an Android device"""
    
    def __init__(self, serial: str, status: str):
        self.serial = serial
        self.status = status
        self.model = ""
        self.device_name = ""
        self.android_version = ""
        self.sdk_version = ""
        self.battery_level = 0
        self.is_rooted = False
    
    def __repr__(self):
        return f"Device({self.serial}, {self.status})"

class DeviceManager:
    """Manages device detection and operations"""
    
    def __init__(self, adb_path: str):
        self.adb_path = adb_path
        self.devices: List[Device] = []
    
    def refresh_devices(self) -> Tuple[bool, List[Device]]:
        """Detect connected devices"""
        try:
            result = subprocess.run(
                [self.adb_path, "devices"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            self.devices = []
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            
            for line in lines:
                if not line.strip():
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    serial = parts[0]
                    status = parts[1]
                    device = Device(serial, status)
                    
                    # Get device info if connected
                    if status == "device":
                        self._fetch_device_info(device)
                    
                    self.devices.append(device)
            
            logger.info(f"Found {len(self.devices)} device(s)")
            return True, self.devices
        except Exception as e:
            logger.error(f"Failed to refresh devices: {str(e)}")
            return False, []
    
    def _fetch_device_info(self, device: Device):
        """Fetch detailed information about device"""
        try:
            # Model
            device.model = self._adb_shell(device.serial, "getprop ro.product.model").strip()
            
            # Device name
            device.device_name = self._adb_shell(device.serial, "getprop ro.product.device").strip()
            
            # Android version
            device.android_version = self._adb_shell(device.serial, "getprop ro.build.version.release").strip()
            
            # SDK version
            device.sdk_version = self._adb_shell(device.serial, "getprop ro.build.version.sdk").strip()
            
            # Battery level
            try:
                battery = self._adb_shell(device.serial, "dumpsys battery | grep level").strip()
                match = re.search(r'level: (\d+)', battery)
                if match:
                    device.battery_level = int(match.group(1))
            except:
                pass
            
            # Check if rooted
            try:
                su_result = self._adb_shell(device.serial, "command -v su")
                device.is_rooted = bool(su_result.strip())
            except:
                device.is_rooted = False
        except Exception as e:
            logger.debug(f"Could not fetch full device info: {str(e)}")
    
    def _adb_shell(self, serial: str, command: str) -> str:
        """Execute ADB shell command"""
        result = subprocess.run(
            [self.adb_path, "-s", serial, "shell", command],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout
    
    def push_file(self, serial: str, local_path: str, device_path: str) -> Tuple[bool, str]:
        """Push file to device"""
        try:
            result = subprocess.run(
                [self.adb_path, "-s", serial, "push", local_path, device_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return True, f"File pushed to {device_path}"
            else:
                return False, result.stderr
        except Exception as e:
            return False, str(e)
    
    def pull_file(self, serial: str, device_path: str, local_path: str) -> Tuple[bool, str]:
        """Pull file from device"""
        try:
            result = subprocess.run(
                [self.adb_path, "-s", serial, "pull", device_path, local_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return True, f"File pulled to {local_path}"
            else:
                return False, result.stderr
        except Exception as e:
            return False, str(e)
    
    def install_apk(self, serial: str, apk_path: str) -> Tuple[bool, str]:
        """Install APK on device"""
        try:
            result = subprocess.run(
                [self.adb_path, "-s", serial, "install", apk_path],
                capture_output=True,
                text=True,
                timeout=60
            )
            if "Success" in result.stdout or result.returncode == 0:
                return True, "APK installed successfully"
            else:
                return False, result.stdout
        except Exception as e:
            return False, str(e)
    
    def uninstall_package(self, serial: str, package_name: str) -> Tuple[bool, str]:
        """Uninstall package from device"""
        try:
            result = subprocess.run(
                [self.adb_path, "-s", serial, "uninstall", package_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            if "Success" in result.stdout or result.returncode == 0:
                return True, f"{package_name} uninstalled"
            else:
                return False, result.stdout
        except Exception as e:
            return False, str(e)
    
    def reboot(self, serial: str, mode: str = "system") -> Tuple[bool, str]:
        """Reboot device"""
        try:
            if mode == "bootloader":
                cmd = [self.adb_path, "-s", serial, "reboot", "bootloader"]
            elif mode == "recovery":
                cmd = [self.adb_path, "-s", serial, "reboot", "recovery"]
            else:
                cmd = [self.adb_path, "-s", serial, "reboot"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return True, f"Device rebooting to {mode}"
        except Exception as e:
            return False, str(e)
    
    def get_logcat(self, serial: str, lines: int = 100) -> str:
        """Get logcat output"""
        try:
            result = subprocess.run(
                [self.adb_path, "-s", serial, "logcat", "-d", "-n", str(lines)],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout
        except Exception as e:
            return f"Error getting logcat: {str(e)}"
    
    def clear_logcat(self, serial: str) -> Tuple[bool, str]:
        """Clear logcat"""
        try:
            subprocess.run(
                [self.adb_path, "-s", serial, "logcat", "-c"],
                capture_output=True,
                timeout=5
            )
            return True, "Logcat cleared"
        except Exception as e:
            return False, str(e)
    
    def get_connected_devices(self) -> List[Device]:
        """Get list of connected devices"""
        return [d for d in self.devices if d.status == "device"]
    
    def flash_rom(self, serial: str, rom_file: str) -> Tuple[bool, str]:
        """Flash ROM file to device"""
        try:
            # This is a generic ROM flashing - actual implementation depends on ROM type
            result = subprocess.run(
                [self.adb_path, "-s", serial, "sideload", rom_file],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                return True, "ROM flashing initiated"
            else:
                return False, result.stderr
        except Exception as e:
            return False, str(e)
    
    def flash_bootloader(self, fastboot_path: str, serial: str, bootloader_file: str) -> Tuple[bool, str]:
        """Flash bootloader using fastboot"""
        try:
            result = subprocess.run(
                [fastboot_path, "-s", serial, "flash", "bootloader", bootloader_file],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                return True, "Bootloader flashed successfully"
            else:
                return False, result.stderr
        except Exception as e:
            return False, str(e)
    
    def flash_recovery(self, fastboot_path: str, serial: str, recovery_file: str) -> Tuple[bool, str]:
        """Flash recovery using fastboot"""
        try:
            result = subprocess.run(
                [fastboot_path, "-s", serial, "flash", "recovery", recovery_file],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                return True, "Recovery flashed successfully"
            else:
                return False, result.stderr
        except Exception as e:
            return False, str(e)
    
    def flash_partition(self, fastboot_path: str, serial: str, partition: str, file: str) -> Tuple[bool, str]:
        """Flash generic partition using fastboot"""
        try:
            result = subprocess.run(
                [fastboot_path, "-s", serial, "flash", partition, file],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                return True, f"Partition '{partition}' flashed successfully"
            else:
                return False, result.stderr
        except Exception as e:
            return False, str(e)
    
    def reboot_edl_mode(self, serial: str) -> Tuple[bool, str]:
        """Reboot device to EDL (Emergency Download) mode"""
        try:
            # Try fastboot method first
            result = subprocess.run(
                [self.adb_path, "-s", serial, "reboot", "edl"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if "error" not in result.stdout.lower() and result.returncode == 0:
                return True, "Device rebooting to EDL mode"
            
            # Alternative: try bootloader route
            result2 = subprocess.run(
                [self.adb_path, "-s", serial, "shell", "setprop", "sys.usb.config", "file_sync"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return True, "EDL mode command sent"
        except Exception as e:
            return False, str(e)
    
    def get_fastboot_devices(self, fastboot_path: str) -> Tuple[bool, List[str]]:
        """Get list of devices in fastboot mode"""
        try:
            result = subprocess.run(
                [fastboot_path, "devices"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            devices = []
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line.strip() and "fastboot" not in line.lower():
                    parts = line.split()
                    if len(parts) >= 1:
                        devices.append(parts[0])
            
            return True, devices
        except Exception as e:
            return False, []
    
    def sideload_package(self, serial: str, package_path: str) -> Tuple[bool, str]:
        """Sideload package via adb sideload"""
        try:
            # Ensure device is in sideload mode first
            result = subprocess.run(
                [self.adb_path, "-s", serial, "sideload", package_path],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                return True, "Package sideloaded successfully"
            else:
                return False, result.stderr if result.stderr else result.stdout
        except Exception as e:
            return False, str(e)
