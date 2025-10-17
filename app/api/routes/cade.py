"""
CADe (Computer-Aided Detection) API routes.

This module handles API endpoints for chest X-ray finding detection,
including single and batch detection operations.
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import os
import uuid
from typing import List
import time

from app.core.database import get_db
from app.core.config import get_settings
from app.schemas.detection import (
    CADeResponse, 
    BatchCADeResponse, 
    DetectionCreate,
    DetectionResult
)
from app.schemas.prediction import PredictionCreate
from app.services.detection_service import DetectionService
from app.services.prediction_service import PredictionService
from app.ml.detection_inference import DetectionInference
from app.ml.preprocessing.image_processor import ImageProcessor
import json

router = APIRouter()
settings = get_settings()
detection_inference = DetectionInference()
image_processor = ImageProcessor()


@router.post("/detect", response_model=CADeResponse, status_code=status.HTTP_201_CREATED)
async def detect_findings(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload chest X-ray image and detect findings with bounding boxes.
    
    Supports standard image formats (PNG, JPEG) and DICOM files (.dcm).
    Returns all detected findings with bounding boxes and confidence scores.
    
    Detectable findings:
    - Pulmonary Nodule
    - Pneumothorax
    - Pleural Effusion
    - Cardiomegaly
    - Infiltrates/Consolidation
    """
    # Validate file type (support both images and DICOM)
    is_dicom = file.filename.lower().endswith('.dcm') if file.filename else False
    if not is_dicom and not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image (PNG/JPEG) or DICOM (.dcm) file"
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
            detail="Invalid image format. Please upload PNG, JPEG, or DICOM file"
        )
    
    # Run detection
    try:
        # Extract DICOM metadata if applicable
        image_tensor, dicom_metadata = image_processor.process_image_with_metadata(file_path)
        
        # Create prediction record first (for tracking)
        prediction_data = PredictionCreate(
            image_filename=unique_filename,
            model_name="chest_xray_detector_v1",
            prediction_class="Detection",  # Placeholder for CADe
            confidence_score=1.0,  # Not applicable for detection
            processing_time=0.0,  # Will update after detection
            prediction_metadata=None,
            dicom_metadata=json.dumps(dicom_metadata) if dicom_metadata else None
        )
        
        db_prediction = PredictionService.create_prediction(db, prediction_data)
        
        # Run detection inference
        detections, processing_time = detection_inference.detect(file_path)
        
        # Update prediction processing time
        db_prediction.processing_time = processing_time
        db.commit()
        
        # Store detections in database
        detection_results = []
        if detections:
            detections_data = []
            for det in detections:
                detection_create = DetectionCreate(
                    prediction_id=db_prediction.id,
                    finding_type=det['finding_type'],
                    confidence_score=det['confidence'],
                    bbox_x1=det['bbox'][0],
                    bbox_y1=det['bbox'][1],
                    bbox_x2=det['bbox'][2],
                    bbox_y2=det['bbox'][3]
                )
                detections_data.append(detection_create)
            
            # Save all detections
            db_detections = DetectionService.create_detections_batch(db, detections_data)
            
            # Convert to response format
            detection_results = [
                DetectionResult.from_db_model(db_det) 
                for db_det in db_detections
            ]
        
        return CADeResponse(
            prediction_id=db_prediction.id,
            image_filename=unique_filename,
            model_name="chest_xray_detector_v1",
            num_findings=len(detection_results),
            processing_time=processing_time,
            detections=detection_results
        )
        
    except Exception as e:
        # Clean up file on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Detection error: {str(e)}"
        )


@router.post("/detect/batch", response_model=BatchCADeResponse, status_code=status.HTTP_201_CREATED)
async def detect_findings_batch(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload multiple chest X-ray images and detect findings in all.
    
    Accepts up to 50 images at once. Returns summary statistics and
    individual detection results for each image.
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
    successful_results = []
    failed_detections = []
    saved_files = []
    
    # Process each file
    for idx, file in enumerate(files):
        file_path = None
        try:
            # Validate file type
            is_dicom = file.filename.lower().endswith('.dcm') if file.filename else False
            if not is_dicom and not file.content_type.startswith("image/"):
                failed_detections.append({
                    "filename": file.filename,
                    "error": "File must be an image or DICOM file"
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
                failed_detections.append({
                    "filename": file.filename,
                    "error": "Invalid image format"
                })
                continue
            
            # Extract DICOM metadata if applicable
            image_tensor, dicom_metadata = image_processor.process_image_with_metadata(file_path)
            
            # Create prediction record
            prediction_data = PredictionCreate(
                image_filename=unique_filename,
                model_name="chest_xray_detector_v1",
                prediction_class="Detection",
                confidence_score=1.0,
                processing_time=0.0,
                prediction_metadata=None,
                dicom_metadata=json.dumps(dicom_metadata) if dicom_metadata else None
            )
            
            db_prediction = PredictionService.create_prediction(db, prediction_data)
            
            # Run detection
            detections, processing_time = detection_inference.detect(file_path)
            
            # Update prediction processing time
            db_prediction.processing_time = processing_time
            db.commit()
            
            # Store detections
            detection_results = []
            if detections:
                detections_data = []
                for det in detections:
                    detection_create = DetectionCreate(
                        prediction_id=db_prediction.id,
                        finding_type=det['finding_type'],
                        confidence_score=det['confidence'],
                        bbox_x1=det['bbox'][0],
                        bbox_y1=det['bbox'][1],
                        bbox_x2=det['bbox'][2],
                        bbox_y2=det['bbox'][3]
                    )
                    detections_data.append(detection_create)
                
                db_detections = DetectionService.create_detections_batch(db, detections_data)
                detection_results = [
                    DetectionResult.from_db_model(db_det) 
                    for db_det in db_detections
                ]
            
            # Add to successful results
            successful_results.append(CADeResponse(
                prediction_id=db_prediction.id,
                image_filename=unique_filename,
                model_name="chest_xray_detector_v1",
                num_findings=len(detection_results),
                processing_time=processing_time,
                detections=detection_results
            ))
            
        except Exception as e:
            failed_detections.append({
                "filename": file.filename,
                "error": str(e)
            })
            # Clean up file on error
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                if file_path in saved_files:
                    saved_files.remove(file_path)
    
    total_processing_time = time.time() - batch_start_time
    
    return BatchCADeResponse(
        total_images=len(files),
        successful=len(successful_results),
        failed=len(failed_detections),
        total_processing_time=total_processing_time,
        results=successful_results,
        errors=failed_detections
    )


@router.get("/detections/{prediction_id}", response_model=List[DetectionResult])
async def get_detections_for_prediction(
    prediction_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all detections for a specific prediction.
    
    Returns all findings detected for the given prediction ID.
    """
    detections = DetectionService.get_detections_by_prediction(db, prediction_id)
    
    if not detections:
        # Check if prediction exists
        prediction = PredictionService.get_prediction(db, prediction_id)
        if not prediction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prediction with id {prediction_id} not found"
            )
        # Prediction exists but has no detections
        return []
    
    return [DetectionResult.from_db_model(det) for det in detections]


@router.get("/detections", response_model=List[DetectionResult])
async def get_all_detections(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    finding_type: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get all detections with optional filtering and pagination.
    
    Query parameters:
    - skip: Number of records to skip (default: 0)
    - limit: Maximum records to return (default: 100, max: 500)
    - finding_type: Filter by finding type (optional)
    """
    if finding_type:
        detections = DetectionService.get_detections_by_finding_type(
            db, finding_type, skip=skip, limit=limit
        )
    else:
        detections = DetectionService.get_all_detections(db, skip=skip, limit=limit)
    
    return [DetectionResult.from_db_model(det) for det in detections]
