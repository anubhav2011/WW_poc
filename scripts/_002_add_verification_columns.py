"""
Migration: Add Document Verification Columns
Purpose: Add verification fields to support name and DOB matching 
         between personal and educational documents
Date: 2026-02-10
"""

import sys
import sqlite3
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from migration_base import Migration

logger = logging.getLogger(__name__)


class AddVerificationColumns(Migration):
    """Add verification columns to workers and educational_documents tables."""
    
    name = "AddVerificationColumns"
    description = "Add verification columns for name and DOB matching"
    
    def up(self, connection: sqlite3.Connection) -> bool:
        """Apply the migration - add verification columns."""
        try:
            cursor = connection.cursor()
            logger.info(f"[{self.name}] Starting migration...")
            
            # Add verification columns to workers table
            logger.info("[AddVerificationColumns] Adding columns to workers table...")
            cursor.execute("ALTER TABLE workers ADD COLUMN IF NOT EXISTS verification_status TEXT DEFAULT 'pending'")
            cursor.execute("ALTER TABLE workers ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP DEFAULT NULL")
            cursor.execute("ALTER TABLE workers ADD COLUMN IF NOT EXISTS verification_errors TEXT DEFAULT NULL")
            cursor.execute("ALTER TABLE workers ADD COLUMN IF NOT EXISTS personal_extracted_name TEXT DEFAULT NULL")
            cursor.execute("ALTER TABLE workers ADD COLUMN IF NOT EXISTS personal_extracted_dob TEXT DEFAULT NULL")
            
            logger.info("[AddVerificationColumns] Adding columns to educational_documents table...")
            # Add extraction and verification columns to educational_documents table
            cursor.execute("ALTER TABLE educational_documents ADD COLUMN IF NOT EXISTS raw_ocr_text TEXT DEFAULT NULL")
            cursor.execute("ALTER TABLE educational_documents ADD COLUMN IF NOT EXISTS llm_extracted_data TEXT DEFAULT NULL")
            cursor.execute("ALTER TABLE educational_documents ADD COLUMN IF NOT EXISTS extracted_name TEXT DEFAULT NULL")
            cursor.execute("ALTER TABLE educational_documents ADD COLUMN IF NOT EXISTS extracted_dob TEXT DEFAULT NULL")
            cursor.execute("ALTER TABLE educational_documents ADD COLUMN IF NOT EXISTS verification_status TEXT DEFAULT 'pending'")
            cursor.execute("ALTER TABLE educational_documents ADD COLUMN IF NOT EXISTS verification_errors TEXT DEFAULT NULL")
            
            # Create indexes for faster verification queries
            logger.info("[AddVerificationColumns] Creating indexes...")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_workers_verification_status ON workers(verification_status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_educational_documents_verification ON educational_documents(worker_id, verification_status)")
            
            connection.commit()
            logger.info(f"[{self.name}] ✓ Migration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"[{self.name}] ✗ Error applying migration: {str(e)}", exc_info=True)
            connection.rollback()
            return False
    
    def down(self, connection: sqlite3.Connection) -> bool:
        """Rollback the migration - remove verification columns."""
        try:
            cursor = connection.cursor()
            logger.warning(f"[{self.name}] ROLLBACK: Removing verification columns...")
            
            # SQLite doesn't support dropping columns directly in older versions
            # We'll need to use the table recreation approach for complete rollback
            # For now, we'll just alert the user
            logger.warning("[AddVerificationColumns] Note: SQLite doesn't support direct column drops")
            logger.warning("[AddVerificationColumns] To fully rollback, manual database recreation may be needed")
            logger.warning("[AddVerificationColumns] Marking migration as not applied instead")
            
            return True
            
        except Exception as e:
            logger.error(f"[{self.name}] ✗ Error rolling back migration: {str(e)}", exc_info=True)
            return False
