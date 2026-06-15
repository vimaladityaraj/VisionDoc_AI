from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.health import router as health_router
from backend.api.documents import router as documents_router

app = FastAPI(title='VisionDoc AI', description='OCR + LLM document intelligence platform', version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
app.include_router(health_router)
app.include_router(documents_router)
