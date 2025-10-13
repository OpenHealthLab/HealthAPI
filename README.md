
# Healthcare AI Backend

REST API backend for healthcare AI models, starting with chest X-ray image analysis.

## Features

- 🏥 Chest X-ray classification (Normal, Pneumonia, COVID-19)
- 🚀 FastAPI with async support
- 🧠 PyTorch deep learning models
- 💾 SQLAlchemy ORM with SQLite database
- 🔒 API key authentication
- 📁 Organized project structure
- 🌍 Environment-based configuration

## Setup

1. **Clone and navigate to project:**
```bash
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
```bash
POST /api/v1/predict
- Upload chest X-ray image (PNG/JPEG)
- Returns prediction with confidence score

GET /api/v1/predictions
- Get all predictions (paginated)

GET /api/v1/predictions/{id}
- Get specific prediction by ID
```

## API Documentation

Interactive API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
healthcare-ai-backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── core/                # Core configurations
│   ├── models/              # Database models
│   ├── schemas/             # Pydantic schemas
│   ├── api/                 # API routes
│   ├── ml/                  # ML models and inference
│   └── services/            # Business logic
├── uploads/                 # Uploaded images
├── ml_models/              # Trained PyTorch models
├── .env                    # Environment variables
├── requirements.txt        # Dependencies
└── run.py                 # Application entry point
```

## Usage Example

```python
import requests

url = "http://localhost:8000/api/v1/predict"
files = {"file": open("chest_xray.png", "rb")}

response = requests.post(url, files=files)
print(response.json())
```

Response:
```json
{
  "id": 1,
  "image_filename": "abc123.png",
  "model_name": "chest_xray_v1",
  "prediction_class": "Normal",
  "confidence_score": 0.95,
  "processing_time": 0.234,
  "created_at": "2025-10-13T10:30:00Z"
}
```

## Model Training

To train your own chest X-ray model:

1. Prepare dataset in the format:
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

2. Train using PyTorch and save weights to `ml_models/chest_xray_model.pth`

## Adding New Models

1. Create model class in `app/ml/models/`
2. Add preprocessing in `app/ml/preprocessing/`
3. Update inference logic in `app/ml/inference.py`
4. Create new routes in `app/api/routes/`

## Testing

```bash
pytest tests/
```

## Security

- API key authentication for protected endpoints
- File type validation
- Size limits on uploads
- Input sanitization

## License

MIT License

## Contributing

Pull requests welcome! Please ensure tests pass and code follows project structure.

---

**Note:** This is a prototype. For production use:
- Add comprehensive error handling
- Implement proper authentication (JWT)
- Use PostgreSQL instead of SQLite
- Add model versioning
- Implement caching
- Add monitoring and logging
- Deploy with Docker/Kubernetes


