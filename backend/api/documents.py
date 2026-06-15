"""Document analysis API routes."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.core.config import get_settings
from backend.core.llm_client import LLMClient
from backend.models.schemas import AnalyzeResponse, ExtractedDocument
from backend.storage.document_store import DocumentStore
from backend.utils.ocr import SUPPORTED_EXTS, extract_text
from backend.utils.validators import validate_fields

router = APIRouter(prefix="/documents", tags=["documents"])

MAX_UPLOAD_BYTES = 15 * 1024 * 1024


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_document(file: UploadFile = File(...)) -> AnalyzeResponse:
    """Upload a PDF/image, run OCR, extract structured fields, and persist the result."""
    cfg = get_settings()
    filename = Path(file.filename or "upload").name
    ext = Path(filename).suffix.lower()

    if ext not in SUPPORTED_EXTS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}. Supported: {sorted(SUPPORTED_EXTS)}")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File is too large. Maximum supported size is 15 MB.")

    target_path = cfg.upload_path / filename
    target_path.write_bytes(content)

    try:
        raw_text = extract_text(target_path)
        if not raw_text.strip():
            raise HTTPException(
                status_code=422,
                detail="No readable text found. Check Tesseract installation or upload a clearer document.",
            )

        extraction = LLMClient().analyze(raw_text)
        doc_type = extraction.get("document_type", "unknown")
        fields = extraction.get("fields", {}) or {}
        validation = validate_fields(doc_type, fields)

        payload = {
            "document_type": doc_type,
            "raw_text": raw_text,
            "fields": fields,
            "validation": validation,
        }
        doc_id = DocumentStore().save(filename, payload)
        return AnalyzeResponse(document=ExtractedDocument(document_id=doc_id, filename=filename, **payload))
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001 - API should return readable errors for portfolio/demo usage
        raise HTTPException(status_code=500, detail=f"Document analysis failed: {exc}") from exc


@router.get("/")
def list_documents() -> list[dict]:
    """List previously analyzed documents."""
    return DocumentStore().list_documents()


@router.get("/{doc_id}")
def get_document(doc_id: str) -> dict:
    """Return a stored document analysis by ID."""
    try:
        return DocumentStore().read(doc_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Document not found") from exc
