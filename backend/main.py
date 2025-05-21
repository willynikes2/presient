from fastapi import FastAPI
from backend.routes import presence  # Import the new module

app = FastAPI()

# Include the presence route
app.include_router(presence.router)
