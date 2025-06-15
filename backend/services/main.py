# main.py

import logging
import sys
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Configure logging to stdout first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment and app components
import os
from dotenv import load_dotenv
load_dotenv()

from backend.db import engine, Base
from backend.services.mqtt import initialize_mqtt, shutdown_mqtt, mqtt_publisher
from backend.utils.biometric_matcher import SQLiteBiometricMatcher
from backend.utils.biometric_matcher import load_profiles_from_db

# Optional MR60BHA2 MQTT sensor integration
try:
    from backend.services import mqtt_subscriber

    startup_mr60bha2_integration = mqtt_subscriber.startup_mr60bha2_integration
    shutdown_mr60bha2_integration = mqtt_subscriber.shutdown_mr60bha2_integration
    get_mr60bha2_status = mqtt_subscriber.get_mr60bha2_status

    MR60BHA2_AVAILABLE = True
    logger.info("📡 MR60BHA2 integration module loaded successfully")
except ImportError as e:
    logger.warning(f"📡 MR60BHA2 integration not available: {e}")
    MR60BHA2_AVAILABLE = False

    async def startup_mr60bha2_integration(*args, **kwargs): return False
    async def shutdown_mr60bha2_integration(): pass
    def get_mr60bha2_status(): return {"connected": False}

# Global state
biometric_matcher: SQLiteBiometricMatcher = None
biometric_profiles = {}

# FastAPI lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Presient API starting up...")

    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready!")

    # Initialize biometric system
    await startup_biometric_system()

    # Initialize MQTT
    await initialize_mqtt()

    # Initialize MR60BHA2 if available
    if MR60BHA2_AVAILABLE:
        try:
            await startup_mr60bha2_integration()
            logger.info("📡 MR60BHA2 sensor integration initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize MR60BHA2 integration: {e}")

    yield

    logger.info("🛑 Presient API shutting down...")
    await shutdown_biometric_system()
    await shutdown_mqtt()
    if MR60BHA2_AVAILABLE:
        await shutdown_mr60bha2_integration()

async def startup_biometric_system():
    global biometric_matcher, biometric_profiles
    try:
        db_path = os.getenv("PRESIENT_DB_PATH", "presient.db")
        logger.info(f"📊 Initializing biometric database: {db_path}")
        biometric_matcher = SQLiteBiometricMatcher(db_path)
        biometric_profiles = biometric_matcher.load_profiles_from_db()
        logger.info(f"✅ Loaded {len(biometric_profiles)} biometric profiles")
        logger.info(f"👥 Enrolled users: {', '.join(biometric_profiles.keys())}")
        logger.info(f"🔍 Database integrity check: {biometric_matcher.get_profile_count()} profiles in DB")
    except Exception as e:
        logger.error(f"❌ Failed to initialize biometric system: {e}")
        biometric_matcher = None
        biometric_profiles = {}

async def shutdown_biometric_system():
    global biometric_matcher, biometric_profiles
    biometric_matcher = None
    biometric_profiles = {}
    logger.info("💾 Biometric system shutdown complete")

# App instance
app = FastAPI(
    title="Presient API",
    version="1.0",
    lifespan=lifespan
)

# Test route
@app.get("/")
async def root():
    return {
        "status": "ok",
        "mr60bha2": get_mr60bha2_status(),
        "profiles_loaded": len(biometric_profiles)
    }
