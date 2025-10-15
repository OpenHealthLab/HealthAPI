# Development Guide

This guide provides detailed instructions for setting up your local development environment and working with the Healthcare AI Backend codebase.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Development Workflow](#development-workflow)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Database Management](#database-management)
- [Working with ML Models](#working-with-ml-models)
- [Debugging](#debugging)
- [Common Tasks](#common-tasks)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

## Prerequisites

### Required Software

- **Python**: 3.8 or higher
  ```bash
  python --version  # Should be >= 3.8
  ```

- **pip**: Latest version
  ```bash
  pip install --upgrade pip
  ```

- **Git**: For version control
  ```bash
  git --version
  ```

### Recommended Tools

- **VS Code** or **PyCharm**: IDE with Python support
- **Docker**: For containerized development (optional)
- **Postman** or **curl**: For API testing
- **HTTPie**: User-friendly HTTP client (optional)

### System Requirements

- **RAM**: Minimum 4GB (8GB+ recommended for ML model training)
- **Storage**: At least 2GB free space
- **OS**: Linux, macOS, or Windows with WSL2

## Initial Setup

### 1. Fork and Clone Repository

```bash
# Fork the repository on GitHub first, then:
git clone https://github.com/YOUR_USERNAME/HealthAPI.git
cd HealthAPI

# Add upstream remote
git remote add upstream https://github.com/OpenHealthLab/HealthAPI.git

# Verify remotes
git remote -v
```

### 2. Create Virtual Environment

#### Using venv (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Verify activation (should show venv in prompt)
which python  # Should point to venv/bin/python
```

#### Using conda (Alternative)

```bash
conda create -n healthapi python=3.9
conda activate healthapi
```

### 3. Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Verify installation
pip list
```

### 4. Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your configurations
# Required variables:
# - API_KEY: Your API authentication key
# - DATABASE_URL: Database connection string
# - MODEL_PATH: Path to ML model files
```

Example `.env` file:
```env
# API Configuration
API_KEY=your-secret-api-key-here
API_TITLE=Healthcare AI Backend
API_VERSION=1.0.0
DEBUG=True

# Database Configuration
DATABASE_URL=sqlite:///./healthcare_ai.db

# ML Model Configuration
MODEL_PATH=ml_models/chest_xray_model.pth
MODEL_NAME=chest_xray_v1

# File Upload Configuration
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE=10485760  # 10MB
ALLOWED_EXTENSIONS=png,jpg,jpeg

# Server Configuration
HOST=0.0.0.0
PORT=8000
RELOAD=True
```

### 5. Create Required Directories

```bash
mkdir -p uploads ml_models logs
```

### 6. Set Up Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install git hooks
pre-commit install

# Test pre-commit (optional)
pre-commit run --all-files
```

### 7. Initialize Database

```bash
# The database will be created automatically on first run
python run.py

# Or manually initialize
python -c "from app.core.database import init_db; init_db()"
```

### 8. Verify Setup

```bash
# Run tests
pytest

# Start development server
python run.py

# In another terminal, test the API
curl http://localhost:8000/health
```

## Development Workflow

### Daily Workflow

1. **Update your local repository**
   ```bash
   git checkout main
   git pull upstream main
   ```

2. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make changes and test**
   ```bash
   # Make your code changes
   
   # Run tests
   pytest
   
   # Check code quality
   pre-commit run --all-files
   ```

4. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create pull request on GitHub
   ```

### Branch Naming Conventions

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test updates
- `chore/description` - Maintenance tasks

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): brief description

Detailed description (optional)

Fixes #123
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style/formatting
- `refactor`: Code refactoring
- `test`: Testing
- `chore`: Maintenance
- `perf`: Performance improvements

## Running the Application

### Development Server

```bash
# Standard run
python run.py

# With auto-reload (default in .env)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# With custom port
uvicorn app.main:app --reload --port 8080

# With log level
uvicorn app.main:app --reload --log-level debug
```

### Production Server

```bash
# Using Gunicorn with Uvicorn workers
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

### Docker (Optional)

```bash
# Build image
docker build -t healthapi:dev .

# Run container
docker run -p 8000:8000 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/ml_models:/app/ml_models \
  --env-file .env \
  healthapi:dev

# Using Docker Compose
docker-compose up -d
```

### Accessing the Application

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_api.py

# Run specific test
pytest tests/test_api.py::test_health_endpoint

# Run tests matching pattern
pytest -k "test_predict"

# Run with coverage
pytest --cov=app --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Writing Tests

#### Test Structure

```python
# tests/test_example.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)

def test_example_endpoint(client):
    """Test example endpoint returns correct response."""
    # Arrange
    expected_status = 200
    
    # Act
    response = client.get("/api/v1/example")
    
    # Assert
    assert response.status_code == expected_status
    assert "data" in response.json()
```

#### Test Fixtures

```python
# tests/conftest.py
import pytest
from PIL import Image
import io

@pytest.fixture
def test_image():
    """Create test image."""
    image = Image.new('RGB', (224, 224), color='white')
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

@pytest.fixture
def test_api_key():
    """Return test API key."""
    return "test-api-key-12345"
```

### Test Coverage Goals

- **Overall**: >80%
- **Critical Paths**: 100%
- **API Endpoints**: 100%
- **ML Inference**: >90%

## Code Quality

### Linting and Formatting

```bash
# Format code with Black
black app/ tests/

# Sort imports with isort
isort app/ tests/

# Lint with Flake8
flake8 app/ tests/

# Type check with mypy
mypy app/

# Run all checks
pre-commit run --all-files
```

### Configuration Files

#### `.flake8`
```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,venv,env
```

#### `pyproject.toml` (Black & isort)
```toml
[tool.black]
line-length = 88
target-version = ['py38']

[tool.isort]
profile = "black"
line_length = 88
```

### Pre-commit Configuration

The `.pre-commit-config.yaml` runs these checks automatically:
- Code formatting (Black)
- Import sorting (isort)
- Linting (Flake8)
- Type checking (mypy)
- Trailing whitespace removal
- End of file fixes

## Database Management

### Using SQLite (Development)

```bash
# View database
sqlite3 healthcare_ai.db

# List tables
.tables

# View table schema
.schema predictions

# Query data
SELECT * FROM predictions LIMIT 10;

# Exit
.quit
```

### Database Migrations (Future)

When Alembic is added:

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Reset Database

```bash
# Backup first
cp healthcare_ai.db healthcare_ai.db.backup

# Delete database
rm healthcare_ai.db

# Restart app to recreate
python run.py
```

## Working with ML Models

### Model Files

Place trained PyTorch models in the `ml_models/` directory:

```
ml_models/
├── chest_xray_model.pth
├── chest_xray_v2.pth
└── metadata.json
```

### Training Models

See the Jupyter notebook: `scripts/train_model.ipynb`

```bash
# Start Jupyter
jupyter notebook scripts/train_model.ipynb

# Or use JupyterLab
jupyter lab
```

### Testing Inference

```python
# Test model loading
from app.ml.models.chest_xray_model import ChestXrayModel

model = ChestXrayModel()
model.load_model("ml_models/chest_xray_model.pth")

# Test prediction
from PIL import Image
image = Image.open("test_xray.png")
prediction = model.predict(image)
print(prediction)
```

## Debugging

### Python Debugger (pdb)

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use built-in breakpoint()
breakpoint()
```

### VS Code Debugging

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload"
      ],
      "jinja": true,
      "justMyCode": false
    }
  ]
}
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# In your code
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

View logs:
```bash
tail -f logs/app.log
```

## Common Tasks

### Adding a New API Endpoint

1. **Create route file** (if needed): `app/api/routes/new_feature.py`
2. **Define endpoint**:
   ```python
   from fastapi import APIRouter, Depends
   
   router = APIRouter()
   
   @router.get("/new-endpoint")
   async def new_endpoint():
       return {"message": "Hello"}
   ```
3. **Register router**: Add to `app/main.py`
4. **Add tests**: Create `tests/test_new_feature.py`
5. **Update documentation**: Update README if needed

### Adding Dependencies

```bash
# Install package
pip install package-name

# Add to requirements.txt
pip freeze | grep package-name >> requirements.txt

# Or manually edit requirements.txt
echo "package-name==1.0.0" >> requirements.txt
```

### Updating Dependencies

```bash
# Show outdated packages
pip list --outdated

# Update specific package
pip install --upgrade package-name

# Update all packages (careful!)
pip install --upgrade -r requirements.txt
```

## Troubleshooting

### Common Issues

#### Port Already in Use

```bash
# Find process using port 8000
lsof -ti:8000

# Kill process
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn app.main:app --port 8080
```

#### Module Import Errors

```bash
# Ensure virtual environment is activated
which python  # Should show venv path

# Reinstall dependencies
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

#### Database Locked

```bash
# Close all connections to database
# Restart application
# If persists, check for zombie processes
ps aux | grep python
```

#### Model Loading Errors

```bash
# Check model file exists
ls -lh ml_models/

# Check MODEL_PATH in .env
cat .env | grep MODEL_PATH

# Verify model file integrity
python -c "import torch; torch.load('ml_models/chest_xray_model.pth')"
```

#### Permission Errors

```bash
# Fix upload directory permissions
chmod 755 uploads/

# Fix model directory permissions
chmod 755 ml_models/
```

### Getting Help

1. **Check documentation**: README, CONTRIBUTING, this guide
2. **Search issues**: Look for similar problems
3. **Ask in discussions**: GitHub Discussions
4. **Create issue**: Provide detailed information

## FAQ

### How do I add a new ML model?

1. Train your model using PyTorch
2. Save model to `ml_models/`
3. Create model class in `app/ml/models/`
4. Register model in `app/ml/inference.py`
5. Update environment configuration
6. Add tests for new model

### How do I run tests for a specific feature?

```bash
pytest tests/test_feature.py -v
```

### How do I check test coverage?

```bash
pytest --cov=app --cov-report=term-missing
```

### How do I format my code before committing?

```bash
pre-commit run --all-files
```

Or install pre-commit hooks to run automatically:
```bash
pre-commit install
```

### How do I update my fork with upstream changes?

```bash
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

### How do I run the app in production mode?

```bash
export DEBUG=False
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

### How do I contribute without being assigned to an issue?

Comment on the issue expressing interest. For small fixes or documentation, you can submit a PR directly.

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PyTorch Documentation](https://pytorch.org/docs/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---

**Need more help?** Open an issue or ask in [GitHub Discussions](https://github.com/OpenHealthLab/HealthAPI/discussions).
