from fastapi import FastAPI
from backend.db import engine, Base

# Import all your models so they're registered with Base
import backend.models.profile
import backend.models.presence_events
from backend.routes import presence, profiles

# Create tables on startup
Base.metadata.create_all(bind=engine)


app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}
app.include_router(presence.router)
app.include_router(profiles.router)
