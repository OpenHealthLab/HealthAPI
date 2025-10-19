# Test Suite Documentation

This directory contains the organized test suite for the HealthAPI application.

## Test Structure

The test suite has been reorganized into focused, modular files for better maintainability:

### V1 API Tests

1. **test_health.py** - Health check and root endpoint tests (2 tests)
2. **test_predictions.py** - Single prediction endpoint tests (9 tests)
3. **test_predictions_batch.py** - Batch prediction tests (7 tests)
4. **test_cade_detection.py** - CADe detection tests for single and batch (7 tests)
5. **test_cade_retrieval.py** - CADe retrieval, filtering, and pagination (6 tests)
6. **test_integration.py** - End-to-end workflows and concurrent operations (3 tests)
7. **test_error_handling.py** - Error scenarios and edge cases (5 tests)
8. **test_validation.py** - Response schema and data validation (2 tests)

### V2 API Tests

9. **test_v2_auth.py** - Authentication, registration, login, rate limiting (4 tests)
10. **test_v2_users.py** - User management and protected endpoints (3 tests)
11. **test_v2_roles.py** - Role management and authorization (3 tests)

### Legacy Tests

- **test_api.py** - Original monolithic test file (kept for reference, 37 tests)
- **test_v2_api.py** - Original V2 API tests (kept for reference, 3 tests)

### Shared Configuration

- **conftest.py** - Pytest fixtures and configuration (database setup, rate limiter reset, etc.)

## Running Tests

### Run all tests
```bash
pytest tests/ -v
```

### Run specific test file
```bash
pytest tests/test_health.py -v
pytest tests/test_predictions.py -v
pytest tests/test_v2_auth.py -v
```

### Run tests by category
```bash
# V1 API tests only
pytest tests/test_health.py tests/test_predictions.py tests/test_predictions_batch.py -v

# V2 API tests only
pytest tests/test_v2_*.py -v

# Integration tests only
pytest tests/test_integration.py -v
```

### Run with coverage
```bash
pytest tests/ --cov=app --cov-report=html
```

### Run specific test function
```bash
pytest tests/test_predictions.py::test_predict_chest_xray_success -v
```

## Test Statistics

- **Total Test Files**: 13 (11 new organized + 2 legacy)
- **Total Tests**: 92
- **Pass Rate**: 96.7% (89 passed, 3 failed)
- **Test Categories**:
  - Health Checks: 2 tests
  - Predictions: 16 tests
  - CADe Detection: 13 tests
  - Integration: 3 tests
  - Error Handling: 5 tests
  - Validation: 2 tests
  - V2 Auth: 4 tests
  - V2 Users: 3 tests
  - V2 Roles: 3 tests
  - Legacy: 40 tests

## Benefits of the New Structure

✅ **Better Organization** - Related tests grouped together
✅ **Faster Test Runs** - Can run specific test files
✅ **Easier Maintenance** - Smaller, focused files
✅ **Better Readability** - Clear test categories
✅ **Parallel Execution** - Can run files in parallel
✅ **Easier to Find** - Logical naming convention

## Test Coverage

### Endpoints Covered

**V1 API:**
- ✅ `GET /` - Root endpoint
- ✅ `GET /health` - Health check
- ✅ `POST /api/v1/predict` - Single prediction
- ✅ `POST /api/v1/predict/batch` - Batch prediction
- ✅ `GET /api/v1/predictions` - List predictions
- ✅ `POST /api/v1/cade/detect` - Single CADe detection
- ✅ `POST /api/v1/cade/detect/batch` - Batch CADe detection
- ✅ `GET /api/v1/cade/detections/{prediction_id}` - Get detections for prediction
- ✅ `GET /api/v1/cade/detections` - List all detections

**V2 API:**
- ✅ `POST /api/v2/auth/register` - User registration
- ✅ `POST /api/v2/auth/login` - User login
- ✅ `GET /api/v2/users/me` - Get current user
- ✅ `POST /api/v2/roles/` - Create role
- ✅ `GET /api/v2/roles/` - List roles
- ✅ `GET /api/v2/roles/{id}` - Get role details

## Dependencies

```bash
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-anyio>=0.21.0
httpx>=0.24.0
Pillow>=10.0.0
```

## Notes

- Tests use SQLite in-memory database for speed and isolation
- Each test has a clean database state
- Test images are generated in-memory using PIL
- Rate limiter is reset between tests
- All tests are independent and can run in any order

## Future Enhancements

Potential areas for additional test coverage:
- Audit logging tests
- Security tests (SQL injection, XSS)
- Performance/load tests
- Model inference mocking
- DICOM file format tests
- Extended V2 API coverage
