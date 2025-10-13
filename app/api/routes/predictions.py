
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
import os
import uuid
from typing import List
import json

from app.core.database import get_db
from app.core.config import get_settings
from app.schemas.prediction import PredictionResponse, PredictionCreate
from app.services.prediction_service import PredictionService
from app.ml.inference import model_inference
from app.ml.preprocessing.image_processor import ImageProcessor

router = APIRouter()
settings = get_settings()
image_processor = ImageProcessor()

@router.post("/predict", response_model=PredictionResponse, status_code=status.HTTP_201_CREATED)
async def predict_chest_xray(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload chest X-ray image and get prediction
    """
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(settings.upload_dir, unique_filename)
    
    # Save uploaded file
    try:
        os.makedirs(settings.upload_dir, exist_ok=True)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving file: {str(e)}"
        )
    
    # Validate image
    if not image_processor.validate_image(file_path):
        os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format. Please upload PNG or JPEG"
        )
    
    # Make prediction
    try:
        pred_class, confidence, proc_time, all_probs = model_inference.predict(file_path)
        
        # Create prediction record
        prediction_data = PredictionCreate(
            image_filename=unique_filename,
            model_name="chest_xray_v1",
            prediction_class=pred_class,
            confidence_score=confidence,
            processing_time=proc_time,
            metadata=json.dumps(all_probs)
        )
        
        db_prediction = PredictionService.create_prediction(db, prediction_data)
        
        return db_prediction
        
    except Exception as e:
        # Clean up file on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction error: {str(e)}"
        )

@router.get("/predictions", response_model=List[PredictionResponse])
async def get_all_predictions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all predictions with pagination"""
    predictions = PredictionService.get_predictions(db, skip=skip, limit=limit)
    return predictions

