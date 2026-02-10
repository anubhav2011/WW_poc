#!/usr/bin/env python3
"""
Standalone Migration Script: Add Verification Columns
This script adds verification-related columns directly to existing database tables.
Run: python migrate_add_verification_columns.py
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "workers.db"


def migrate_add_verification_columns():
    """Add verification columns to existing database tables."""
    
    if not DB_PATH.exists():
        logger.error(f"Database not found at: {DB_PATH}")
        return False
    
    conn = None
    try:
        logger.info("=" * 70)
        logger.info("Migration: Add Verification Columns")
        logger.info("=" * 70)
        logger.info(f"Database: {DB_PATH}")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info("=" * 70)
        
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get current tables to verify they exist
        logger.info("\n[INFO] Checking existing tables...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"Found tables: {', '.join(existing_tables)}")
        
        # Add verification columns to workers table
        if 'workers' in existing_tables:
            logger.info("\n[WORKERS TABLE] Adding verification columns...")
            try:
                cursor.execute("ALTER TABLE workers ADD COLUMN IF NOT EXISTS verification_status TEXT DEFAULT 'pending'")
                logger.info("  ✓ Added column: verification_status")
            except Exception as e:
                logger.warning(f"  ⚠ verification_status: {str(e)}")
            
            try:
                cursor.execute("ALTER TABLE workers ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP DEFAULT NULL")
                logger.info("  ✓ Added column: verified_at")
            except Exception as e:
                logger.warning(f"  ⚠ verified_at: {str(e)}")
            
            try:
                cursor.execute("ALTER TABLE workers ADD COLUMN IF NOT EXISTS verification_errors TEXT DEFAULT NULL")
                logger.info("  ✓ Added column: verification_errors")
            except Exception as e:
                logger.warning(f"  ⚠ verification_errors: {str(e)}")
            
            try:
                cursor.execute("ALTER TABLE workers ADD COLUMN IF NOT EXISTS personal_extracted_name TEXT DEFAULT NULL")
                logger.info("  ✓ Added column: personal_extracted_name")
            except Exception as e:
                logger.warning(f"  ⚠ personal_extracted_name: {str(e)}")
            
            try:
                cursor.execute("ALTER TABLE workers ADD COLUMN IF NOT EXISTS personal_extracted_dob TEXT DEFAULT NULL")
                logger.info("  ✓ Added column: personal_extracted_dob")
            except Exception as e:
                logger.warning(f"  ⚠ personal_extracted_dob: {str(e)}")
        else:
            logger.warning("  ⚠ workers table not found, skipping")
        
        # Add extraction and verification columns to educational_documents table
        if 'educational_documents' in existing_tables:
            logger.info("\n[EDUCATIONAL_DOCUMENTS TABLE] Adding verification columns...")
            try:
                cursor.execute("ALTER TABLE educational_documents ADD COLUMN IF NOT EXISTS raw_ocr_text TEXT DEFAULT NULL")
                logger.info("  ✓ Added column: raw_ocr_text")
            except Exception as e:
                logger.warning(f"  ⚠ raw_ocr_text: {str(e)}")
            
            try:
                cursor.execute("ALTER TABLE educational_documents ADD COLUMN IF NOT EXISTS llm_extracted_data TEXT DEFAULT NULL")
                logger.info("  ✓ Added column: llm_extracted_data")
            except Exception as e:
                logger.warning(f"  ⚠ llm_extracted_data: {str(e)}")
            
            try:
                cursor.execute("ALTER TABLE educational_documents ADD COLUMN IF NOT EXISTS extracted_name TEXT DEFAULT NULL")
                logger.info("  ✓ Added column: extracted_name")
            except Exception as e:
                logger.warning(f"  ⚠ extracted_name: {str(e)}")
            
            try:
                cursor.execute("ALTER TABLE educational_documents ADD COLUMN IF NOT EXISTS extracted_dob TEXT DEFAULT NULL")
                logger.info("  ✓ Added column: extracted_dob")
            except Exception as e:
                logger.warning(f"  ⚠ extracted_dob: {str(e)}")
            
            try:
                cursor.execute("ALTER TABLE educational_documents ADD COLUMN IF NOT EXISTS verification_status TEXT DEFAULT 'pending'")
                logger.info("  ✓ Added column: verification_status")
            except Exception as e:
                logger.warning(f"  ⚠ verification_status: {str(e)}")
            
            try:
                cursor.execute("ALTER TABLE educational_documents ADD COLUMN IF NOT EXISTS verification_errors TEXT DEFAULT NULL")
                logger.info("  ✓ Added column: verification_errors")
            except Exception as e:
                logger.warning(f"  ⚠ verification_errors: {str(e)}")
        else:
            logger.warning("  ⚠ educational_documents table not found, skipping")
        
        # Create indexes for faster verification queries
        logger.info("\n[INDEXES] Creating performance indexes...")
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_workers_verification_status ON workers(verification_status)")
            logger.info("  ✓ Created index: idx_workers_verification_status")
        except Exception as e:
            logger.warning(f"  ⚠ idx_workers_verification_status: {str(e)}")
        
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_educational_documents_verification ON educational_documents(worker_id, verification_status)")
            logger.info("  ✓ Created index: idx_educational_documents_verification")
        except Exception as e:
            logger.warning(f"  ⚠ idx_educational_documents_verification: {str(e)}")
        
        conn.commit()
        
        # Log final status
        logger.info("\n" + "=" * 70)
        logger.info("✓ MIGRATION COMPLETED SUCCESSFULLY")
        logger.info("=" * 70)
        logger.info("\nColumns added:")
        logger.info("  - workers: verification_status, verified_at, verification_errors,")
        logger.info("             personal_extracted_name, personal_extracted_dob")
        logger.info("  - educational_documents: raw_ocr_text, llm_extracted_data,")
        logger.info("                           extracted_name, extracted_dob,")
        logger.info("                           verification_status, verification_errors")
        logger.info("=" * 70)
        
        return True
        
    except Exception as e:
        logger.error(f"\n✗ MIGRATION FAILED: {str(e)}", exc_info=True)
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    success = migrate_add_verification_columns()
    exit(0 if success else 1)
