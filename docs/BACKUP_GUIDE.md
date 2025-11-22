# Database Backup Guide

This guide explains how to use the SQLite database backup script to protect your Healthcare AI data.

## Overview

The `scripts/backup_database.py` script creates timestamped backups of your SQLite database with optional automatic cleanup of old backups.

## Quick Start

### Basic Usage

Create a backup with default settings (keeps last 30 days):

```bash
python scripts/backup_database.py
```

This will:
- Create a backup in the `backups/` directory
- Name it with a timestamp: `healthcare_ai_backup_YYYYMMDD_HHMMSS.db`
- Remove backups older than 30 days

### Common Options

**Backup custom database:**
```bash
python scripts/backup_database.py --db-path ./data/custom.db
```

**Keep only last 7 days of backups:**
```bash
python scripts/backup_database.py --keep-days 7
```

**Disable automatic cleanup:**
```bash
python scripts/backup_database.py --keep-days 0
```

**Use custom backup directory:**
```bash
python scripts/backup_database.py --backup-dir ./my_backups
```

**Cleanup old backups without creating new one:**
```bash
python scripts/backup_database.py --cleanup-only
```

## Features

### ✅ Acceptance Criteria

- **Timestamped Backups**: Each backup includes date and time in filename
- **Directory Creation**: Automatically creates backup directory if it doesn't exist
- **Error Handling**: Gracefully handles missing files, permissions, and other errors
- **Documentation**: Complete docs with examples and best practices
- **Cleanup**: Optional automatic removal of old backups to save space

### Additional Features

- **Progress Feedback**: Clear console output showing what's happening
- **Verification**: Confirms backup was created and shows file sizes
- **Flexible Options**: Command-line arguments for all settings
- **Help Text**: Built-in help with `--help` flag

## Automation

### Schedule Daily Backups (Linux/macOS)

Add to crontab for daily backups at 2 AM:

```bash
crontab -e
```

Add this line:
```
0 2 * * * cd /path/to/HealthAPI && python scripts/backup_database.py --keep-days 7
```

### Schedule with Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., Daily at 2:00 AM)
4. Action: Start a program
   - Program: `python`
   - Arguments: `scripts/backup_database.py --keep-days 7`
   - Start in: `C:\path\to\HealthAPI`

### Docker Integration

Add to your Docker Compose file:

```yaml
services:
  backup:
    image: python:3.8
    volumes:
      - ./:/app
    working_dir: /app
    command: python scripts/backup_database.py --keep-days 7
    profiles: ["backup"]
```

Run with:
```bash
docker-compose run --rm backup
```

## Best Practices

### Backup Frequency

- **Development**: Daily backups with 7-day retention
- **Production**: Multiple daily backups with 30-day retention
- **Critical Systems**: Hourly backups with longer retention

### Storage Recommendations

1. **Local Backups**: Fast recovery, vulnerable to hardware failure
2. **Network Storage**: Better redundancy, requires network access
3. **Cloud Storage**: Best redundancy, may have compliance considerations

### Testing Backups

Regularly verify your backups can be restored:

```bash
# Copy backup to test location
cp backups/healthcare_ai_backup_20231115_140000.db test_restore.db

# Test database integrity
sqlite3 test_restore.db "PRAGMA integrity_check;"

# Test application with restored database
DATABASE_URL=sqlite:///./test_restore.db python run.py
```

## Troubleshooting

### "Source database not found"

**Cause**: Database file doesn't exist at specified path

**Solution**: Check database path in `.env` file:
```bash
cat .env | grep DATABASE_URL
```

### "Permission denied"

**Cause**: Insufficient permissions to read database or write backups

**Solution**: Check file permissions:
```bash
ls -l healthcare_ai.db
ls -ld backups/
```

Fix permissions:
```bash
chmod 644 healthcare_ai.db
chmod 755 backups/
```

### Disk Space Issues

Monitor backup directory size:
```bash
du -sh backups/
```

Reduce retention period:
```bash
python scripts/backup_database.py --keep-days 3
```

Or manually cleanup:
```bash
python scripts/backup_database.py --cleanup-only --keep-days 7
```

## Recovery

### Restoring from Backup

1. **Stop the application:**
```bash
# Stop running server
pkill -f "python run.py"
```

2. **Backup current database (safety):**
```bash
cp healthcare_ai.db healthcare_ai.db.emergency_backup
```

3. **Restore from backup:**
```bash
cp backups/healthcare_ai_backup_20231115_140000.db healthcare_ai.db
```

4. **Verify integrity:**
```bash
sqlite3 healthcare_ai.db "PRAGMA integrity_check;"
```

5. **Restart application:**
```bash
python run.py
```

### Partial Recovery

If you need data from a backup without full restoration:

```bash
# Open both databases
sqlite3 healthcare_ai.db

# Attach backup database
sqlite> ATTACH 'backups/healthcare_ai_backup_20231115_140000.db' AS backup;

# Copy specific data
sqlite> INSERT INTO predictions SELECT * FROM backup.predictions WHERE created_at > '2023-11-15';

# Detach and close
sqlite> DETACH backup;
sqlite> .quit
```

## Security Considerations

1. **Encryption**: Backups inherit permissions from source database
2. **Access Control**: Restrict backup directory permissions
3. **Compliance**: Ensure backup retention meets regulatory requirements
4. **Offsite Storage**: Consider encrypted cloud storage for critical data

## Examples

### Development Environment

```bash
# Quick backup before major changes
python scripts/backup_database.py

# Backup before database migration
python scripts/backup_database.py --backup-dir ./migration_backups
```

### Production Environment

```bash
# Production backup with 90-day retention
python scripts/backup_database.py --keep-days 90 --backup-dir /mnt/backups

# Offsite backup to network storage
python scripts/backup_database.py --backup-dir /mnt/nfs/healthapi_backups
```

### CI/CD Pipeline

```yaml
# .github/workflows/backup.yml
name: Daily Backup
on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM daily

jobs:
  backup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - name: Create Backup
        run: python scripts/backup_database.py --keep-days 30
      - name: Upload to S3
        run: aws s3 sync backups/ s3://my-bucket/healthapi-backups/
```

## Support

For issues or questions:
- Create an issue: [GitHub Issues](https://github.com/OpenHealthLab/HealthAPI/issues)
- Check logs: Look for error messages in console output
- Verify permissions: Ensure read/write access to database and backup directory

---

**Last Updated**: November 2025
**Maintainer**: Healthcare AI Backend Contributors
