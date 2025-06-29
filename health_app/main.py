import logging
from logging.handlers import RotatingFileHandler
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from dotenv import load_dotenv

# Load environment variables from a .env file BEFORE importing settings
load_dotenv()

# Import settings and routers
from .config import settings
from .routers.patients_router import patients_router
# from .routers.doctors_router import doctors_router 
# from .routers.appointments_router import appointments_router
# from .routers.medical_records_router import medical_records_router
from .middleware.log_request_time import add_process_time_header_and_log
# Import the function to create DB tables
from .database.config import create_tables

# Configure Logging 
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)')
log_handler = RotatingFileHandler('app.log', maxBytes=5*1024*1024, backupCount=3)
log_handler.setFormatter(log_formatter)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.handlers = [log_handler]
module_logger = logging.getLogger(__name__)


# Lifespan Event Handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown events.
    - On startup: Creates database tables if they don't exist.
    """
    module_logger.info("Application starting up...")
    try:
        # This will create the 'patients' table and any others defined
        create_tables()
    except Exception as e:
        module_logger.critical(f"Could not connect to the database or create tables: {e}", exc_info=True)
    module_logger.info(f"Persistence mode is set to: '{settings.PERSISTENCE_MODE}'")
    
    yield
    module_logger.info("Application shutting down...")


# Create FastAPI app instance and register the lifespan handler
app = FastAPI(
    title=settings.APP_NAME,
    description="API for managing patient medical records, doctors, and appointments.",
    lifespan=lifespan
)

# Middleware
app.middleware("http")(add_process_time_header_and_log)

# Custom Exception Handlers
@app.exception_handler(RequestValidationError)
async def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
    # ... (no change)
    module_logger.error(f"Request Validation Error for {request.method} {request.url.path}: {exc.errors()}")
    serializable_errors = jsonable_encoder(exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation Error", "errors": serializable_errors},
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

# Include Routers
app.include_router(patients_router, prefix=settings.API_V1_STR)
# app.include_router(doctors_router, prefix=settings.API_V1_STR)
# app.include_router(appointments_router, prefix=settings.API_V1_STR)
# app.include_router(medical_records_router, prefix=settings.API_V1_STR)

# Root and Health Check Endpoints
@app.get("/", tags=["Root"], include_in_schema=False)
async def read_root():
    return {"message": f"Welcome to the {settings.APP_NAME} API!"}

@app.get("/health", tags=["Health Check"])
async def health_check():
    return {"status": "ok", "persistence_mode": settings.PERSISTENCE_MODE}
