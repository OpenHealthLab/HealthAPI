# Healthcare AI Backend

[![CI/CD](https://github.com/OpenHealthLab/HealthAPI/workflows/CI/badge.svg)](https://github.com/OpenHealthLab/HealthAPI/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

REST API backend for healthcare AI models, starting with chest X-ray image analysis.

> ⚠️ **Medical Disclaimer**: This software is for research and educational purposes only. It is **NOT** intended for clinical use or medical diagnosis without proper validation and regulatory approval.

## 🌟 Quick Links

- [Features](#features)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [Documentation](#documentation)

## Features

- 🏥 Chest X-ray classification (Normal, Pneumonia, COVID-19)
- 🚀 FastAPI with async support
- 🧠 PyTorch deep learning models
- 💾 SQLAlchemy ORM with SQLite database
- 🔒 API key authentication
- 📦 Batch prediction support
- 📁 Organized project structure
- 🌍 Environment-based configuration

## Quick Start

### Prerequisites

- Python 3.8 or higher
- pip and virtualenv
- Git

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/healthcare-ai-backend.git
cd healthcare-ai-backend
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Setup environment variables:**
```bash
cp .env.example .env
# Edit .env with your configurations
```

5. **Create necessary directories:**
```bash
mkdir -p uploads ml_models
```

6. **Run the application:**
```bash
python run.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Health Check
```bash
GET /health
GET /api/v1/health
```

### Predictions

**Single Prediction:**
```bash
POST /api/v1/predict
- Upload chest X-ray image (PNG/JPEG)
- Returns prediction with confidence score
```

**Batch Prediction:**
```bash
POST /api/v1/predict/batch
- Upload multiple chest X-ray images (up to 50)
- Returns summary statistics and individual predictions
```

**Get Predictions:**
```bash
GET /api/v1/predictions
- Get all predictions (paginated)
- Query params: skip, limit
```

## API Documentation

Interactive API documentation available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Usage Examples

### Single Prediction

**Using curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/predict" \
  -H "X-API-Key: your-secret-api-key" \
  -F "file=@chest_xray.png"
```

**Using Python:**
```python
import requests

url = "http://localhost:8000/api/v1/predict"
headers = {"X-API-Key": "your-secret-api-key"}
files = {"file": open("chest_xray.png", "rb")}

response = requests.post(url, headers=headers, files=files)
print(response.json())
```

**Response:**
```json
{
  "id": 1,
  "image_filename": "abc123.png",
  "model_name": "chest_xray_v1",
  "prediction_class": "Normal",
  "confidence_score": 0.95,
  "processing_time": 0.234,
  "created_at": "2025-01-15T10:30:00Z"
}
```

### Batch Prediction

**Using Python:**
```python
import requests

url = "http://localhost:8000/api/v1/predict/batch"
headers = {"X-API-Key": "your-secret-api-key"}
files = [
    ("files", open("xray1.png", "rb")),
    ("files", open("xray2.png", "rb")),
    ("files", open("xray3.png", "rb"))
]

response = requests.post(url, headers=headers, files=files)
print(response.json())
```

**Response:**
```json
{
  "total_images": 3,
  "successful": 3,
  "failed": 0,
  "total_processing_time": 0.456,
  "predictions": [...],
  "errors": []
}
```

## Project Structure

```
healthcare-ai-backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── core/                # Core configurations
│   │   ├── config.py        # Settings management
│   │   └── database.py      # Database setup
│   ├── models/              # Database models
│   │   └── database_models.py
│   ├── schemas/             # Pydantic schemas
│   │   └── prediction.py
│   ├── api/                 # API routes
│   │   ├── deps.py          # Dependencies
│   │   └── routes/
│   │       ├── health.py
│   │       └── predictions.py
│   ├── ml/                  # ML models and inference
│   │   ├── inference.py
│   │   ├── models/
│   │   │   └── chest_xray_model.py
│   │   └── preprocessing/
│   │       └── image_processor.py
│   ├── services/            # Business logic
│   │   └── prediction_service.py
│   └── utils/               # Utility functions
│       └── helpers.py
├── tests/                   # Test files
│   └── test_api.py
├── scripts/                 # Utility scripts
│   └── train_model.ipynb
├── docs/                    # Documentation
│   ├── DEVELOPMENT.md       # Development guide
│   └── ARCHITECTURE.md      # Architecture docs
├── uploads/                 # Uploaded images
├── ml_models/              # Trained PyTorch models
├── .env                    # Environment variables
├── requirements.txt        # Dependencies
├── requirements-dev.txt    # Dev dependencies
└── run.py                 # Application entry point
```

## Development

### Setting Up Development Environment

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed development setup instructions.

Quick start:
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_api.py

# Run with coverage report
pytest --cov=app --cov-report=html
```

## Model Training

To train your own chest X-ray model, see the Jupyter notebook at `scripts/train_model.ipynb`.

### Dataset Structure

Your dataset should be organized as follows:
```
dataset/
├── train/
│   ├── Normal/
│   ├── Pneumonia/
│   └── COVID-19/
└── val/
    ├── Normal/
    ├── Pneumonia/
    └── COVID-19/
```

### Training Steps

1. Prepare your dataset in the above structure
2. Open `scripts/train_model.ipynb` in Jupyter
3. Follow the notebook instructions
4. Save trained model to `ml_models/chest_xray_model.pth`

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:

- Setting up your development environment
- Code style and standards
- Submitting pull requests
- Reporting bugs
- Suggesting features

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

## Documentation

- **[Development Guide](docs/DEVELOPMENT.md)** - Detailed development setup and workflow
- **[Architecture Documentation](docs/ARCHITECTURE.md)** - System architecture and design decisions
- **[API Documentation](http://localhost:8000/docs)** - Interactive API docs (when server is running)
- **[Security Policy](SECURITY.md)** - Security guidelines and reporting vulnerabilities

## Security

For security concerns, please review our [Security Policy](SECURITY.md) and report vulnerabilities responsibly.

**Important**: This is a research and educational project. It is **NOT** intended for clinical use or medical diagnosis without proper validation and regulatory approval.

## Deployment

### Production Considerations

Before deploying to production:

- [ ] Change default API keys
- [ ] Enable HTTPS/TLS
- [ ] Use PostgreSQL instead of SQLite
- [ ] Configure CORS for specific domains
- [ ] Implement rate limiting
- [ ] Set up monitoring and logging
- [ ] Enable automatic backups
- [ ] Review security checklist in SECURITY.md

### Docker Deployment

```bash
# Build image
docker build -t healthcare-ai-backend .

# Run container
docker run -p 8000:8000 \
  -e API_KEY=your-secret-key \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/ml_models:/app/ml_models \
  healthcare-ai-backend
```

### Using Gunicorn (Production)

```bash
pip install gunicorn
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

## Architecture

The application follows a layered architecture pattern:

- **API Layer**: FastAPI routes and request handling
- **Service Layer**: Business logic and orchestration
- **ML Layer**: Model inference and preprocessing
- **Data Layer**: Database operations and persistence

For detailed architecture documentation, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Technology Stack

- **Framework**: FastAPI 0.104+
- **ML Framework**: PyTorch 2.0+
- **Database**: SQLAlchemy with SQLite/PostgreSQL
- **Validation**: Pydantic 2.0+
- **Testing**: pytest
- **Code Quality**: black, flake8, mypy, isort
- **Documentation**: Swagger UI, ReDoc

## Roadmap

### Current Version (1.0.0)
- ✅ Single image prediction
- ✅ Batch image prediction
- ✅ Database persistence
- ✅ API key authentication
- ✅ Comprehensive documentation

### Planned Features
- [ ] User authentication and authorization
- [ ] Model versioning
- [ ] Async batch processing with Celery
- [ ] Redis caching
- [ ] Rate limiting
- [ ] Audit logging
- [ ] Monitoring and metrics (Prometheus)
- [ ] Multi-model support
- [ ] DICOM image support

## Performance

- **Single prediction**: ~100-500ms (CPU), ~50-200ms (GPU)
- **Batch prediction**: ~50-200ms per image
- **Throughput**: ~10-50 requests/second (single instance)

For performance optimization strategies, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#performance-characteristics).

## Troubleshooting

### Common Issues

**Model not loading:**
```bash
# Check if model file exists
ls -la ml_models/chest_xray_model.pth

# Verify MODEL_PATH in .env
cat .env | grep MODEL_PATH
```

**Port already in use:**
```bash
# Change port in .env or kill existing process
lsof -ti:8000 | xargs kill -9
```

**Import errors:**
```bash
# Ensure virtual environment is activated
which python  # Should point to venv/bin/python
```

For more troubleshooting tips, see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md#troubleshooting).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use this project in your research, please cite:

```bibtex
@software{healthcare_ai_backend,
  title = {Healthcare AI Backend},
  author = {Your Name},
  year = {2025},
  url = {https://github.com/yourusername/healthcare-ai-backend}
}
```

## Acknowledgments

- ResNet architecture from [Deep Residual Learning for Image Recognition](https://arxiv.org/abs/1512.03385)
- FastAPI framework by Sebastián Ramírez
- PyTorch team for the deep learning framework

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/healthcare-ai-backend/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/healthcare-ai-backend/discussions)
- **Documentation**: [Project Wiki](https://github.com/yourusername/healthcare-ai-backend/wiki)

## Contributors

Thanks to all contributors who have helped improve this project!

<!-- Add contributor list here -->

---

**Disclaimer**: This software is for research and educational purposes only. It is not intended for clinical use or medical diagnosis. Always consult with qualified healthcare professionals for medical advice.

**Made with ❤️ by the Healthcare AI Community**
