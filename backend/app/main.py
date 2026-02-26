"""
FastAPI application factory and configuration.
Main entry point for the backend server.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings, get_available_models_formatted
from app.core.database import connect_to_mongo, close_mongo_connection
from app.api.endpoints import auth, resume, interview, interviews, analytics, answer_lab, coding, career_intelligence, settings as settings_endpoint
from app.api.dependencies import get_current_user

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered Virtual Interviewer Platform"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=getattr(settings, "CORS_ORIGIN_REGEX", None),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ============= LIFESPAN EVENTS =============

@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    print("[STARTUP] Starting AI Virtual Interviewer Backend")
    print(f"   - App: {settings.APP_NAME}")
    print(f"   - Version: {settings.APP_VERSION}")
    print(f"   - Debug: {settings.DEBUG}")
    
    # Check OpenRouter
    if settings.OPENROUTER_API_KEY:
        api_key_short = settings.OPENROUTER_API_KEY[:10] + "***"
        print(f"   - OpenRouter API Key: {api_key_short}")
    else:
        print(f"   - [WARNING] OPENROUTER_API_KEY not set! Interview evaluation will fail.")
    
    await connect_to_mongo()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("🛑 Shutting down backend")
    await close_mongo_connection()


# ============= HEALTH CHECK =============

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
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
        "api_key_set": False,
        "test_call_success": False,
        "error": None
    }
    
    # Check API key
    result["api_key_set"] = bool(settings.OPENROUTER_API_KEY)
    
    if not result["api_key_set"]:
        result["error"] = "OPENROUTER_API_KEY not set in environment"
        return result
    
    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPENROUTER_API_KEY
        )
        result["openrouter_configured"] = True
        
        # Try using configured model name
        try:
            response = client.chat.completions.create(
                model=settings.OPENROUTER_MODEL_NAME,
                messages=[{"role": "user", "content": 'Return JSON: {"test": "success"}'}]
            )
            result["test_call_success"] = bool(response.choices[0].message.content)
        except Exception as e:
            # Try listing models to provide a helpful error message
            available_models = get_available_models_formatted()
            result["error"] = f"Model '{settings.OPENROUTER_MODEL_NAME}' unavailable: {e}. Available models: {available_models}"
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


# ============= API ROUTES =============

# Include routers
app.include_router(auth.router)
app.include_router(resume.router, dependencies=[Depends(get_current_user)])
app.include_router(interview.router, dependencies=[Depends(get_current_user)])
app.include_router(interviews.router, dependencies=[Depends(get_current_user)])
app.include_router(analytics.router, dependencies=[Depends(get_current_user)])
app.include_router(career_intelligence.router, dependencies=[Depends(get_current_user)])
app.include_router(settings_endpoint.router, dependencies=[Depends(get_current_user)])
app.include_router(answer_lab.router, dependencies=[Depends(get_current_user)])
app.include_router(coding.router, dependencies=[Depends(get_current_user)])


# ============= ROOT ENDPOINT =============

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to AI Virtual Interviewer API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


# ============= ERROR HANDLERS =============

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
