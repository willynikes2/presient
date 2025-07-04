# backend/services/heartbeat_auth.py
# Simplified Heartbeat Authentication for Presient MVP

import json
import hashlib
from fastapi import HTTPException
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter()

@dataclass
class HeartbeatSample:
    """Single heartbeat measurement"""
    timestamp: datetime
    heart_rate: float
    confidence: float
    
@dataclass
class HeartbeatPattern:
    """User's heartbeat authentication pattern"""
    user_id: str
    avg_heart_rate: float
    heart_rate_variance: float
    pattern_signature: str
    confidence_threshold: float
    sample_count: int
    created_at: datetime

class HeartbeatAuthenticator:
    """Simplified heartbeat authentication for Presient MVP"""
    
    def __init__(self):
        self.enrolled_users: Dict[str, HeartbeatPattern] = {}
        self.min_enrollment_samples = 30  # 30 seconds of data
        self.min_auth_samples = 10       # 10 seconds for authentication
        self.base_confidence_threshold = 0.75
        
    def enroll_user(self, user_id: str, samples: List[HeartbeatSample]) -> Dict[str, any]:
        """Enroll user's heartbeat pattern for authentication"""
        
        if len(samples) < self.min_enrollment_samples:
            return {
                "success": False,
                "error": f"Need {self.min_enrollment_samples} samples, got {len(samples)}"
            }
        
        # Extract heart rate values
        hr_values = [s.heart_rate for s in samples if 40 <= s.heart_rate <= 150]
        
        if len(hr_values) < self.min_enrollment_samples:
            return {
                "success": False,
                "error": "Insufficient valid heart rate readings"
            }
        
        # Calculate pattern features
        avg_hr = np.mean(hr_values)
        hr_variance = np.var(hr_values)
        
        # Create unique signature from pattern
        pattern_data = {
            "avg_hr": round(avg_hr, 2),
            "variance": round(hr_variance, 2),
            "sample_count": len(hr_values)
        }
        
        signature = hashlib.sha256(
            json.dumps(pattern_data, sort_keys=True).encode()
        ).hexdigest()[:16]
        
        # Calculate confidence threshold based on data quality
        confidence_threshold = self._calculate_threshold(hr_values)
        
        # Store pattern
        pattern = HeartbeatPattern(
            user_id=user_id,
            avg_heart_rate=avg_hr,
            heart_rate_variance=hr_variance,
            pattern_signature=signature,
            confidence_threshold=confidence_threshold,
            sample_count=len(hr_values),
            created_at=datetime.utcnow()
        )
        
        self.enrolled_users[user_id] = pattern
        
        logger.info(f"Enrolled user {user_id} with {len(hr_values)} samples")
        
        return {
            "success": True,
            "user_id": user_id,
            "signature": signature,
            "avg_heart_rate": avg_hr,
            "confidence_threshold": confidence_threshold,
            "sample_count": len(hr_values)
        }
    
    def authenticate(self, samples: List[HeartbeatSample]) -> Dict[str, any]:
        """Authenticate user based on heartbeat samples"""
        
        if len(samples) < self.min_auth_samples:
            return {
                "authenticated": False,
                "user_id": None,
                "confidence": 0.0,
                "error": f"Need {self.min_auth_samples} samples for authentication"
            }
        
        if not self.enrolled_users:
            return {
                "authenticated": False,
                "user_id": None,
                "confidence": 0.0,
                "error": "No enrolled users"
            }
        
        # Extract heart rate values
        hr_values = [s.heart_rate for s in samples if 40 <= s.heart_rate <= 150]
        
        if len(hr_values) < self.min_auth_samples:
            return {
                "authenticated": False,
                "user_id": None,
                "confidence": 0.0,
                "error": "Insufficient valid heart rate readings"
            }
        
        # Calculate current pattern
        current_avg = np.mean(hr_values)
        current_variance = np.var(hr_values)
        
        # Compare against all enrolled users
        best_match = None
        best_confidence = 0.0
        
        for user_id, pattern in self.enrolled_users.items():
            confidence = self._calculate_similarity(
                current_avg, current_variance,
                pattern.avg_heart_rate, pattern.heart_rate_variance
            )
            
            if confidence > best_confidence and confidence >= pattern.confidence_threshold:
                best_match = user_id
                best_confidence = confidence
        
        # Authentication result
        authenticated = best_match is not None and best_confidence >= self.base_confidence_threshold
        
        result = {
            "authenticated": authenticated,
            "user_id": best_match,
            "confidence": round(best_confidence, 3),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if authenticated:
            logger.info(f"User {best_match} authenticated with {best_confidence:.3f} confidence")
        else:
            logger.info(f"Authentication failed. Best confidence: {best_confidence:.3f}")
        
        return result
    
    def _calculate_similarity(self, avg1: float, var1: float, avg2: float, var2: float) -> float:
        """Calculate similarity between two heartbeat patterns"""
        
        # Heart rate average similarity (weighted 60%)
        hr_diff = abs(avg1 - avg2)
        hr_similarity = max(0, 1 - (hr_diff / 30))  # Normalize by 30 bpm
        
        # Variance similarity (weighted 40%)
        var_diff = abs(var1 - var2)
        var_similarity = max(0, 1 - (var_diff / 50))  # Normalize by variance range
        
        # Weighted combination
        total_similarity = (hr_similarity * 0.6) + (var_similarity * 0.4)
        
        return min(1.0, max(0.0, total_similarity))
    
    def _calculate_threshold(self, hr_values: List[float]) -> float:
        """Calculate appropriate confidence threshold based on data quality"""
        
        # Base threshold
        base_threshold = 0.75
        
        # Adjust based on heart rate stability
        hr_stability = 1 - (np.std(hr_values) / np.mean(hr_values))
        
        # More stable heart rate = lower threshold needed
        adjusted_threshold = base_threshold * (2 - hr_stability)
        
        return max(0.6, min(0.9, adjusted_threshold))
    
    def get_enrolled_users(self) -> List[Dict[str, any]]:
        """Get list of enrolled users"""
        
        return [
            {
                "user_id": pattern.user_id,
                "signature": pattern.pattern_signature,
                "avg_heart_rate": round(pattern.avg_heart_rate, 1),
                "enrolled_at": pattern.created_at.isoformat(),
                "sample_count": pattern.sample_count,
                "confidence_threshold": round(pattern.confidence_threshold, 3)
            }
            for pattern in self.enrolled_users.values()
        ]
    
    def delete_user(self, user_id: str) -> bool:
        """Delete enrolled user"""
        
        if user_id in self.enrolled_users:
            del self.enrolled_users[user_id]
            logger.info(f"Deleted user {user_id}")
            return True
        return False
    
    def get_enrollment_progress(self, current_samples: int) -> Dict[str, any]:
        """Get enrollment progress information"""
        
        progress = min(100, (current_samples / self.min_enrollment_samples) * 100)
        
        return {
            "samples_collected": current_samples,
            "samples_needed": self.min_enrollment_samples,
            "progress_percentage": round(progress, 1),
            "enrollment_ready": current_samples >= self.min_enrollment_samples,
            "estimated_time_remaining": max(0, self.min_enrollment_samples - current_samples)
        }


# Example usage for testing
if __name__ == "__main__":
    # Test the authenticator
    auth = HeartbeatAuthenticator()
    
    # Simulate enrollment samples
    enrollment_samples = []
    base_hr = 75
    
    for i in range(35):  # 35 samples for enrollment
        hr = base_hr + np.random.normal(0, 3)  # Natural variation
        sample = HeartbeatSample(
            timestamp=datetime.utcnow(),
            heart_rate=max(50, min(120, hr)),
            confidence=0.9
        )
        enrollment_samples.append(sample)
    
    # Enroll user
    result = auth.enroll_user("john_doe", enrollment_samples)
    print(f"Enrollment result: {result}")
    
    # Simulate authentication samples
    auth_samples = []
    for i in range(15):  # 15 samples for authentication
        hr = base_hr + np.random.normal(0, 2)  # Similar pattern
        sample = HeartbeatSample(
            timestamp=datetime.utcnow(),
            heart_rate=max(50, min(120, hr)),
            confidence=0.85
        )
        auth_samples.append(sample)
    
    # Authenticate
    auth_result = auth.authenticate(auth_samples)
    print(f"Authentication result: {auth_result}")

   