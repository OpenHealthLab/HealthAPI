# Logging Documentation

## Overview

The HealthAPI application uses a centralized logging system that provides comprehensive logging across all components including API routes, services, and ML inference modules.

## Features

- **Centralized Configuration**: Single point of configuration for all logging
- **Multiple Output Targets**: Console and file logging with rotation
- **Structured Logging**: Consistent format across all modules
- **Log Levels**: Configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **Rotating Files**: Automatic log file rotation to manage disk space
- **Performance Tracking**: Detailed timing information for API calls and ML inference

## Configuration

### Environment Variables

Configure logging through environment variables in your `.env` file:

```env
# Logging Configuration
LOG_LEVEL=INFO           # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=app.log         # Optional: Log file name (omit for console-only logging)
```

### Log Levels

- **DEBUG**: Detailed diagnostic information, useful for development
- **INFO**: General informational messages about application operation
- **WARNING**: Warning messages for potentially problematic situations
- **ERROR**: Error messages for failures that don't stop the application
- **CRITICAL**: Critical errors that may cause application failure

### File Logging

When `LOG_FILE` is specified:
- Logs are written to `logs/{LOG_FILE}`
- Files automatically rotate at 10MB
- 5 backup files are retained
- Logs include detailed context (module, function, line number)

### Console Logging

Console output uses a simplified format:
```
2025-01-17 18:30:45 - INFO - Server ready at http://0.0.0.0:8000
```

## Logging by Component

### Application Startup (main.py)

Logs application lifecycle events:
```python
logger.info("🏥 Starting Healthcare AI Backend...")
logger.info("✓ Database tables created successfully")
logger.info("✓ Classification model loaded successfully")
logger.warning("Could not load detection model: [error]")
```

### API Routes

#### Predictions Endpoint
- Request received with filename
- File validation and saving
- Image processing steps
- Model inference timing
- Database operations
- Error handling with cleanup

Example log flow:
```
INFO - Received prediction request for file: xray.png
DEBUG - Generated unique filename: abc123.png
INFO - File saved successfully to: ./uploads/abc123.png
INFO - Processing image for prediction: abc123.png
INFO - Running model inference for: abc123.png
INFO - Prediction completed - Class: Normal, Confidence: 0.9234, Time: 0.145s
INFO - Prediction record saved to database with ID: 42
```

#### CADe Detection Endpoint
- Detection request received
- File processing
- Detection inference
- Findings saved to database

Example log flow:
```
INFO - Received CADe detection request for file: chest.dcm
INFO - CADe file saved successfully: ./uploads/def456.dcm
DEBUG - Extracted DICOM metadata for CADe: def456.dcm
INFO - Running detection inference for: def456.dcm
INFO - CADe detection completed - Found 2 findings in 0.234s
INFO - Successfully saved 2 detections to database
```

### ML Inference

#### Classification (inference.py)
- Model loading and initialization
- Device selection (CPU/CUDA)
- Image preprocessing
- Inference execution
- Result extraction

Example log flow:
```
INFO - Initializing ModelInference on device: cpu
INFO - Loading classification model...
INFO - ✓ Model loaded successfully from ./ml_models/chest_xray_model.pth
DEBUG - Starting inference for image: ./uploads/abc123.png
DEBUG - Preprocessing image...
DEBUG - Running model inference...
DEBUG - Inference completed: Normal (0.9234) in 0.145s
```

#### Detection (detection_inference.py)
- Detection model loading
- Mock vs real detection mode
- Batch detection processing

Example log flow:
```
INFO - Initializing DetectionInference on device: cuda
INFO - Loading detection model...
WARNING - Detection model not found at ./ml_models/chest_xray_detector.pth
WARNING - Using mock detections for demonstration purposes
DEBUG - Starting detection for image: ./uploads/def456.dcm
DEBUG - Running detection inference (mock=True)...
DEBUG - Detection completed: Found 2 findings in 0.234s
```

### Batch Operations

Batch endpoints log progress for each file:
```
INFO - Received batch prediction request with 5 files
INFO - Starting batch processing...
DEBUG - Processing file 1/5: image1.png
DEBUG - Processing file 2/5: image2.png
...
INFO - Batch processing completed - Total: 5, Successful: 4, Failed: 1, Time: 2.45s
```

## Using Logging in Code

### Import Logger

```python
from app.core.logging_config import get_logger

logger = get_logger(__name__)
```

### Log Messages

```python
# Informational messages
logger.info("Processing started")
logger.info(f"Processing image: {filename}")

# Debug details (only shown when LOG_LEVEL=DEBUG)
logger.debug(f"Image tensor shape: {tensor.shape}")
logger.debug("Preprocessing completed")

# Warnings
logger.warning("Model file not found, using fallback")
logger.warning(f"Invalid file type: {content_type}")

# Errors with stack traces
try:
    # ... code ...
except Exception as e:
    logger.error(f"Failed to process: {str(e)}", exc_info=True)
```

### Structured Logging

For consistent logging, follow these patterns:

**API Requests:**
```python
logger.info(f"Received {endpoint} request for file: {filename}")
```

**File Operations:**
```python
logger.info(f"File saved successfully to: {path}")
logger.debug(f"Generated unique filename: {unique_name}")
```

**Processing Steps:**
```python
logger.info(f"Processing image for {operation}: {filename}")
logger.debug(f"Preprocessing image...")
```

**Timing Information:**
```python
logger.info(f"Operation completed in {time:.3f}s")
```

**Database Operations:**
```python
logger.info(f"Record saved to database with ID: {record.id}")
logger.info(f"Retrieved {len(results)} records from database")
```

## Log File Location

- **Directory**: `logs/` (created automatically)
- **Current Log**: `logs/{LOG_FILE}` (e.g., `logs/app.log`)
- **Rotated Logs**: `logs/{LOG_FILE}.1`, `logs/{LOG_FILE}.2`, etc.

## Monitoring and Debugging

### Production Monitoring

For production deployments, monitor these log patterns:

**Critical Issues:**
```bash
grep "ERROR\|CRITICAL" logs/app.log
```

**Model Loading:**
```bash
grep "Model loaded\|Model failed" logs/app.log
```

**Performance:**
```bash
grep "completed" logs/app.log | grep -o "Time: [0-9.]*s"
```

### Development Debugging

Enable DEBUG logging for detailed diagnostics:

```env
LOG_LEVEL=DEBUG
```

This provides:
- Detailed function entry/exit
- Variable values
- Processing steps
- Timing breakdown

### Common Log Patterns

**Successful Prediction:**
```
INFO - Received prediction request for file: xray.png
INFO - File saved successfully
INFO - Prediction completed - Class: Normal, Confidence: 0.9234, Time: 0.145s
INFO - Prediction record saved to database with ID: 42
```

**Failed Prediction:**
```
INFO - Received prediction request for file: invalid.txt
WARNING - Invalid file type received: text/plain
ERROR - Prediction error for abc123.txt: Invalid format
```

**Model Not Found:**
```
INFO - Loading classification model...
WARNING - Model file not found at ./ml_models/chest_xray_model.pth
WARNING - Using untrained model for demonstration purposes
```

## Best Practices

1. **Use Appropriate Log Levels**
   - DEBUG: Development/diagnostic information
   - INFO: Normal operation events
   - WARNING: Recoverable issues
   - ERROR: Failures requiring attention

2. **Include Context**
   - Always include relevant identifiers (filename, ID, etc.)
   - Use f-strings for clear, readable messages

3. **Log Exceptions Properly**
   ```python
   logger.error(f"Error message", exc_info=True)  # Includes stack trace
   ```

4. **Avoid Sensitive Data**
   - Don't log passwords, API keys, or PHI
   - Log identifiers instead of full data

5. **Performance Considerations**
   - Use DEBUG level for verbose logging
   - Avoid excessive logging in tight loops
   - Log timing for performance-critical operations

## Troubleshooting

### Logs Not Appearing

1. Check `LOG_LEVEL` in `.env`
2. Verify log file permissions
3. Ensure `logs/` directory is writable

### Log File Too Large

- Log rotation is automatic at 10MB
- Adjust `max_bytes` in `logging_config.py` if needed
- Increase/decrease `backup_count` for more/fewer backups

### Cannot Find Logs

Default locations:
- Console: stdout (visible in terminal)
- File: `logs/{LOG_FILE}` (only if LOG_FILE is set)

## Integration with Monitoring Tools

The logging system integrates with:

- **ELK Stack**: Structured logs can be parsed by Logstash
- **CloudWatch**: Direct integration for AWS deployments
- **Application Insights**: For Azure deployments
- **Custom Tools**: Standard Python logging format

## Examples

### Enable File Logging

```env
LOG_LEVEL=INFO
LOG_FILE=app.log
```

Results in logs at: `logs/app.log`

### Debug Mode

```env
LOG_LEVEL=DEBUG
LOG_FILE=debug.log
```

Produces verbose output with detailed diagnostics.

### Production Mode

```env
LOG_LEVEL=WARNING
LOG_FILE=production.log
```

Logs only warnings and errors, reducing noise.

## Summary

The HealthAPI logging system provides:
- ✅ Comprehensive coverage of all operations
- ✅ Configurable verbosity and output
- ✅ Automatic log rotation
- ✅ Performance tracking
- ✅ Error diagnostics with stack traces
- ✅ Production-ready monitoring

For questions or issues with logging, refer to the code in `app/core/logging_config.py`.
