import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RequestTimer")


class LogRequestTimeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        process_time = time.time() - start_time
        formatted_process_time = f"{process_time:.4f}s"

        logger.info(f"{request.method} {request.url.path} - {formatted_process_time}")

        # Optionally add processing time as a header in the response
        response.headers["X-Process-Time"] = formatted_process_time

        return response
