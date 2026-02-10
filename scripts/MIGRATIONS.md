# Database Migration System

Professional database migration management for your SQLite application.

## Quick Start

### Run All Migrations

```bash
cd scripts
python run_migrations.py
```

This will:
1. Initialize the database schema (if not already done)
2. Apply all pending migrations in order
3. Track which migrations have been applied
4. Display a summary of results

### Check Migration Status

```bash
python run_migrations.py --status
```

Shows:
- Total migrations applied
- List of applied migrations with timestamps

### Rollback Last Migration

```bash
python run_migrations.py --rollback
```

⚠️ **Warning**: Only use for development. Be careful with production databases.

## Migration Files

### Current Migrations

#### `_001_init_schema.py` - Initialize Database Schema
- Creates all required tables: workers, personal_documents, educational_documents, experience, skills, jobs, job_matches, cv_data
- Adds auto-update triggers
- Creates foreign key relationships

#### `_002_add_verification_columns.py` - Add Verification Columns
- Adds verification columns to `workers` table:
  - `verification_status` - Track verification state
  - `verified_at` - Timestamp of verification
  - `verification_errors` - Error messages if verification fails
  - `personal_extracted_name` - Name extracted from personal document
  - `personal_extracted_dob` - DOB extracted from personal document

- Adds verification columns to `educational_documents` table:
  - `raw_ocr_text` - Raw OCR output
  - `llm_extracted_data` - Structured data from LLM
  - `extracted_name` - Name from document
  - `extracted_dob` - DOB from document
  - `verification_status` - Verification state
  - `verification_errors` - Error details

- Creates indexes for faster queries:
  - `idx_workers_verification_status` - For filtering by verification status
  - `idx_educational_documents_verification` - For verification queries

## Creating New Migrations

### Step 1: Create Migration File

Create a new file in `scripts/` following the naming convention: `_NNN_description.py`

Example: `_003_add_new_table.py`

### Step 2: Implement Migration Class

```python
import sys
import sqlite3
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from migration_base import Migration

logger = logging.getLogger(__name__)


class AddNewTable(Migration):
    """Description of what this migration does."""
    
    name = "AddNewTable"
    description = "Add a new table for feature X"
    
    def up(self, connection: sqlite3.Connection) -> bool:
        """Apply the migration."""
        try:
            cursor = connection.cursor()
            logger.info("[AddNewTable] Creating new_table...")
            
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS new_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                column1 TEXT NOT NULL,
                column2 INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            connection.commit()
            logger.info("[AddNewTable] ✓ Table created successfully")
            return True
            
        except Exception as e:
            logger.error(f"[AddNewTable] ✗ Error: {str(e)}", exc_info=True)
            connection.rollback()
            return False
    
    def down(self, connection: sqlite3.Connection) -> bool:
        """Rollback the migration."""
        try:
            cursor = connection.cursor()
            logger.warning("[AddNewTable] ROLLBACK: Dropping new_table...")
            
            cursor.execute("DROP TABLE IF EXISTS new_table")
            connection.commit()
            logger.warning("[AddNewTable] ✓ Table dropped")
            return True
            
        except Exception as e:
            logger.error(f"[AddNewTable] ✗ Error rolling back: {str(e)}", exc_info=True)
            connection.rollback()
            return False
```

### Step 3: Register Migration

Edit `run_migrations.py` and add your migration to the imports and migrations list:

```python
from _003_add_new_table import AddNewTable

# In run_all_migrations() function:
migrations = [
    InitializeSchema(),
    AddVerificationColumns(),
    AddNewTable(),  # Add your migration here
]
```

### Step 4: Run Migrations

```bash
python run_migrations.py
```

## Best Practices

### ✓ DO:
- Use descriptive migration names
- Always include both `up()` and `down()` methods
- Add logging for debugging
- Test migrations on a copy of your database first
- Keep migrations focused on a single change
- Use transactions (handled by MigrationRunner)

### ✗ DON'T:
- Modify existing migrations after they're applied
- Make breaking changes without a proper migration
- Skip migration steps
- Use migrations for data cleanup (use scripts instead)

## Database Location

- **Development**: `data/workers.db`
- **SQLite WAL mode**: Enabled automatically in database.py

## Troubleshooting

### Migration Fails
1. Check the error message in logs
2. Verify the database file exists and has correct permissions
3. Test the SQL manually in a SQLite client
4. Rollback and try again

### Database Locked
- Ensure no other processes are using the database
- Close any SQLite clients
- Check for lingering database connections

### Can't Rollback
- Some operations in SQLite can't be reversed (e.g., dropping columns)
- Use `--status` to see which migrations are applied
- Manual database recreation may be needed in some cases

## Integration with Your Application

The migrations are tracked in a `migrations` table. Your application can check this to understand the current schema version:

```python
from scripts.migration_base import MigrationRunner

runner = MigrationRunner("path/to/workers.db")
applied = runner.get_applied_migrations()
status = runner.get_migration_status()

# Use this information for schema validation, feature flags, etc.
```

## Example Commands

```bash
# Run all pending migrations
python run_migrations.py

# Check current status
python run_migrations.py --status

# Rollback last migration (development only)
python run_migrations.py --rollback

# Show help
python run_migrations.py --help
```

## Migration History

All applied migrations are permanently recorded in the database with timestamps, allowing you to track schema evolution over time.
