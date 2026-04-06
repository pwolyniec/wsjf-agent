"""tools/ingest.py — Auto-detect and normalize backlog input to a DataFrame."""
from __future__ import annotations
import re, io
import pandas as pd
import httpx
from pathlib import Path

REQUIRED_COLS = {"id", "name", "description"}
COL_ALIASES = {
    "title": "name", "summary": "name", "story": "name",
    "feature_name": "name",
    "details": "description", "body": "description", "acceptance_criteria": "description",
    "ticket": "id", "key": "id", "item_id": "id",
    "feature_id": "id",
    "job_duration": "job_size",
    "risk_reduction_/_opportunity_enablement": "risk_reduction",
}

def ingest(source: str) -> pd.DataFrame:
    raw = _load_raw(source)
    df = _parse(raw, source)
    df = _normalize_columns(df)
    _validate(df)
    df["id"] = df["id"].astype(str).str.strip()
    df["description"] = df["description"].fillna("").str.strip()
    return df

def _load_raw(source: str) -> bytes | str:
    if source.startswith("http://") or source.startswith("https://"):
        r = httpx.get(source, follow_redirects=True, timeout=15)
        r.raise_for_status()
        return r.content
    return Path(source).read_bytes()

def _parse(raw: bytes | str, source: str) -> pd.DataFrame:
    src = source.lower()
    if src.endswith(".xlsx") or src.endswith(".xls"):
        return pd.read_excel(io.BytesIO(raw))
    if src.endswith(".csv") or _looks_like_csv(raw):
        text = raw.decode() if isinstance(raw, bytes) else raw
        return pd.read_csv(io.StringIO(text))
    # Fallback: try CSV, then plain text
    try:
        text = raw.decode() if isinstance(raw, bytes) else raw
        return pd.read_csv(io.StringIO(text))
    except Exception:
        return _parse_plaintext(raw.decode() if isinstance(raw, bytes) else raw)

def _looks_like_csv(raw: bytes | str) -> bool:
    sample = (raw[:500].decode(errors="ignore") if isinstance(raw, bytes) else raw[:500])
    return sample.count(",") > sample.count("\t") * 2

def _parse_plaintext(text: str) -> pd.DataFrame:
    """Each line becomes a description; IDs are auto-assigned."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return pd.DataFrame({"id": range(1, len(lines)+1), "name": lines, "description": lines})

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    for alias, canonical in COL_ALIASES.items():
        if alias in df.columns and canonical not in df.columns:
            df = df.rename(columns={alias: canonical})
    return df

def _validate(df: pd.DataFrame):
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        # Try to infer: if only one text column, treat it as description
        if len(df.columns) == 1:
            df["id"] = range(1, len(df)+1)
            df["name"] = df.iloc[:, 0]
            df["description"] = df.iloc[:, 0]
        else:
            raise ValueError(f"Missing required columns: {missing}. Available: {list(df.columns)}")