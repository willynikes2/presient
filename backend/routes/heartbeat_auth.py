# backend/routes/heartbeat_auth.py
# Heartbeat Authentication API Routes for Presient MVP

import asyncio
import os
import aiohttp
import json
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

# Configurable Light Control System
LIGHT_CONTROL_ENABLED = os.getenv("LIGHT_CONTROL_ENABLED", "true").lower() == "true"
LIGHT_CONTROL_METHOD = os.getenv("LIGHT_CONTROL_METHOD", "none")  # none, homeassistant, mqtt, mobile
HA_WEBHOOK_URL = os.getenv("HA_WEBHOOK_URL", "")
MQTT_BROKER_URL = os.getenv("MQTT_BROKER_URL", "")
MOBILE_WEBHOOK_URL = os.getenv("MOBILE_WEBHOOK_URL", "")

async def send_light_command(color: str, user_id: str = None, duration: int = 3):
    """Send light command based on configured method"""
    
    if not LIGHT_CONTROL_ENABLED:
        logger.info(f"Light control disabled - would set {color} for {user_id}")
        return {"method": "disabled", "success": True}
    
    # Method 1: Home Assistant Webhook
    if LIGHT_CONTROL_METHOD == "homeassistant" and HA_WEBHOOK_URL:
        try:
            payload = {
                "color": color,
                "user_id": user_id,
                "duration": duration,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(HA_WEBHOOK_URL, json=payload) as response:
                    success = response.status == 200
                    logger.info(f"HA webhook sent: {color} - Status: {response.status}")
                    return {"method": "homeassistant", "success": success}
                    
        except Exception as e:
            logger.error(f"HA webhook failed: {str(e)}")
            return {"method": "homeassistant", "success": False, "error": str(e)}
    
    # Method 2: Direct MQTT (for standalone ESP32)
    elif LIGHT_CONTROL_METHOD == "mqtt" and MQTT_BROKER_URL:
        try:
            mqtt_topic = "presient/light/command"
            mqtt_payload = {
                "color": color,
                "user_id": user_id,
                "duration": duration
            }
            
            # TODO: Implement direct MQTT publishing when needed
            logger.info(f"MQTT would publish to {mqtt_topic}: {mqtt_payload}")
            return {"method": "mqtt", "success": True, "note": "MQTT implementation ready"}
            
        except Exception as e:
            logger.error(f"MQTT failed: {str(e)}")
            return {"method": "mqtt", "success": False, "error": str(e)}
    
    # Method 3: Mobile App Webhook
    elif LIGHT_CONTROL_METHOD == "mobile" and MOBILE_WEBHOOK_URL:
        try:
            payload = {
                "type": "light_control",
                "color": color,
                "user_id": user_id,
                "duration": duration,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(MOBILE_WEBHOOK_URL, json=payload) as response:
                    success = response.status == 200
                    logger.info(f"Mobile webhook sent: {color} - Status: {response.status}")
                    return {"method": "mobile", "success": success}
                    
        except Exception as e:
            logger.error(f"Mobile webhook failed: {str(e)}")
            return {"method": "mobile", "success": False, "error": str(e)}
    
    # Method 4: Log only (no physical lights)
    else:
        logger.info(f"Light command (log only): {color} for {user_id} ({duration}s)")
        return {"method": "log_only", "success": True}

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


# PATCHED: Configurable Light Control
@router.post("/light/control")
async def control_status_light(
    color: str = "blue",
    user_id: Optional[str] = None,
    duration: int = 3
):
    """Control status lights - works with multiple backends"""
    
    color_commands = {
        "off": {"state": "OFF"},
        "blue": {"state": "ON", "color": {"r": 0, "g": 50, "b": 255}},
        "green": {"state": "ON", "color": {"r": 0, "g": 255, "b": 0}},
        "yellow": {"state": "ON", "color": {"r": 255, "g": 255, "b": 0}},
        "purple": {"state": "ON", "color": {"r": 128, "g": 0, "b": 255}},
        "red": {"state": "ON", "color": {"r": 255, "g": 0, "b": 0}}
    }
    
    command = color_commands.get(color, color_commands["blue"])
    
    # Log the command
    logger.info(f"Light control: Setting {color} light for user {user_id}")
    
    # Send light command using configured method
    light_result = await send_light_command(color, user_id, duration)
    
    return {
        "success": True,
        "color": color,
        "user_id": user_id,
        "duration": duration,
        "command": command,
        "light_control": light_result,
        "config": {
            "enabled": LIGHT_CONTROL_ENABLED,
            "method": LIGHT_CONTROL_METHOD
        },
        "message": f"Light command processed: {color}"
    }


@router.post("/test/light-sequence")
async def test_light_sequence():
    """Test all light colors in sequence"""
    
    colors = ["blue", "green", "yellow", "purple", "red", "off"]
    results = []
    
    for color in colors:
        result = await send_light_command(color, "test", 2)
        results.append({"color": color, "result": result})
        await asyncio.sleep(1)  # 1 second delay between colors
    
    return {
        "success": True,
        "sequence_completed": True,
        "colors_tested": colors,
        "results": results,
        "light_method": LIGHT_CONTROL_METHOD,
        "message": "Light sequence test completed"
    }


@router.post("/presence/smart-with-light")
async def smart_presence_with_light(sensor_data: Dict[str, Any]):
    """Smart presence detection with configurable light feedback"""
    
    try:
        # Set scanning light first
        await send_light_command("blue", duration=2)
        
        # Process smart presence detection
        result = await smart_presence_detection(sensor_data)
        
        # Set result light based on authentication
        if result.authenticated_presence:
            await send_light_command("green", result.user_id, 5)
        elif result.presence_detected:
            await send_light_command("yellow", "unknown", 3)
        else:
            await send_light_command("off")
        
        return {
            **result.dict(),
            "light_feedback": True,
            "light_method": LIGHT_CONTROL_METHOD
        }
        
    except Exception as e:
        logger.error(f"Smart presence with light failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Smart presence with light failed: {str(e)}")


# Configuration endpoint
@router.get("/config/lights")
async def get_light_config():
    """Get current light control configuration"""
    return {
        "light_control_enabled": LIGHT_CONTROL_ENABLED,
        "method": LIGHT_CONTROL_METHOD,
        "available_methods": ["none", "homeassistant", "mqtt", "mobile"],
        "endpoints_configured": {
            "homeassistant": bool(HA_WEBHOOK_URL),
            "mqtt": bool(MQTT_BROKER_URL),
            "mobile": bool(MOBILE_WEBHOOK_URL)
        },
        "status": "Light control system ready"
    }


# Legacy webhook endpoints (kept for backward compatibility)
@router.post("/webhook/light-control")
async def webhook_light_control(request: Dict[str, Any]):
    """Webhook for VM to control lights via Codespace"""
    try:
        color = request.get("color", "blue")
        user_id = request.get("user_id")
        duration = request.get("duration", 3)

        logger.info(f"🔗 Webhook: VM requesting {color} light for {user_id}")

        # Use the new configurable system
        light_result = await send_light_command(color, user_id, duration)

        color_commands = {
            "off": {"state": "OFF"},
            "blue": {"state": "ON", "color": {"r": 0, "g": 50, "b": 255}},
            "green": {"state": "ON", "color": {"r": 0, "g": 255, "b": 0}},
            "yellow": {"state": "ON", "color": {"r": 255, "g": 255, "b": 0}},
            "purple": {"state": "ON", "color": {"r": 128, "g": 0, "b": 255}},
            "red": {"state": "ON", "color": {"r": 255, "g": 0, "b": 0}}
        }

        command = color_commands.get(color, color_commands["blue"])

        enhanced_command = {
            **command,
            "user_id": user_id,
            "duration": duration,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "presient_webhook"
        }

        mqtt_topic = "presient/princeton/light/status_light/command"

        return {
            "success": True,
            "color": color,
            "user_id": user_id,
            "duration": duration,
            "mqtt_topic": mqtt_topic,
            "mqtt_command": enhanced_command,
            "light_control": light_result,
            "webhook_processed": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return {"success": False, "error": str(e)}


@router.post("/webhook/smart-presence")
async def webhook_smart_presence(sensor_data: Dict[str, Any]):
    """Webhook for smart presence detection with automatic light control"""
    
    try:
        logger.info(f"🔗 Webhook: VM sending sensor data for smart presence")
        
        # Process using the new smart presence with lights
        result = await smart_presence_with_light(sensor_data)
        
        return {
            **result,
            "webhook_processed": True,
            "flow": ["sensor_data", "authentication", "light_command", "configured_method"]
        }
        
    except Exception as e:
        logger.error(f"Webhook smart presence failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook smart presence failed: {str(e)}")


@router.post("/webhook/test-sequence")
async def webhook_test_sequence():
    """Webhook for testing all light colors"""
    
    try:
        result = await test_light_sequence()
        
        return {
            **result,
            "webhook_processed": True,
            "instructions": f"Using {LIGHT_CONTROL_METHOD} method for light control"
        }
        
    except Exception as e:
        logger.error(f"Webhook test sequence failed: {str(e)}")
        return {"success": False, "error": str(e)}