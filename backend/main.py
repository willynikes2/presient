from fastapi import FastAPI
from backend.routes import presence

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

app.include_router(presence.router)
