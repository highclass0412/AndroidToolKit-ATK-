import sqlite3
import json
from pathlib import Path
from datetime import datetime
from config import CONFIG_DIR

DB_PATH = CONFIG_DIR / "adb_manager.db"

class Database:
    """SQLite database management for ADB Manager"""
    
    def __init__(self):
        self.db_path = DB_PATH
        self.init_db()
    
    def init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Device history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                serial TEXT UNIQUE,
                model TEXT,
                device_name TEXT,
                android_version TEXT,
                sdk_version TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                rooted BOOLEAN DEFAULT 0
            )
        ''')
        
        # Operations log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_serial TEXT,
                operation_type TEXT,
                operation_details TEXT,
                status TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_serial) REFERENCES devices(serial)
            )
        ''')
        
        # Settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE,
                value TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_device(self, serial, model, device_name, android_version, sdk_version, rooted=False):
        """Add or update device in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO devices (serial, model, device_name, android_version, sdk_version, rooted)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (serial, model, device_name, android_version, sdk_version, rooted))
        except sqlite3.IntegrityError:
            # Device exists, update last_seen
            cursor.execute('''
                UPDATE devices 
                SET last_seen = CURRENT_TIMESTAMP, rooted = ?
                WHERE serial = ?
            ''', (rooted, serial))
        
        conn.commit()
        conn.close()
    
    def get_device_history(self):
        """Get all devices in history"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM devices ORDER BY last_seen DESC')
        devices = cursor.fetchall()
        conn.close()
        
        return [dict(device) for device in devices]
    
    def log_operation(self, device_serial, operation_type, details, status="pending"):
        """Log an operation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        details_json = json.dumps(details) if isinstance(details, dict) else str(details)
        
        cursor.execute('''
            INSERT INTO operations (device_serial, operation_type, operation_details, status)
            VALUES (?, ?, ?, ?)
        ''', (device_serial, operation_type, details_json, status))
        
        conn.commit()
        conn.close()
    
    def get_operation_log(self, device_serial=None, limit=100):
        """Get operation log"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if device_serial:
            cursor.execute('''
                SELECT * FROM operations 
                WHERE device_serial = ?
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (device_serial, limit))
        else:
            cursor.execute('''
                SELECT * FROM operations 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
        
        logs = cursor.fetchall()
        conn.close()
        
        return [dict(log) for log in logs]
    
    def update_operation_status(self, operation_id, status, details=None):
        """Update operation status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if details:
            details_json = json.dumps(details) if isinstance(details, dict) else str(details)
            cursor.execute('''
                UPDATE operations 
                SET status = ?, operation_details = ?
                WHERE id = ?
            ''', (status, details_json, operation_id))
        else:
            cursor.execute('''
                UPDATE operations 
                SET status = ?
                WHERE id = ?
            ''', (status, operation_id))
        
        conn.commit()
        conn.close()
    
    def set_setting(self, key, value):
        """Set application setting"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('INSERT INTO settings (key, value) VALUES (?, ?)', (key, value))
        except sqlite3.IntegrityError:
            cursor.execute('UPDATE settings SET value = ? WHERE key = ?', (value, key))
        
        conn.commit()
        conn.close()
    
    def get_setting(self, key, default=None):
        """Get application setting"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else default
    
    def get_all_settings(self):
        """Get all settings"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM settings')
        settings = cursor.fetchall()
        conn.close()
        
        return {row['key']: row['value'] for row in settings}
