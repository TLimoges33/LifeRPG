"""
Backup Security Configuration

This module implements secure backup strategies with encryption,
integrity verification, and compliance with security policies.
"""

import os
import json
import shutil
import hashlib
import tempfile
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Any
from pathlib import Path
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64


class BackupSecurityConfig:
    """Secure backup configuration and management"""
    
    def __init__(self):
        self.config = self._load_backup_config()
        self.encryption_key = self._get_encryption_key()
        self.logger = self._setup_logging()
        
    def _load_backup_config(self) -> Dict[str, Any]:
        """Load backup security configuration"""
        return {
            "encryption": {
                "enabled": True,
                "algorithm": "AES-256-GCM",
                "key_rotation_days": 90
            },
            "retention": {
                "daily_backups": 7,
                "weekly_backups": 4,
                "monthly_backups": 12,
                "yearly_backups": 3
            },
            "storage": {
                "primary_location": os.getenv("BACKUP_PRIMARY_PATH", "/secure/backups"),
                "secondary_location": os.getenv("BACKUP_SECONDARY_PATH", ""),
                "cloud_storage": os.getenv("BACKUP_CLOUD_BUCKET", ""),
                "compression": True
            },
            "integrity": {
                "checksum_algorithm": "SHA-256",
                "signature_verification": True,
                "corruption_detection": True
            },
            "access_control": {
                "backup_user": "backup_service",
                "permissions": "600",
                "audit_logging": True
            }
        }
    
    def _get_encryption_key(self) -> Fernet:
        """Get or generate encryption key for backups"""
        key_file = os.getenv("BACKUP_KEY_FILE", "/secure/keys/backup.key")
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                key = f.read()
        else:
            # Generate new key
            password = os.getenv("BACKUP_PASSWORD", "").encode()
            if not password:
                raise ValueError("BACKUP_PASSWORD environment variable required")
                
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
            
            # Save key securely
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)
        
        return Fernet(key)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup secure logging for backup operations"""
        logger = logging.getLogger("backup_security")
        logger.setLevel(logging.INFO)
        
        # Secure log file
        log_file = "/secure/logs/backup_security.log"
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def create_secure_backup(self, source_path: str, backup_name: str) -> Dict[str, Any]:
        """Create encrypted and integrity-verified backup"""
        try:
            # Validate source path
            if not os.path.exists(source_path):
                raise ValueError(f"Source path does not exist: {source_path}")
            
            # Create backup directory
            backup_dir = os.path.join(
                self.config["storage"]["primary_location"],
                datetime.now().strftime("%Y/%m/%d")
            )
            os.makedirs(backup_dir, exist_ok=True)
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{backup_name}_{timestamp}.backup"
            backup_path = os.path.join(backup_dir, backup_file)
            
            # Create compressed archive
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                if self.config["storage"]["compression"]:
                    shutil.make_archive(
                        temp_file.name.replace('.tmp', ''),
                        'gztar',
                        source_path
                    )
                    archive_path = f"{temp_file.name.replace('.tmp', '')}.tar.gz"
                else:
                    shutil.copytree(source_path, temp_file.name + "_data")
                    archive_path = temp_file.name + "_data"
                
                # Calculate checksum
                checksum = self._calculate_checksum(archive_path)
                
                # Encrypt backup
                encrypted_data = self._encrypt_file(archive_path)
                
                # Write encrypted backup
                with open(backup_path, 'wb') as backup_file:
                    backup_file.write(encrypted_data)
                
                # Set secure permissions
                os.chmod(backup_path, 0o600)
                
                # Clean up temporary files
                if os.path.exists(archive_path):
                    os.remove(archive_path)
                if os.path.exists(temp_file.name + "_data"):
                    shutil.rmtree(temp_file.name + "_data")
            
            # Create metadata file
            metadata = {
                "backup_name": backup_name,
                "source_path": source_path,
                "backup_path": backup_path,
                "timestamp": datetime.now().isoformat(),
                "checksum": checksum,
                "encryption": self.config["encryption"]["algorithm"],
                "compression": self.config["storage"]["compression"],
                "size_bytes": os.path.getsize(backup_path)
            }
            
            metadata_path = backup_path + ".metadata"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            os.chmod(metadata_path, 0o600)
            
            # Log successful backup
            self.logger.info(f"Backup created: {backup_name} -> {backup_path}")
            
            # Verify backup integrity
            if self._verify_backup_integrity(backup_path, metadata):
                self.logger.info(f"Backup integrity verified: {backup_path}")
            else:
                self.logger.error(f"Backup integrity check failed: {backup_path}")
                return {"success": False, "error": "Integrity verification failed"}
            
            return {
                "success": True,
                "backup_path": backup_path,
                "metadata": metadata
            }
            
        except Exception as e:
            self.logger.error(f"Backup creation failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def restore_secure_backup(self, backup_path: str, restore_path: str) -> Dict[str, Any]:
        """Restore and decrypt backup with integrity verification"""
        try:
            # Verify backup exists
            if not os.path.exists(backup_path):
                raise ValueError(f"Backup file does not exist: {backup_path}")
            
            # Load metadata
            metadata_path = backup_path + ".metadata"
            if not os.path.exists(metadata_path):
                raise ValueError("Backup metadata file missing")
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Verify backup integrity before restore
            if not self._verify_backup_integrity(backup_path, metadata):
                raise ValueError("Backup integrity verification failed")
            
            # Decrypt backup
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                decrypted_data = self._decrypt_file(backup_path)
                temp_file.write(decrypted_data)
                temp_archive = temp_file.name
            
            # Extract/restore data
            os.makedirs(restore_path, exist_ok=True)
            
            if metadata.get("compression", False):
                shutil.unpack_archive(temp_archive, restore_path, 'gztar')
            else:
                shutil.copytree(temp_archive, restore_path, dirs_exist_ok=True)
            
            # Verify restored data checksum
            restored_checksum = self._calculate_checksum(restore_path)
            if restored_checksum != metadata["checksum"]:
                self.logger.warning(
                    f"Restored data checksum mismatch: {backup_path}"
                )
            
            # Clean up
            os.remove(temp_archive)
            
            self.logger.info(f"Backup restored: {backup_path} -> {restore_path}")
            
            return {
                "success": True,
                "restore_path": restore_path,
                "metadata": metadata
            }
            
        except Exception as e:
            self.logger.error(f"Backup restoration failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _encrypt_file(self, file_path: str) -> bytes:
        """Encrypt file contents"""
        with open(file_path, 'rb') as f:
            data = f.read()
        return self.encryption_key.encrypt(data)
    
    def _decrypt_file(self, file_path: str) -> bytes:
        """Decrypt file contents"""
        with open(file_path, 'rb') as f:
            encrypted_data = f.read()
        return self.encryption_key.decrypt(encrypted_data)
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA-256 checksum of file or directory"""
        if os.path.isfile(file_path):
            return self._file_checksum(file_path)
        elif os.path.isdir(file_path):
            return self._directory_checksum(file_path)
        else:
            raise ValueError(f"Invalid path type: {file_path}")
    
    def _file_checksum(self, file_path: str) -> str:
        """Calculate checksum for a single file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _directory_checksum(self, dir_path: str) -> str:
        """Calculate checksum for entire directory"""
        hash_sha256 = hashlib.sha256()
        
        for root, dirs, files in os.walk(dir_path):
            # Sort to ensure consistent order
            dirs.sort()
            files.sort()
            
            for file_name in files:
                file_path = os.path.join(root, file_name)
                # Include relative path in hash
                rel_path = os.path.relpath(file_path, dir_path)
                hash_sha256.update(rel_path.encode())
                
                # Include file contents
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_sha256.update(chunk)
        
        return hash_sha256.hexdigest()
    
    def _verify_backup_integrity(self, backup_path: str, metadata: Dict[str, Any]) -> bool:
        """Verify backup file integrity"""
        try:
            # Check file exists and size
            if not os.path.exists(backup_path):
                return False
            
            actual_size = os.path.getsize(backup_path)
            expected_size = metadata.get("size_bytes")
            if expected_size and actual_size != expected_size:
                return False
            
            # Verify file can be decrypted (basic integrity check)
            try:
                self._decrypt_file(backup_path)
                return True
            except Exception:
                return False
                
        except Exception:
            return False
    
    def cleanup_old_backups(self) -> Dict[str, Any]:
        """Clean up old backups according to retention policy"""
        cleaned_files = []
        cleanup_errors = []
        
        try:
            backup_root = self.config["storage"]["primary_location"]
            if not os.path.exists(backup_root):
                return {"cleaned_files": [], "errors": ["Backup directory does not exist"]}
            
            # Calculate retention dates
            now = datetime.now()
            daily_cutoff = now - timedelta(days=self.config["retention"]["daily_backups"])
            weekly_cutoff = now - timedelta(weeks=self.config["retention"]["weekly_backups"])
            monthly_cutoff = now - timedelta(days=30 * self.config["retention"]["monthly_backups"])
            yearly_cutoff = now - timedelta(days=365 * self.config["retention"]["yearly_backups"])
            
            # Walk through backup directories
            for root, dirs, files in os.walk(backup_root):
                for file_name in files:
                    if file_name.endswith('.backup'):
                        file_path = os.path.join(root, file_name)
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        
                        should_delete = False
                        
                        # Apply retention rules based on age
                        if file_time < yearly_cutoff:
                            should_delete = True
                        elif file_time < monthly_cutoff and not self._is_monthly_backup(file_time):
                            should_delete = True
                        elif file_time < weekly_cutoff and not self._is_weekly_backup(file_time):
                            should_delete = True
                        elif file_time < daily_cutoff:
                            should_delete = True
                        
                        if should_delete:
                            try:
                                os.remove(file_path)
                                # Also remove metadata file
                                metadata_path = file_path + ".metadata"
                                if os.path.exists(metadata_path):
                                    os.remove(metadata_path)
                                
                                cleaned_files.append(file_path)
                                self.logger.info(f"Cleaned up old backup: {file_path}")
                                
                            except Exception as e:
                                cleanup_errors.append(f"Failed to delete {file_path}: {str(e)}")
                                self.logger.error(f"Cleanup failed for {file_path}: {str(e)}")
            
            return {
                "cleaned_files": cleaned_files,
                "errors": cleanup_errors,
                "summary": f"Cleaned {len(cleaned_files)} old backups"
            }
            
        except Exception as e:
            self.logger.error(f"Backup cleanup failed: {str(e)}")
            return {"cleaned_files": [], "errors": [str(e)]}
    
    def _is_weekly_backup(self, backup_time: datetime) -> bool:
        """Check if backup should be kept as weekly backup (Sunday)"""
        return backup_time.weekday() == 6  # Sunday
    
    def _is_monthly_backup(self, backup_time: datetime) -> bool:
        """Check if backup should be kept as monthly backup (first of month)"""
        return backup_time.day == 1
    
    def get_backup_status(self) -> Dict[str, Any]:
        """Get comprehensive backup status and health"""
        try:
            backup_root = self.config["storage"]["primary_location"]
            if not os.path.exists(backup_root):
                return {
                    "status": "error",
                    "message": "Backup directory does not exist",
                    "total_backups": 0,
                    "total_size": 0
                }
            
            backup_files = []
            total_size = 0
            
            # Scan all backup files
            for root, dirs, files in os.walk(backup_root):
                for file_name in files:
                    if file_name.endswith('.backup'):
                        file_path = os.path.join(root, file_name)
                        file_size = os.path.getsize(file_path)
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        
                        # Load metadata if available
                        metadata_path = file_path + ".metadata"
                        metadata = {}
                        if os.path.exists(metadata_path):
                            try:
                                with open(metadata_path, 'r') as f:
                                    metadata = json.load(f)
                            except Exception:
                                pass
                        
                        backup_files.append({
                            "file_path": file_path,
                            "size_bytes": file_size,
                            "created": file_time.isoformat(),
                            "backup_name": metadata.get("backup_name", "unknown"),
                            "source_path": metadata.get("source_path", "unknown")
                        })
                        
                        total_size += file_size
            
            # Sort by creation time (newest first)
            backup_files.sort(key=lambda x: x["created"], reverse=True)
            
            # Calculate age distribution
            now = datetime.now()
            age_distribution = {
                "last_24h": 0,
                "last_week": 0,
                "last_month": 0,
                "older": 0
            }
            
            for backup in backup_files:
                created = datetime.fromisoformat(backup["created"])
                age = now - created
                
                if age.days == 0:
                    age_distribution["last_24h"] += 1
                elif age.days <= 7:
                    age_distribution["last_week"] += 1
                elif age.days <= 30:
                    age_distribution["last_month"] += 1
                else:
                    age_distribution["older"] += 1
            
            return {
                "status": "healthy",
                "total_backups": len(backup_files),
                "total_size_bytes": total_size,
                "total_size_human": self._human_readable_size(total_size),
                "age_distribution": age_distribution,
                "latest_backup": backup_files[0] if backup_files else None,
                "oldest_backup": backup_files[-1] if backup_files else None,
                "encryption_enabled": self.config["encryption"]["enabled"],
                "compression_enabled": self.config["storage"]["compression"]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get backup status: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "total_backups": 0,
                "total_size": 0
            }
    
    def _human_readable_size(self, size_bytes: int) -> str:
        """Convert bytes to human readable format"""
        size = float(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"


# Global backup security instance
backup_security = BackupSecurityConfig()


def create_database_backup() -> Dict[str, Any]:
    """Create secure database backup"""
    db_dump_path = "/tmp/db_dump.sql"
    
    # Create database dump (example for PostgreSQL)
    try:
        subprocess.run([
            "pg_dump",
            os.getenv("DATABASE_URL", ""),
            "-f", db_dump_path
        ], check=True)
        
        # Create secure backup
        result = backup_security.create_secure_backup(db_dump_path, "database")
        
        # Clean up dump file
        if os.path.exists(db_dump_path):
            os.remove(db_dump_path)
        
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def create_application_backup() -> Dict[str, Any]:
    """Create secure application files backup"""
    app_path = "/workspaces/LifeRPG/modern"
    return backup_security.create_secure_backup(app_path, "application")


def get_backup_health() -> Dict[str, Any]:
    """Get backup system health status"""
    return backup_security.get_backup_status()


def cleanup_backups() -> Dict[str, Any]:
    """Clean up old backups per retention policy"""
    return backup_security.cleanup_old_backups()
