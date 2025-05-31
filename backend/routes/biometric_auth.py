# backend/routes/biometric_auth.py
# Presient Biometric Authentication API Routes

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from backend.database import get_db
from ..services.biometric_engine import PresientBiometricEngine, HeartRateSample
from ..models.biometric import BiometricTemplate as DBTemplate, BiometricEnrollmentSession
from backend.core.auth import get_current_user

router = APIRouter(prefix="/api/biometric", tags=["biometric-auth"])
logger = logging.getLogger(__name__)

# Initialize biometric engine (singleton)
biometric_engine = PresientBiometricEngine()

# Pydantic models for API
class HeartRateSampleAPI(BaseModel):
    heart_rate: float = Field(..., ge=30, le=200, description="Heart rate in BPM")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Signal confidence")
    distance: float = Field(..., ge=0, le=1000, description="Distance to sensor in cm")
    timestamp: Optional[datetime] = None

class EnrollmentStartResponse(BaseModel):
    status: str
    user_id: str
    session_id: str
    samples_needed: int
    message: str

class EnrollmentProgressResponse(BaseModel):
    status: str
    samples_collected: int
    samples_needed: int
    progress_percentage: float
    enrollment_ready: bool
    estimated_time_remaining: float
    message: str

class AuthenticationResponse(BaseModel):
    authenticated: bool
    user_id: Optional[str]
    confidence: float
    method: str = "hrv_biometric"
    timestamp: datetime
    biometric_signature: Optional[str] = None

class SmartPresenceResponse(BaseModel):
    authenticated_presence: bool
    user_id: Optional[str]
    confidence: Optional[float]
    presence_detected: bool
    method: str = "hrv_biometric"
    timestamp: datetime


@router.post("/enroll/start/{user_id}", response_model=EnrollmentStartResponse)
async def start_biometric_enrollment(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Start biometric enrollment for a user"""
    
    try:
        # Check if user already has active enrollment
        existing_enrollment = db.query(BiometricEnrollmentSession).filter(
            BiometricEnrollmentSession.user_id == user_id,
            BiometricEnrollmentSession.status.in_(["started", "collecting"])
        ).first()
        
        if existing_enrollment:
            return EnrollmentStartResponse(
                status="enrollment_in_progress",
                user_id=user_id,
                session_id=existing_enrollment.id,
                samples_needed=biometric_engine.min_enrollment_samples,
                message="Enrollment already in progress. Continue collecting samples."
            )
        
        # Check if user already has biometric template
        existing_template = db.query(DBTemplate).filter(
            DBTemplate.user_id == user_id,
            DBTemplate.is_active == True
        ).first()
        
        if existing_template:
            raise HTTPException(
                status_code=409,
                detail="User already has active biometric template. Delete existing template first."
            )
        
        # Create new enrollment session
        enrollment_session = BiometricEnrollmentSession(
            user_id=user_id,
            status="started",
            samples_required=biometric_engine.min_enrollment_samples,
            started_at=datetime.utcnow()
        )
        
        db.add(enrollment_session)
        db.commit()
        db.refresh(enrollment_session)
        
        logger.info(f"Started biometric enrollment for user {user_id}")
        
        return EnrollmentStartResponse(
            status="enrollment_started",
            user_id=user_id,
            session_id=enrollment_session.id,
            samples_needed=biometric_engine.min_enrollment_samples,
            message="Hold sensor close to chest. Remain still for 30 seconds while we learn your heartbeat pattern."
        )
        
    except Exception as e:
        logger.error(f"Failed to start enrollment for {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Enrollment failed: {str(e)}")


@router.post("/enroll/sample/{user_id}", response_model=EnrollmentProgressResponse)
async def add_enrollment_sample(
    user_id: str,
    sample: HeartRateSampleAPI,
    db: Session = Depends(get_db)
):
    """Add biometric sample during enrollment"""
    
    try:
        # Find active enrollment session
        enrollment_session = db.query(BiometricEnrollmentSession).filter(
            BiometricEnrollmentSession.user_id == user_id,
            BiometricEnrollmentSession.status.in_(["started", "collecting"])
        ).first()
        
        if not enrollment_session:
            raise HTTPException(
                status_code=404,
                detail="No active enrollment session found. Start enrollment first."
            )
        
        # Convert API sample to engine format
        hr_sample = HeartRateSample(
            timestamp=sample.timestamp or datetime.utcnow(),
            heart_rate=sample.heart_rate,
            confidence=sample.confidence,
            distance=sample.distance
        )
        
        # Store sample in session (you'll need to add this to your model)
        enrollment_session.samples_collected += 1
        enrollment_session.status = "collecting"
        
        # Update session statistics
        if enrollment_session.average_heart_rate:
            enrollment_session.average_heart_rate = (
                (enrollment_session.average_heart_rate * (enrollment_session.samples_collected - 1) + 
                 sample.heart_rate) / enrollment_session.samples_collected
            )
        else:
            enrollment_session.average_heart_rate = sample.heart_rate
        
        db.commit()
        
        # Get enrollment progress
        progress = biometric_engine.get_enrollment_progress(enrollment_session.samples_collected)
        
        response = EnrollmentProgressResponse(
            status="collecting" if not progress["enrollment_ready"] else "ready_to_complete",
            samples_collected=progress["samples_collected"],
            samples_needed=progress["samples_needed"],
            progress_percentage=progress["progress_percentage"],
            enrollment_ready=progress["enrollment_ready"],
            estimated_time_remaining=progress["estimated_time_remaining"],
            message="Keep holding sensor steady..." if not progress["enrollment_ready"] 
                   else "Enrollment complete! Ready to finalize your biometric template."
        )
        
        logger.debug(f"Enrollment progress for {user_id}: {progress['progress_percentage']:.1f}%")
        return response
        
    except Exception as e:
        logger.error(f"Failed to add enrollment sample for {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sample processing failed: {str(e)}")


@router.post("/enroll/complete/{user_id}")
async def complete_biometric_enrollment(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Complete biometric enrollment and create template"""
    
    try:
        # Find enrollment session
        enrollment_session = db.query(BiometricEnrollmentSession).filter(
            BiometricEnrollmentSession.user_id == user_id,
            BiometricEnrollmentSession.status.in_(["started", "collecting"])
        ).first()
        
        if not enrollment_session:
            raise HTTPException(
                status_code=404,
                detail="No active enrollment session found"
            )
        
        if enrollment_session.samples_collected < biometric_engine.min_enrollment_samples:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient samples. Need {biometric_engine.min_enrollment_samples}, got {enrollment_session.samples_collected}"
            )
        
        # For this example, we'll simulate getting the collected samples
        # In a real implementation, you'd retrieve the stored samples from the database
        enrollment_samples = await _get_enrollment_samples(db, enrollment_session.id)
        
        # Create biometric template using the engine
        template = biometric_engine.create_biometric_template(user_id, enrollment_samples)
        
        # Save template to database
        db_template = DBTemplate(
            user_id=user_id,
            heart_rate_pattern=biometric_engine.export_template(user_id),
            biometric_signature=template.signature,
            sample_count=template.sample_count,
            quality_score=template.confidence_threshold,
            enrollment_duration=30.0,
            enrolled_at=template.created_at,
            confidence_threshold=template.confidence_threshold
        )
        
        db.add(db_template)
        
        # Update enrollment session
        enrollment_session.status = "completed"
        enrollment_session.completed_at = datetime.utcnow()
        enrollment_session.success = True
        enrollment_session.template_id = db_template.id
        
        db.commit()
        
        logger.info(f"Completed biometric enrollment for user {user_id}")
        
        return {
            "status": "enrollment_complete",
            "user_id": user_id,
            "biometric_signature": template.signature,
            "confidence_threshold": template.confidence_threshold,
            "sample_count": template.sample_count,
            "message": f"Biometric enrollment complete! Your unique heartbeat signature: {template.signature}"
        }
        
    except Exception as e:
        logger.error(f"Failed to complete enrollment for {user_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Enrollment completion failed: {str(e)}")


@router.post("/authenticate", response_model=AuthenticationResponse)
async def authenticate_biometric(
    samples: List[HeartRateSampleAPI],
    db: Session = Depends(get_db)
):
    """Authenticate user based on biometric samples"""
    
    try:
        if len(samples) < biometric_engine.min_auth_samples:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient samples for authentication. Need {biometric_engine.min_auth_samples}, got {len(samples)}"
            )
        
        # Load all enrolled templates into the engine
        await _load_enrolled_templates(db)
        
        # Convert API samples to engine format
        hr_samples = [
            HeartRateSample(
                timestamp=sample.timestamp or datetime.utcnow(),
                heart_rate=sample.heart_rate,
                confidence=sample.confidence,
                distance=sample.distance
            )
            for sample in samples
        ]
        
        # Perform authentication
        auth_result = biometric_engine.authenticate_user(hr_samples)
        
        # Store authentication attempt in database
        await _log_authentication_attempt(db, auth_result, hr_samples)
        
        response = AuthenticationResponse(
            authenticated=auth_result["authenticated"],
            user_id=auth_result["user_id"],
            confidence=auth_result["confidence"],
            timestamp=datetime.fromisoformat(auth_result["timestamp"]),
            biometric_signature=auth_result.get("signature")
        )
        
        if auth_result["authenticated"]:
            logger.info(f"User {auth_result['user_id']} authenticated with {auth_result['confidence']:.2f} confidence")
        else:
            logger.info(f"Authentication failed. Confidence: {auth_result['confidence']:.2f}")
        
        return response
        
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


@router.post("/presence/smart", response_model=SmartPresenceResponse)
async def smart_presence_detection(
    sensor_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Smart presence detection with biometric authentication"""
    
    try:
        # Extract sensor data
        heart_rate = float(sensor_data.get("heart_rate", 0))
        breathing_rate = float(sensor_data.get("breathing_rate", 0))
        distance = float(sensor_data.get("distance", 0))
        target_count = int(sensor_data.get("target_count", 0))
        confidence = float(sensor_data.get("confidence", 0.8))
        
        # Basic presence detection
        presence_detected = target_count > 0 and heart_rate > 30
        
        if not presence_detected:
            return SmartPresenceResponse(
                authenticated_presence=False,
                user_id=None,
                confidence=None,
                presence_detected=False,
                timestamp=datetime.utcnow()
            )
        
        # If we have heart rate data, attempt biometric authentication
        if heart_rate > 30:
            # Create sample for authentication (in real implementation, you'd collect multiple samples)
            hr_sample = HeartRateSample(
                timestamp=datetime.utcnow(),
                heart_rate=heart_rate,
                confidence=confidence,
                distance=distance
            )
            
            # For single-sample authentication, we need to collect more samples over time
            # This is a simplified version - in production, you'd accumulate samples
            samples = [hr_sample]  # In reality, collect 10+ samples over 10 seconds
            
            if len(samples) >= biometric_engine.min_auth_samples:
                # Load enrolled templates
                await _load_enrolled_templates(db)
                
                # Perform authentication
                auth_result = biometric_engine.authenticate_user(samples)
                
                return SmartPresenceResponse(
                    authenticated_presence=auth_result["authenticated"],
                    user_id=auth_result["user_id"],
                    confidence=auth_result["confidence"],
                    presence_detected=True,
                    timestamp=datetime.utcnow()
                )
        
        # Presence detected but insufficient data for authentication
        return SmartPresenceResponse(
            authenticated_presence=False,
            user_id="unknown",
            confidence=confidence,
            presence_detected=True,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Smart presence detection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Smart presence detection failed: {str(e)}")


@router.get("/templates")
async def get_biometric_templates(
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get biometric templates"""
    
    try:
        query = db.query(DBTemplate).filter(DBTemplate.is_active == True)
        
        if user_id:
            query = query.filter(DBTemplate.user_id == user_id)
        
        templates = query.all()
        
        return [
            {
                "user_id": template.user_id,
                "biometric_signature": template.biometric_signature,
                "enrolled_at": template.enrolled_at.isoformat(),
                "sample_count": template.sample_count,
                "quality_score": template.quality_score,
                "confidence_threshold": template.confidence_threshold,
                "is_active": template.is_active
            }
            for template in templates
        ]
        
    except Exception as e:
        logger.error(f"Failed to get biometric templates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve templates: {str(e)}")


@router.delete("/templates/{user_id}")
async def delete_biometric_template(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Delete biometric template for user"""
    
    try:
        template = db.query(DBTemplate).filter(
            DBTemplate.user_id == user_id,
            DBTemplate.is_active == True
        ).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="Biometric template not found")
        
        # Deactivate template
        template.is_active = False
        template.last_updated = datetime.utcnow()
        
        # Remove from biometric engine
        if user_id in biometric_engine.enrolled_users:
            del biometric_engine.enrolled_users[user_id]
        
        db.commit()
        
        logger.info(f"Deleted biometric template for user {user_id}")
        
        return {"status": "template_deleted", "user_id": user_id}
        
    except Exception as e:
        logger.error(f"Failed to delete template for {user_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Template deletion failed: {str(e)}")


@router.get("/analytics/{user_id}")
async def get_biometric_analytics(
    user_id: str,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get biometric analytics for user"""
    
    try:
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Get user's template
        template = db.query(DBTemplate).filter(
            DBTemplate.user_id == user_id,
            DBTemplate.is_active == True
        ).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="User not enrolled")
        
        # Get authentication attempts (you'd need to implement this table)
        # auth_attempts = db.query(AuthenticationAttempt).filter(...)
        
        return {
            "user_id": user_id,
            "period_days": days,
            "template_info": {
                "enrolled": True,
                "enrollment_date": template.enrolled_at.isoformat(),
                "quality_score": template.quality_score,
                "sample_count": template.sample_count,
                "biometric_signature": template.biometric_signature
            },
            "authentication_stats": {
                "total_attempts": 0,  # Implement based on your logging
                "successful_attempts": 0,
                "success_rate": 0.0,
                "average_confidence": 0.0
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get analytics for {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analytics generation failed: {str(e)}")


# Helper functions
async def _get_enrollment_samples(db: Session, session_id: str) -> List[HeartRateSample]:
    """Get enrollment samples from database (mock implementation)"""
    
    # In a real implementation, you'd query stored samples
    # For now, return mock data based on your actual sensor readings
    samples = []
    
    # Mock enrollment data based on your CSV analysis
    base_hr = 77.3  # Your average heart rate
    
    for i in range(60):  # 60 samples for 30 seconds
        # Add natural variation similar to your real data
        hr = base_hr + np.random.normal(0, 10.5)  # Your std deviation
        hr = max(51, min(105, hr))  # Your actual range
        
        sample = HeartRateSample(
            timestamp=datetime.utcnow() + timedelta(seconds=i * 0.5),
            heart_rate=hr,
            confidence=0.9,
            distance=150
        )
        samples.append(sample)
    
    return samples


async def _load_enrolled_templates(db: Session):
    """Load all enrolled templates into the biometric engine"""
    
    templates = db.query(DBTemplate).filter(DBTemplate.is_active == True).all()
    
    for db_template in templates:
        if db_template.user_id not in biometric_engine.enrolled_users:
            # Import template into engine
            template_data = db_template.heart_rate_pattern
            if template_data:
                biometric_engine.import_template(template_data)


async def _log_authentication_attempt(db: Session, auth_result: Dict, samples: List[HeartRateSample]):
    """Log authentication attempt to database"""
    
    # Implementation depends on your authentication logging table
    # This is where you'd store authentication attempts for analytics
    pass


# Import numpy for mock data generation
import numpy as np