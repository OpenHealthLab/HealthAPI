
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
import os
import uuid
from typing import List
import json
import time

from app.core.database import get_db
from app.core.config import get_settings
from app.schemas.prediction import PredictionResponse, PredictionCreate, BatchPredictionResponse
from app.services.prediction_service import PredictionService
from app.ml.inference import ModelInference
from app.ml.preprocessing.image_processor import ImageProcessor

router = APIRouter()
settings = get_settings()
model_inference = ModelInference()
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
            prediction_metadata=json.dumps(all_probs)
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

@router.post("/predict/batch", response_model=BatchPredictionResponse, status_code=status.HTTP_201_CREATED)
async def predict_chest_xray_batch(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload multiple chest X-ray images and get predictions for all
    
    Accepts up to 50 images at once. Returns summary statistics and individual predictions.
    Failed predictions are reported in the errors list without stopping the batch.
    """
    # Validate batch size
    if len(files) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided"
        )
    
    if len(files) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 50 images allowed per batch"
        )
    
    batch_start_time = time.time()
    successful_predictions = []
    failed_predictions = []
    predictions_data = []
    saved_files = []
    
    # Process each file
    for idx, file in enumerate(files):
        file_path = None
        try:
            # Validate file type
            if not file.content_type.startswith("image/"):
                failed_predictions.append({
                    "filename": file.filename,
                    "error": "File must be an image"
                })
                continue
            
            # Generate unique filename
            file_extension = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(settings.upload_dir, unique_filename)
            
            # Save uploaded file
            os.makedirs(settings.upload_dir, exist_ok=True)
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            saved_files.append(file_path)
            
            # Validate image
            if not image_processor.validate_image(file_path):
                failed_predictions.append({
                    "filename": file.filename,
                    "error": "Invalid image format. Please upload PNG or JPEG"
                })
                continue
            
            # Make prediction
            pred_class, confidence, proc_time, all_probs = model_inference.predict(file_path)
            
            # Create prediction data
            prediction_data = PredictionCreate(
                image_filename=unique_filename,
                model_name="chest_xray_v1",
                prediction_class=pred_class,
                confidence_score=confidence,
                processing_time=proc_time,
                prediction_metadata=json.dumps(all_probs)
            )
            
            predictions_data.append(prediction_data)
            
        except Exception as e:
            failed_predictions.append({
                "filename": file.filename,
                "error": str(e)
            })
            # Clean up file on error
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                if file_path in saved_files:
                    saved_files.remove(file_path)
    
    # Save all successful predictions to database in batch
    if predictions_data:
        try:
            db_predictions = PredictionService.create_predictions_batch(db, predictions_data)
            successful_predictions = db_predictions
        except Exception as e:
            # Clean up all saved files on database error
            for file_path in saved_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
    
    total_processing_time = time.time() - batch_start_time
    
    return BatchPredictionResponse(
        total_images=len(files),
        successful=len(successful_predictions),
        failed=len(failed_predictions),
        total_processing_time=total_processing_time,
        predictions=successful_predictions,
        errors=failed_predictions
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

