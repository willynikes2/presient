# backend/services/biometric_engine.py
# Presient Biometric Processing Engine
# Heart Rate Variability (HRV) based authentication system

import numpy as np
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from scipy import signal
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)

@dataclass
class HeartRateSample:
    """Individual heart rate measurement"""
    timestamp: datetime
    heart_rate: float
    confidence: float
    distance: float
    
@dataclass
class BiometricFeatures:
    """Extracted biometric features from heart rate data"""
    mean_hr: float
    std_hr: float
    rmssd: float  # Root Mean Square of Successive Differences
    pnn50: float  # Percentage of successive RR intervals that differ by more than 50ms
    hr_patterns: List[int]  # Sequential heart rate patterns
    frequency_domain: Dict[str, float]  # Frequency analysis
    geometric_features: Dict[str, float]  # Geometric HRV measures
    
@dataclass
class BiometricTemplate:
    """User's biometric template for authentication"""
    user_id: str
    features: BiometricFeatures
    signature: str  # Unique hash of the template
    confidence_threshold: float
    created_at: datetime
    sample_count: int

class PresientBiometricEngine:
    """Core biometric processing engine for Presient authentication"""
    
    def __init__(self):
        self.enrolled_users: Dict[str, BiometricTemplate] = {}
        self.min_enrollment_samples = 60  # 30 seconds at ~2 samples/second
        self.min_auth_samples = 20  # 10 seconds at ~2 samples/second
        self.confidence_threshold = 0.75
        
    def extract_hrv_features(self, hr_samples: List[HeartRateSample]) -> BiometricFeatures:
        """Extract comprehensive HRV features from heart rate samples"""
        
        if len(hr_samples) < 10:
            raise ValueError("Insufficient samples for HRV analysis")
        
        # Extract heart rate values and timestamps
        hr_values = [sample.heart_rate for sample in hr_samples]
        timestamps = [sample.timestamp for sample in hr_samples]
        
        # Basic statistical measures
        mean_hr = np.mean(hr_values)
        std_hr = np.std(hr_values)
        
        # Time domain HRV analysis
        rr_intervals = self._calculate_rr_intervals(hr_values)
        rmssd = self._calculate_rmssd(rr_intervals)
        pnn50 = self._calculate_pnn50(rr_intervals)
        
        # Pattern analysis (5-beat sequences)
        hr_patterns = self._extract_patterns(hr_values, pattern_length=5)
        
        # Frequency domain analysis
        frequency_features = self._frequency_analysis(rr_intervals, timestamps)
        
        # Geometric measures
        geometric_features = self._geometric_analysis(rr_intervals)
        
        return BiometricFeatures(
            mean_hr=mean_hr,
            std_hr=std_hr,
            rmssd=rmssd,
            pnn50=pnn50,
            hr_patterns=hr_patterns,
            frequency_domain=frequency_features,
            geometric_features=geometric_features
        )
    
    def _calculate_rr_intervals(self, hr_values: List[float]) -> List[float]:
        """Calculate RR intervals from heart rate values"""
        # Convert HR to RR intervals (60/HR * 1000 for milliseconds)
        rr_intervals = []
        for hr in hr_values:
            if hr > 0:
                rr_interval = (60.0 / hr) * 1000  # Convert to milliseconds
                rr_intervals.append(rr_interval)
        return rr_intervals
    
    def _calculate_rmssd(self, rr_intervals: List[float]) -> float:
        """Calculate Root Mean Square of Successive Differences"""
        if len(rr_intervals) < 2:
            return 0.0
        
        successive_diffs = []
        for i in range(1, len(rr_intervals)):
            diff = rr_intervals[i] - rr_intervals[i-1]
            successive_diffs.append(diff ** 2)
        
        return np.sqrt(np.mean(successive_diffs))
    
    def _calculate_pnn50(self, rr_intervals: List[float]) -> float:
        """Calculate percentage of successive RR intervals differing by >50ms"""
        if len(rr_intervals) < 2:
            return 0.0
        
        count_over_50 = 0
        total_pairs = len(rr_intervals) - 1
        
        for i in range(1, len(rr_intervals)):
            diff = abs(rr_intervals[i] - rr_intervals[i-1])
            if diff > 50:  # >50ms difference
                count_over_50 += 1
        
        return (count_over_50 / total_pairs) * 100
    
    def _extract_patterns(self, hr_values: List[float], pattern_length: int = 5) -> List[int]:
        """Extract sequential heart rate patterns for biometric identification"""
        patterns = []
        
        for i in range(len(hr_values) - pattern_length + 1):
            pattern = hr_values[i:i + pattern_length]
            
            # Normalize pattern relative to first value
            if pattern[0] > 0:
                normalized_pattern = [int(round((hr - pattern[0]) + 100)) for hr in pattern]
                patterns.extend(normalized_pattern)
        
        return patterns
    
    def _frequency_analysis(self, rr_intervals: List[float], timestamps: List[datetime]) -> Dict[str, float]:
        """Perform frequency domain analysis on RR intervals"""
        
        if len(rr_intervals) < 10:
            return {"vlf_power": 0.0, "lf_power": 0.0, "hf_power": 0.0, "lf_hf_ratio": 0.0}
        
        try:
            # Interpolate RR intervals for frequency analysis
            rr_array = np.array(rr_intervals)
            
            # Calculate power spectral density
            frequencies, psd = signal.periodogram(rr_array, fs=1.0)
            
            # Define frequency bands (Hz)
            vlf_band = (0.0033, 0.04)  # Very Low Frequency
            lf_band = (0.04, 0.15)     # Low Frequency
            hf_band = (0.15, 0.4)      # High Frequency
            
            # Calculate power in each band
            vlf_power = np.trapz(psd[(frequencies >= vlf_band[0]) & (frequencies < vlf_band[1])])
            lf_power = np.trapz(psd[(frequencies >= lf_band[0]) & (frequencies < lf_band[1])])
            hf_power = np.trapz(psd[(frequencies >= hf_band[0]) & (frequencies < hf_band[1])])
            
            # Calculate LF/HF ratio
            lf_hf_ratio = lf_power / hf_power if hf_power > 0 else 0.0
            
            return {
                "vlf_power": float(vlf_power),
                "lf_power": float(lf_power),
                "hf_power": float(hf_power),
                "lf_hf_ratio": float(lf_hf_ratio)
            }
        
        except Exception as e:
            logger.warning(f"Frequency analysis failed: {e}")
            return {"vlf_power": 0.0, "lf_power": 0.0, "hf_power": 0.0, "lf_hf_ratio": 0.0}
    
    def _geometric_analysis(self, rr_intervals: List[float]) -> Dict[str, float]:
        """Calculate geometric HRV measures"""
        
        if len(rr_intervals) < 20:
            return {"triangular_index": 0.0, "tinn": 0.0}
        
        try:
            rr_array = np.array(rr_intervals)
            
            # Triangular index (total number of RR intervals / height of histogram)
            hist, bin_edges = np.histogram(rr_array, bins=50)
            triangular_index = len(rr_array) / np.max(hist) if np.max(hist) > 0 else 0.0
            
            # TINN (Triangular Interpolation of NN interval histogram)
            # Simplified calculation
            tinn = np.max(rr_array) - np.min(rr_array)
            
            return {
                "triangular_index": float(triangular_index),
                "tinn": float(tinn)
            }
        
        except Exception as e:
            logger.warning(f"Geometric analysis failed: {e}")
            return {"triangular_index": 0.0, "tinn": 0.0}
    
    def create_biometric_template(self, user_id: str, hr_samples: List[HeartRateSample]) -> BiometricTemplate:
        """Create biometric template from enrollment samples"""
        
        if len(hr_samples) < self.min_enrollment_samples:
            raise ValueError(f"Insufficient samples for enrollment. Need {self.min_enrollment_samples}, got {len(hr_samples)}")
        
        # Extract comprehensive features
        features = self.extract_hrv_features(hr_samples)
        
        # Create unique signature
        signature = self._generate_signature(features)
        
        # Determine confidence threshold based on data quality
        confidence_threshold = self._calculate_confidence_threshold(hr_samples)
        
        template = BiometricTemplate(
            user_id=user_id,
            features=features,
            signature=signature,
            confidence_threshold=confidence_threshold,
            created_at=datetime.utcnow(),
            sample_count=len(hr_samples)
        )
        
        # Store template
        self.enrolled_users[user_id] = template
        
        logger.info(f"Created biometric template for user {user_id} with {len(hr_samples)} samples")
        return template
    
    def authenticate_user(self, hr_samples: List[HeartRateSample]) -> Dict[str, any]:
        """Authenticate user against enrolled templates"""
        
        if len(hr_samples) < self.min_auth_samples:
            return {
                "authenticated": False,
                "user_id": None,
                "confidence": 0.0,
                "error": f"Insufficient samples for authentication. Need {self.min_auth_samples}, got {len(hr_samples)}"
            }
        
        if not self.enrolled_users:
            return {
                "authenticated": False,
                "user_id": None,
                "confidence": 0.0,
                "error": "No enrolled users found"
            }
        
        # Extract features from current samples
        try:
            current_features = self.extract_hrv_features(hr_samples)
        except Exception as e:
            return {
                "authenticated": False,
                "user_id": None,
                "confidence": 0.0,
                "error": f"Feature extraction failed: {str(e)}"
            }
        
        # Compare against all enrolled users
        best_match = None
        best_confidence = 0.0
        
        for user_id, template in self.enrolled_users.items():
            confidence = self._calculate_similarity(current_features, template.features)
            
            if confidence > best_confidence and confidence >= template.confidence_threshold:
                best_match = user_id
                best_confidence = confidence
        
        # Authentication result
        authenticated = best_match is not None and best_confidence >= self.confidence_threshold
        
        result = {
            "authenticated": authenticated,
            "user_id": best_match,
            "confidence": best_confidence,
            "threshold": self.confidence_threshold,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if authenticated:
            logger.info(f"User {best_match} authenticated with {best_confidence:.2f} confidence")
        else:
            logger.info(f"Authentication failed. Best match: {best_confidence:.2f}")
        
        return result
    
    def _calculate_similarity(self, features1: BiometricFeatures, features2: BiometricFeatures) -> float:
        """Calculate similarity between two biometric feature sets"""
        
        similarities = []
        
        # Time domain similarity
        hr_diff = abs(features1.mean_hr - features2.mean_hr)
        hr_similarity = max(0, 1 - (hr_diff / 50))  # Normalize by 50 bpm
        similarities.append(hr_similarity * 0.2)
        
        # HRV similarity (RMSSD)
        rmssd_diff = abs(features1.rmssd - features2.rmssd)
        rmssd_similarity = max(0, 1 - (rmssd_diff / 100))  # Normalize by 100ms
        similarities.append(rmssd_similarity * 0.25)
        
        # PNN50 similarity
        pnn50_diff = abs(features1.pnn50 - features2.pnn50)
        pnn50_similarity = max(0, 1 - (pnn50_diff / 50))  # Normalize by 50%
        similarities.append(pnn50_similarity * 0.15)
        
        # Pattern similarity
        if features1.hr_patterns and features2.hr_patterns:
            pattern_similarity = self._calculate_pattern_similarity(
                features1.hr_patterns, features2.hr_patterns
            )
            similarities.append(pattern_similarity * 0.25)
        
        # Frequency domain similarity
        freq_similarity = self._calculate_frequency_similarity(
            features1.frequency_domain, features2.frequency_domain
        )
        similarities.append(freq_similarity * 0.15)
        
        # Weighted average
        total_similarity = sum(similarities)
        return min(1.0, max(0.0, total_similarity))
    
    def _calculate_pattern_similarity(self, patterns1: List[int], patterns2: List[int]) -> float:
        """Calculate similarity between heart rate patterns"""
        
        if not patterns1 or not patterns2:
            return 0.0
        
        # Convert to numpy arrays for cosine similarity
        try:
            # Truncate to same length
            min_length = min(len(patterns1), len(patterns2))
            p1 = np.array(patterns1[:min_length]).reshape(1, -1)
            p2 = np.array(patterns2[:min_length]).reshape(1, -1)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(p1, p2)[0][0]
            return max(0.0, similarity)
        
        except Exception as e:
            logger.warning(f"Pattern similarity calculation failed: {e}")
            return 0.0
    
    def _calculate_frequency_similarity(self, freq1: Dict[str, float], freq2: Dict[str, float]) -> float:
        """Calculate similarity between frequency domain features"""
        
        similarities = []
        
        for key in ['vlf_power', 'lf_power', 'hf_power', 'lf_hf_ratio']:
            if key in freq1 and key in freq2:
                val1, val2 = freq1[key], freq2[key]
                if val1 > 0 and val2 > 0:
                    # Calculate relative difference
                    diff = abs(val1 - val2) / max(val1, val2)
                    similarity = max(0, 1 - diff)
                    similarities.append(similarity)
        
        return np.mean(similarities) if similarities else 0.0
    
    def _generate_signature(self, features: BiometricFeatures) -> str:
        """Generate unique signature from biometric features"""
        
        # Create signature from key features
        signature_data = {
            "mean_hr": round(features.mean_hr, 1),
            "rmssd": round(features.rmssd, 1),
            "pnn50": round(features.pnn50, 1),
            "pattern_hash": hashlib.md5(str(features.hr_patterns).encode()).hexdigest()[:8]
        }
        
        signature_string = json.dumps(signature_data, sort_keys=True)
        return hashlib.sha256(signature_string.encode()).hexdigest()[:16]
    
    def _calculate_confidence_threshold(self, hr_samples: List[HeartRateSample]) -> float:
        """Calculate appropriate confidence threshold based on data quality"""
        
        # Analyze data quality
        hr_values = [s.heart_rate for s in hr_samples]
        confidences = [s.confidence for s in hr_samples]
        
        # Base threshold
        base_threshold = 0.75
        
        # Adjust based on data quality
        avg_confidence = np.mean(confidences)
        hr_stability = 1 - (np.std(hr_values) / np.mean(hr_values))
        
        # Quality factor (0.8 - 1.0)
        quality_factor = (avg_confidence + hr_stability) / 2
        
        # Adjust threshold (higher quality = lower threshold needed)
        adjusted_threshold = base_threshold * (2 - quality_factor)
        
        return max(0.6, min(0.9, adjusted_threshold))
    
    def get_enrollment_progress(self, current_samples: int) -> Dict[str, any]:
        """Get enrollment progress information"""
        
        progress = min(100, (current_samples / self.min_enrollment_samples) * 100)
        
        return {
            "samples_collected": current_samples,
            "samples_needed": self.min_enrollment_samples,
            "progress_percentage": round(progress, 1),
            "enrollment_ready": current_samples >= self.min_enrollment_samples,
            "estimated_time_remaining": max(0, (self.min_enrollment_samples - current_samples) * 0.5)  # seconds
        }
    
    def export_template(self, user_id: str) -> Optional[Dict]:
        """Export biometric template for storage"""
        
        if user_id not in self.enrolled_users:
            return None
        
        template = self.enrolled_users[user_id]
        
        return {
            "user_id": template.user_id,
            "features": {
                "mean_hr": template.features.mean_hr,
                "std_hr": template.features.std_hr,
                "rmssd": template.features.rmssd,
                "pnn50": template.features.pnn50,
                "hr_patterns": template.features.hr_patterns,
                "frequency_domain": template.features.frequency_domain,
                "geometric_features": template.features.geometric_features
            },
            "signature": template.signature,
            "confidence_threshold": template.confidence_threshold,
            "created_at": template.created_at.isoformat(),
            "sample_count": template.sample_count
        }
    
    def import_template(self, template_data: Dict) -> bool:
        """Import biometric template from storage"""
        
        try:
            features = BiometricFeatures(
                mean_hr=template_data["features"]["mean_hr"],
                std_hr=template_data["features"]["std_hr"],
                rmssd=template_data["features"]["rmssd"],
                pnn50=template_data["features"]["pnn50"],
                hr_patterns=template_data["features"]["hr_patterns"],
                frequency_domain=template_data["features"]["frequency_domain"],
                geometric_features=template_data["features"]["geometric_features"]
            )
            
            template = BiometricTemplate(
                user_id=template_data["user_id"],
                features=features,
                signature=template_data["signature"],
                confidence_threshold=template_data["confidence_threshold"],
                created_at=datetime.fromisoformat(template_data["created_at"]),
                sample_count=template_data["sample_count"]
            )
            
            self.enrolled_users[template.user_id] = template
            logger.info(f"Imported biometric template for user {template.user_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to import template: {e}")
            return False


# Example usage and testing
if __name__ == "__main__":
    # Initialize biometric engine
    engine = PresientBiometricEngine()
    
    # Simulate enrollment data (30 seconds of heart rate)
    enrollment_samples = []
    base_hr = 75
    
    for i in range(60):  # 60 samples = 30 seconds
        hr = base_hr + np.random.normal(0, 3)  # Natural variation
        sample = HeartRateSample(
            timestamp=datetime.utcnow() + timedelta(seconds=i),
            heart_rate=max(50, min(120, hr)),
            confidence=0.9,
            distance=150
        )
        enrollment_samples.append(sample)
    
    # Create biometric template
    try:
        template = engine.create_biometric_template("john_doe", enrollment_samples)
        print(f"✅ Enrollment successful!")
        print(f"   User ID: {template.user_id}")
        print(f"   Signature: {template.signature}")
        print(f"   Confidence Threshold: {template.confidence_threshold:.2f}")
        print(f"   Sample Count: {template.sample_count}")
        
        # Simulate authentication attempt
        auth_samples = []
        for i in range(20):  # 20 samples = 10 seconds
            hr = base_hr + np.random.normal(0, 2)  # Similar pattern
            sample = HeartRateSample(
                timestamp=datetime.utcnow() + timedelta(seconds=i),
                heart_rate=max(50, min(120, hr)),
                confidence=0.85,
                distance=160
            )
            auth_samples.append(sample)
        
        # Authenticate
        auth_result = engine.authenticate_user(auth_samples)
        print(f"\n🔐 Authentication Result:")
        print(f"   Authenticated: {auth_result['authenticated']}")
        print(f"   User ID: {auth_result['user_id']}")
        print(f"   Confidence: {auth_result['confidence']:.2f}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
