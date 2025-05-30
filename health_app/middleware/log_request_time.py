from fastapi import Request, Response
import logging
import time
import uuid 

# Using a more specific logger name for middleware.
logger = logging.getLogger("health_app.middleware") 

async def add_process_time_header_and_log(request: Request, call_next) -> Response:
    """
    Middleware to:
    1. Generate a unique request ID.
    2. Log basic information about incoming requests and outgoing responses.
    3. Add a custom X-Process-Time header to responses indicating processing time.
    4. Add a custom X-Request-ID header to responses.
    """
    request_id = str(uuid.uuid4()) # Generate a unique ID for this request
    
    # Store request_id in request.state to make it accessible in path operations if needed
    request.state.request_id = request_id

    start_time = time.time()
    
    # Log incoming request
    log_message_request = (
        f"Incoming request: ID={request_id} - "
        f"{request.method} {request.url.path} - "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )
    # Optionally log query parameters if any
    if request.query_params:
        log_message_request += f" - Query: {request.query_params}"
    logger.info(log_message_request)

    try:
        response: Response = await call_next(request)
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Error processing request: ID={request_id} - "
            f"{request.method} {request.url.path} - Error: {e} - Processed in: {process_time:.4f}s",
            exc_info=True # Adds exception traceback to the log
        )
        # Re-raise the exception so FastAPI's error handling can take over
        raise
    else:
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        response.headers["X-Request-ID"] = request_id # Also add request ID to response headers
        
        logger.info(
            f"Outgoing response: ID={request_id} - "
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - Processed in: {process_time:.4f}s"
        )
    return response

