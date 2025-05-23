# backend/utils/exceptions.py
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from fastapi import status
from pydantic import ValidationError
from fastapi.exceptions import RequestValidationError


def http_error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )


def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )


# backend/main.py (add these lines after FastAPI app initialization)
from fastapi.middleware.cors import CORSMiddleware
from backend.utils.exceptions import http_error_handler, validation_exception_handler
from fastapi.exceptions import RequestValidationError

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, http_error_handler)

# backend/routes/presence.py (example usage for custom error)
from fastapi import HTTPException

@router.post("/presence/event")
async def presence_event(event: PresenceEvent, db: Session = Depends(get_db)):
    if event.confidence < 0.5:
        raise HTTPException(
            status_code=400,
            detail="Confidence value too low to record presence event."
        )
    # continue with DB logic
