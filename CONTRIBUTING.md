# Contributing to Healthcare AI Backend

Thank you for your interest in contributing to Healthcare AI Backend! We welcome contributions from the community and are grateful for your support.

## 🌟 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Community](#community)

## 📜 Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## 🚀 Getting Started

### Finding Issues to Work On

1. **Good First Issues**: Look for issues labeled [`good first issue`](https://github.com/OpenHealthLab/HealthAPI/labels/good%20first%20issue) - these are great for newcomers
2. **Help Wanted**: Check [`help wanted`](https://github.com/OpenHealthLab/HealthAPI/labels/help%20wanted) label for issues that need community support
3. **Bug Reports**: Look for [`bug`](https://github.com/OpenHealthLab/HealthAPI/labels/bug) labeled issues
4. **Feature Requests**: Explore [`enhancement`](https://github.com/OpenHealthLab/HealthAPI/labels/enhancement) labeled issues

### Before You Start

1. **Search existing issues** to avoid duplicates
2. **Comment on the issue** you'd like to work on to claim it
3. **Wait for assignment** before starting major work
4. **Ask questions** if anything is unclear

## 💻 Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- pip and virtualenv
- (Optional) Docker for containerized development

### Local Setup

1. **Fork and Clone**
```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/HealthAPI.git
cd HealthAPI

# Add upstream remote
git remote add upstream https://github.com/OpenHealthLab/HealthAPI.git
```

2. **Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Dependencies**
```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

4. **Set Up Environment Variables**
```bash
cp .env.example .env
# Edit .env with your configurations
```

5. **Create Necessary Directories**
```bash
mkdir -p uploads ml_models
```

6. **Install Pre-commit Hooks**
```bash
pre-commit install
```

7. **Verify Setup**
```bash
# Run tests
pytest

# Run the application
python run.py
```

Visit `http://localhost:8000/docs` to verify the API is running.

For detailed setup instructions, see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## 🤝 How to Contribute

### Types of Contributions

We welcome various types of contributions:

- **🐛 Bug Fixes**: Fix issues and improve stability
- **✨ New Features**: Add new functionality
- **📚 Documentation**: Improve or add documentation
- **🧪 Tests**: Add or improve test coverage
- **🎨 Code Quality**: Refactoring and code improvements
- **⚡ Performance**: Optimization improvements
- **🌐 Translations**: Help with internationalization

### Contribution Workflow

1. **Create a Branch**
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

Branch naming conventions:
- `feature/description` - for new features
- `fix/description` - for bug fixes
- `docs/description` - for documentation
- `refactor/description` - for code refactoring
- `test/description` - for tests

2. **Make Your Changes**
- Write clean, readable code
- Follow our coding standards (see below)
- Add tests for new functionality
- Update documentation as needed

3. **Commit Your Changes**
```bash
git add .
git commit -m "type: brief description"
```

Commit message format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

Examples:
```
feat: add batch prediction endpoint
fix: resolve image upload validation issue
docs: update API documentation
test: add tests for prediction service
```

4. **Push to Your Fork**
```bash
git push origin feature/your-feature-name
```

5. **Create Pull Request**
- Go to your fork on GitHub
- Click "New Pull Request"
- Fill out the PR template completely
- Link related issues

## 📋 Coding Standards

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with these tools:

#### Code Formatting
- **Black**: Code formatter (line length: 88)
```bash
black app/ tests/
```

#### Code Quality
- **Flake8**: Linting
```bash
flake8 app/ tests/
```

- **isort**: Import sorting
```bash
isort app/ tests/
```

- **mypy**: Type checking
```bash
mypy app/
```

#### Running All Checks
```bash
# Pre-commit will run these automatically
pre-commit run --all-files
```

### Code Style Guidelines

1. **Type Hints**: Always use type hints
```python
def predict_image(image: UploadFile, model: str = "default") -> PredictionResponse:
    pass
```

2. **Docstrings**: Use Google-style docstrings
```python
def process_image(image_path: str) -> np.ndarray:
    """Process image for model inference.
    
    Args:
        image_path: Path to the image file.
        
    Returns:
        Processed image as numpy array.
        
    Raises:
        ValueError: If image format is not supported.
    """
    pass
```

3. **Function Length**: Keep functions focused and concise (<50 lines)

4. **Variable Names**: Use descriptive names
```python
# Good
prediction_confidence = 0.95
user_uploaded_file = request.file

# Bad
pc = 0.95
f = request.file
```

5. **Error Handling**: Always handle exceptions appropriately
```python
try:
    result = process_image(path)
except ValueError as e:
    logger.error(f"Image processing failed: {e}")
    raise HTTPException(status_code=400, detail=str(e))
```

## 🧪 Testing Guidelines

### Writing Tests

1. **Test Coverage**: Aim for >80% coverage
2. **Test Structure**: Use Arrange-Act-Assert pattern
3. **Test Naming**: Use descriptive names

```python
def test_predict_endpoint_returns_valid_response():
    """Test that predict endpoint returns proper response structure."""
    # Arrange
    client = TestClient(app)
    image_file = create_test_image()
    
    # Act
    response = client.post("/api/v1/predict", files={"file": image_file})
    
    # Assert
    assert response.status_code == 200
    assert "prediction_class" in response.json()
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_api.py::test_predict_endpoint_returns_valid_response
```

### Test Organization

- Place tests in `tests/` directory
- Mirror the app structure
- Use fixtures for common setup
- Mock external dependencies

## 📖 Documentation

### Documentation Standards

1. **Code Comments**: Explain "why", not "what"
2. **Docstrings**: Document all public functions and classes
3. **README Updates**: Update if adding features
4. **API Documentation**: FastAPI auto-generates, ensure schemas are documented

### Updating Documentation

- Update `README.md` for user-facing changes
- Update `docs/DEVELOPMENT.md` for development changes
- Update `docs/ARCHITECTURE.md` for architectural changes
- Add docstrings to new functions/classes

## 🔄 Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass locally
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] No merge conflicts with main branch
- [ ] Pre-commit hooks pass

### PR Template Checklist

Fill out the PR template completely:
- Clear description of changes
- Link to related issues
- Test coverage information
- Screenshots (if UI changes)
- Breaking changes noted

### Review Process

1. **Automated Checks**: CI/CD must pass
2. **Code Review**: At least one maintainer approval required
3. **Testing**: Reviewers may test locally
4. **Discussion**: Address feedback and comments
5. **Merge**: Maintainer will merge once approved

### After Merge

- Delete your feature branch
- Update your local repository
```bash
git checkout main
git pull upstream main
```

## 🐛 Issue Guidelines

### Creating Issues

#### Bug Reports
Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md) and include:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Error messages/logs

#### Feature Requests
Use the [feature request template](.github/ISSUE_TEMPLATE/feature_request.md) and include:
- Clear description of feature
- Use case and motivation
- Proposed solution
- Alternative approaches

#### Documentation Issues
Use the [documentation template](.github/ISSUE_TEMPLATE/documentation.md) for:
- Missing documentation
- Unclear instructions
- Outdated information

### Issue Labels

- `bug` - Something isn't working
- `enhancement` - New feature or request
- `documentation` - Documentation improvements
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `question` - Further information requested
- `wontfix` - This will not be worked on
- `duplicate` - This issue already exists

## 💬 Community

### Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Check docs first

### Communication Guidelines

- Be respectful and constructive
- Provide context and details
- Search before asking
- Help others when you can

## 🎯 Development Tips

### Best Practices

1. **Keep PRs Small**: Easier to review and merge
2. **Test Thoroughly**: Both manual and automated testing
3. **Document Changes**: Help others understand your work
4. **Stay Updated**: Regularly sync with upstream
5. **Ask Questions**: Don't hesitate to ask for clarification

### Staying in Sync

```bash
# Fetch upstream changes
git fetch upstream

# Merge upstream main into your branch
git checkout main
git merge upstream/main

# Rebase your feature branch
git checkout feature/your-feature
git rebase main
```

## 📊 Project Structure

Understanding the codebase:

```
app/
├── api/              # API routes and dependencies
├── core/             # Configuration and database
├── ml/               # ML models and inference
├── models/           # Database models
├── schemas/          # Pydantic schemas
├── services/         # Business logic
└── utils/            # Utility functions
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture.

## 🏆 Recognition

Contributors will be recognized in:
- GitHub Contributors page
- CONTRIBUTORS.md file
- Release notes

## 📝 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## ❓ Questions?

- Check the [FAQ](docs/DEVELOPMENT.md#faq)
- Ask in [GitHub Discussions](https://github.com/OpenHealthLab/HealthAPI/discussions)
- Open a [question issue](.github/ISSUE_TEMPLATE/bug_report.md)

---

Thank you for contributing to Healthcare AI Backend! Your efforts help advance open-source healthcare technology. 🏥💻

**Happy Coding! 🚀**
