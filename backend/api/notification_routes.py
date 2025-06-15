# Backend Notification System - Build Note 2
# backend/api/notification_routes.py

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import httpx
import logging
import json
from datetime import datetime

# Notification models
class PushTokenRegistration(BaseModel):
    user_id: str
    push_token: str
    device_type: str  # 'ios' or 'android'
    device_id: str

class AutomationSettings(BaseModel):
    user_id: str
    settings: Dict[str, Any]

class PresenceNotification(BaseModel):
    user_id: str
    person: str
    sensor_id: str
    confidence: float
    timestamp: str
    location: Optional[str] = None
    heart_rate: Optional[float] = None
    heart_rate_wearable: Optional[float] = None
    source: Optional[str] = 'phone_only'

router = APIRouter()

# In-memory storage for demo (replace with database)
push_tokens: Dict[str, str] = {}
automation_settings: Dict[str, Dict[str, Any]] = {}

class NotificationService:
    """Service for handling Ring-style push notifications"""
    
    def __init__(self):
        self.expo_push_url = "https://exp.host/--/api/v2/push/send"
    
    async def send_presence_notification(self, notification: PresenceNotification) -> bool:
        """Send Ring-style presence notification to user"""
        try:
            # Get user's push token
            push_token = push_tokens.get(notification.user_id)
            if not push_token:
                logging.warning(f"No push token found for user: {notification.user_id}")
                return False
            
            # Get user's automation settings
            user_settings = automation_settings.get(notification.user_id, {})
            if not user_settings.get('pushNotificationsEnabled', True):
                logging.info(f"Push notifications disabled for user: {notification.user_id}")
                return False
            
            # Format person name for display
            person_display = notification.person.replace('_', ' ').replace('gmail com', '').replace('hmali com', '').strip()
            if not person_display:
                person_display = notification.person
            
            # Format sensor name for display  
            sensor_display = self._format_sensor_name(notification.sensor_id)
            
            # Create Ring-style notification message
            message = {
                "to": push_token,
                "title": f"🏠 {person_display} detected",
                "body": f"Recognized at {sensor_display} with {notification.confidence:.1f}% confidence",
                "data": {
                    "person": notification.person,
                    "sensor": notification.sensor_id,
                    "confidence": notification.confidence,
                    "timestamp": notification.timestamp,
                    "location": notification.location,
                    "heart_rate": notification.heart_rate,
                    "heart_rate_wearable": notification.heart_rate_wearable,
                    "source": notification.source,
                    "type": "presence_detection"
                },
                "sound": "default",
                "badge": 1,
                "priority": "high",
                "channelId": "presence_alerts"
            }
            
            # Send to Expo Push Service
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.expo_push_url,
                    json=message,
                    headers={
                        "Accept": "application/json",
                        "Accept-encoding": "gzip, deflate",
                        "Content-Type": "application/json",
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logging.info(f"✅ Ring-style notification sent to {notification.user_id}: {result}")
                    return True
                else:
                    logging.error(f"❌ Failed to send notification: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logging.error(f"❌ Error sending presence notification: {str(e)}")
            return False
    
    async def trigger_app_routine(self, notification: PresenceNotification) -> bool:
        """Execute app-based automation routine for non-HA users"""
        try:
            user_settings = automation_settings.get(notification.user_id, {})
            
            if not user_settings.get('appRoutinesEnabled', False):
                return False
            
            selected_routine = user_settings.get('selectedRoutine', 'notify_only')
            
            logging.info(f"🎯 Executing app routine '{selected_routine}' for {notification.user_id}")
            
            # Execute routine actions based on selection
            if selected_routine == 'notify_only':
                # Just send notification (already handled)
                pass
            elif selected_routine == 'notify_sound':
                # Send notification + sound instruction
                # This would be handled by the mobile app
                pass
            elif selected_routine == 'notify_haptic':
                # Send notification + haptic instruction
                pass
            elif selected_routine == 'full_routine':
                # Full routine: notification + sound + haptic
                pass
            elif selected_routine == 'webhook_custom':
                # Send to custom webhook
                webhook_url = user_settings.get('webhookUrl')
                if webhook_url:
                    await self._send_webhook(webhook_url, notification)
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Error executing app routine: {str(e)}")
            return False
    
    async def _send_webhook(self, webhook_url: str, notification: PresenceNotification):
        """Send presence event to custom webhook"""
        try:
            webhook_data = {
                "event": "presence_detected",
                "person": notification.person,
                "sensor": notification.sensor_id,
                "confidence": notification.confidence,
                "timestamp": notification.timestamp,
                "location": notification.location,
                "biometric_data": {
                    "heart_rate": notification.heart_rate,
                    "heart_rate_wearable": notification.heart_rate_wearable,
                    "source": notification.source
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook_url,
                    json=webhook_data,
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    logging.info(f"✅ Webhook sent successfully to {webhook_url}")
                else:
                    logging.warning(f"⚠️ Webhook failed: {response.status_code}")
                    
        except Exception as e:
            logging.error(f"❌ Webhook error: {str(e)}")
    
    def _format_sensor_name(self, sensor_id: str) -> str:
        """Format sensor ID for user-friendly display"""
        sensor_names = {
            'mobile_app_sensor': 'Mobile Sensor',
            'front_door_sensor': 'Front Door',
            'entryway_1': 'Entryway',
            'living_room_sensor': 'Living Room',
            'kitchen_sensor': 'Kitchen',
            'bedroom_sensor': 'Bedroom',
        }
        return sensor_names.get(sensor_id, sensor_id.replace('_', ' ').title())

# Initialize notification service
notification_service = NotificationService()

# API Endpoints
@router.post("/api/notifications/register-token")
async def register_push_token(registration: PushTokenRegistration):
    """Register user's push token for Ring-style notifications"""
    try:
        logging.info(f"📱 Registering push token for user: {registration.user_id}")
        
        # Store push token (in production, save to database)
        push_tokens[registration.user_id] = registration.push_token
        
        logging.info(f"✅ Push token registered for {registration.user_id}")
        
        return {
            "success": True,
            "message": "Push token registered successfully",
            "user_id": registration.user_id,
            "device_type": registration.device_type
        }
        
    except Exception as e:
        logging.error(f"❌ Error registering push token: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/api/automation/settings")
async def save_automation_settings(settings: AutomationSettings):
    """Save user's automation preferences"""
    try:
        logging.info(f"⚙️ Saving automation settings for user: {settings.user_id}")
        
        # Store settings (in production, save to database)
        automation_settings[settings.user_id] = settings.settings
        
        logging.info(f"✅ Automation settings saved for {settings.user_id}")
        
        return {
            "success": True,
            "message": "Automation settings saved successfully",
            "user_id": settings.user_id,
            "settings": settings.settings
        }
        
    except Exception as e:
        logging.error(f"❌ Error saving automation settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Save failed: {str(e)}")

@router.get("/api/automation/settings/{user_id}")
async def get_automation_settings(user_id: str):
    """Get user's automation preferences"""
    try:
        settings = automation_settings.get(user_id, {
            "homeAssistantEnabled": True,
            "pushNotificationsEnabled": True,
            "appRoutinesEnabled": False,
            "selectedRoutine": "notify_only",
            "soundEnabled": True,
            "hapticEnabled": True
        })
        
        return {
            "success": True,
            "user_id": user_id,
            "settings": settings
        }
        
    except Exception as e:
        logging.error(f"❌ Error getting automation settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Get failed: {str(e)}")

@router.post("/api/notifications/send-presence")
async def send_presence_notification(notification: PresenceNotification):
    """Send Ring-style presence notification (internal API)"""
    try:
        logging.info(f"🔔 Sending presence notification: {notification.person} at {notification.sensor_id}")
        
        # Send push notification
        notification_sent = await notification_service.send_presence_notification(notification)
        
        # Execute app routine if enabled
        routine_executed = await notification_service.trigger_app_routine(notification)
        
        return {
            "success": True,
            "notification_sent": notification_sent,
            "routine_executed": routine_executed,
            "person": notification.person,
            "sensor": notification.sensor_id,
            "confidence": notification.confidence
        }
        
    except Exception as e:
        logging.error(f"❌ Error sending presence notification: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Notification failed: {str(e)}")

@router.get("/api/notifications/status/{user_id}")
async def get_notification_status(user_id: str):
    """Get user's notification status"""
    try:
        has_token = user_id in push_tokens
        settings = automation_settings.get(user_id, {})
        
        return {
            "success": True,
            "user_id": user_id,
            "has_push_token": has_token,
            "notifications_enabled": settings.get('pushNotificationsEnabled', True),
            "home_assistant_enabled": settings.get('homeAssistantEnabled', True),
            "app_routines_enabled": settings.get('appRoutinesEnabled', False),
            "selected_routine": settings.get('selectedRoutine', 'notify_only')
        }
        
    except Exception as e:
        logging.error(f"❌ Error getting notification status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

# Enhanced presence event endpoint that includes notifications
@router.post("/api/presence/event-with-notifications")
async def presence_event_with_notifications(event_data: dict):
    """Enhanced presence event endpoint that triggers both MQTT and notifications"""
    try:
        logging.info(f"📡 Processing presence event with notifications: {event_data}")
        
        # Process biometric authentication (existing logic)
        # ... your existing presence event logic here ...
        
        # If authentication successful, send notification
        if event_data.get('confidence', 0) >= 0.75:  # 75% threshold
            notification = PresenceNotification(
                user_id=event_data.get('user_id', 'unknown_user'),
                person=event_data.get('user_id', 'unknown_person'),
                sensor_id=event_data.get('sensor_id', 'unknown_sensor'),
                confidence=event_data.get('confidence', 0.0) * 100,  # Convert to percentage
                timestamp=event_data.get('timestamp', datetime.now().isoformat()),
                location=event_data.get('location'),
                heart_rate=event_data.get('heart_rate'),
                heart_rate_wearable=event_data.get('heart_rate_wearable'),
                source=event_data.get('source', 'phone_only')
            )
            
            # Send Ring-style notification
            await notification_service.send_presence_notification(notification)
            
            # Execute app routine if enabled
            await notification_service.trigger_app_routine(notification)
        
        return {
            "success": True,
            "message": "Presence event processed with notifications",
            "notifications_triggered": True
        }
        
    except Exception as e:
        logging.error(f"❌ Error processing presence event with notifications: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Event processing failed: {str(e)}")

# Add these routes to your main FastAPI app
# app.include_router(router)