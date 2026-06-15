from fastapi import APIRouter
from backend.core.config import get_settings
from backend.models.schemas import HealthResponse

router = APIRouter(prefix='/health', tags=['health'])

@router.get('/', response_model=HealthResponse)
def health():
    cfg = get_settings()
    model = cfg.ollama_model if cfg.llm_provider == 'ollama' else cfg.openai_model
    return HealthResponse(status='ok', provider=cfg.llm_provider, model=model)
