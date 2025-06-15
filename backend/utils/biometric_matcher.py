# backend/utils/biometric_matcher.py
import sqlite3
import json
import logging
import uuid
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import statistics
import math

logger = logging.getLogger(__name__)

class SQLiteBiometricMatcher:
    """SQLite-backed biometric profile matcher for Presient MVP"""
    
    def __init__(self, db_path: str = "presient.db"):
        self.db_path = db_path
        self.tolerance_percent = 50.0  # ±15% tolerance for matching
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with biometric profiles schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create biometric profiles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS biometric_profiles (
                    id TEXT PRIMARY KEY,
                    user_id TEXT UNIQUE,
                    mean_hr REAL,
                    std_hr REAL,
                    range_hr REAL,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            
            # Create enrollment sessions table for temporary storage
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS enrollment_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    samples TEXT,
                    created_at TEXT,
                    status TEXT DEFAULT 'active'
                )
            ''')
            
            # Create authentication logs for debugging
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auth_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    live_mean_hr REAL,
                    live_std_hr REAL,
                    live_range_hr REAL,
                    matched_user_id TEXT,
                    confidence REAL,
                    status TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info(f"SQLite database initialized: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def load_profiles_from_db(self, db_path: str = None) -> Dict[str, Dict]:
        """Load all biometric profiles from database"""
        if db_path:
            self.db_path = db_path
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id, mean_hr, std_hr, range_hr, created_at 
                FROM biometric_profiles
            ''')
            
            profiles = {}
            for row in cursor.fetchall():
                user_id, mean_hr, std_hr, range_hr, created_at = row
                profiles[user_id] = {
                    "mean_hr": mean_hr,
                    "std_hr": std_hr,
                    "range_hr": range_hr,
                    "created_at": created_at
                }
            
            conn.close()
            logger.info(f"Loaded {len(profiles)} biometric profiles from database")
            return profiles
            
        except Exception as e:
            logger.error(f"Failed to load profiles from database: {e}")
            return {}
    
    def add_profile(self, user_id: str, mean_hr: float, std_hr: float, range_hr: float) -> bool:
        """Add or update a biometric profile in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            profile_id = str(uuid.uuid4())
            current_time = self._get_current_timestamp()
            
            # Use INSERT OR REPLACE to handle updates
            cursor.execute('''
                INSERT OR REPLACE INTO biometric_profiles 
                (id, user_id, mean_hr, std_hr, range_hr, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (profile_id, user_id, mean_hr, std_hr, range_hr, current_time, current_time))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Added/updated biometric profile for user: {user_id}")
            logger.debug(f"Profile stats - Mean HR: {mean_hr}, Std HR: {std_hr}, Range HR: {range_hr}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add profile for {user_id}: {e}")
            return False
    
    def match_profile(self, live_hr_values: List[float]) -> Optional[str]:
        """Match live heart rate values against stored profiles"""
        if not live_hr_values or len(live_hr_values) < 3:
            logger.warning("Insufficient heart rate data for matching")
            return None
        
        # Calculate live biometric features
        live_stats = self._calculate_hr_stats(live_hr_values)
        if not live_stats:
            logger.warning("Failed to calculate live HR stats")
            return None
        
        live_mean, live_std, live_range = live_stats
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id, mean_hr, std_hr, range_hr 
                FROM biometric_profiles
            ''')
            
            best_match = None
            best_confidence = 0.0
            
            for row in cursor.fetchall():
                user_id, stored_mean, stored_std, stored_range = row
                
                # Calculate similarity for each feature
                mean_similarity = self._calculate_similarity(live_mean, stored_mean)
                std_similarity = self._calculate_similarity(live_std, stored_std)
                range_similarity = self._calculate_similarity(live_range, stored_range)
                
                # Weighted confidence score
                confidence = (
                    mean_similarity * 0.85 +    # Mean HR is most important
                    std_similarity * 0.10 +     # Variability is secondary
                    range_similarity * 0.05     # Range is least important
                )
                
                logger.info(f"🔍 User {user_id} - Confidence: {confidence:.3f} "
                           f"(mean: {mean_similarity:.3f}, std: {std_similarity:.3f}, range: {range_similarity:.3f})")
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = user_id
            
            conn.close()
            
            # Log authentication attempt
            self._log_authentication(live_mean, live_std, live_range, best_match, best_confidence)
            
            # Return match if confidence is above threshold
            confidence_threshold = (100 - self.tolerance_percent) / 100.0
            
            if best_confidence >= confidence_threshold:
                logger.info(f"Biometric match found: {best_match} (confidence: {best_confidence:.3f})")
                return best_match
            else:
                logger.info(f"No biometric match found. Best confidence: {best_confidence:.3f} (threshold: {confidence_threshold:.3f})")
                return None
                
        except Exception as e:
            logger.error(f"Profile matching failed: {e}")
            return None
    
    def _calculate_hr_stats(self, hr_values: List[float]) -> Optional[Tuple[float, float, float]]:
        """Calculate mean, std deviation, and range from heart rate values"""
        try:
            # Filter out invalid values
            valid_values = [hr for hr in hr_values if 30 <= hr <= 220]
            
            if len(valid_values) < 3:
                logger.warning(f"Insufficient valid HR values: {len(valid_values)}/3 minimum")
                return None
            
            mean_hr = statistics.mean(valid_values)
            std_hr = statistics.stdev(valid_values) if len(valid_values) > 1 else 0.0
            range_hr = max(valid_values) - min(valid_values)
            
            return mean_hr, std_hr, range_hr
            
        except Exception as e:
            logger.error(f"Failed to calculate HR stats: {e}")
            return None
    
    def _calculate_similarity(self, live_value: float, stored_value: float) -> float:
        """Calculate similarity between live and stored values (0.0 to 1.0)"""
        if stored_value == 0:
            return 0.0
        
        # Calculate percentage difference
        diff_percent = abs(live_value - stored_value) / stored_value * 100
        
        # Convert to similarity score (inverse of difference)
        if diff_percent <= self.tolerance_percent:
            similarity = 1.0 - (diff_percent / self.tolerance_percent)
            return max(0.0, similarity)
        else:
            return 0.0
    
    def _log_authentication(self, live_mean: float, live_std: float, live_range: float, 
                          matched_user: Optional[str], confidence: float):
        """Log authentication attempt for debugging"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            status = "matched" if matched_user else "unmatched"
            
            cursor.execute('''
                INSERT INTO auth_logs 
                (timestamp, live_mean_hr, live_std_hr, live_range_hr, matched_user_id, confidence, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                self._get_current_timestamp(),
                live_mean,
                live_std, 
                live_range,
                matched_user,
                confidence,
                status
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to log authentication: {e}")
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def get_profile_count(self) -> int:
        """Get number of enrolled profiles"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM biometric_profiles')
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f"Failed to get profile count: {e}")
            return 0
    
    def delete_profile(self, user_id: str) -> bool:
        """Delete a user's biometric profile"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM biometric_profiles WHERE user_id = ?', (user_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if deleted:
                logger.info(f"Deleted biometric profile for user: {user_id}")
            else:
                logger.warning(f"No profile found for user: {user_id}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Failed to delete profile for {user_id}: {e}")
            return False
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get specific user's biometric profile"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT mean_hr, std_hr, range_hr, created_at, updated_at
                FROM biometric_profiles 
                WHERE user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                mean_hr, std_hr, range_hr, created_at, updated_at = row
                return {
                    "user_id": user_id,
                    "mean_hr": mean_hr,
                    "std_hr": std_hr,
                    "range_hr": range_hr,
                    "created_at": created_at,
                    "updated_at": updated_at
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get profile for {user_id}: {e}")
            return None

# Global matcher instance
biometric_matcher = SQLiteBiometricMatcher()

# Helper functions for easy import
def load_profiles_from_db(db_path: str = "presient.db") -> Dict[str, Dict]:
    """Load profiles from database - convenience function"""
    matcher = SQLiteBiometricMatcher(db_path)
    return matcher.load_profiles_from_db()

def match_heartbeat_profile(hr_values: List[float], db_path: str = "presient.db") -> Optional[str]:
    """Match heartbeat against profiles - convenience function"""
    matcher = SQLiteBiometricMatcher(db_path)
    return matcher.match_profile(hr_values)

def add_biometric_profile(user_id: str, mean_hr: float, std_hr: float, range_hr: float, 
                         db_path: str = "presient.db") -> bool:
    """Add biometric profile - convenience function"""
    matcher = SQLiteBiometricMatcher(db_path)
    return matcher.add_profile(user_id, mean_hr, std_hr, range_hr)