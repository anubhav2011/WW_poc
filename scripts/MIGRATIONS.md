# Database Migration System

This directory contains the database migration framework for the Worker CV/Job Matching system.

## Overview

The migration system uses a simple Python-based approach that:
- Tracks all applied migrations automatically
- Supports upgrade (up) and rollback (down) operations
- Uses SQLite WAL mode for reliable concurrent access
- Records migration history in the `migrations` table

## Files

- **`migration_base.py`** - Core migration framework (base classes and runner)
- **`_001_init_schema.py`** - Initial schema creation migration
- **`run_migrations.py`** - Main migration runner script
- **`MIGRATIONS.md`** - This documentation file

## Usage

### Run All Pending Migrations
```bash
python scripts/run_migrations.py
```

### Check Migration Status
```bash
python scripts/run_migrations.py --status
```

### Rollback Last Migration (Careful!)
```bash
python scripts/run_migrations.py --rollback
```

## Creating New Migrations

To add a new migration (e.g., adding a new table):

### 1. Create Migration File
Create a new file in `/scripts` following the naming pattern: `_NNN_description.py`

Example: `_002_add_job_applicants_table.py`

### 2. Define Migration Class
Inherit from `Migration` base class and implement `up()` and `down()` methods:

```python
from migration_base import Migration
import sqlite3
import logging

logger = logging.getLogger(__name__)

class AddJobApplicantsTable(Migration):
    """Add job_applicants table for tracking applications."""
    
    def up(self, conn: sqlite3.Connection) -> bool:
        """Create new table."""
        cursor = conn.cursor()
        try:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_applicants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_id TEXT NOT NULL,
                job_id INTEGER NOT NULL,
                status TEXT DEFAULT 'applied',
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (worker_id) REFERENCES workers(worker_id),
                FOREIGN KEY (job_id) REFERENCES jobs(job_id)
            )
            """)
            conn.commit()
            logger.info("✓ job_applicants table created")
            return True
        except Exception as e:
            logger.error(f"Error: {str(e)}", exc_info=True)
            conn.rollback()
            return False
    
    def down(self, conn: sqlite3.Connection) -> bool:
        """Drop table (rollback)."""
        cursor = conn.cursor()
        try:
            cursor.execute("DROP TABLE IF EXISTS job_applicants")
            conn.commit()
            logger.info("✓ job_applicants table dropped")
            return True
        except Exception as e:
            logger.error(f"Error: {str(e)}", exc_info=True)
            conn.rollback()
            return False
```

### 3. Register Migration
Add the migration to `run_migrations.py`:

```python
def run_all_migrations():
    """Run all migrations in order."""
    runner = MigrationRunner(str(DB_PATH))
    
    # Define migrations in order
    InitSchema = load_migration("_001_init_schema", "InitializeSchema")
    AddApplicants = load_migration("_002_add_job_applicants", "AddJobApplicantsTable")
    
    migrations = [
        InitSchema(),
        AddApplicants(),  # New migration
    ]
    
    success = runner.run_migrations(migrations)
    return success
```

### 4. Run Migrations
```bash
python scripts/run_migrations.py
```

## Migration Tracking

All applied migrations are stored in the `migrations` table:

```
id | migration_name      | applied_at
---|---------------------|---------------------------
1  | InitializeSchema    | 2024-01-15 10:30:45.123456
2  | AddJobApplicants    | 2024-01-15 10:35:20.654321
```

The runner automatically:
- Checks if a migration has already been applied
- Skips previously applied migrations
- Logs all actions for audit trail

## Best Practices

1. **Always use `up()` and `down()` methods** - Allows rollback if needed
2. **Use descriptive names** - File names should clearly indicate what changes
3. **Log actions** - Use `logger.info()` for visibility into what's happening
4. **Return True/False** - Indicates success/failure for proper error handling
5. **Use try-finally** - Ensure connections are always closed
6. **Test migrations** - Run on test database before production

## Troubleshooting

### Migration Fails with "Database is locked"
- SQLite is busy with another process
- Wait a few seconds and retry
- The timeout is set to 30 seconds by default

### Migration Shows as Applied But Tables Missing
- Check if `migrations` table has an entry
- Clear the entry: `DELETE FROM migrations WHERE migration_name = 'YourMigration'`
- Re-run the migration

### Need to Clear All Migrations (Development Only)
```bash
sqlite3 data/workers.db "DELETE FROM migrations; DROP TABLE IF EXISTS migrations;"
```

## Integration with FastAPI

The migration system runs automatically when the app initializes:

```python
# In main.py
from db.database import init_db
from scripts.run_migrations import run_all_migrations

if __name__ == "__main__":
    # Run migrations before starting app
    run_all_migrations()
    
    # Then start the app
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

You can also run migrations manually anytime before running the app.
