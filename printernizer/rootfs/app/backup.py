#!/usr/bin/env python3
"""
Data Management and Backup Module for Printernizer HA Addon
Handles backup, restore, and data migration functionality
"""

import asyncio
import json
import logging
import shutil
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import bashio
    HAS_BASHIO = True
except ImportError:
    HAS_BASHIO = False
    class MockBashio:
        @staticmethod
        def info(msg: str) -> None:
            logging.info(f"[BACKUP] {msg}")
        
        @staticmethod
        def warning(msg: str) -> None:
            logging.warning(f"[BACKUP] {msg}")
        
        @staticmethod
        def error(msg: str) -> None:
            logging.error(f"[BACKUP] {msg}")
    
    bashio = MockBashio()

logger = logging.getLogger(__name__)

class DataManager:
    """Manages data persistence, backup and restore operations"""
    
    def __init__(self, data_path: str = "/data"):
        self.data_path = Path(data_path)
        self.backup_path = self.data_path / "backups"
        self.database_path = self.data_path / "printernizer.db"
        self.config_path = self.data_path / "config"
        
        # Ensure directories exist
        self.backup_path.mkdir(exist_ok=True)
        self.config_path.mkdir(exist_ok=True)
    
    async def initialize_data_structure(self):
        """Initialize data directory structure"""
        try:
            # Create required directories
            directories = [
                self.data_path / "downloads",
                self.data_path / "logs",
                self.data_path / "temp",
                self.data_path / "backups",
                self.data_path / "config",
                self.data_path / "uploads"
            ]
            
            for directory in directories:
                directory.mkdir(exist_ok=True)
                bashio.info(f"Created directory: {directory}")
            
            # Set up logging configuration
            await self._setup_logging()
            
            # Initialize database if needed
            if not self.database_path.exists():
                await self._initialize_database()
            
            bashio.info("Data structure initialization complete")
            
        except Exception as e:
            bashio.error(f"Failed to initialize data structure: {e}")
            raise
    
    async def _setup_logging(self):
        """Setup logging configuration"""
        log_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                }
            },
            "handlers": {
                "file": {
                    "level": "INFO",
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": str(self.data_path / "logs" / "printernizer.log"),
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5,
                    "formatter": "standard"
                }
            },
            "loggers": {
                "": {
                    "handlers": ["file"],
                    "level": "INFO",
                    "propagate": True
                }
            }
        }
        
        # Save logging config
        with open(self.config_path / "logging.json", "w") as f:
            json.dump(log_config, f, indent=2)
    
    async def _initialize_database(self):
        """Initialize SQLite database with basic structure"""
        try:
            conn = sqlite3.connect(str(self.database_path))
            cursor = conn.cursor()
            
            # Create printers table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS printers (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    ip_address TEXT,
                    access_code TEXT,
                    api_key TEXT,
                    serial_number TEXT,
                    enabled BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create print_jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS print_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    printer_id TEXT NOT NULL,
                    filename TEXT,
                    status TEXT,
                    progress REAL DEFAULT 0,
                    started_at DATETIME,
                    completed_at DATETIME,
                    estimated_time INTEGER,
                    filament_used REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (printer_id) REFERENCES printers (id)
                )
            """)
            
            # Create settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert default settings
            default_settings = [
                ("addon_version", "1.0.0"),
                ("database_version", "1.0"),
                ("installation_date", datetime.now().isoformat())
            ]
            
            cursor.executemany(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                default_settings
            )
            
            conn.commit()
            conn.close()
            
            bashio.info(f"Database initialized at {self.database_path}")
            
        except Exception as e:
            bashio.error(f"Failed to initialize database: {e}")
            raise
    
    async def create_backup(self, include_logs: bool = False) -> Optional[str]:
        """Create a backup of all addon data"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"printernizer_backup_{timestamp}.zip"
            backup_filepath = self.backup_path / backup_filename
            
            bashio.info(f"Creating backup: {backup_filename}")
            
            with zipfile.ZipFile(backup_filepath, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
                # Backup database
                if self.database_path.exists():
                    backup_zip.write(self.database_path, "printernizer.db")
                
                # Backup configuration files
                if self.config_path.exists():
                    for config_file in self.config_path.rglob("*"):
                        if config_file.is_file():
                            backup_zip.write(config_file, f"config/{config_file.name}")
                
                # Backup downloads (optional, can be large)
                downloads_path = self.data_path / "downloads"
                if downloads_path.exists():
                    for download_file in downloads_path.rglob("*"):
                        if download_file.is_file() and download_file.stat().st_size < 100 * 1024 * 1024:  # Skip files > 100MB
                            backup_zip.write(download_file, f"downloads/{download_file.name}")
                
                # Backup logs if requested
                if include_logs:
                    logs_path = self.data_path / "logs"
                    if logs_path.exists():
                        for log_file in logs_path.glob("*.log"):
                            backup_zip.write(log_file, f"logs/{log_file.name}")
                
                # Add backup metadata
                metadata = {
                    "backup_date": datetime.now().isoformat(),
                    "addon_version": "1.0.0",
                    "backup_type": "full",
                    "include_logs": include_logs
                }
                backup_zip.writestr("backup_metadata.json", json.dumps(metadata, indent=2))
            
            # Clean up old backups (keep last 5)
            await self._cleanup_old_backups()
            
            bashio.info(f"Backup created successfully: {backup_filename}")
            return str(backup_filepath)
            
        except Exception as e:
            bashio.error(f"Failed to create backup: {e}")
            return None
    
    async def restore_backup(self, backup_filepath: str) -> bool:
        """Restore from a backup file"""
        try:
            backup_path = Path(backup_filepath)
            if not backup_path.exists():
                bashio.error(f"Backup file not found: {backup_filepath}")
                return False
            
            bashio.info(f"Restoring from backup: {backup_path.name}")
            
            # Create temporary restoration directory
            temp_restore_path = self.data_path / "temp" / "restore"
            temp_restore_path.mkdir(parents=True, exist_ok=True)
            
            # Extract backup
            with zipfile.ZipFile(backup_path, 'r') as backup_zip:
                backup_zip.extractall(temp_restore_path)
            
            # Verify backup metadata
            metadata_file = temp_restore_path / "backup_metadata.json"
            if metadata_file.exists():
                with open(metadata_file) as f:
                    metadata = json.load(f)
                bashio.info(f"Restoring backup from {metadata.get('backup_date', 'unknown date')}")
            
            # Stop services during restoration (would need to be implemented)
            bashio.info("Stopping services for restoration...")
            
            # Backup current data before restoration
            current_backup = await self.create_backup()
            if current_backup:
                bashio.info(f"Current data backed up to: {Path(current_backup).name}")
            
            # Restore database
            db_backup = temp_restore_path / "printernizer.db"
            if db_backup.exists():
                shutil.copy2(db_backup, self.database_path)
                bashio.info("Database restored")
            
            # Restore configuration
            config_backup = temp_restore_path / "config"
            if config_backup.exists():
                shutil.rmtree(self.config_path, ignore_errors=True)
                shutil.copytree(config_backup, self.config_path)
                bashio.info("Configuration restored")
            
            # Restore downloads
            downloads_backup = temp_restore_path / "downloads"
            if downloads_backup.exists():
                downloads_path = self.data_path / "downloads"
                shutil.rmtree(downloads_path, ignore_errors=True)
                shutil.copytree(downloads_backup, downloads_path)
                bashio.info("Downloads restored")
            
            # Clean up temporary files
            shutil.rmtree(temp_restore_path, ignore_errors=True)
            
            bashio.info("Backup restoration completed successfully")
            return True
            
        except Exception as e:
            bashio.error(f"Failed to restore backup: {e}")
            return False
    
    async def _cleanup_old_backups(self, keep_count: int = 5):
        """Clean up old backup files, keeping only the most recent ones"""
        try:
            backup_files = list(self.backup_path.glob("printernizer_backup_*.zip"))
            
            if len(backup_files) <= keep_count:
                return
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remove old backups
            for old_backup in backup_files[keep_count:]:
                old_backup.unlink()
                bashio.info(f"Removed old backup: {old_backup.name}")
                
        except Exception as e:
            bashio.error(f"Failed to cleanup old backups: {e}")
    
    async def get_backup_info(self) -> Dict[str, Any]:
        """Get information about available backups"""
        try:
            backup_files = list(self.backup_path.glob("printernizer_backup_*.zip"))
            backup_info = []
            
            for backup_file in sorted(backup_files, key=lambda x: x.stat().st_mtime, reverse=True):
                stat = backup_file.stat()
                
                # Try to read metadata
                metadata = {}
                try:
                    with zipfile.ZipFile(backup_file, 'r') as zf:
                        if "backup_metadata.json" in zf.namelist():
                            metadata = json.loads(zf.read("backup_metadata.json"))
                except:
                    pass
                
                backup_info.append({
                    "filename": backup_file.name,
                    "filepath": str(backup_file),
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "metadata": metadata
                })
            
            return {
                "backups": backup_info,
                "backup_path": str(self.backup_path),
                "total_backups": len(backup_info)
            }
            
        except Exception as e:
            bashio.error(f"Failed to get backup info: {e}")
            return {"backups": [], "error": str(e)}
    
    async def migrate_data(self, from_version: str, to_version: str) -> bool:
        """Migrate data between addon versions"""
        try:
            bashio.info(f"Migrating data from version {from_version} to {to_version}")
            
            # Create backup before migration
            backup_file = await self.create_backup()
            if not backup_file:
                bashio.error("Failed to create backup before migration")
                return False
            
            # Version-specific migration logic would go here
            # For now, just update the version in settings
            conn = sqlite3.connect(str(self.database_path))
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                ("addon_version", to_version, datetime.now().isoformat())
            )
            
            conn.commit()
            conn.close()
            
            bashio.info(f"Data migration completed successfully")
            return True
            
        except Exception as e:
            bashio.error(f"Failed to migrate data: {e}")
            return False

# Global data manager instance
data_manager: Optional[DataManager] = None

async def initialize_data_management(data_path: str = "/data") -> DataManager:
    """Initialize data management"""
    global data_manager
    
    data_manager = DataManager(data_path)
    await data_manager.initialize_data_structure()
    
    return data_manager

async def get_data_manager() -> Optional[DataManager]:
    """Get the global data manager instance"""
    return data_manager

if __name__ == "__main__":
    # Test data management functionality
    async def test():
        dm = await initialize_data_management("/tmp/test_data")
        backup_file = await dm.create_backup(include_logs=True)
        if backup_file:
            print(f"Test backup created: {backup_file}")
        
        backup_info = await dm.get_backup_info()
        print(f"Backup info: {backup_info}")
    
    asyncio.run(test())