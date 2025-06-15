#!/usr/bin/env python3
"""
Real Biometric Matcher for Presient
Statistical heart rate analysis and authentication
"""

import sqlite3
import logging
import statistics
import math
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)

@dataclass
class BiometricSample:
    """Individual biometric sample"""
    heart_rate: float
    breathing_rate: Optional[float] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass 
class BiometricProfile:
    """User biometric profile"""
    user_id: str
    name: str
    heart_rate_baseline: float
    heart_rate_range: List[float]  # [min, max]
    heart_rate_stdev: float
    breathing_rate_baseline: Optional[float] = None
    confidence_threshold: float = 0.80
    samples_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'user_id': self.user_id,
            'name': self.name,
            'heart_rate_baseline': self.heart_rate_baseline,
            'heart_rate_range': self.heart_rate_range,
            'heart_rate_stdev': self.heart_rate_stdev,
            'breathing_rate_baseline': self.breathing_rate_baseline,
            'confidence_threshold': self.confidence_threshold,
            'samples_count': self.samples_count
        }

@dataclass
class MatchResult:
    """Biometric match result"""
    user_id: str
    name: str
    confidence: float
    match_details: Dict[str, Any]
    
class RealBiometricMatcher:
    """Real biometric matching with statistical analysis"""
    
    def __init__(self, db_path: str = "presient.db"):
        self.db_path = db_path
        self.profiles: Dict[str, BiometricProfile] = {}
        self.recent_samples: List[BiometricSample] = []
        self.max_samples = 30
        
        # Initialize database
        self._init_database()
        self._load_profiles_from_db()
        
        logger.info(f"✅ Real biometric matcher initialized")
        logger.info(f"📊 Loaded {len(self.profiles)} profiles")
    
    def _init_database(self):
        """Initialize SQLite database for biometric profiles"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS biometric_profiles (
                        user_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        heart_rate_baseline REAL NOT NULL,
                        heart_rate_min REAL NOT NULL,
                        heart_rate_max REAL NOT NULL,
                        heart_rate_stdev REAL NOT NULL,
                        breathing_rate_baseline REAL,
                        confidence_threshold REAL DEFAULT 0.80,
                        samples_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS biometric_samples (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        heart_rate REAL NOT NULL,
                        breathing_rate REAL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES biometric_profiles (user_id)
                    )
                ''')
                
                conn.commit()
                logger.info(f"📊 SQLite database initialized: {self.db_path}")
                
        except Exception as e:
            logger.error(f"❌ Database initialization error: {e}")
            raise
    
    def _load_profiles_from_db(self):
        """Load biometric profiles from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_id, name, heart_rate_baseline, heart_rate_min, heart_rate_max,
                           heart_rate_stdev, breathing_rate_baseline, confidence_threshold, samples_count
                    FROM biometric_profiles
                ''')
                
                rows = cursor.fetchall()
                
                for row in rows:
                    user_id, name, baseline, hr_min, hr_max, stdev, breathing_baseline, threshold, samples = row
                    
                    profile = BiometricProfile(
                        user_id=user_id,
                        name=name,
                        heart_rate_baseline=baseline,
                        heart_rate_range=[hr_min, hr_max],
                        heart_rate_stdev=stdev,
                        breathing_rate_baseline=breathing_baseline,
                        confidence_threshold=threshold,
                        samples_count=samples
                    )
                    
                    self.profiles[user_id] = profile
                    
                logger.info(f"✅ Loaded {len(self.profiles)} biometric profiles from database")
                
        except Exception as e:
            logger.error(f"❌ Error loading profiles: {e}")
    
    def add_profile(self, profile: BiometricProfile):
        """Add or update a biometric profile"""
        try:
            self.profiles[profile.user_id] = profile
            
            # Save to database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO biometric_profiles 
                    (user_id, name, heart_rate_baseline, heart_rate_min, heart_rate_max,
                     heart_rate_stdev, breathing_rate_baseline, confidence_threshold, samples_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    profile.user_id, profile.name, profile.heart_rate_baseline,
                    profile.heart_rate_range[0], profile.heart_rate_range[1],
                    profile.heart_rate_stdev, profile.breathing_rate_baseline,
                    profile.confidence_threshold, profile.samples_count
                ))
                conn.commit()
                
            logger.info(f"✅ Added profile: {profile.name} (baseline: {profile.heart_rate_baseline:.1f} BPM)")
            
        except Exception as e:
            logger.error(f"❌ Error adding profile: {e}")
            raise
    
    def enroll_user_with_samples(self, user_id: str, name: str, samples: List[BiometricSample]) -> BiometricProfile:
        """Enroll user with collected biometric samples"""
        if len(samples) < 5:
            raise ValueError("Need at least 5 samples for enrollment")
        
        # Calculate statistics
        heart_rates = [s.heart_rate for s in samples]
        breathing_rates = [s.breathing_rate for s in samples if s.breathing_rate is not None]
        
        baseline = statistics.mean(heart_rates)
        stdev = statistics.stdev(heart_rates) if len(heart_rates) > 1 else 3.0
        hr_min = min(heart_rates)
        hr_max = max(heart_rates)
        
        # Expand range by 1 standard deviation for better matching
        expanded_min = max(40, baseline - (2 * stdev))
        expanded_max = min(180, baseline + (2 * stdev))
        
        breathing_baseline = statistics.mean(breathing_rates) if breathing_rates else None
        
        # Create profile
        profile = BiometricProfile(
            user_id=user_id,
            name=name,
            heart_rate_baseline=baseline,
            heart_rate_range=[expanded_min, expanded_max],
            heart_rate_stdev=stdev,
            breathing_rate_baseline=breathing_baseline,
            confidence_threshold=0.75,  # Lower for wider acceptance
            samples_count=len(samples)
        )
        
        # Add profile
        self.add_profile(profile)
        
        # Store sample data
        self._store_samples(user_id, samples)
        
        logger.info(f"🎯 Enrolled user: {name}")
        logger.info(f"📊 Baseline: {baseline:.1f} BPM, Range: {expanded_min:.1f}-{expanded_max:.1f}, StdDev: {stdev:.1f}")
        
        return profile
    
    def _store_samples(self, user_id: str, samples: List[BiometricSample]):
        """Store enrollment samples in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for sample in samples:
                    cursor.execute('''
                        INSERT INTO biometric_samples (user_id, heart_rate, breathing_rate, timestamp)
                        VALUES (?, ?, ?, ?)
                    ''', (user_id, sample.heart_rate, sample.breathing_rate, 
                          sample.timestamp.isoformat() if sample.timestamp else datetime.now().isoformat()))
                
                conn.commit()
                logger.info(f"💾 Stored {len(samples)} samples for {user_id}")
                
        except Exception as e:
            logger.error(f"❌ Error storing samples: {e}")
    
    def add_sample(self, sample: BiometricSample):
        """Add a real-time biometric sample"""
        self.recent_samples.append(sample)
        
        # Keep only recent samples
        if len(self.recent_samples) > self.max_samples:
            self.recent_samples.pop(0)
            
        logger.debug(f"📊 Added sample: HR {sample.heart_rate:.1f} BPM (buffer: {len(self.recent_samples)})")
    
    def get_current_biometrics(self) -> Optional[Dict[str, float]]:
        """Get current biometric readings (averaged from recent samples)"""
        if not self.recent_samples:
            return None
        
        # Use last 5 samples for current reading
        recent = self.recent_samples[-5:]
        
        heart_rates = [s.heart_rate for s in recent]
        breathing_rates = [s.breathing_rate for s in recent if s.breathing_rate is not None]
        
        current = {
            'heart_rate': statistics.mean(heart_rates),
            'sample_count': len(recent)
        }
        
        if breathing_rates:
            current['breathing_rate'] = statistics.mean(breathing_rates)
            
        return current
    
    def calculate_confidence(self, profile: BiometricProfile, current_hr: float, 
                           presence_detected: bool = False) -> float:
        """Calculate confidence score for biometric match"""
        
        # Base confidence from heart rate matching
        baseline_diff = abs(current_hr - profile.heart_rate_baseline)
        stdev = profile.heart_rate_stdev
        
        # Statistical confidence using normal distribution
        if stdev > 0:
            z_score = baseline_diff / stdev
            # Convert z-score to confidence (closer to baseline = higher confidence)
            stat_confidence = max(0, 1.0 - (z_score / 3.0))  # 3 sigma rule
        else:
            stat_confidence = 0.5
        
        # Range check confidence
        hr_min, hr_max = profile.heart_rate_range
        if hr_min <= current_hr <= hr_max:
            range_confidence = 1.0
        else:
            # How far outside the range?
            if current_hr < hr_min:
                range_penalty = (hr_min - current_hr) / profile.heart_rate_stdev
            else:
                range_penalty = (current_hr - hr_max) / profile.heart_rate_stdev
            range_confidence = max(0, 1.0 - (range_penalty / 2.0))
        
        # Combine confidences
        base_confidence = (stat_confidence * 0.6) + (range_confidence * 0.4)
        
        # Presence detection boost
        if presence_detected:
            base_confidence = min(1.0, base_confidence * 1.1)
        
        # Sample count boost (more recent samples = higher confidence)
        sample_boost = min(0.05, len(self.recent_samples) * 0.002)
        final_confidence = min(1.0, base_confidence + sample_boost)
        
        return final_confidence
    
    def find_best_match(self, presence_detected: bool = False) -> Optional[MatchResult]:
        """Find best biometric match from recent samples"""
        
        current = self.get_current_biometrics()
        if not current:
            logger.debug("🤔 No recent samples for matching")
            return None
        
        current_hr = current['heart_rate']
        
        # Check against all profiles
        best_match = None
        best_confidence = 0.0
        
        for user_id, profile in self.profiles.items():
            confidence = self.calculate_confidence(profile, current_hr, presence_detected)
            
            logger.debug(f"🎯 {profile.name}: {confidence:.2%} (HR: {current_hr:.1f}, baseline: {profile.heart_rate_baseline:.1f})")
            
            if confidence > best_confidence and confidence >= profile.confidence_threshold:
                best_confidence = confidence
                best_match = MatchResult(
                    user_id=user_id,
                    name=profile.name,
                    confidence=confidence,
                    match_details={
                        'current_heart_rate': current_hr,
                        'baseline_heart_rate': profile.heart_rate_baseline,
                        'heart_rate_stdev': profile.heart_rate_stdev,
                        'presence_detected': presence_detected,
                        'sample_count': current['sample_count'],
                        'timestamp': datetime.now().isoformat()
                    }
                )
        
        if best_match:
            logger.info(f"🎯 Best match: {best_match.name} ({best_match.confidence:.1%})")
        else:
            logger.debug(f"🤔 No confident match for HR: {current_hr:.1f} BPM")
        
        return best_match
    
    def get_all_profiles(self) -> List[BiometricProfile]:
        """Get all enrolled profiles"""
        return list(self.profiles.values())
    
    def clear_profiles(self):
        """Clear all profiles (for testing/reset)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM biometric_samples')
                cursor.execute('DELETE FROM biometric_profiles')
                conn.commit()
                
            self.profiles.clear()
            self.recent_samples.clear()
            
            logger.info("🗑️ Cleared all biometric profiles and samples")
            
        except Exception as e:
            logger.error(f"❌ Error clearing profiles: {e}")
            raise