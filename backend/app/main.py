"""
FastAPI application factory and configuration.
Main entry point for the backend server.
"""

import logging
import time
from fastapi import FastAPI, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import settings, get_available_models_formatted
from app.core.database import connect_to_mongo, close_mongo_connection, create_indexes
from app.core.logging import setup_logging
from app.api.endpoints import auth, resume, interview, interviews, analytics, answer_lab, coding, career_intelligence, settings as settings_endpoint, notifications as notifications_endpoint, practice_center, coach
from app.api.dependencies import get_current_user
from app.services.notification_service import ensure_notifications_indexes
from app.services.scheduler import shutdown_scheduler, start_scheduler

# Bootstrap structured logging before anything else
setup_logging("DEBUG" if settings.DEBUG else "INFO")
logger = logging.getLogger(__name__)

# Rate limiter (key = client IP)
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"])

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="CareerIQ - AI-powered interview preparation platform"
)

# Attach limiter to app state so slowapi middleware can find it
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_origin_regex=settings.get_cors_origin_regex(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ============= LIFESPAN EVENTS =============

@app.on_event("startup")
async def startup_event():
    logger.info("Starting %s v%s (debug=%s)", settings.APP_NAME, settings.APP_VERSION, settings.DEBUG)
    logger.info("CORS origins: %s", settings.get_cors_origins())
    if settings.OPENROUTER_API_KEY:
        logger.info("OpenRouter configured (%s***)", settings.OPENROUTER_API_KEY[:10])
    else:
        logger.warning("OPENROUTER_API_KEY not set — interview evaluation will use fallback")
    await connect_to_mongo()
    create_indexes()
    ensure_notifications_indexes()
    start_scheduler()
    logger.info("Startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down %s", settings.APP_NAME)
    shutdown_scheduler()
    await close_mongo_connection()


# ============= GLOBAL ERROR HANDLERS =============

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning("HTTP %s on %s -- %s", exc.status_code, request.url.path, exc.detail)
    detail = exc.detail
    if isinstance(detail, dict):
        message = detail.get("message") or detail.get("detail") or str(detail)
    else:
        message = str(detail) if detail else "An error occurred"
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": message}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first = errors[0] if errors else {}
    locs = first.get("loc", [])[1:]
    field = " -> ".join(str(loc) for loc in locs)
    msg = first.get("msg", "Validation error")
    message = f"{field}: {msg}" if field else msg
    logger.warning("Validation error on %s -- %s", request.url.path, message)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"success": False, "error": message, "details": errors}
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"success": False, "error": "Internal server error. Please try again later."}
    )


# ============= REQUEST LOGGING MIDDLEWARE =============

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    logger.info("%s %s -> %s (%.0fms)", request.method, request.url.path, response.status_code, elapsed)
    return response


# ============= HEALTH CHECK =============

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "success": True,
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@app.get("/test-openrouter")
async def test_openrouter():
    """Test OpenRouter API connection and configuration."""
    from openai import OpenAI
    result = {
        "openrouter_configured": False,
        "api_key_set": bool(settings.OPENROUTER_API_KEY),
        "test_call_success": False,
        "error": None
    }
    if not result["api_key_set"]:
        result["error"] = "OPENROUTER_API_KEY not set in environment"
        return result
    try:
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=settings.OPENROUTER_API_KEY)
        result["openrouter_configured"] = True
        try:
            resp = client.chat.completions.create(
                model=settings.OPENROUTER_MODEL_NAME,
                messages=[{"role": "user", "content": "Return JSON: {test: success}"}]
            )
            result["test_call_success"] = bool(resp.choices[0].message.content)
        except Exception as e:
            available = get_available_models_formatted()
            result["error"] = f"Model unavailable: {e}. Available: {available}"
    except Exception as e:
        result["error"] = str(e)
    return result


# ============= API ROUTES =============

app.include_router(auth.router)
app.include_router(resume.router, dependencies=[Depends(get_current_user)])
app.include_router(interview.router, dependencies=[Depends(get_current_user)])
app.include_router(interviews.router, dependencies=[Depends(get_current_user)])
app.include_router(analytics.router, dependencies=[Depends(get_current_user)])
app.include_router(career_intelligence.router, dependencies=[Depends(get_current_user)])
app.include_router(settings_endpoint.router, dependencies=[Depends(get_current_user)])
app.include_router(notifications_endpoint.router, dependencies=[Depends(get_current_user)])
app.include_router(practice_center.router, dependencies=[Depends(get_current_user)])
app.include_router(coach.router, dependencies=[Depends(get_current_user)])
app.include_router(answer_lab.router, dependencies=[Depends(get_current_user)])
app.include_router(coding.router, dependencies=[Depends(get_current_user)])


# ============= ROOT ENDPOINT =============

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "success": True,
        "message": "Welcome to CareerIQ API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)