import sys
import logging
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QListWidget, QListWidgetItem,
    QTabWidget, QTextEdit, QFileDialog, QDialog, QMessageBox,
    QProgressBar, QLineEdit, QTableWidget, QTableWidgetItem,
    QCheckBox, QSpinBox, QGroupBox, QFormLayout, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject, QMimeData
from PyQt5.QtGui import QFont, QColor, QIcon, QDrag
from config import APP_NAME, APP_VERSION, WINDOW_WIDTH, WINDOW_HEIGHT, REFRESH_INTERVAL
from device_manager import DeviceManager
from tool_manager import ToolManager
from database import Database

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dark mode stylesheet
DARK_STYLESHEET = """
    QMainWindow {
        background-color: #1e1e1e;
        color: #e0e0e0;
    }
    QWidget {
        background-color: #1e1e1e;
        color: #e0e0e0;
    }
    QPushButton {
        background-color: #0d47a1;
        color: #ffffff;
        border: none;
        padding: 5px;
        border-radius: 3px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #1565c0;
    }
    QPushButton:pressed {
        background-color: #0d3a8c;
    }
    QLineEdit, QTextEdit, QComboBox {
        background-color: #2d2d2d;
        color: #e0e0e0;
        border: 1px solid #444;
        padding: 5px;
        border-radius: 3px;
    }
    QTabWidget::pane {
        border: 1px solid #444;
    }
    QTabBar::tab {
        background-color: #2d2d2d;
        color: #e0e0e0;
        padding: 5px;
        border: 1px solid #444;
    }
    QTabBar::tab:selected {
        background-color: #0d47a1;
        color: #ffffff;
    }
    QTableWidget {
        background-color: #2d2d2d;
        color: #e0e0e0;
        gridline-color: #444;
    }
    QHeaderView::section {
        background-color: #3d3d3d;
        color: #e0e0e0;
        border: none;
        padding: 5px;
    }
    QGroupBox {
        color: #e0e0e0;
        border: 1px solid #444;
        border-radius: 3px;
        margin-top: 10px;
        padding-top: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 3px 0 3px;
    }
"""

class WorkerThread(QThread):
    """Worker thread for device operations"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(str)
    
    def __init__(self, operation, *args):
        super().__init__()
        self.operation = operation
        self.args = args
    
    def run(self):
        try:
            self.operation(*self.args)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class ADBManagerApp(QMainWindow):
    """Main ADB Manager Application with Dark Mode"""
    
    def __init__(self):
        super().__init__()
        self.tool_manager = ToolManager()
        self.device_manager = None
        self.selected_device = None
        self.db = Database()
        
        # Check if tools are available
        if not self.tool_manager.is_tools_available():
            self.show_download_dialog()
        else:
            self.device_manager = DeviceManager(self.tool_manager.get_adb_path())
        
        self.init_ui()
        self.setup_refresh_timer()
        self.apply_dark_mode()
    
    def show_download_dialog(self):
        """Show download dialog for ADB tools"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Download ADB Tools")
        dialog.setGeometry(100, 100, 400, 150)
        
        layout = QVBoxLayout()
        label = QLabel("ADB/Fastboot tools not found. Download now?")
        layout.addWidget(label)
        
        progress = QProgressBar()
        layout.addWidget(progress)
        
        btn_download = QPushButton("Download")
        btn_skip = QPushButton("Skip (use system ADB)")
        
        def download():
            success, msg = self.tool_manager.download_tools(
                lambda p: progress.setValue(p)
            )
            if success:
                self.device_manager = DeviceManager(self.tool_manager.get_adb_path())
                QMessageBox.information(self, "Success", msg)
                dialog.close()
            else:
                QMessageBox.critical(self, "Error", msg)
        
        def skip():
            adb_path = self.tool_manager.get_adb_path()
            if adb_path:
                self.device_manager = DeviceManager(adb_path)
                dialog.close()
            else:
                QMessageBox.critical(self, "Error", "No ADB found in system PATH")
        
        btn_download.clicked.connect(download)
        btn_skip.clicked.connect(skip)
        
        layout.addWidget(btn_download)
        layout.addWidget(btn_skip)
        dialog.setLayout(layout)
        dialog.exec_()
    
    def apply_dark_mode(self):
        """Apply dark mode theme"""
        self.setStyleSheet(DARK_STYLESHEET)
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        
        # Device selection area
        device_layout = QHBoxLayout()
        device_layout.addWidget(QLabel("Select Device:"))
        self.device_combo = QComboBox()
        device_layout.addWidget(self.device_combo)
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.refresh_devices)
        device_layout.addWidget(btn_refresh)
        main_layout.addLayout(device_layout)
        
        # Device info area
        self.device_info = QTextEdit()
        self.device_info.setReadOnly(True)
        self.device_info.setMaximumHeight(100)
        main_layout.addWidget(QLabel("Device Info:"))
        main_layout.addWidget(self.device_info)
        
        # Tabs for different operations
        tabs = QTabWidget()
        
        # File Operations Tab
        file_tab = self.create_file_tab()
        tabs.addTab(file_tab, "Files")
        
        # App Management Tab
        app_tab = self.create_app_tab()
        tabs.addTab(app_tab, "Apps")
        
        # ROM Flashing Tab
        rom_tab = self.create_rom_tab()
        tabs.addTab(rom_tab, "ROM Flashing")
        
        # Reboot Tab
        reboot_tab = self.create_reboot_tab()
        tabs.addTab(reboot_tab, "Reboot")
        
        # Logcat Tab
        logcat_tab = self.create_logcat_tab()
        tabs.addTab(logcat_tab, "Logcat")
        
        # Device History Tab
        history_tab = self.create_history_tab()
        tabs.addTab(history_tab, "History")
        
        main_layout.addWidget(tabs)
        
        # Status bar
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)
        
        central_widget.setLayout(main_layout)
        
        # Initial refresh
        self.refresh_devices()
    
    def create_file_tab(self):
        """Create file operations tab"""
        file_tab = QWidget()
        file_layout = QVBoxLayout()
        
        # Push file
        push_group = QGroupBox("Push File to Device")
        push_form = QFormLayout()
        
        self.push_path = QLineEdit()
        btn_browse_push = QPushButton("Browse")
        btn_browse_push.clicked.connect(self.browse_local_file)
        
        push_layout = QHBoxLayout()
        push_layout.addWidget(self.push_path)
        push_layout.addWidget(btn_browse_push)
        push_form.addRow("Local File:", push_layout)
        
        self.device_push_path = QLineEdit()
        self.device_push_path.setText("/sdcard/")
        push_form.addRow("Device Path:", self.device_push_path)
        
        btn_push = QPushButton("Push File")
        btn_push.clicked.connect(self.push_file)
        push_form.addRow(btn_push)
        
        push_group.setLayout(push_form)
        file_layout.addWidget(push_group)
        
        # Pull file
        pull_group = QGroupBox("Pull File from Device")
        pull_form = QFormLayout()
        
        self.pull_path = QLineEdit()
        pull_form.addRow("Device Path:", self.pull_path)
        
        self.save_path = QLineEdit()
        btn_browse_save = QPushButton("Browse")
        btn_browse_save.clicked.connect(self.browse_save_location)
        
        save_layout = QHBoxLayout()
        save_layout.addWidget(self.save_path)
        save_layout.addWidget(btn_browse_save)
        pull_form.addRow("Save to:", save_layout)
        
        btn_pull = QPushButton("Pull File")
        btn_pull.clicked.connect(self.pull_file)
        pull_form.addRow(btn_pull)
        
        pull_group.setLayout(pull_form)
        file_layout.addWidget(pull_group)
        
        file_layout.addStretch()
        file_tab.setLayout(file_layout)
        return file_tab
    
    def create_app_tab(self):
        """Create app management tab"""
        app_tab = QWidget()
        app_layout = QVBoxLayout()
        
        # Install APK
        install_group = QGroupBox("Install APK")
        install_form = QFormLayout()
        
        self.apk_path = QLineEdit()
        btn_browse_apk = QPushButton("Browse")
        btn_browse_apk.clicked.connect(self.browse_apk_file)
        
        apk_layout = QHBoxLayout()
        apk_layout.addWidget(self.apk_path)
        apk_layout.addWidget(btn_browse_apk)
        install_form.addRow("APK File:", apk_layout)
        
        btn_install = QPushButton("Install APK")
        btn_install.clicked.connect(self.install_apk)
        install_form.addRow(btn_install)
        
        install_group.setLayout(install_form)
        app_layout.addWidget(install_group)
        
        # Uninstall Package
        uninstall_group = QGroupBox("Uninstall Package")
        uninstall_form = QFormLayout()
        
        self.package_input = QLineEdit()
        uninstall_form.addRow("Package Name:", self.package_input)
        
        btn_uninstall = QPushButton("Uninstall Package")
        btn_uninstall.clicked.connect(self.uninstall_package)
        uninstall_form.addRow(btn_uninstall)
        
        uninstall_group.setLayout(uninstall_form)
        app_layout.addWidget(uninstall_group)
        
        # Sideload Package
        sideload_group = QGroupBox("Sideload Package")
        sideload_form = QFormLayout()
        
        self.sideload_path = QLineEdit()
        btn_browse_sideload = QPushButton("Browse")
        btn_browse_sideload.clicked.connect(self.browse_sideload_file)
        
        sideload_layout = QHBoxLayout()
        sideload_layout.addWidget(self.sideload_path)
        sideload_layout.addWidget(btn_browse_sideload)
        sideload_form.addRow("Package File:", sideload_layout)
        
        btn_sideload = QPushButton("Sideload Package")
        btn_sideload.clicked.connect(self.sideload_package)
        sideload_form.addRow(btn_sideload)
        
        sideload_group.setLayout(sideload_form)
        app_layout.addWidget(sideload_group)
        
        app_layout.addStretch()
        app_tab.setLayout(app_layout)
        return app_tab
    
    def create_rom_tab(self):
        """Create ROM flashing tab"""
        rom_tab = QWidget()
        rom_layout = QVBoxLayout()
        
        # ROM Flashing
        rom_group = QGroupBox("Flash ROM via Sideload")
        rom_form = QFormLayout()
        
        self.rom_path = QLineEdit()
        btn_browse_rom = QPushButton("Browse ROM")
        btn_browse_rom.clicked.connect(self.browse_rom_file)
        
        rom_layout_h = QHBoxLayout()
        rom_layout_h.addWidget(self.rom_path)
        rom_layout_h.addWidget(btn_browse_rom)
        rom_form.addRow("ROM File:", rom_layout_h)
        
        btn_flash_rom = QPushButton("Flash ROM")
        btn_flash_rom.clicked.connect(self.flash_rom)
        rom_form.addRow(btn_flash_rom)
        
        rom_group.setLayout(rom_form)
        rom_layout.addWidget(rom_group)
        
        # Fastboot Flashing
        fastboot_group = QGroupBox("Fastboot Partition Flashing")
        fastboot_form = QFormLayout()
        
        self.partition_name = QLineEdit()
        self.partition_name.setPlaceholderText("e.g., recovery, bootloader, boot")
        fastboot_form.addRow("Partition:", self.partition_name)
        
        self.partition_file = QLineEdit()
        btn_browse_partition = QPushButton("Browse File")
        btn_browse_partition.clicked.connect(self.browse_partition_file)
        
        partition_layout = QHBoxLayout()
        partition_layout.addWidget(self.partition_file)
        partition_layout.addWidget(btn_browse_partition)
        fastboot_form.addRow("File:", partition_layout)
        
        btn_flash_partition = QPushButton("Flash Partition")
        btn_flash_partition.clicked.connect(self.flash_partition)
        fastboot_form.addRow(btn_flash_partition)
        
        fastboot_group.setLayout(fastboot_form)
        rom_layout.addWidget(fastboot_group)
        
        # EDL Mode
        edl_group = QGroupBox("EDL Mode")
        edl_form = QFormLayout()
        
        btn_edl = QPushButton("Reboot to EDL Mode")
        btn_edl.clicked.connect(self.reboot_edl)
        edl_form.addRow(btn_edl)
        
        self.edl_info = QTextEdit()
        self.edl_info.setReadOnly(True)
        self.edl_info.setText("EDL (Emergency Download) Mode:\n- Used for emergency device recovery\n- Requires EDL cable or software\n- Device won't be visible in adb")
        edl_form.addRow(self.edl_info)
        
        edl_group.setLayout(edl_form)
        rom_layout.addWidget(edl_group)
        
        rom_layout.addStretch()
        rom_tab.setLayout(rom_layout)
        return rom_tab
    
    def create_reboot_tab(self):
        """Create reboot tab"""
        reboot_tab = QWidget()
        reboot_layout = QVBoxLayout()
        
        btn_reboot_system = QPushButton("Reboot System")
        btn_reboot_system.setMinimumHeight(50)
        btn_reboot_system.clicked.connect(lambda: self.reboot_device("system"))
        reboot_layout.addWidget(btn_reboot_system)
        
        btn_reboot_bootloader = QPushButton("Reboot to Bootloader")
        btn_reboot_bootloader.setMinimumHeight(50)
        btn_reboot_bootloader.clicked.connect(lambda: self.reboot_device("bootloader"))
        reboot_layout.addWidget(btn_reboot_bootloader)
        
        btn_reboot_recovery = QPushButton("Reboot to Recovery")
        btn_reboot_recovery.setMinimumHeight(50)
        btn_reboot_recovery.clicked.connect(lambda: self.reboot_device("recovery"))
        reboot_layout.addWidget(btn_reboot_recovery)
        
        btn_reboot_sideload = QPushButton("Reboot to Sideload")
        btn_reboot_sideload.setMinimumHeight(50)
        btn_reboot_sideload.clicked.connect(lambda: self.reboot_device("sideload"))
        reboot_layout.addWidget(btn_reboot_sideload)
        
        reboot_layout.addStretch()
        reboot_tab.setLayout(reboot_layout)
        return reboot_tab
    
    def create_logcat_tab(self):
        """Create logcat tab"""
        logcat_tab = QWidget()
        logcat_layout = QVBoxLayout()
        
        self.logcat_display = QTextEdit()
        self.logcat_display.setReadOnly(True)
        logcat_layout.addWidget(self.logcat_display)
        
        logcat_btn_layout = QHBoxLayout()
        btn_logcat_load = QPushButton("Load Logcat")
        btn_logcat_load.clicked.connect(self.load_logcat)
        btn_logcat_clear = QPushButton("Clear Logcat")
        btn_logcat_clear.clicked.connect(self.clear_logcat)
        
        logcat_btn_layout.addWidget(btn_logcat_load)
        logcat_btn_layout.addWidget(btn_logcat_clear)
        logcat_layout.addLayout(logcat_btn_layout)
        
        logcat_tab.setLayout(logcat_layout)
        return logcat_tab
    
    def create_history_tab(self):
        """Create device history tab"""
        history_tab = QWidget()
        history_layout = QVBoxLayout()
        
        history_layout.addWidget(QLabel("Device History:"))
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels(["Serial", "Model", "Android", "First Seen", "Last Seen", "Rooted"])
        self.history_table.setColumnWidth(0, 150)
        self.history_table.setColumnWidth(1, 150)
        history_layout.addWidget(self.history_table)
        
        history_layout.addWidget(QLabel("Operation Log:"))
        
        self.operation_table = QTableWidget()
        self.operation_table.setColumnCount(5)
        self.operation_table.setHorizontalHeaderLabels(["Device", "Operation", "Status", "Time", "Details"])
        history_layout.addWidget(self.operation_table)
        
        btn_refresh_history = QPushButton("Refresh History")
        btn_refresh_history.clicked.connect(self.refresh_history)
        history_layout.addWidget(btn_refresh_history)
        
        history_tab.setLayout(history_layout)
        return history_tab
    
    def setup_refresh_timer(self):
        """Setup auto-refresh timer"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_devices_quiet)
        self.timer.start(REFRESH_INTERVAL)
    
    def refresh_devices(self):
        """Refresh device list"""
        if not self.device_manager:
            self.status_label.setText("ADB tools not available")
            return
        
        success, devices = self.device_manager.refresh_devices()
        self.device_combo.clear()
        
        for device in devices:
            display_name = f"{device.serial} ({device.status})"
            self.device_combo.addItem(display_name, device)
            
            # Log to database
            if device.status == "device":
                self.db.add_device(device.serial, device.model, device.device_name, 
                                  device.android_version, device.sdk_version, device.is_rooted)
        
        if devices:
            self.on_device_selected()
            self.status_label.setText(f"Found {len(devices)} device(s)")
        else:
            self.status_label.setText("No devices found")
    
    def refresh_devices_quiet(self):
        """Quiet refresh without UI disruption"""
        if self.device_manager:
            self.device_manager.refresh_devices()
    
    def on_device_selected(self):
        """Handle device selection"""
        if self.device_combo.count() == 0:
            return
        
        device = self.device_combo.currentData()
        if device:
            self.selected_device = device
            self.update_device_info(device)
    
    def update_device_info(self, device):
        """Update device info display"""
        info = f"""
Serial: {device.serial}
Status: {device.status}
Model: {device.model}
Device: {device.device_name}
Android: {device.android_version}
SDK: {device.sdk_version}
Battery: {device.battery_level}%
Rooted: {"Yes" if device.is_rooted else "No"}
        """
        self.device_info.setText(info)
    
    def browse_local_file(self):
        """Browse for local file"""
        path, _ = QFileDialog.getOpenFileName(self, "Select File to Push")
        if path:
            self.push_path.setText(path)
            self.db.log_operation(self.selected_device.serial if self.selected_device else "N/A", 
                                "browse_file", {"action": "push", "file": path})
    
    def browse_save_location(self):
        """Browse for save location"""
        path = QFileDialog.getSaveFileName(self, "Save File As")[0]
        if path:
            self.save_path.setText(path)
    
    def browse_apk_file(self):
        """Browse for APK file"""
        path, _ = QFileDialog.getOpenFileName(self, "Select APK", filter="APK Files (*.apk)")
        if path:
            self.apk_path.setText(path)
    
    def browse_rom_file(self):
        """Browse for ROM file"""
        path, _ = QFileDialog.getOpenFileName(self, "Select ROM File", 
                                             filter="ROM Files (*.zip);;All Files (*)")
        if path:
            self.rom_path.setText(path)
    
    def browse_sideload_file(self):
        """Browse for sideload package"""
        path, _ = QFileDialog.getOpenFileName(self, "Select Package", 
                                             filter="ZIP Files (*.zip);;All Files (*)")
        if path:
            self.sideload_path.setText(path)
    
    def browse_partition_file(self):
        """Browse for partition file"""
        path, _ = QFileDialog.getOpenFileName(self, "Select Partition File")
        if path:
            self.partition_file.setText(path)
    
    def push_file(self):
        """Push file to device"""
        if not self.selected_device:
            QMessageBox.warning(self, "Error", "No device selected")
            return
        
        local = self.push_path.text()
        device = self.device_push_path.text()
        
        if not local or not device:
            QMessageBox.warning(self, "Error", "Enter both paths")
            return
        
        self.db.log_operation(self.selected_device.serial, "push_file", 
                            {"local": local, "device": device})
        
        success, msg = self.device_manager.push_file(self.selected_device.serial, local, device)
        if success:
            QMessageBox.information(self, "Success", msg)
            self.db.log_operation(self.selected_device.serial, "push_file", 
                                {"local": local, "device": device}, "success")
        else:
            QMessageBox.critical(self, "Error", msg)
            self.db.log_operation(self.selected_device.serial, "push_file", 
                                {"error": msg}, "failed")
    
    def pull_file(self):
        """Pull file from device"""
        if not self.selected_device:
            QMessageBox.warning(self, "Error", "No device selected")
            return
        
        device = self.pull_path.text()
        local = self.save_path.text()
        
        if not device or not local:
            QMessageBox.warning(self, "Error", "Enter both paths")
            return
        
        success, msg = self.device_manager.pull_file(self.selected_device.serial, device, local)
        if success:
            QMessageBox.information(self, "Success", msg)
        else:
            QMessageBox.critical(self, "Error", msg)
    
    def install_apk(self):
        """Install APK on device"""
        if not self.selected_device:
            QMessageBox.warning(self, "Error", "No device selected")
            return
        
        apk = self.apk_path.text()
        if not apk:
            QMessageBox.warning(self, "Error", "Select APK file")
            return
        
        success, msg = self.device_manager.install_apk(self.selected_device.serial, apk)
        if success:
            QMessageBox.information(self, "Success", msg)
        else:
            QMessageBox.critical(self, "Error", msg)
    
    def uninstall_package(self):
        """Uninstall package from device"""
        if not self.selected_device:
            QMessageBox.warning(self, "Error", "No device selected")
            return
        
        package = self.package_input.text()
        if not package:
            QMessageBox.warning(self, "Error", "Enter package name")
            return
        
        success, msg = self.device_manager.uninstall_package(self.selected_device.serial, package)
        if success:
            QMessageBox.information(self, "Success", msg)
        else:
            QMessageBox.critical(self, "Error", msg)
    
    def sideload_package(self):
        """Sideload package"""
        if not self.selected_device:
            QMessageBox.warning(self, "Error", "No device selected")
            return
        
        package = self.sideload_path.text()
        if not package:
            QMessageBox.warning(self, "Error", "Select package file")
            return
        
        success, msg = self.device_manager.sideload_package(self.selected_device.serial, package)
        if success:
            QMessageBox.information(self, "Success", msg)
        else:
            QMessageBox.critical(self, "Error", msg)
    
    def flash_rom(self):
        """Flash ROM"""
        if not self.selected_device:
            QMessageBox.warning(self, "Error", "No device selected")
            return
        
        rom = self.rom_path.text()
        if not rom:
            QMessageBox.warning(self, "Error", "Select ROM file")
            return
        
        reply = QMessageBox.question(self, "Confirm", 
                                    "Flashing ROM will wipe data. Continue?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No:
            return
        
        success, msg = self.device_manager.flash_rom(self.selected_device.serial, rom)
        if success:
            QMessageBox.information(self, "Success", msg)
        else:
            QMessageBox.critical(self, "Error", msg)
    
    def flash_partition(self):
        """Flash partition"""
        if not self.selected_device:
            QMessageBox.warning(self, "Error", "No device selected")
            return
        
        partition = self.partition_name.text()
        file_path = self.partition_file.text()
        
        if not partition or not file_path:
            QMessageBox.warning(self, "Error", "Enter partition and file")
            return
        
        success, msg = self.device_manager.flash_partition(
            self.tool_manager.get_fastboot_path(), 
            self.selected_device.serial, 
            partition, 
            file_path
        )
        if success:
            QMessageBox.information(self, "Success", msg)
        else:
            QMessageBox.critical(self, "Error", msg)
    
    def reboot_edl(self):
        """Reboot to EDL mode"""
        if not self.selected_device:
            QMessageBox.warning(self, "Error", "No device selected")
            return
        
        success, msg = self.device_manager.reboot_edl_mode(self.selected_device.serial)
        if success:
            QMessageBox.information(self, "EDL Mode", msg)
        else:
            QMessageBox.critical(self, "Error", msg)
    
    def reboot_device(self, mode):
        """Reboot device"""
        if not self.selected_device:
            QMessageBox.warning(self, "Error", "No device selected")
            return
        
        success, msg = self.device_manager.reboot(self.selected_device.serial, mode)
        if success:
            QMessageBox.information(self, "Reboot", msg)
        else:
            QMessageBox.critical(self, "Error", msg)
    
    def load_logcat(self):
        """Load logcat"""
        if not self.selected_device:
            QMessageBox.warning(self, "Error", "No device selected")
            return
        
        self.status_label.setText("Loading logcat...")
        logcat = self.device_manager.get_logcat(self.selected_device.serial)
        self.logcat_display.setText(logcat)
        self.status_label.setText("Logcat loaded")
    
    def clear_logcat(self):
        """Clear logcat"""
        if not self.selected_device:
            QMessageBox.warning(self, "Error", "No device selected")
            return
        
        success, msg = self.device_manager.clear_logcat(self.selected_device.serial)
        if success:
            QMessageBox.information(self, "Success", msg)
            self.logcat_display.setText("")
        else:
            QMessageBox.critical(self, "Error", msg)
    
    def refresh_history(self):
        """Refresh device and operation history"""
        # Populate device history
        devices = self.db.get_device_history()
        self.history_table.setRowCount(len(devices))
        
        for row, device in enumerate(devices):
            self.history_table.setItem(row, 0, QTableWidgetItem(device.get('serial', '')))
            self.history_table.setItem(row, 1, QTableWidgetItem(device.get('model', '')))
            self.history_table.setItem(row, 2, QTableWidgetItem(device.get('android_version', '')))
            self.history_table.setItem(row, 3, QTableWidgetItem(str(device.get('first_seen', ''))))
            self.history_table.setItem(row, 4, QTableWidgetItem(str(device.get('last_seen', ''))))
            self.history_table.setItem(row, 5, QTableWidgetItem("Yes" if device.get('rooted') else "No"))
        
        # Populate operation log
        operations = self.db.get_operation_log(limit=50)
        self.operation_table.setRowCount(len(operations))
        
        for row, op in enumerate(operations):
            self.operation_table.setItem(row, 0, QTableWidgetItem(op.get('device_serial', '')))
            self.operation_table.setItem(row, 1, QTableWidgetItem(op.get('operation_type', '')))
            self.operation_table.setItem(row, 2, QTableWidgetItem(op.get('status', '')))
            self.operation_table.setItem(row, 3, QTableWidgetItem(str(op.get('timestamp', ''))))
            self.operation_table.setItem(row, 4, QTableWidgetItem(op.get('operation_details', '')[:50]))

def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    window = ADBManagerApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
