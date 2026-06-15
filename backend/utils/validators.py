from typing import Any

def validate_fields(document_type: str, fields: dict[str, Any]) -> list[str]:
    notes: list[str] = []
    total = _to_float(fields.get('total'))
    subtotal = _to_float(fields.get('subtotal'))
    tax = _to_float(fields.get('tax'))
    if total is not None and subtotal is not None and tax is not None:
        if abs((subtotal + tax) - total) > 0.05:
            notes.append('Subtotal + tax does not match total.')
        else:
            notes.append('Invoice/receipt arithmetic check passed.')
    if document_type in {'invoice','receipt'} and total is None:
        notes.append('Total amount could not be confidently identified.')
    return notes

def _to_float(value: Any) -> float | None:
    if value is None: return None
    try:
        return float(str(value).replace('$','').replace(',','').strip())
    except ValueError:
        return None
