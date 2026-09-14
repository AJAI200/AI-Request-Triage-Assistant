import hmac
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.services.auth_service import decode_access_token
from src.utils.exceptions import AuthenticationError
from src.settings import settings

logger = logging.getLogger("triage_assistant.auth_middleware")

PUBLIC_PATHS = {"/", "/favicon.ico", "/docs", "/openapi.json", "/auth/login", "/auth/register", "/redoc"}

class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.debug(f"Entering JWTAuthMiddleware.dispatch for {request.method} {request.url.path}")
        start_time = time.time()
        path = request.url.path

        # Bypass public static assets, devtools probes, and auth endpoints
        if path in PUBLIC_PATHS or path.startswith("/assets/") or path.startswith("/.well-known/"):
            response = await call_next(request)
            process_time_ms = round((time.time() - start_time) * 1000, 2)
            response.headers["X-Process-Time"] = f"{process_time_ms}ms"
            logger.info(f"Public request {request.method} {path} processed in {process_time_ms}ms with status {response.status_code}")
            return response

        # Check Authorization header (Bearer token) or X-API-Key header fallback
        auth_header = request.headers.get("Authorization")
        api_key_header = request.headers.get("X-API-Key")

        user_info = None

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                user_info = decode_access_token(token)
            except AuthenticationError as exc:
                process_time_ms = round((time.time() - start_time) * 1000, 2)
                logger.warning(f"Auth failed for {path}: {exc}")
                res = JSONResponse(status_code=401, content={"detail": str(exc)})
                res.headers["X-Process-Time"] = f"{process_time_ms}ms"
                return res
        elif api_key_header:
            expected_key = settings.API_KEY
            if expected_key and hmac.compare_digest(api_key_header.encode('utf-8'), expected_key.encode('utf-8')):
                user_info = {"sub": "api_client", "username": "api_key_client", "role": "admin"}
            else:
                process_time_ms = round((time.time() - start_time) * 1000, 2)
                logger.warning(f"Invalid API Key header provided for {path}")
                res = JSONResponse(status_code=401, content={"detail": "Invalid X-API-Key header"})
                res.headers["X-Process-Time"] = f"{process_time_ms}ms"
                return res
        else:
            process_time_ms = round((time.time() - start_time) * 1000, 2)
            logger.warning(f"Missing auth headers for {path}")
            res = JSONResponse(status_code=401, content={"detail": "Missing Authorization header or X-API-Key header"})
            res.headers["X-Process-Time"] = f"{process_time_ms}ms"
            return res

        request.state.user = user_info
        response = await call_next(request)
        process_time_ms = round((time.time() - start_time) * 1000, 2)
        request.state.process_time_ms = process_time_ms
        response.headers["X-Process-Time"] = f"{process_time_ms}ms"
        logger.info(f"Authenticated request {request.method} {path} processed in {process_time_ms}ms with status {response.status_code}")
        return response
