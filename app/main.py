from contextlib import asynccontextmanager
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import open_pool, close_pool, init_database
from app.routes import ai_cv, auth, platform

@asynccontextmanager
async def lifespan(_app:FastAPI):
    open_pool(); init_database()
    try: yield
    finally: close_pool()

app=FastAPI(title=settings.app_name,version="3.0.0",description="Makwande Careers PostgreSQL backend with AI CV Builder",lifespan=lifespan,swagger_ui_parameters={"persistAuthorization":True,"displayRequestDuration":True,"filter":True})
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origins,allow_credentials=True,allow_methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"],allow_headers=["Authorization","Content-Type","X-Request-ID"])

@app.middleware("http")
async def headers(request:Request,call_next):
    response=await call_next(request)
    response.headers["X-Request-ID"]=request.headers.get("X-Request-ID",str(uuid4()))
    response.headers["X-Content-Type-Options"]="nosniff"
    response.headers["X-Frame-Options"]="DENY"
    response.headers["Referrer-Policy"]="strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"]="camera=(), microphone=(), geolocation=()"
    return response

@app.get("/",tags=["System"])
def root(): return {"name":settings.app_name,"version":"3.0.0","status":"live","docs":"/docs","health":"/health"}

@app.get("/health",tags=["System"])
def health(): return {"status":"ok","service":settings.app_name,"version":"3.0.0"}

app.include_router(auth.router,prefix="/api")
app.include_router(platform.router,prefix="/api")
app.include_router(ai_cv.router,prefix="/api")
