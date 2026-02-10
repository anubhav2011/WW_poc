"""
Base Migration Framework
Provides base class and runner for database migrations.
"""

import sqlite3
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)


class Migration(ABC):
    """Abstract base class for all migrations."""
    
    name: str = None
    description: str = None
    
    @abstractmethod
    def up(self, connection: sqlite3.Connection) -> bool:
        """Apply the migration. Returns True if successful."""
        pass
    
    @abstractmethod
    def down(self, connection: sqlite3.Connection) -> bool:
        """Rollback the migration. Returns True if successful."""
        pass


class MigrationRunner:
    """Manages migration execution and tracking."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_migrations_table()
    
    def _init_migrations_table(self):
        """Initialize the migrations tracking table if it doesn't exist."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'applied'
            )
            """)
            conn.commit()
            logger.info("[MigrationRunner] Migrations table initialized")
        except Exception as e:
            logger.error(f"[MigrationRunner] Error initializing migrations table: {str(e)}", exc_info=True)
        finally:
            if conn:
                conn.close()
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of already applied migration names."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM migrations WHERE status = 'applied' ORDER BY applied_at")
            rows = cursor.fetchall()
            return [row[0] for row in rows]
        except Exception as e:
            logger.error(f"[MigrationRunner] Error getting applied migrations: {str(e)}", exc_info=True)
            return []
        finally:
            if conn:
                conn.close()
    
    def is_migration_applied(self, migration_name: str) -> bool:
        """Check if a specific migration has been applied."""
        return migration_name in self.get_applied_migrations()
    
    def run_migration(self, migration: Migration) -> bool:
        """Run a single migration and track it."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Check if already applied
            if self.is_migration_applied(migration.name):
                logger.info(f"[MigrationRunner] Migration '{migration.name}' already applied, skipping")
                return True
            
            # Execute migration
            logger.info(f"[MigrationRunner] Running migration: {migration.name}")
            logger.info(f"[MigrationRunner] Description: {migration.description}")
            
            success = migration.up(conn)
            
            if success:
                # Track the migration
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO migrations (name, status) VALUES (?, 'applied')",
                    (migration.name,)
                )
                conn.commit()
                logger.info(f"[MigrationRunner] ✓ Migration '{migration.name}' applied successfully")
                return True
            else:
                logger.error(f"[MigrationRunner] ✗ Migration '{migration.name}' failed")
                return False
                
        except Exception as e:
            logger.error(f"[MigrationRunner] Error running migration '{migration.name}': {str(e)}", exc_info=True)
            return False
        finally:
            if conn:
                conn.close()
    
    def rollback_migration(self, migration: Migration) -> bool:
        """Rollback a migration and remove tracking."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            
            logger.warning(f"[MigrationRunner] Rolling back migration: {migration.name}")
            success = migration.down(conn)
            
            if success:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM migrations WHERE name = ?", (migration.name,))
                conn.commit()
                logger.info(f"[MigrationRunner] ✓ Migration '{migration.name}' rolled back successfully")
                return True
            else:
                logger.error(f"[MigrationRunner] ✗ Rollback failed for migration '{migration.name}'")
                return False
                
        except Exception as e:
            logger.error(f"[MigrationRunner] Error rolling back migration '{migration.name}': {str(e)}", exc_info=True)
            return False
        finally:
            if conn:
                conn.close()
    
    def get_migration_status(self) -> dict:
        """Get detailed status of all migrations."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name, applied_at, status FROM migrations ORDER BY applied_at")
            rows = cursor.fetchall()
            return {
                "total": len(rows),
                "migrations": [
                    {
                        "name": row[0],
                        "applied_at": row[1],
                        "status": row[2]
                    }
                    for row in rows
                ]
            }
        except Exception as e:
            logger.error(f"[MigrationRunner] Error getting migration status: {str(e)}", exc_info=True)
            return {"total": 0, "migrations": []}
        finally:
            if conn:
                conn.close()
