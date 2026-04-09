import json
from typing import Any
from sqlmodel import Session, select, or_

from app.models.stock import StockSymbol


def search_symbols(query: str, session: Session) -> list[dict]:
    """Search StockSymbol by symbol or company_name (case-insensitive)."""
    if not query:
        return [{"error": "query is required"}]
    results = session.exec(
        select(StockSymbol).where(
            or_(
                StockSymbol.symbol.ilike(f"%{query}%"),
                StockSymbol.company_name.ilike(f"%{query}%"),
            )
        ).limit(20)
    ).all()
    return [{"symbol": r.symbol, "company_name": r.company_name, "exchange": r.exchange} for r in results]


def format_response(data: Any) -> str:
    """Pretty-print a dict or list as formatted JSON string."""
    try:
        return json.dumps(data, indent=2, default=str)
    except Exception:
        return str(data)


def validate_input(params: dict, schema: dict) -> dict | None:
    """
    Validate params against schema.
    Schema format: {field_name: {"type": type, "required": bool, "min": val, "max": val}}
    Returns error dict if invalid, None if valid.
    """
    errors = []
    for field, rules in schema.items():
        value = params.get(field)
        if rules.get("required") and value is None:
            errors.append(f"'{field}' is required")
            continue
        if value is None:
            continue
        expected_type = rules.get("type")
        if expected_type and not isinstance(value, expected_type):
            errors.append(f"'{field}' must be {expected_type.__name__}, got {type(value).__name__}")
            continue
        if "min" in rules and value < rules["min"]:
            errors.append(f"'{field}' must be >= {rules['min']}")
        if "max" in rules and value > rules["max"]:
            errors.append(f"'{field}' must be <= {rules['max']}")
    return {"errors": errors} if errors else None
