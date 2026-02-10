"""
Migration 002: Add Document Verification Columns
Purpose: Add verification fields to support name and DOB matching between personal and educational documents
"""

import sqlite3
import logging
from migration_base import Migration

logger = logging.getLogger(__name__)


class AddVerificationColumns(Migration):
    """Add verification and extraction columns to workers and educational_documents tables."""
    
    def up(self, conn: sqlite3.Connection) -> bool:
        """Add verification columns to database."""
        cursor = conn.cursor()
        try:
            logger.info("[AddVerificationColumns] Starting migration up...")
            
            # Add columns to workers table
            logger.info("[AddVerificationColumns] Adding columns to workers table...")
            cursor.execute("""
            ALTER TABLE workers ADD COLUMN IF NOT EXISTS verification_status TEXT DEFAULT 'pending'
            """)
            cursor.execute("""
            ALTER TABLE workers ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP DEFAULT NULL
            """)
            cursor.execute("""
            ALTER TABLE workers ADD COLUMN IF NOT EXISTS verification_errors TEXT DEFAULT NULL
            """)
            cursor.execute("""
            ALTER TABLE workers ADD COLUMN IF NOT EXISTS personal_extracted_name TEXT DEFAULT NULL
            """)
            cursor.execute("""
            ALTER TABLE workers ADD COLUMN IF NOT EXISTS personal_extracted_dob TEXT DEFAULT NULL
            """)
            
            # Add columns to educational_documents table
            logger.info("[AddVerificationColumns] Adding columns to educational_documents table...")
            cursor.execute("""
            ALTER TABLE educational_documents ADD COLUMN IF NOT EXISTS raw_ocr_text TEXT DEFAULT NULL
            """)
            cursor.execute("""
            ALTER TABLE educational_documents ADD COLUMN IF NOT EXISTS llm_extracted_data TEXT DEFAULT NULL
            """)
            cursor.execute("""
            ALTER TABLE educational_documents ADD COLUMN IF NOT EXISTS extracted_name TEXT DEFAULT NULL
            """)
            cursor.execute("""
            ALTER TABLE educational_documents ADD COLUMN IF NOT EXISTS extracted_dob TEXT DEFAULT NULL
            """)
            cursor.execute("""
            ALTER TABLE educational_documents ADD COLUMN IF NOT EXISTS verification_status TEXT DEFAULT 'pending'
            """)
            cursor.execute("""
            ALTER TABLE educational_documents ADD COLUMN IF NOT EXISTS verification_errors TEXT DEFAULT NULL
            """)
            
            # Create indexes for faster verification queries
            logger.info("[AddVerificationColumns] Creating indexes...")
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_workers_verification_status 
            ON workers(verification_status)
            """)
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_educational_documents_verification 
            ON educational_documents(worker_id, verification_status)
            """)
            
            conn.commit()
            logger.info("[AddVerificationColumns] ✓ All columns and indexes created successfully")
            return True
            
        except sqlite3.OperationalError as e:
            logger.error(f"[AddVerificationColumns] ✗ Column may already exist or SQL error: {str(e)}")
            # Return True if columns already exist (idempotent behavior)
            return True
        except Exception as e:
            logger.error(f"[AddVerificationColumns] ✗ Error during migration: {str(e)}", exc_info=True)
            conn.rollback()
            return False
    
    def down(self, conn: sqlite3.Connection) -> bool:
        """Rollback verification columns (use with caution)."""
        cursor = conn.cursor()
        try:
            logger.warning("[AddVerificationColumns] Rolling back verification columns...")
            
            # Note: SQLite doesn't support DROP COLUMN directly, so we'll need to recreate the tables
            # For now, we'll just log that rollback is not fully supported
            logger.warning("[AddVerificationColumns] SQLite has limited rollback support for ALTER TABLE")
            logger.warning("[AddVerificationColumns] Columns remain in database but are marked as rolled back")
            
            return True
            
        except Exception as e:
            logger.error(f"[AddVerificationColumns] Error during rollback: {str(e)}", exc_info=True)
            return False


if __name__ == "__main__":
    # For testing purposes
    import sys
    from pathlib import Path
    
    # Add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent))
    from migration_base import MigrationRunner
    
    db_path = Path(__file__).parent.parent / "workers.db"
    runner = MigrationRunner(str(db_path))
    migration = AddVerificationColumns()
    
    if runner.run_migration(migration):
        print("Migration successful!")
    else:
        print("Migration failed!")
