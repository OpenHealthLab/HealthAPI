#!/usr/bin/env python3
"""
SQLite Database Backup Script

This script creates timestamped backups of the SQLite database with optional
cleanup of old backups to manage storage space.

Usage:
    python scripts/backup_database.py
    python scripts/backup_database.py --db-path custom.db
    python scripts/backup_database.py --keep-days 7
    python scripts/backup_database.py --cleanup-only

Author: Healthcare AI Backend Contributors
License: MIT
"""

import argparse
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List


def backup_database(
    db_path: str = "healthcare_ai.db",
    backup_dir: str = "backups",
    keep_days: int = 30,
) -> Path:
    """
    Create a timestamped backup of the SQLite database.

    Args:
        db_path: Path to the source database file
        backup_dir: Directory where backups will be stored
        keep_days: Number of days to keep old backups (0 to disable cleanup)

    Returns:
        Path: Path to the created backup file

    Raises:
        FileNotFoundError: If source database doesn't exist
        PermissionError: If unable to create backup directory or copy file
        OSError: If other file system errors occur
    """
    try:
        # Convert paths to Path objects
        source_db = Path(db_path)
        backup_path = Path(backup_dir)

        # Validate source database exists
        if not source_db.exists():
            raise FileNotFoundError(
                f"Source database not found: {source_db.absolute()}"
            )

        if not source_db.is_file():
            raise ValueError(
                f"Source path is not a file: {source_db.absolute()}"
            )

        # Create backup directory if it doesn't exist
        backup_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Backup directory ready: {backup_path.absolute()}")

        # Generate timestamped backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_name = source_db.stem  # Filename without extension
        backup_file = backup_path / f"{db_name}_backup_{timestamp}.db"

        # Copy database to backup location
        # Using copy2 to preserve metadata (timestamps, permissions)
        shutil.copy2(source_db, backup_file)

        # Verify backup was created
        if not backup_file.exists():
            raise OSError(f"Backup file was not created: {backup_file}")

        # Get file sizes for confirmation
        source_size = source_db.stat().st_size
        backup_size = backup_file.stat().st_size

        print(f"✓ Database backed up successfully!")
        print(f"  Source: {source_db.absolute()} ({source_size:,} bytes)")
        print(f"  Backup: {backup_file.absolute()} ({backup_size:,} bytes)")

        # Cleanup old backups if requested
        if keep_days > 0:
            cleanup_old_backups(backup_path, keep_days, db_name)

        return backup_file

    except FileNotFoundError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        print(
            f"  Make sure the database exists at: {Path(db_path).absolute()}",
            file=sys.stderr,
        )
        raise

    except PermissionError as e:
        print(f"✗ Permission Error: {e}", file=sys.stderr)
        print(
            "  Check that you have write permissions for the backup directory",
            file=sys.stderr,
        )
        raise

    except Exception as e:
        print(f"✗ Unexpected error during backup: {e}", file=sys.stderr)
        raise


def cleanup_old_backups(
    backup_dir: Path, keep_days: int, db_name: str = "healthcare_ai"
) -> List[Path]:
    """
    Remove backup files older than the specified number of days.

    Args:
        backup_dir: Directory containing backup files
        keep_days: Number of days to keep backups
        db_name: Base name of the database to match backup files

    Returns:
        List[Path]: List of deleted backup files
    """
    deleted_files = []
    cutoff_date = datetime.now() - timedelta(days=keep_days)

    try:
        # Find all backup files for this database
        pattern = f"{db_name}_backup_*.db"
        backup_files = list(backup_dir.glob(pattern))

        if not backup_files:
            print(f"  No backup files found matching pattern: {pattern}")
            return deleted_files

        print(f"\n🗑️  Checking for backups older than {keep_days} days...")

        for backup_file in backup_files:
            # Get file modification time
            file_mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)

            if file_mtime < cutoff_date:
                try:
                    file_size = backup_file.stat().st_size
                    backup_file.unlink()
                    deleted_files.append(backup_file)
                    print(
                        f"  ✓ Deleted old backup: {backup_file.name} "
                        f"({file_size:,} bytes, {file_mtime.strftime('%Y-%m-%d')})"
                    )
                except Exception as e:
                    print(
                        f"  ✗ Failed to delete {backup_file.name}: {e}",
                        file=sys.stderr,
                    )

        if deleted_files:
            print(f"  Cleaned up {len(deleted_files)} old backup(s)")
        else:
            print(f"  No backups older than {keep_days} days found")

    except Exception as e:
        print(f"✗ Error during cleanup: {e}", file=sys.stderr)

    return deleted_files


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Backup SQLite database with optional cleanup of old backups",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic backup with default settings (keep 30 days)
  python scripts/backup_database.py

  # Backup with custom database path
  python scripts/backup_database.py --db-path ./data/custom.db

  # Keep only last 7 days of backups
  python scripts/backup_database.py --keep-days 7

  # Disable automatic cleanup
  python scripts/backup_database.py --keep-days 0

  # Only run cleanup without creating new backup
  python scripts/backup_database.py --cleanup-only

  # Custom backup directory
  python scripts/backup_database.py --backup-dir ./my_backups
        """,
    )

    parser.add_argument(
        "--db-path",
        default="healthcare_ai.db",
        help="Path to the SQLite database file (default: healthcare_ai.db)",
    )

    parser.add_argument(
        "--backup-dir",
        default="backups",
        help="Directory to store backups (default: backups)",
    )

    parser.add_argument(
        "--keep-days",
        type=int,
        default=30,
        help="Number of days to keep old backups, 0 to disable cleanup (default: 30)",
    )

    parser.add_argument(
        "--cleanup-only",
        action="store_true",
        help="Only cleanup old backups without creating a new one",
    )

    return parser.parse_args()


def main():
    """Main entry point for the backup script."""
    args = parse_arguments()

    print("=" * 60)
    print("SQLite Database Backup Script")
    print("=" * 60)
    print(f"Database: {args.db_path}")
    print(f"Backup Directory: {args.backup_dir}")
    print(f"Retention: {args.keep_days} days" if args.keep_days > 0 else "Retention: Unlimited")
    print("=" * 60)
    print()

    try:
        if args.cleanup_only:
            # Only perform cleanup
            print("Running cleanup only (no new backup will be created)...\n")
            db_name = Path(args.db_path).stem
            cleanup_old_backups(Path(args.backup_dir), args.keep_days, db_name)
        else:
            # Create backup (cleanup happens automatically if keep_days > 0)
            backup_file = backup_database(
                db_path=args.db_path,
                backup_dir=args.backup_dir,
                keep_days=args.keep_days,
            )

        print("\n" + "=" * 60)
        print("✓ Backup process completed successfully!")
        print("=" * 60)
        return 0

    except Exception as e:
        print("\n" + "=" * 60, file=sys.stderr)
        print("✗ Backup process failed!", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
