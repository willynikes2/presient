
from fastapi import APIRouter

router = APIRouter()

@router.post("/trigger")
def trigger_routine(data: dict):
    # Stub for automation call
    return {"triggered": True, "data": data}
