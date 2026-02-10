#!/usr/bin/env python3
"""
Direct Database Migration Runner
Applies migrations without complex imports
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

# Use absolute path
DB_PATH = Path("/vercel/share/v0-project/data/workers.db")

def init_migrations_table(conn):
    """Initialize the migrations tracking table if it doesn't exist."""
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
    logger.info("✓ Migrations table initialized")

def is_migration_applied(conn, migration_name):
    """Check if a migration has already been applied."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM migrations WHERE name = ? AND status = 'applied'", (migration_name,))
    return cursor.fetchone()[0] > 0

def record_migration(conn, migration_name):
    """Record a migration as applied."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO migrations (name, status) VALUES (?, 'applied')",
        (migration_name,)
    )
    conn.commit()

def apply_add_verification_columns(conn):
    """Apply the AddVerificationColumns migration."""
    try:
        cursor = conn.cursor()
        logger.info("Applying AddVerificationColumns migration...")
        
        # Add verification columns to workers table
        logger.info("  - Adding columns to workers table...")
        cursor.execute("ALTER TABLE workers ADD COLUMN IF NOT EXISTS verification_status TEXT DEFAULT 'pending'")
        cursor.execute("ALTER TABLE workers ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP DEFAULT NULL")
        cursor.execute("ALTER TABLE workers ADD COLUMN IF NOT EXISTS verification_errors TEXT DEFAULT NULL")
        cursor.execute("ALTER TABLE workers ADD COLUMN IF NOT EXISTS personal_extracted_name TEXT DEFAULT NULL")
        cursor.execute("ALTER TABLE workers ADD COLUMN IF NOT EXISTS personal_extracted_dob TEXT DEFAULT NULL")
        
        logger.info("  - Adding columns to educational_documents table...")
        # Add extraction and verification columns to educational_documents table
        cursor.execute("ALTER TABLE educational_documents ADD COLUMN IF NOT EXISTS raw_ocr_text TEXT DEFAULT NULL")
        cursor.execute("ALTER TABLE educational_documents ADD COLUMN IF NOT EXISTS llm_extracted_data TEXT DEFAULT NULL")
        cursor.execute("ALTER TABLE educational_documents ADD COLUMN IF NOT EXISTS extracted_name TEXT DEFAULT NULL")
        cursor.execute("ALTER TABLE educational_documents ADD COLUMN IF NOT EXISTS extracted_dob TEXT DEFAULT NULL")
        cursor.execute("ALTER TABLE educational_documents ADD COLUMN IF NOT EXISTS verification_status TEXT DEFAULT 'pending'")
        cursor.execute("ALTER TABLE educational_documents ADD COLUMN IF NOT EXISTS verification_errors TEXT DEFAULT NULL")
        
        # Create indexes for faster verification queries
        logger.info("  - Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_workers_verification_status ON workers(verification_status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_educational_documents_verification ON educational_documents(worker_id, verification_status)")
        
        conn.commit()
        logger.info("✓ AddVerificationColumns migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ Error applying migration: {str(e)}", exc_info=True)
        conn.rollback()
        return False

def main():
    """Run migrations."""
    logger.info("=" * 60)
    logger.info("Database Migration Runner")
    logger.info("=" * 60)
    logger.info(f"Database: {DB_PATH}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        
        # Initialize migrations table
        init_migrations_table(conn)
        
        # List of migrations to apply
        migrations = [
            ("AddVerificationColumns", apply_add_verification_columns),
        ]
        
        successful = 0
        failed = 0
        
        for migration_name, migration_func in migrations:
            if is_migration_applied(conn, migration_name):
                logger.info(f"⊘ Migration '{migration_name}' already applied, skipping")
            else:
                if migration_func(conn):
                    record_migration(conn, migration_name)
                    successful += 1
                else:
                    failed += 1
        
        # Print summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("Migration Summary")
        logger.info("=" * 60)
        logger.info(f"Total migrations to process: {len(migrations)}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {failed}")
        
        # Show applied migrations
        cursor = conn.cursor()
        cursor.execute("SELECT name, applied_at FROM migrations ORDER BY applied_at")
        rows = cursor.fetchall()
        
        logger.info(f"\nApplied migrations ({len(rows)}):")
        for migration_name, applied_at in rows:
            logger.info(f"  ✓ {migration_name} (applied at {applied_at})")
        
        logger.info("=" * 60)
        
        if failed == 0:
            logger.info("✓ All migrations completed successfully!")
        else:
            logger.error(f"✗ {failed} migration(s) failed")
        
        conn.close()
        return failed == 0
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
