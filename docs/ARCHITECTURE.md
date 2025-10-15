# Architecture Documentation

This document provides a comprehensive overview of the Healthcare AI Backend architecture, design decisions, and technical implementation details.

## Table of Contents

- [System Overview](#system-overview)
- [Architecture Patterns](#architecture-patterns)
- [Technology Stack](#technology-stack)
- [Component Architecture](#component-architecture)
- [Data Flow](#data-flow)
- [API Design](#api-design)
- [Database Schema](#database-schema)
- [ML Pipeline](#ml-pipeline)
- [Security Architecture](#security-architecture)
- [Performance Characteristics](#performance-characteristics)
- [Design Decisions](#design-decisions)
- [Future Considerations](#future-considerations)

## System Overview

Healthcare AI Backend is a FastAPI-based REST API service that provides machine learning inference capabilities for medical image analysis, specifically chest X-ray classification.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Applications                     │
│              (Web, Mobile, Desktop, API Clients)            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ HTTP/HTTPS
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                     API Gateway Layer                        │
│                    (FastAPI Application)                     │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Health    │  │ Predictions  │  │   Future     │      │
│  │  Endpoints  │  │  Endpoints   │  │  Endpoints   │      │
│  └─────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────┬──────────────────────────────────┘
                           │
            ┌──────────────┴──────────────┐
            │                             │
┌───────────▼──────────┐      ┌──────────▼───────────┐
│   Service Layer      │      │   ML Inference       │
│   (Business Logic)   │      │   Engine             │
│                      │      │                      │
│  - Validation        │      │  - Model Loading     │
│  - Orchestration     │      │  - Preprocessing     │
│  - Error Handling    │      │  - Prediction        │
└───────────┬──────────┘      └──────────┬───────────┘
            │                             │
            │                             │
┌───────────▼──────────┐      ┌──────────▼───────────┐
│   Data Layer         │      │   File Storage       │
│   (SQLite/PostgreSQL)│      │   (Uploads/Models)   │
│                      │      │                      │
│  - Predictions       │      │  - Images            │
│  - Users (future)    │      │  - Model Files       │
└──────────────────────┘      └──────────────────────┘
```

## Architecture Patterns

### 1. Layered Architecture

The application follows a clean, layered architecture:

```
┌─────────────────────────────────────────┐
│          API/Presentation Layer         │  FastAPI routes, request/response
│              (app/api/)                 │  handling, validation
├─────────────────────────────────────────┤
│            Service Layer                │  Business logic, orchestration,
│           (app/services/)               │  error handling
├─────────────────────────────────────────┤
│         Machine Learning Layer          │  Model inference, preprocessing,
│              (app/ml/)                  │  prediction logic
├─────────────────────────────────────────┤
│            Data Layer                   │  Database operations, ORM models,
│      (app/models/, app/core/)          │  persistence
└─────────────────────────────────────────┘
```

**Benefits:**
- Clear separation of concerns
- Easy to test individual layers
- Flexibility to swap implementations
- Maintainable and scalable

### 2. Dependency Injection

FastAPI's dependency injection system is used throughout:

```python
# Example: app/api/deps.py
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Usage in routes
@router.post("/predict")
async def predict(
    file: UploadFile,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    ...
```

**Benefits:**
- Loose coupling between components
- Easy to mock dependencies for testing
- Clean, readable code
- Automatic dependency resolution

### 3. Repository Pattern (Future)

For database operations:

```python
class PredictionRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, prediction: PredictionCreate) -> Prediction:
        ...
    
    def get(self, id: int) -> Optional[Prediction]:
        ...
    
    def list(self, skip: int, limit: int) -> List[Prediction]:
        ...
```

### 4. Factory Pattern

For model creation:

```python
class ModelFactory:
    @staticmethod
    def create_model(model_type: str) -> BaseModel:
        if model_type == "chest_xray":
            return ChestXrayModel()
        elif model_type == "skin_lesion":
            return SkinLesionModel()
        ...
```

## Technology Stack

### Backend Framework

- **FastAPI 0.104+**
  - High performance (built on Starlette and Pydantic)
  - Automatic API documentation (OpenAPI/Swagger)
  - Built-in validation
  - Async support
  - Type hints support

### Machine Learning

- **PyTorch 2.0+**
  - Deep learning framework
  - Dynamic computation graphs
  - GPU support
  - Pre-trained model support
  
- **Pillow (PIL)**
  - Image processing
  - Format conversion
  - Preprocessing

- **NumPy**
  - Numerical operations
  - Array manipulation

### Database

- **SQLAlchemy 2.0+**
  - SQL toolkit and ORM
  - Database agnostic
  - Migration support (with Alembic)
  
- **SQLite (Development)**
  - File-based database
  - No setup required
  - Suitable for development/testing
  
- **PostgreSQL (Production)**
  - Production-grade database
  - Better concurrent access
  - Advanced features

### Data Validation

- **Pydantic 2.0+**
  - Data validation using Python type hints
  - JSON schema generation
  - Settings management
  - Automatic error messages

### Development Tools

- **pytest**: Testing framework
- **black**: Code formatter
- **flake8**: Linting
- **isort**: Import sorting
- **mypy**: Static type checking
- **pre-commit**: Git hooks

## Component Architecture

### API Layer (`app/api/`)

**Responsibilities:**
- Handle HTTP requests/responses
- Route management
- Request validation
- Response formatting
- API documentation

**Structure:**
```
app/api/
├── __init__.py
├── deps.py              # Shared dependencies
└── routes/
    ├── __init__.py
    ├── health.py        # Health check endpoints
    └── predictions.py   # Prediction endpoints
```

**Key Components:**

1. **Dependencies (`deps.py`)**
   - Database session management
   - API key verification
   - Common utilities

2. **Routes**
   - Health checks
   - Single/batch predictions
   - Prediction history

### Service Layer (`app/services/`)

**Responsibilities:**
- Business logic implementation
- Workflow orchestration
- Data transformation
- Error handling

**Structure:**
```
app/services/
├── __init__.py
└── prediction_service.py   # Prediction business logic
```

**Example Service:**
```python
class PredictionService:
    def __init__(self, db: Session):
        self.db = db
        self.inference_engine = InferenceEngine()
    
    async def predict_image(
        self,
        image: UploadFile,
        user_id: Optional[int] = None
    ) -> PredictionResponse:
        # 1. Validate image
        # 2. Save file
        # 3. Run inference
        # 4. Save prediction to DB
        # 5. Return result
```

### ML Layer (`app/ml/`)

**Responsibilities:**
- Model loading and management
- Image preprocessing
- Inference execution
- Result post-processing

**Structure:**
```
app/ml/
├── __init__.py
├── inference.py           # Main inference engine
├── models/
│   ├── __init__.py
│   └── chest_xray_model.py
└── preprocessing/
    ├── __init__.py
    └── image_processor.py
```

**Key Components:**

1. **Inference Engine (`inference.py`)**
   - Model lifecycle management
   - Batch processing
   - Performance optimization

2. **Models (`models/`)**
   - Model architecture definitions
   - Model loading/saving
   - Forward pass implementation

3. **Preprocessing (`preprocessing/`)**
   - Image loading
   - Resizing and normalization
   - Data augmentation (training)

### Data Layer (`app/models/`, `app/core/`)

**Responsibilities:**
- Database models (ORM)
- Database configuration
- Data persistence

**Structure:**
```
app/models/
├── __init__.py
└── database_models.py    # SQLAlchemy models

app/core/
├── __init__.py
├── config.py            # Settings management
└── database.py          # Database setup
```

### Schema Layer (`app/schemas/`)

**Responsibilities:**
- API request/response models
- Data validation
- JSON serialization

**Structure:**
```
app/schemas/
├── __init__.py
└── prediction.py        # Prediction schemas
```

## Data Flow

### Single Prediction Flow

```
1. Client Request
   │
   ▼
2. API Endpoint (/api/v1/predict)
   │ - Validate API key
   │ - Validate request
   ▼
3. Prediction Service
   │ - Save uploaded file
   │ - Validate image format
   ▼
4. ML Inference Engine
   │ - Load model (if not cached)
   │ - Preprocess image
   │ - Run inference
   │ - Post-process results
   ▼
5. Database
   │ - Save prediction record
   ▼
6. Response
   │ - Format response
   │ - Return to client
```

### Batch Prediction Flow

```
1. Client uploads multiple images
   │
   ▼
2. API validates and accepts files
   │
   ▼
3. For each image (parallel processing):
   │ ├─ Preprocess
   │ ├─ Run inference
   │ └─ Save result
   ▼
4. Aggregate results
   │ - Calculate statistics
   │ - Collect errors
   ▼
5. Return batch response
```

## API Design

### RESTful Principles

- **Resource-based URLs**: `/api/v1/predictions`
- **HTTP methods**: GET, POST, PUT, DELETE
- **Status codes**: Appropriate HTTP status codes
- **JSON format**: Consistent request/response format

### Versioning

API versioning through URL path:
```
/api/v1/predict
/api/v2/predict  (future)
```

### Request/Response Format

**Request:**
```json
POST /api/v1/predict
Headers:
  X-API-Key: your-api-key
  Content-Type: multipart/form-data

Body:
  file: <binary_image_data>
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

### Error Handling

Consistent error format:
```json
{
  "detail": "Error message",
  "status_code": 400,
  "timestamp": "2025-01-15T10:30:00Z"
}
```

## Database Schema

### Predictions Table

```sql
CREATE TABLE predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_filename VARCHAR(255) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    prediction_class VARCHAR(50) NOT NULL,
    confidence_score FLOAT NOT NULL,
    processing_time FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_created_at (created_at),
    INDEX idx_prediction_class (prediction_class)
);
```

### Future Tables

**Users:**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**API Keys:**
```sql
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    key_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## ML Pipeline

### Model Architecture

Currently using ResNet-based architecture:

```python
ChestXrayModel (ResNet18/34/50)
├── Convolutional layers
├── Batch normalization
├── Residual blocks
├── Global average pooling
└── Fully connected layer (3 classes)
```

### Training Pipeline (Jupyter Notebook)

```
1. Data Loading
   │ - Load chest X-ray images
   │ - Split train/val/test
   ▼
2. Data Augmentation
   │ - Random rotation
   │ - Random flip
   │ - Color jitter
   ▼
3. Model Training
   │ - Forward pass
   │ - Loss calculation
   │ - Backpropagation
   │ - Optimizer step
   ▼
4. Validation
   │ - Evaluate on validation set
   │ - Track metrics
   ▼
5. Model Saving
   │ - Save best model
   │ - Save training history
```

### Inference Pipeline

```
1. Image Input (PIL Image/bytes)
   │
   ▼
2. Preprocessing
   │ - Resize to 224x224
   │ - Convert to tensor
   │ - Normalize (ImageNet stats)
   ▼
3. Model Inference
   │ - Forward pass
   │ - Softmax activation
   ▼
4. Post-processing
   │ - Get class probabilities
   │ - Select top prediction
   │ - Format output
```

## Security Architecture

### Authentication

**Current: API Key Authentication**
```
X-API-Key: secret-key-here
```

**Future: JWT-based Authentication**
```
Authorization: Bearer <jwt_token>
```

### Input Validation

- File type validation
- File size limits
- Image format verification
- SQL injection prevention (ORM)
- XSS prevention (input sanitization)

### Data Protection

- Secure file storage
- Database encryption (production)
- HTTPS in production
- Sensitive data masking in logs

### Rate Limiting (Future)

```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/predict")
@limiter.limit("100/hour")
async def predict(...):
    ...
```

## Performance Characteristics

### Response Times

- **Health Check**: < 10ms
- **Single Prediction**: 100-500ms (CPU), 50-200ms (GPU)
- **Batch Prediction**: 50-200ms per image

### Throughput

- **Single Instance**: 10-50 requests/second
- **With Load Balancer**: Scales linearly

### Memory Usage

- **Base Application**: ~100-200MB
- **With Model Loaded**: ~500MB-1GB
- **During Inference**: +100-200MB per request

### Optimization Strategies

1. **Model Optimization**
   - Model quantization
   - ONNX conversion
   - TensorRT optimization

2. **Caching**
   - Model caching in memory
   - Response caching (Redis)
   - Static file caching

3. **Async Processing**
   - FastAPI async endpoints
   - Background tasks for batch processing
   - Celery for distributed processing

4. **Database Optimization**
   - Connection pooling
   - Query optimization
   - Proper indexing

## Design Decisions

### Why FastAPI?

**Pros:**
- High performance (comparable to Node.js and Go)
- Automatic API documentation
- Built-in validation
- Modern Python features (async/await, type hints)
- Easy to learn and use

**Cons:**
- Relatively new framework
- Smaller ecosystem than Flask/Django

### Why PyTorch over TensorFlow?

**Pros:**
- More Pythonic API
- Dynamic computation graphs
- Better for research and prototyping
- Strong community support
- Easier debugging

**Cons:**
- Slightly larger model files
- Less production deployment tools

### Why SQLite (Development)?

**Pros:**
- No setup required
- File-based (easy backup)
- Fast for small datasets
- Perfect for development

**Cons:**
- Not suitable for production
- Limited concurrent writes
- No built-in replication

### Why Separate Preprocessing Module?

**Pros:**
- Reusable across models
- Easy to test independently
- Can be updated without touching model code
- Supports different input formats

**Cons:**
- Additional abstraction layer

## Future Considerations

### Scalability

1. **Horizontal Scaling**
   - Load balancer (Nginx/HAProxy)
   - Multiple API instances
   - Shared storage (S3/GCS)

2. **Caching Layer**
   - Redis for session/cache
   - Model result caching
   - CDN for static assets

3. **Message Queue**
   - Celery + Redis/RabbitMQ
   - Async batch processing
   - Job scheduling

### Monitoring

1. **Application Monitoring**
   - Prometheus metrics
   - Grafana dashboards
   - Health check endpoints

2. **Logging**
   - Structured logging (JSON)
   - Centralized logs (ELK Stack)
   - Log rotation

3. **Tracing**
   - OpenTelemetry
   - Distributed tracing
   - Performance profiling

### Infrastructure

1. **Containerization**
   - Docker images
   - Kubernetes deployment
   - Helm charts

2. **CI/CD**
   - GitHub Actions
   - Automated testing
   - Automated deployment

3. **Cloud Deployment**
   - AWS (ECS, Lambda)
   - GCP (Cloud Run, GKE)
   - Azure (Container Instances)

### Features

1. **Multi-Model Support**
   - Model versioning
   - A/B testing
   - Model switching

2. **User Management**
   - Authentication
   - Authorization
   - API key management

3. **Advanced Analytics**
   - Prediction history
   - Usage statistics
   - Model performance metrics

### Security Enhancements

1. **Enhanced Authentication**
   - OAuth2/OIDC
   - MFA support
   - Role-based access control

2. **Data Protection**
   - Data encryption at rest
   - Audit logging
   - GDPR compliance

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PyTorch Documentation](https://pytorch.org/docs/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [The Twelve-Factor App](https://12factor.net/)
- [REST API Best Practices](https://restfulapi.net/)

---

**Questions or suggestions about the architecture?** Open an issue or discussion on GitHub!
