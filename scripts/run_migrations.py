#!/usr/bin/env python3
"""
Database Migration Runner
Execute all pending migrations automatically
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
try:
    SCRIPTS_DIR = Path(__file__).parent
    PROJECT_ROOT = SCRIPTS_DIR.parent
except NameError:
    # Fallback: assume we're in the project root or scripts directory
    cwd = Path.cwd()
    if cwd.name == 'scripts':
        SCRIPTS_DIR = cwd
        PROJECT_ROOT = cwd.parent
    else:
        PROJECT_ROOT = cwd
        SCRIPTS_DIR = cwd / 'scripts'

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SCRIPTS_DIR))

from migration_base import MigrationRunner
from _001_init_schema import InitializeSchema
from _002_add_verification_columns import AddVerificationColumns

# Database path
DB_PATH = PROJECT_ROOT / "data" / "workers.db"


def run_all_migrations():
    """Run all pending migrations in order."""
    logger.info("=" * 60)
    logger.info("Database Migration Runner")
    logger.info("=" * 60)
    logger.info(f"Database: {DB_PATH}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    runner = MigrationRunner(str(DB_PATH))
    
    # Define all migrations in order
    # These will run in sequence, skipping any already applied
    migrations = [
        InitializeSchema(),
        AddVerificationColumns(),
    ]
    
    logger.info(f"Total migrations to process: {len(migrations)}")
    logger.info("")
    
    successful = 0
    failed = 0
    
    for migration in migrations:
        logger.info(f"Processing: {migration.name}")
        if runner.run_migration(migration):
            successful += 1
        else:
            failed += 1
        logger.info("")
    
    # Print summary
    logger.info("=" * 60)
    logger.info("Migration Summary")
    logger.info("=" * 60)
    logger.info(f"Total migrations: {len(migrations)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info("=" * 60)
    
    # Show applied migrations
    applied = runner.get_applied_migrations()
    logger.info(f"\nApplied migrations ({len(applied)}):")
    for migration_name in applied:
        logger.info(f"  ✓ {migration_name}")
    logger.info("")
    
    if failed == 0:
        logger.info("✓ All migrations completed successfully!")
        return True
    else:
        logger.error(f"✗ {failed} migration(s) failed")
        return False


def show_status():
    """Show current migration status."""
    logger.info("=" * 60)
    logger.info("Migration Status")
    logger.info("=" * 60)
    
    runner = MigrationRunner(str(DB_PATH))
    status = runner.get_migration_status()
    
    logger.info(f"Total applied migrations: {status['total']}")
    logger.info("")
    
    if status['migrations']:
        logger.info("Applied Migrations:")
        for migration in status['migrations']:
            logger.info(f"  ✓ {migration['name']}")
            logger.info(f"    Applied at: {migration['applied_at']}")
            logger.info(f"    Status: {migration['status']}")
    else:
        logger.info("No migrations applied yet")
    
    logger.info("=" * 60)


def rollback_last():
    """Rollback the last migration (use with caution)."""
    logger.warning("=" * 60)
    logger.warning("ROLLBACK MODE - This will undo the last migration!")
    logger.warning("=" * 60)
    
    runner = MigrationRunner(str(DB_PATH))
    applied = runner.get_applied_migrations()
    
    if not applied:
        logger.warning("No migrations to rollback")
        return False
    
    last_migration_name = applied[-1]
    logger.warning(f"Rolling back: {last_migration_name}")
    
    # Map migration names to classes
    migration_map = {
        "InitializeSchema": InitializeSchema(),
        "AddVerificationColumns": AddVerificationColumns(),
    }
    
    if last_migration_name not in migration_map:
        logger.error(f"Unknown migration: {last_migration_name}")
        return False
    
    migration = migration_map[last_migration_name]
    success = runner.rollback_migration(migration)
    
    logger.warning("=" * 60)
    if success:
        logger.warning("✓ Rollback completed")
    else:
        logger.error("✗ Rollback failed")
    logger.warning("=" * 60)
    
    return success


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "--status":
            show_status()
        elif command == "--rollback":
            rollback_last()
        elif command == "--help":
            print("Database Migration Runner")
            print("")
            print("Usage: python run_migrations.py [COMMAND]")
            print("")
            print("Commands:")
            print("  (none)          Run all pending migrations (default)")
            print("  --status        Show current migration status")
            print("  --rollback      Rollback the last migration (use with caution)")
            print("  --help          Show this help message")
            print("")
            print(f"Database path: {DB_PATH}")
        else:
            logger.error(f"Unknown command: {command}")
            print("Use --help for usage information")
    else:
        # Default: run all migrations
        success = run_all_migrations()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
