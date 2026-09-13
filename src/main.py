import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from src.database import init_db
from src.routes.triage_routes import router as triage_router
from src.routes.auth_routes import router as auth_router
from src.middleware.auth_middleware import JWTAuthMiddleware
from src.utils.error_logger import log_error_to_db

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize async database via migrations runner and seed lookup tables
    await init_db()
    yield
    # Shutdown logic (if any)

app = FastAPI(
    title="AI Request Triage Assistant",
    description="Automated business request triage, classification, priority routing & response drafting",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add JWT Authentication Middleware
app.add_middleware(JWTAuthMiddleware)

# Global Exception Handler Envelope + DB Error Logging
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    await log_error_to_db(exc)
    logger.error(f"Unhandled exception at {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."}
    )

# Mount React frontend build assets
project_root = os.path.dirname(os.path.dirname(__file__))
react_dist = os.path.join(project_root, "frontend", "dist")
react_assets = os.path.join(react_dist, "assets")

if os.path.exists(react_assets):
    app.mount("/assets", StaticFiles(directory=react_assets), name="react_assets")

@app.get("/", include_in_schema=False)
async def serve_ui():
    react_index = os.path.join(react_dist, "index.html")
    if os.path.exists(react_index):
        return FileResponse(react_index)
    return {"message": "AI Request Triage Assistant API is running. Access /docs for OpenAPI specifications."}

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

@app.get("/.well-known/{full_path:path}", include_in_schema=False)
async def well_known_probes(full_path: str):
    return Response(status_code=204)

# Register API routes
app.include_router(auth_router)
app.include_router(triage_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
