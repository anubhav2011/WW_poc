#!/usr/bin/env python3
"""
Database Migration Script for Worker CV/Job Matching POC
Initializes SQLite database schema with all required tables
Run before starting the main application
"""

import sqlite3
import os
import sys
from pathlib import Path
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Use absolute path so the same DB is used regardless of cwd
# Works in both direct execution and script execution environments
DB_PATH = Path("/vercel/share/v0-project/data/workers.db")


def get_db_connection(timeout: float = 30.0):
    """Get SQLite database connection with WAL mode and timeout."""
    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH), timeout=timeout)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=30000")  # 30 seconds in ms
        except sqlite3.OperationalError:
            pass  # DB may be locked by another process; connection still usable with timeout
        logger.debug(f"Database connection established: {DB_PATH}")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}", exc_info=True)
        raise


def run_migration():
    """Execute database migration to create all required tables and columns."""
    max_attempts = 3
    lock_wait_sec = 2
    conn = None
    cursor = None

    try:
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Initializing database at {DB_PATH} (attempt {attempt}/{max_attempts})")
                DB_PATH.parent.mkdir(parents=True, exist_ok=True)
                conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
                conn.row_factory = sqlite3.Row
                try:
                    conn.execute("PRAGMA journal_mode=WAL")
                    conn.execute("PRAGMA busy_timeout=30000")
                except sqlite3.OperationalError as e:
                    logger.warning(f"Could not set WAL/busy_timeout (database may be in use): {e}. Continuing.")
                cursor = conn.cursor()
                break
            except sqlite3.OperationalError as e:
                if conn is not None:
                    try:
                        conn.close()
                    except Exception:
                        pass
                    conn = None
                if "locked" in str(e).lower() and attempt < max_attempts:
                    logger.warning(f"Database locked (attempt {attempt}), waiting {lock_wait_sec}s before retry: {e}")
                    time.sleep(lock_wait_sec)
                else:
                    raise

        if conn is None or cursor is None:
            raise RuntimeError("Failed to obtain database connection after retries")

        # Workers table
        logger.info("Creating workers table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            worker_id TEXT PRIMARY KEY,
            mobile_number TEXT NOT NULL,
            name TEXT,
            dob TEXT,
            address TEXT,
            personal_document_path TEXT,
            educational_document_paths TEXT,
            video_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Work experience table
        logger.info("Creating work_experience table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS work_experience (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id TEXT NOT NULL,
            primary_skill TEXT,
            experience_years INTEGER,
            skills TEXT,
            preferred_location TEXT,
            current_location TEXT,
            availability TEXT,
            workplaces TEXT,
            total_experience_duration INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (worker_id) REFERENCES workers(worker_id)
        )
        """)

        # Voice call sessions table
        logger.info("Creating voice_sessions table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS voice_sessions (
            call_id TEXT PRIMARY KEY,
            worker_id TEXT,
            phone_number TEXT,
            status TEXT DEFAULT 'initiated',
            current_step INTEGER DEFAULT 0,
            responses_json TEXT,
            transcript TEXT,
            experience_json TEXT,
            exp_ready BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (worker_id) REFERENCES workers(worker_id)
        )
        """)

        # Job listings table
        logger.info("Creating jobs table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            required_skills TEXT,
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Educational documents table
        logger.info("Creating educational_documents table...")
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

        # Experience conversation sessions table
        logger.info("Creating experience_sessions table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS experience_sessions (
            session_id TEXT PRIMARY KEY,
            worker_id TEXT NOT NULL,
            current_question INTEGER DEFAULT 0,
            raw_conversation TEXT,
            structured_data TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (worker_id) REFERENCES workers(worker_id)
        )
        """)

        # Pending OCR results table (for step-by-step review workflow)
        logger.info("Creating pending_ocr_results table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pending_ocr_results (
            worker_id TEXT PRIMARY KEY,
            personal_document_path TEXT,
            educational_document_path TEXT,
            personal_data_json TEXT,
            education_data_json TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (worker_id) REFERENCES workers(worker_id)
        )
        """)

        # CV status table - tracks CV generation status for each worker
        logger.info("Creating cv_status table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cv_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id TEXT UNIQUE NOT NULL,
            has_cv BOOLEAN DEFAULT 0,
            cv_generated_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (worker_id) REFERENCES workers(worker_id)
        )
        """)

        # Add trigger to auto-update updated_at on cv_status
        logger.info("Creating trigger for cv_status timestamp...")
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_cv_status_timestamp 
        AFTER UPDATE ON cv_status
        BEGIN
            UPDATE cv_status SET updated_at = CURRENT_TIMESTAMP WHERE worker_id = NEW.worker_id;
        END
        """)

        # Add verification columns to workers table
        logger.info("Adding verification columns to workers table...")
        try:
            cursor.execute("ALTER TABLE workers ADD COLUMN name_verified BOOLEAN DEFAULT 0")
            logger.info("  ✓ Added name_verified column")
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                raise
            logger.info("  - name_verified column already exists")

        try:
            cursor.execute("ALTER TABLE workers ADD COLUMN dob_verified BOOLEAN DEFAULT 0")
            logger.info("  ✓ Added dob_verified column")
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                raise
            logger.info("  - dob_verified column already exists")

        try:
            cursor.execute("ALTER TABLE workers ADD COLUMN verification_status TEXT DEFAULT 'pending'")
            logger.info("  ✓ Added verification_status column")
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                raise
            logger.info("  - verification_status column already exists")

        try:
            cursor.execute("ALTER TABLE workers ADD COLUMN verified_at TIMESTAMP")
            logger.info("  ✓ Added verified_at column")
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                raise
            logger.info("  - verified_at column already exists")

        # Add verification columns to educational_documents table
        logger.info("Adding verification columns to educational_documents table...")
        try:
            cursor.execute("ALTER TABLE educational_documents ADD COLUMN verified BOOLEAN DEFAULT 0")
            logger.info("  ✓ Added verified column")
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                raise
            logger.info("  - verified column already exists")

        try:
            cursor.execute("ALTER TABLE educational_documents ADD COLUMN verification_notes TEXT")
            logger.info("  ✓ Added verification_notes column")
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                raise
            logger.info("  - verification_notes column already exists")

        conn.commit()
        logger.info("Database initialized successfully!")
        logger.info(f"Database location: {DB_PATH}")
        return True

    except Exception as e:
        logger.error(f"Error during migration: {str(e)}", exc_info=True)
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        return False

    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


if __name__ == "__main__":
    logger.info("Starting database migration...")
    success = run_migration()
    sys.exit(0 if success else 1)
