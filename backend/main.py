
from fastapi import FastAPI
from routes import sensors

app = FastAPI(title="Presient API", version="0.1.0")

# Include sensor routes
app.include_router(sensors.router, prefix="/sensors", tags=["Sensors"])

@app.get("/")
def read_root():
    return {"message": "Presient backend is running!"}
