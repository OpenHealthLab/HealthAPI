import time
import uuid
import json
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.concurrency import iterate_in_threadpool
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        request_id = str(uuid.uuid4())

        headers = dict(request.headers)
        if "authorization" in headers:
            headers["authorization"] = "***MASKED***"
            
        logger.info(f"Incoming Request: {request.method} {request.url.path} | ID: {request_id} | Headers: {headers}")

        try:
            response = await call_next(request)
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.error(f"Request Failed: {e} | Time: {process_time:.2f}ms")
            raise e

        process_time = (time.time() - start_time) * 1000
        
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)

        logger.info(
            f"Response Sent: Status {response.status_code} | "
            f"Time: {process_time:.2f}ms | "
            f"ID: {request_id}"
        )

        return response