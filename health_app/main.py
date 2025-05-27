import logging

from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware # Optional
from fastapi.encoders import jsonable_encoder


from dotenv import load_dotenv
load_dotenv() # Loads variables from .env into environment variables


# --- Import Routers ---
from .routers.patients_router import patients_router
from .routers.doctors_router import doctors_router
from .routers.appointments_router import appointments_router
from .routers.medical_records_router import medical_records_router

# --- Import Middleware ---
from .middleware.log_request_time import add_process_time_header_and_log

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
module_logger = logging.getLogger("health_app.main")

# --- Create FastAPI app instance ---
app = FastAPI(
    title="Patient Medical Record Management System",
    description="API for managing patient medical records, doctors, and appointments. "      
)

# --- Middleware Registration ---
app.middleware("http")(add_process_time_header_and_log)

# --- Custom Exception Handlers ---
@app.exception_handler(RequestValidationError)
async def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
    module_logger.error(f"Request Validation Error for {request.method} {request.url.path}: {exc.errors()}")
    # Use jsonable_encoder to ensure all parts of exc.errors() are serializable
    serializable_errors = jsonable_encoder(exc.errors()) # <--- USE jsonable_encoder HERE
    response_content = {"detail": "Validation Error", "errors": serializable_errors}
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_content,
    )

@app.exception_handler(HTTPException) 
async def fastapi_http_exception_handler(request: Request, exc: HTTPException):
    module_logger.error(
        f"HTTPException caught for {request.method} {request.url.path}: "
        f"Status={exc.status_code}, Detail='{exc.detail}'"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}, 
        headers=exc.headers, 
    )

@app.exception_handler(Exception) 
async def generic_exception_handler(request: Request, exc: Exception):
    module_logger.critical(
        f"Unhandled critical exception for {request.method} {request.url.path}: {type(exc).__name__} - {exc}", 
        exc_info=True 
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected internal server error occurred. Please contact support or check server logs."},
    )

# --- Include Routers ---
API_PREFIX = "/api/v1"

app.include_router(patients_router, prefix=API_PREFIX)
app.include_router(doctors_router, prefix=API_PREFIX)
app.include_router(appointments_router, prefix=API_PREFIX)
app.include_router(medical_records_router, prefix=API_PREFIX)

# --- Root Endpoint ---
@app.get("/", tags=["Root"], summary="Root Endpoint")
async def read_root():
    """
    Root endpoint providing a welcome message and links to the API documentation.
    """
    return {
        "message": "Welcome to the Patient Medical Record Management System API!",
    }