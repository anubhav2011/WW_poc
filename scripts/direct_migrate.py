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

# Ensure data directory exists
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
logger.info(f"Data directory: {DB_PATH.parent}")

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

def apply_init_schema(conn):
    """Apply the InitializeSchema migration."""
    try:
        cursor = conn.cursor()
        logger.info("Applying InitializeSchema migration...")
        
        # Create workers table
        logger.info("  - Creating workers table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            worker_id TEXT PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            date_of_birth TEXT,
            mobile_number TEXT UNIQUE,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            personal_document_path TEXT,
            educational_document_paths TEXT
        )
        """)
        
        # Create personal_documents table
        logger.info("  - Creating personal_documents table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS personal_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id TEXT NOT NULL,
            document_type TEXT,
            name TEXT,
            date_of_birth TEXT,
            document_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (worker_id) REFERENCES workers(worker_id)
        )
        """)
        
        # Create educational_documents table
        logger.info("  - Creating educational_documents table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS educational_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id TEXT NOT NULL,
            document_type TEXT,
            qualification TEXT,
            board TEXT,
            stream TEXT,
            year_of_passing TEXT,
            school_name TEXT,
            marks_type TEXT,
            marks TEXT,
            percentage REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (worker_id) REFERENCES workers(worker_id)
        )
        """)
        
        # Create experience table
        logger.info("  - Creating experience table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS experience (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id TEXT NOT NULL,
            position TEXT,
            company TEXT,
            start_date TEXT,
            end_date TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (worker_id) REFERENCES workers(worker_id)
        )
        """)
        
        # Create skills table
        logger.info("  - Creating skills table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id TEXT NOT NULL,
            skill_name TEXT,
            proficiency TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (worker_id) REFERENCES workers(worker_id)
        )
        """)
        
        # Create jobs table
        logger.info("  - Creating jobs table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT,
            description TEXT,
            requirements TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create job_matches table
        logger.info("  - Creating job_matches table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id TEXT NOT NULL,
            job_id INTEGER NOT NULL,
            match_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (worker_id) REFERENCES workers(worker_id),
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
        """)
        
        # Create cv_data table
        logger.info("  - Creating cv_data table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cv_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id TEXT NOT NULL,
            cv_content TEXT,
            language TEXT DEFAULT 'en',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (worker_id) REFERENCES workers(worker_id)
        )
        """)
        
        # Create triggers for updated_at
        logger.info("  - Creating triggers...")
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS workers_updated_at 
        AFTER UPDATE ON workers
        BEGIN
            UPDATE workers SET updated_at = CURRENT_TIMESTAMP WHERE worker_id = NEW.worker_id;
        END
        """)
        
        conn.commit()
        logger.info("✓ InitializeSchema migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ Error applying migration: {str(e)}", exc_info=True)
        conn.rollback()
        return False

def add_column_if_not_exists(cursor, table_name, column_name, column_definition):
    """Helper function to add a column if it doesn't exist."""
    try:
        # Check if column exists by attempting to query it
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        
        if column_name not in columns:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
            logger.info(f"    ✓ Added column {column_name} to {table_name}")
        else:
            logger.info(f"    ⊘ Column {column_name} already exists in {table_name}")
    except Exception as e:
        logger.error(f"    ✗ Error adding column {column_name}: {str(e)}")
        raise

def apply_add_verification_columns(conn):
    """Apply the AddVerificationColumns migration."""
    try:
        cursor = conn.cursor()
        logger.info("Applying AddVerificationColumns migration...")
        
        # Add verification columns to workers table
        logger.info("  - Adding columns to workers table...")
        add_column_if_not_exists(cursor, "workers", "verification_status", "TEXT DEFAULT 'pending'")
        add_column_if_not_exists(cursor, "workers", "verified_at", "TIMESTAMP DEFAULT NULL")
        add_column_if_not_exists(cursor, "workers", "verification_errors", "TEXT DEFAULT NULL")
        add_column_if_not_exists(cursor, "workers", "personal_extracted_name", "TEXT DEFAULT NULL")
        add_column_if_not_exists(cursor, "workers", "personal_extracted_dob", "TEXT DEFAULT NULL")
        
        logger.info("  - Adding columns to educational_documents table...")
        # Add extraction and verification columns to educational_documents table
        add_column_if_not_exists(cursor, "educational_documents", "raw_ocr_text", "TEXT DEFAULT NULL")
        add_column_if_not_exists(cursor, "educational_documents", "llm_extracted_data", "TEXT DEFAULT NULL")
        add_column_if_not_exists(cursor, "educational_documents", "extracted_name", "TEXT DEFAULT NULL")
        add_column_if_not_exists(cursor, "educational_documents", "extracted_dob", "TEXT DEFAULT NULL")
        add_column_if_not_exists(cursor, "educational_documents", "verification_status", "TEXT DEFAULT 'pending'")
        add_column_if_not_exists(cursor, "educational_documents", "verification_errors", "TEXT DEFAULT NULL")
        
        # Create indexes for faster verification queries
        logger.info("  - Creating indexes...")
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_workers_verification_status ON workers(verification_status)")
            logger.info("    ✓ Created index idx_workers_verification_status")
        except Exception as e:
            logger.info(f"    ⊘ Index idx_workers_verification_status already exists")
        
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_educational_documents_verification ON educational_documents(worker_id, verification_status)")
            logger.info("    ✓ Created index idx_educational_documents_verification")
        except Exception as e:
            logger.info(f"    ⊘ Index idx_educational_documents_verification already exists")
        
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
        
        # List of migrations to apply (in order)
        migrations = [
            ("InitializeSchema", apply_init_schema),
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
