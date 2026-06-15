"""Simple JSON-backed persistence for analyzed documents."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from backend.core.config import get_settings


class DocumentStore:
    """Stores each extraction result as one JSON file."""

    def __init__(self) -> None:
        self.cfg = get_settings()

    def save(self, filename: str, payload: dict) -> str:
        doc_id = str(uuid.uuid4())
        output_path = self.cfg.output_path / f"{doc_id}.json"
        record = {
            "document_id": doc_id,
            "filename": filename,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **payload,
        }
        output_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
        return doc_id

    def list_documents(self) -> list[dict]:
        records: list[dict] = []
        for path in sorted(self.cfg.output_path.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
            data = json.loads(path.read_text(encoding="utf-8"))
            records.append(
                {
                    "document_id": data.get("document_id"),
                    "filename": data.get("filename"),
                    "document_type": data.get("document_type"),
                    "created_at": data.get("created_at"),
                }
            )
        return records

    def read(self, doc_id: str) -> dict:
        return json.loads((self.cfg.output_path / f"{doc_id}.json").read_text(encoding="utf-8"))
