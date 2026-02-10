"""
Migration: Initialize Database Schema
Purpose: Create all required tables for the application
Date: 2026-02-10
"""

import sys
import sqlite3
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from migration_base import Migration

logger = logging.getLogger(__name__)


class InitializeSchema(Migration):
    """Initialize all database tables."""
    
    name = "InitializeSchema"
    description = "Create all required database tables"
    
    def up(self, connection: sqlite3.Connection) -> bool:
        """Apply the migration - create all tables."""
        try:
            cursor = connection.cursor()
            logger.info("[InitializeSchema] Starting schema initialization...")
            
            # Create workers table
            logger.info("[InitializeSchema] Creating workers table...")
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
            logger.info("[InitializeSchema] Creating personal_documents table...")
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
            logger.info("[InitializeSchema] Creating educational_documents table...")
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
            logger.info("[InitializeSchema] Creating experience table...")
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
            logger.info("[InitializeSchema] Creating skills table...")
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
            logger.info("[InitializeSchema] Creating jobs table...")
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
            logger.info("[InitializeSchema] Creating job_matches table...")
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
            logger.info("[InitializeSchema] Creating cv_data table...")
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
            logger.info("[InitializeSchema] Creating triggers...")
            cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS workers_updated_at 
            AFTER UPDATE ON workers
            BEGIN
                UPDATE workers SET updated_at = CURRENT_TIMESTAMP WHERE worker_id = NEW.worker_id;
            END
            """)
            
            connection.commit()
            logger.info("[InitializeSchema] ✓ Schema initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"[InitializeSchema] ✗ Error initializing schema: {str(e)}", exc_info=True)
            connection.rollback()
            return False
    
    def down(self, connection: sqlite3.Connection) -> bool:
        """Rollback the migration - drop all tables."""
        try:
            cursor = connection.cursor()
            logger.warning("[InitializeSchema] ROLLBACK: Dropping all tables...")
            
            # Drop tables in reverse order
            cursor.execute("DROP TABLE IF EXISTS migrations")
            cursor.execute("DROP TABLE IF EXISTS job_matches")
            cursor.execute("DROP TABLE IF EXISTS jobs")
            cursor.execute("DROP TABLE IF EXISTS cv_data")
            cursor.execute("DROP TABLE IF EXISTS skills")
            cursor.execute("DROP TABLE IF EXISTS experience")
            cursor.execute("DROP TABLE IF EXISTS educational_documents")
            cursor.execute("DROP TABLE IF EXISTS personal_documents")
            cursor.execute("DROP TABLE IF EXISTS workers")
            
            connection.commit()
            logger.warning("[InitializeSchema] ✓ All tables dropped")
            return True
            
        except Exception as e:
            logger.error(f"[InitializeSchema] ✗ Error rolling back schema: {str(e)}", exc_info=True)
            connection.rollback()
            return False
