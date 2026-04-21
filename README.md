# ADB Manager Pro

A user-friendly desktop application for managing Android devices via ADB and Fastboot.

## Features

✅ **Device Detection**
- Automatically detect connected Android devices
- Display device information (model, Android version, battery level, root status)

✅ **File Operations**
- Push files to device
- Pull files from device

✅ **App Management**
- Install APK files
- Uninstall packages

✅ **Reboot Options**
- Reboot to system
- Reboot to bootloader
- Reboot to recovery mode

✅ **Logcat Viewer**
- View device logs
- Clear logcat
- Filter logs

✅ **Auto Tool Management**
- Automatically download ADB/Fastboot if not available
- Use system ADB if already installed

## Installation

1. Install Python 3.7+
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## Project Structure

```
vmlinux/
├── main.py              # Entry point
├── ui.py                # GUI interface (PyQt5)
├── device_manager.py    # Device operations
├── tool_manager.py      # ADB/Fastboot management
├── config.py            # Configuration
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## System Requirements

- Python 3.7+
- Windows, macOS, or Linux
- USB cable for Android device
- USB Debugging enabled on device

## Troubleshooting

**Device not detected:**
- Enable USB debugging in Developer Options
- Authorize the computer on the device
- Install device drivers (Windows)

**Permission denied:**
- Run with administrator/sudo privileges
- Check USB cable connection

## License

MIT License
