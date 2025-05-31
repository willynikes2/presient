# backend/routes/heartbeat_auth.py
# Heartbeat Authentication API Routes for Presient MVP

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ..services.heartbeat_auth import HeartbeatAuthenticator, HeartbeatSample

router = APIRouter(prefix="/api/heartbeat", tags=["heartbeat-auth"])
logger = logging.getLogger(__name__)

# Initialize authenticator (singleton)
heartbeat_auth = HeartbeatAuthenticator()

# Pydantic models
class HeartRateData(BaseModel):
    heart_rate: float = Field(..., ge=40, le=200, description="Heart rate in BPM")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0, description="Signal confidence")
    timestamp: Optional[datetime] = None

class EnrollmentRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=50)
    samples: List[HeartRateData]

class AuthenticationRequest(BaseModel):
    samples: List[HeartRateData]

class EnrollmentResponse(BaseModel):
    success: bool
    user_id: Optional[str] = None
    signature: Optional[str] = None
    avg_heart_rate: Optional[float] = None
    confidence_threshold: Optional[float] = None
    sample_count: Optional[int] = None
    error: Optional[str] = None

class AuthenticationResponse(BaseModel):
    authenticated: bool
    user_id: Optional[str] = None
    confidence: float
    timestamp: str
    error: Optional[str] = None

class SmartPresenceResponse(BaseModel):
    authenticated_presence: bool
    user_id: Optional[str] = None
    confidence: Optional[float] = None
    presence_detected: bool
    method: str = "heartbeat_authentication"
    timestamp: datetime


@router.post("/enroll", response_model=EnrollmentResponse)
async def enroll_user_heartbeat(request: EnrollmentRequest):
    """Enroll user's heartbeat pattern for authentication"""
    
    try:
        # Convert API samples to internal format
        samples = [
            HeartbeatSample(
                timestamp=sample.timestamp or datetime.utcnow(),
                heart_rate=sample.heart_rate,
                confidence=sample.confidence
            )
            for sample in request.samples
        ]
        
        # Enroll user
        result = heartbeat_auth.enroll_user(request.user_id, samples)
        
        if result["success"]:
            logger.info(f"Successfully enrolled user {request.user_id}")
            return EnrollmentResponse(
                success=True,
                user_id=result["user_id"],
                signature=result["signature"],
                avg_heart_rate=result["avg_heart_rate"],
                confidence_threshold=result["confidence_threshold"],
                sample_count=result["sample_count"]
            )
        else:
            logger.warning(f"Enrollment failed for {request.user_id}: {result['error']}")
            return EnrollmentResponse(
                success=False,
                error=result["error"]
            )
            
    except Exception as e:
        logger.error(f"Enrollment error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Enrollment failed: {str(e)}")


@router.post("/authenticate", response_model=AuthenticationResponse)
async def authenticate_heartbeat(request: AuthenticationRequest):
    """Authenticate user based on heartbeat pattern"""
    
    try:
        # Convert API samples to internal format
        samples = [
            HeartbeatSample(
                timestamp=sample.timestamp or datetime.utcnow(),
                heart_rate=sample.heart_rate,
                confidence=sample.confidence
            )
            for sample in request.samples
        ]
        
        # Authenticate
        result = heartbeat_auth.authenticate(samples)
        
        return AuthenticationResponse(
            authenticated=result["authenticated"],
            user_id=result["user_id"],
            confidence=result["confidence"],
            timestamp=result["timestamp"],
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


@router.post("/presence/smart", response_model=SmartPresenceResponse)
async def smart_presence_detection(sensor_data: Dict[str, Any]):
    """Enhanced presence detection with heartbeat authentication"""
    
    try:
        # Extract sensor data
        heart_rate = float(sensor_data.get("heart_rate", 0))
        target_count = int(sensor_data.get("target_count", 0))
        confidence = float(sensor_data.get("confidence", 0.8))
        
        # Basic presence detection
        presence_detected = target_count > 0 and heart_rate > 40
        
        if not presence_detected:
            return SmartPresenceResponse(
                authenticated_presence=False,
                user_id=None,
                confidence=None,
                presence_detected=False,
                timestamp=datetime.utcnow()
            )
        
        # If we have heart rate data, attempt authentication
        if heart_rate > 40:
            # Create sample for authentication
            sample = HeartbeatSample(
                timestamp=datetime.utcnow(),
                heart_rate=heart_rate,
                confidence=confidence
            )
            
            # For single-sample auth, we use simplified logic
            # In production, you'd collect multiple samples over time
            samples = [sample]
            
            # Simple single-sample authentication
            if len(heartbeat_auth.enrolled_users) > 0:
                auth_result = heartbeat_auth.authenticate(samples)
                
                return SmartPresenceResponse(
                    authenticated_presence=auth_result["authenticated"],
                    user_id=auth_result["user_id"],
                    confidence=auth_result["confidence"],
                    presence_detected=True,
                    timestamp=datetime.utcnow()
                )
        
        # Presence detected but no authentication possible
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


@router.get("/enrolled")
async def get_enrolled_users():
    """Get list of enrolled users"""
    
    try:
        users = heartbeat_auth.get_enrolled_users()
        return {
            "enrolled_users": users,
            "total_count": len(users)
        }
        
    except Exception as e:
        logger.error(f"Failed to get enrolled users: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get enrolled users: {str(e)}")


@router.delete("/enrolled/{user_id}")
async def delete_enrolled_user(user_id: str):
    """Delete enrolled user"""
    
    try:
        success = heartbeat_auth.delete_user(user_id)
        
        if success:
            return {"status": "deleted", "user_id": user_id}
        else:
            raise HTTPException(status_code=404, detail="User not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")


@router.get("/progress/{sample_count}")
async def get_enrollment_progress(sample_count: int):
    """Get enrollment progress"""
    
    try:
        progress = heartbeat_auth.get_enrollment_progress(sample_count)
        return progress
        
    except Exception as e:
        logger.error(f"Failed to get progress: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get progress: {str(e)}")


# Test endpoints for development
@router.post("/test/enroll/{user_id}")
async def test_enroll_user(user_id: str):
    """Test endpoint to enroll user with mock data"""
    
    try:
        # Generate mock enrollment data
        import numpy as np
        
        samples = []
        base_hr = 75
        
        for i in range(35):  # 35 samples
            hr = base_hr + np.random.normal(0, 3)
            sample = HeartRateData(
                heart_rate=max(50, min(120, hr)),
                confidence=0.9
            )
            samples.append(sample)
        
        # Enroll with mock data
        request = EnrollmentRequest(user_id=user_id, samples=samples)
        return await enroll_user_heartbeat(request)
        
    except Exception as e:
        logger.error(f"Test enrollment failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Test enrollment failed: {str(e)}")


@router.post("/test/authenticate")
async def test_authenticate():
    """Test endpoint to authenticate with mock data"""
    
    try:
        import numpy as np
        
        # Generate mock authentication data
        samples = []
        base_hr = 75
        
        for i in range(15):  # 15 samples
            hr = base_hr + np.random.normal(0, 2)
            sample = HeartRateData(
                heart_rate=max(50, min(120, hr)),
                confidence=0.85
            )
            samples.append(sample)
        
        # Authenticate with mock data
        request = AuthenticationRequest(samples=samples)
        return await authenticate_heartbeat(request)
        
    except Exception as e:
        logger.error(f"Test authentication failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Test authentication failed: {str(e)}")