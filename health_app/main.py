import logging
from logging.handlers import RotatingFileHandler
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

#  Import Routers and Middleware 
from .routers.patients_router import patients_router
from .routers.doctors_router import doctors_router
from .routers.appointments_router import appointments_router
from .routers.medical_records_router import medical_records_router
from .middleware.log_request_time import add_process_time_header_and_log

# Configure Logging to a File 
# Set the format for log messages
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)')

# Configure a rotating file handler to save logs to 'app.log'.
# This prevents the log file from growing indefinitely.
log_handler = RotatingFileHandler('app.log', maxBytes=5*1024*1024, backupCount=3) # 5MB per file, 3 backups
log_handler.setFormatter(log_formatter)

# Get the root logger and configure it with our file handler.
# Any logger created in other modules (like getLogger(__name__)) will inherit this.
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO) # Set the minimum level of messages to log
root_logger.handlers = [log_handler] # Replace any existing handlers with our file handler

# Create a specific logger for this module for clarity in logs
module_logger = logging.getLogger(__name__)


#  Create FastAPI app instance 
app = FastAPI(
    title="Patient Medical Record Management System",
    description="API for managing patient medical records, doctors, and appointments."
)

#  Middleware Registration 
app.middleware("http")(add_process_time_header_and_log)

#  Custom Exception Handlers 
@app.exception_handler(RequestValidationError)
async def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
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
    # This is the crucial handler for hiding internal error details from the client.
    module_logger.critical(
        f"Unhandled critical exception for {request.method} {request.url.path}: {type(exc).__name__} - {exc}",
        exc_info=True # This ensures the full stack trace is written to the log file.
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected internal server error occurred. Please contact support or check server logs."},
    )

#  Include Routers 
API_PREFIX = "/api/v1"

app.include_router(patients_router, prefix=API_PREFIX)
app.include_router(doctors_router, prefix=API_PREFIX)
app.include_router(appointments_router, prefix=API_PREFIX)
app.include_router(medical_records_router, prefix=API_PREFIX)

#  Root and Health Check Endpoints 
@app.get("/", tags=["Root"], include_in_schema=False) # Hiding from OpenAPI docs for a cleaner look
async def read_root():
    """
    Root endpoint providing a welcome message.
    """
    return {"message": "Welcome to the Patient Medical Record Management System API!"}

@app.get("/health", tags=["Health Check"])
async def health_check():
    """A simple endpoint to verify that the API is running and accessible."""
    return {"status": "ok"}
