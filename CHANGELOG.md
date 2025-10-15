# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- User authentication and authorization
- Model versioning and management
- Rate limiting
- Redis caching
- Async batch processing with Celery
- PostgreSQL migration for production
- Audit logging
- Prometheus metrics
- DICOM image support
- Multi-model support

## [1.0.0] - 2025-01-15

### Added
- Initial release of Healthcare AI Backend
- Chest X-ray classification API (Normal, Pneumonia, COVID-19)
- FastAPI-based REST API with async support
- PyTorch deep learning models integration
- Single image prediction endpoint
- Batch image prediction endpoint (up to 50 images)
- SQLAlchemy ORM with SQLite database
- API key authentication
- Prediction history retrieval
- Health check endpoints
- Automatic API documentation (Swagger UI & ReDoc)
- Comprehensive test suite with pytest
- Pre-commit hooks for code quality
- Docker support
- Development environment setup
- Project documentation (README, CONTRIBUTING, CODE_OF_CONDUCT)
- Security policy (SECURITY.md)
- CI/CD pipeline with GitHub Actions

### Development
- Black code formatter integration
- Flake8 linting
- isort for import sorting
- mypy for type checking
- pytest with coverage reporting
- Pre-commit hooks configuration

### Documentation
- Comprehensive README with setup instructions
- Contributing guidelines (CONTRIBUTING.md)
- Code of Conduct (CODE_OF_CONDUCT.md)
- Development guide (docs/DEVELOPMENT.md)
- Architecture documentation (docs/ARCHITECTURE.md)
- API usage examples
- Troubleshooting guide

### Infrastructure
- GitHub issue templates (bug report, feature request, documentation)
- Pull request template
- CI/CD workflow for automated testing
- Docker containerization support

## [0.2.0] - 2024-12-20 (Pre-release)

### Added
- Batch prediction support
- Database persistence for predictions
- Environment-based configuration
- File upload validation
- Error handling improvements

### Changed
- Improved code organization
- Enhanced API documentation
- Better error messages

### Fixed
- Image processing edge cases
- Memory leaks in model inference
- Database connection pooling issues

## [0.1.0] - 2024-12-01 (Alpha)

### Added
- Basic FastAPI application structure
- Single prediction endpoint
- PyTorch model integration
- Health check endpoint
- Basic testing setup

---

## Release Notes

### Version 1.0.0

This is the first stable release of Healthcare AI Backend! 🎉

**Highlights:**
- Production-ready REST API for chest X-ray classification
- Support for single and batch predictions
- Comprehensive documentation for contributors
- Automated testing and code quality checks
- Docker support for easy deployment

**Getting Started:**
```bash
git clone https://github.com/OpenHealthLab/HealthAPI.git
cd HealthAPI
pip install -r requirements.txt
python run.py
```

Visit http://localhost:8000/docs for interactive API documentation.

**Breaking Changes:**
- None (first stable release)

**Migration Guide:**
- Not applicable for first release

**Known Issues:**
- SQLite is used for development; consider PostgreSQL for production
- No built-in rate limiting yet
- Single-instance deployment only (no load balancing yet)

**Contributors:**
Thank you to all contributors who made this release possible!

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## Support

- **Issues**: [GitHub Issues](https://github.com/OpenHealthLab/HealthAPI/issues)
- **Discussions**: [GitHub Discussions](https://github.com/OpenHealthLab/HealthAPI/discussions)

---

[Unreleased]: https://github.com/OpenHealthLab/HealthAPI/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/OpenHealthLab/HealthAPI/releases/tag/v1.0.0
[0.2.0]: https://github.com/OpenHealthLab/HealthAPI/releases/tag/v0.2.0
[0.1.0]: https://github.com/OpenHealthLab/HealthAPI/releases/tag/v0.1.0
