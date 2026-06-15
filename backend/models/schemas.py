from pydantic import BaseModel, Field
from typing import Any

class HealthResponse(BaseModel):
    status: str
    provider: str
    model: str

class ExtractedDocument(BaseModel):
    document_id: str
    filename: str
    document_type: str = 'unknown'
    raw_text: str
    fields: dict[str, Any] = Field(default_factory=dict)
    validation: list[str] = Field(default_factory=list)

class AnalyzeResponse(BaseModel):
    document: ExtractedDocument
