# DICOM Support and CADe Features

This document describes the newly added DICOM upload support and Computer-Aided Detection (CADe) features in the HealthAPI.

## Table of Contents

- [DICOM Upload Support](#dicom-upload-support)
- [Computer-Aided Detection (CADe)](#computer-aided-detection-cade)
- [API Endpoints](#api-endpoints)
- [Usage Examples](#usage-examples)
- [Database Schema](#database-schema)
- [Implementation Details](#implementation-details)

## DICOM Upload Support

### Overview

The API now supports DICOM (Digital Imaging and Communications in Medicine) files, the standard format for medical imaging. DICOM files can be uploaded alongside traditional image formats (PNG, JPEG) for both classification and detection tasks.

### Features

- **DICOM File Processing**: Automatically detects and processes `.dcm` files
- **Pixel Data Extraction**: Converts DICOM pixel arrays to tensor format for model inference
- **Photometric Interpretation**: Handles both MONOCHROME1 and MONOCHROME2 formats
- **HIPAA-Compliant Metadata**: Extracts and stores clinically relevant metadata without PHI (Protected Health Information)

### DICOM Metadata Stored

The following metadata is extracted and stored (no PHI):

- `modality`: Imaging modality (e.g., "CR", "DX")
- `study_instance_uid`: Unique study identifier
- `series_instance_uid`: Unique series identifier
- `study_date`: Date of study
- `photometric_interpretation`: MONOCHROME1 or MONOCHROME2
- `rows`: Image height in pixels
- `columns`: Image width in pixels
- `bits_stored`: Number of bits per pixel
- `window_center`: Window center for display
- `window_width`: Window width for display

### Privacy & Compliance

**HIPAA Best Practices:**
- ✅ **Stored**: Study/Series UIDs, imaging parameters, study date
- ❌ **NOT Stored**: Patient Name, DOB, Patient ID, or other PHI
- All metadata is stored in a JSON field in the database
- Original DICOM files are saved with anonymized UUID filenames

### Supported Endpoints

DICOM files are supported on:
- `POST /api/v1/predict` - Classification with DICOM
- `POST /api/v1/predict/batch` - Batch classification
- `POST /api/v1/cade/detect` - CADe detection with DICOM
- `POST /api/v1/cade/detect/batch` - Batch CADe detection

## Computer-Aided Detection (CADe)

### Overview

CADe provides automated detection of common chest X-ray findings with bounding boxes. Unlike classification (which labels the entire image), CADe localizes specific abnormalities within the image.

### Detectable Findings

The system detects **5 common chest X-ray findings**:

1. **Pulmonary Nodule** - Suspicious masses in lung tissue
2. **Pneumothorax** - Collapsed lung with air in pleural space
3. **Pleural Effusion** - Fluid accumulation in pleural space
4. **Cardiomegaly** - Enlarged heart
5. **Infiltrates/Consolidation** - Lung tissue abnormalities

### Features

- **Bounding Box Detection**: Precise localization of findings
- **Confidence Scores**: Per-finding confidence (0.0 to 1.0)
- **Multiple Findings**: Detects 0-N findings per image
- **Batch Processing**: Process up to 50 images at once
- **Database Persistence**: All detections stored for analysis

### Detection Response Format

Each detection includes:
```json
{
  "id": 1,
  "prediction_id": 123,
  "finding_type": "Pulmonary Nodule",
  "confidence_score": 0.87,
  "bounding_box": {
    "x1": 0.35,
    "y1": 0.42,
    "x2": 0.48,
    "y2": 0.55
  },
  "created_at": "2025-01-15T10:30:00Z"
}
```

**Bounding Box Coordinates:**
- Normalized to 0-1 range (relative to image dimensions)
- `(x1, y1)`: Top-left corner
- `(x2, y2)`: Bottom-right corner
- To get pixel coordinates: multiply by image width/height

### Current Implementation

**Note:** The current implementation uses **mock detections** for demonstration purposes. The detection model returns realistic placeholder results with clinically plausible bounding boxes.

**For Production:**
1. Train a detection model (e.g., RetinaNet, Faster R-CNN, YOLO)
2. Save trained weights to `ml_models/chest_xray_detector.pth`
3. The system will automatically load the trained model
4. Update `use_mock_detections = False` once model is trained

## API Endpoints

### CADe Endpoints

#### 1. Detect Findings (Single Image)

```
POST /api/v1/cade/detect
```

Upload a chest X-ray and detect findings with bounding boxes.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (PNG, JPEG, or DICOM)

**Response:**
```json
{
  "prediction_id": 123,
  "image_filename": "uuid.dcm",
  "model_name": "chest_xray_detector_v1",
  "num_findings": 2,
  "processing_time": 0.234,
  "detections": [
    {
      "id": 1,
      "prediction_id": 123,
      "finding_type": "Cardiomegaly",
      "confidence_score": 0.92,
      "bounding_box": {
        "x1": 0.3, "y1": 0.5,
        "x2": 0.7, "y2": 0.9
      },
      "created_at": "2025-01-15T10:30:00Z"
    },
    {
      "id": 2,
      "prediction_id": 123,
      "finding_type": "Pleural Effusion",
      "confidence_score": 0.78,
      "bounding_box": {
        "x1": 0.6, "y1": 0.6,
        "x2": 0.9, "y2": 0.9
      },
      "created_at": "2025-01-15T10:30:01Z"
    }
  ]
}
```

#### 2. Detect Findings (Batch)

```
POST /api/v1/cade/detect/batch
```

Upload multiple chest X-rays (up to 50) for batch detection.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `files` (array of images)

**Response:**
```json
{
  "total_images": 3,
  "successful": 3,
  "failed": 0,
  "total_processing_time": 0.678,
  "results": [
    {
      "prediction_id": 123,
      "image_filename": "uuid1.png",
      "model_name": "chest_xray_detector_v1",
      "num_findings": 1,
      "processing_time": 0.234,
      "detections": [...]
    },
    ...
  ],
  "errors": []
}
```

#### 3. Get Detections by Prediction

```
GET /api/v1/cade/detections/{prediction_id}
```

Retrieve all detections for a specific prediction.

**Response:**
```json
[
  {
    "id": 1,
    "prediction_id": 123,
    "finding_type": "Pulmonary Nodule",
    "confidence_score": 0.87,
    "bounding_box": {...},
    "created_at": "2025-01-15T10:30:00Z"
  }
]
```

#### 4. Get All Detections

```
GET /api/v1/cade/detections?skip=0&limit=100&finding_type=Pneumothorax
```

Retrieve all detections with optional filtering.

**Query Parameters:**
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum records to return (default: 100, max: 500)
- `finding_type`: Filter by finding type (optional)

## Usage Examples

### DICOM Upload Example

**Python:**
```python
import requests

url = "http://localhost:8000/api/v1/predict"
headers = {"X-API-Key": "your-secret-api-key"}
files = {"file": open("chest_xray.dcm", "rb")}

response = requests.post(url, headers=headers, files=files)
result = response.json()

print(f"Prediction: {result['prediction_class']}")
print(f"Confidence: {result['confidence_score']:.2%}")

# Check if DICOM metadata was extracted
if 'dicom_metadata' in result:
    print("DICOM metadata stored (HIPAA-compliant)")
```

**cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/predict" \
  -H "X-API-Key: your-secret-api-key" \
  -F "file=@chest_xray.dcm"
```

### CADe Detection Example

**Python:**
```python
import requests

url = "http://localhost:8000/api/v1/cade/detect"
headers = {"X-API-Key": "your-secret-api-key"}
files = {"file": open("chest_xray.png", "rb")}

response = requests.post(url, headers=headers, files=files)
result = response.json()

print(f"Found {result['num_findings']} findings in {result['processing_time']:.3f}s")

for detection in result['detections']:
    finding = detection['finding_type']
    conf = detection['confidence_score']
    bbox = detection['bounding_box']
    
    print(f"\n{finding} (confidence: {conf:.2%})")
    print(f"  Location: ({bbox['x1']:.2f}, {bbox['y1']:.2f}) to ({bbox['x2']:.2f}, {bbox['y2']:.2f})")
```

**Visualizing Bounding Boxes:**
```python
from PIL import Image, ImageDraw

# Load image
image = Image.open("chest_xray.png")
width, height = image.size

# Draw bounding boxes
draw = ImageDraw.Draw(image)

for detection in result['detections']:
    bbox = detection['bounding_box']
    
    # Convert normalized coords to pixels
    x1 = int(bbox['x1'] * width)
    y1 = int(bbox['y1'] * height)
    x2 = int(bbox['x2'] * width)
    y2 = int(bbox['y2'] * height)
    
    # Draw rectangle
    draw.rectangle([x1, y1, x2, y2], outline="red", width=3)
    
    # Add label
    label = f"{detection['finding_type']}: {detection['confidence_score']:.2%}"
    draw.text((x1, y1-10), label, fill="red")

image.save("output_with_detections.png")
```

## Database Schema

### Updated `predictions` Table

```sql
CREATE TABLE predictions (
    id INTEGER PRIMARY KEY,
    image_filename VARCHAR NOT NULL,
    model_name VARCHAR DEFAULT 'chest_xray_v1',
    prediction_class VARCHAR NOT NULL,
    confidence_score FLOAT NOT NULL,
    processing_time FLOAT,
    prediction_metadata TEXT,
    dicom_metadata TEXT,  -- NEW: HIPAA-compliant DICOM metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### New `detections` Table

```sql
CREATE TABLE detections (
    id INTEGER PRIMARY KEY,
    prediction_id INTEGER NOT NULL,
    finding_type VARCHAR NOT NULL,
    confidence_score FLOAT NOT NULL,
    bbox_x1 FLOAT NOT NULL,  -- Normalized 0-1
    bbox_y1 FLOAT NOT NULL,
    bbox_x2 FLOAT NOT NULL,
    bbox_y2 FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prediction_id) REFERENCES predictions(id)
);
```

## Implementation Details

### File Structure

```
app/
├── ml/
│   ├── models/
│   │   ├── chest_xray_model.py          # Classification model
│   │   └── chest_xray_detector.py       # NEW: Detection model
│   ├── preprocessing/
│   │   └── image_processor.py           # UPDATED: DICOM support
│   ├── inference.py                     # Classification inference
│   └── detection_inference.py           # NEW: Detection inference
├── models/
│   └── database_models.py               # UPDATED: Detection table
├── schemas/
│   ├── prediction.py                    # UPDATED: DICOM metadata
│   └── detection.py                     # NEW: Detection schemas
├── api/routes/
│   ├── predictions.py                   # UPDATED: DICOM support
│   └── cade.py                          # NEW: CADe endpoints
└── services/
    ├── prediction_service.py
    └── detection_service.py             # NEW: Detection service
```

### Key Classes

**ChestXRayDetector** (`app/ml/models/chest_xray_detector.py`):
- PyTorch-based detection model
- Detects 5 finding types
- Returns bounding boxes with confidence scores
- Currently uses mock detections

**DetectionInference** (`app/ml/detection_inference.py`):
- Handles model loading and inference
- Processes images (including DICOM)
- Returns detections with processing time

**ImageProcessor** (`app/ml/preprocessing/image_processor.py`):
- Extended with DICOM support
- Handles photometric interpretation
- Extracts HIPAA-compliant metadata
- Supports both standard images and DICOM

### Configuration

No configuration changes needed. The system automatically:
- Detects DICOM files by extension (`.dcm`)
- Loads detection model if available (`ml_models/chest_xray_detector.pth`)
- Falls back to mock detections for demonstration

### Performance

**DICOM Processing:**
- Adds ~10-50ms overhead for DICOM parsing
- Metadata extraction is cached during processing

**CADe Detection:**
- Mock detections: ~5-20ms per image
- Real model: ~100-500ms per image (CPU), ~50-200ms (GPU)
- Batch processing: Efficiently processes multiple images

## Testing

### Manual Testing

1. **Test DICOM Upload:**
```bash
curl -X POST "http://localhost:8000/api/v1/predict" \
  -H "X-API-Key: your-secret-api-key" \
  -F "file=@sample.dcm"
```

2. **Test CADe Detection:**
```bash
curl -X POST "http://localhost:8000/api/v1/cade/detect" \
  -H "X-API-Key: your-secret-api-key" \
  -F "file=@chest_xray.png"
```

3. **View API Documentation:**
```
http://localhost:8000/docs
```

### Automated Tests

Add tests to `tests/test_api.py`:

```python
def test_dicom_upload():
    """Test DICOM file upload"""
    # Test implementation

def test_cade_detection():
    """Test CADe detection endpoint"""
    # Test implementation

def test_batch_detection():
    """Test batch CADe detection"""
    # Test implementation
```

## Troubleshooting

### DICOM Files Not Processing

**Error:** "Invalid image format"

**Solution:**
- Ensure file has `.dcm` extension
- Verify DICOM file has PixelData attribute
- Check pydicom is installed: `pip install pydicom`

### Detection Model Not Loading

**Warning:** "Using mock detections for demonstration purposes"

**Solution:**
- This is normal for demonstration
- Train and save a detection model to enable real detections
- Model path: `ml_models/chest_xray_detector.pth`

### Bounding Box Coordinates

**Issue:** Boxes appear in wrong location

**Solution:**
- Coordinates are normalized (0-1 range)
- Multiply by image dimensions to get pixels:
  ```python
  pixel_x = bbox_x * image_width
  pixel_y = bbox_y * image_height
  ```

## Next Steps

1. **Train Detection Model:**
   - Collect chest X-ray dataset with bounding box annotations
   - Train detection model (RetinaNet, Faster R-CNN, or YOLO)
   - Save weights to `ml_models/chest_xray_detector.pth`

2. **Model Evaluation:**
   - Evaluate detection performance (mAP, IoU)
   - Tune confidence threshold
   - Optimize inference speed

3. **Production Deployment:**
   - Configure CORS for specific domains
   - Set up rate limiting
   - Enable logging and monitoring
   - Implement model versioning

## References

- **DICOM Standard:** https://www.dicomstandard.org/
- **HIPAA Compliance:** https://www.hhs.gov/hipaa/
- **PyTorch Object Detection:** https://pytorch.org/vision/stable/models.html#object-detection
- **CADe in Medical Imaging:** Various research papers on chest X-ray detection

---

**For support or questions, please open an issue on GitHub.**
