
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
import os
import uuid
from typing import List
import json
import time

from app.core.database import get_db
from app.core.config import get_settings
from app.core.logging_config import get_logger
from app.schemas.prediction import PredictionResponse, PredictionCreate, BatchPredictionResponse
from app.services.prediction_service import PredictionService
from app.ml.inference import ModelInference
from app.ml.preprocessing.image_processor import ImageProcessor

router = APIRouter()
settings = get_settings()
logger = get_logger(__name__)
model_inference = ModelInference()
image_processor = ImageProcessor()

@router.post("/predict", response_model=PredictionResponse, status_code=status.HTTP_201_CREATED)
async def predict_chest_xray(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload chest X-ray image and get prediction.
    
    Supports standard image formats (PNG, JPEG) and DICOM files (.dcm).
    DICOM metadata is extracted and stored (HIPAA-compliant, no PHI).
    """
    logger.info(f"Received prediction request for file: {file.filename}")
    
    # Validate file type (support both images and DICOM)
    is_dicom = file.filename.lower().endswith('.dcm') if file.filename else False
    if not is_dicom and not file.content_type.startswith("image/"):
        logger.warning(f"Invalid file type received: {file.content_type} for file {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image (PNG/JPEG) or DICOM (.dcm) file"
        )
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(settings.upload_dir, unique_filename)
    
    logger.debug(f"Generated unique filename: {unique_filename}")
    
    # Save uploaded file
    try:
        os.makedirs(settings.upload_dir, exist_ok=True)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        logger.info(f"File saved successfully to: {file_path}")
    except Exception as e:
        logger.error(f"Error saving file {file.filename}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving file: {str(e)}"
        )
    
    # Validate image
    logger.debug(f"Validating image: {unique_filename}")
    if not image_processor.validate_image(file_path):
        logger.warning(f"Image validation failed for: {unique_filename}")
        os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format. Please upload PNG or JPEG"
        )
    
    # Make prediction and extract DICOM metadata if applicable
    try:
        logger.info(f"Processing image for prediction: {unique_filename}")
        
        # Process image with metadata extraction
        image_tensor, dicom_metadata = image_processor.process_image_with_metadata(file_path)
        if dicom_metadata:
            logger.debug(f"Extracted DICOM metadata for: {unique_filename}")
        
        # Run inference
        logger.info(f"Running model inference for: {unique_filename}")
        pred_class, confidence, proc_time, all_probs = model_inference.predict(file_path)
        
        logger.info(f"Prediction completed - Class: {pred_class}, Confidence: {confidence:.4f}, Time: {proc_time:.3f}s")
        
        # Create prediction record
        prediction_data = PredictionCreate(
            image_filename=unique_filename,
            model_name="chest_xray_v1",
            prediction_class=pred_class,
            confidence_score=confidence,
            processing_time=proc_time,
            prediction_metadata=json.dumps(all_probs),
            dicom_metadata=json.dumps(dicom_metadata) if dicom_metadata else None
        )
        
        db_prediction = PredictionService.create_prediction(db, prediction_data)
        logger.info(f"Prediction record saved to database with ID: {db_prediction.id}")
        
        return db_prediction
        
    except Exception as e:
        logger.error(f"Prediction error for {unique_filename}: {str(e)}", exc_info=True)
        # Clean up file on error
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Cleaned up file after error: {file_path}")
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
    logger.info(f"Received batch prediction request with {len(files)} files")
    
    # Validate batch size
    if len(files) == 0:
        logger.warning("Batch prediction request with no files")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided"
        )
    
    if len(files) > 50:
        logger.warning(f"Batch prediction request exceeds limit: {len(files)} files")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 50 images allowed per batch"
        )
    
    batch_start_time = time.time()
    successful_predictions = []
    failed_predictions = []
    predictions_data = []
    saved_files = []
    
    logger.info("Starting batch processing...")
    
    # Process each file
    for idx, file in enumerate(files):
        logger.debug(f"Processing file {idx + 1}/{len(files)}: {file.filename}")
        file_path = None
        try:
            # Validate file type
            if not file.content_type.startswith("image/"):
                logger.warning(f"Invalid file type in batch: {file.filename} ({file.content_type})")
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
                logger.warning(f"Image validation failed in batch: {file.filename}")
                failed_predictions.append({
                    "filename": file.filename,
                    "error": "Invalid image format. Please upload PNG or JPEG"
                })
                continue
            
            # Make prediction
            pred_class, confidence, proc_time, all_probs = model_inference.predict(file_path)
            logger.debug(f"Batch prediction {idx + 1}: {pred_class} (confidence: {confidence:.4f})")
            
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
            logger.error(f"Error processing file {file.filename} in batch: {str(e)}")
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
            logger.info(f"Saving {len(predictions_data)} predictions to database...")
            db_predictions = PredictionService.create_predictions_batch(db, predictions_data)
            successful_predictions = db_predictions
            logger.info(f"Successfully saved {len(db_predictions)} predictions to database")
        except Exception as e:
            logger.error(f"Database error during batch save: {str(e)}", exc_info=True)
            # Clean up all saved files on database error
            for file_path in saved_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
    
    total_processing_time = time.time() - batch_start_time
    
    logger.info(f"Batch processing completed - Total: {len(files)}, Successful: {len(successful_predictions)}, Failed: {len(failed_predictions)}, Time: {total_processing_time:.2f}s")
    
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
    logger.info(f"Retrieving predictions (skip={skip}, limit={limit})")
    predictions = PredictionService.get_predictions(db, skip=skip, limit=limit)
    logger.info(f"Retrieved {len(predictions)} predictions from database")
    return predictions
