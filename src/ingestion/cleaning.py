from __future__ import annotations

from datetime import datetime

import pandas as pd

from core.utils import compact_join, normalize_whitespace
from ingestion.crossref import PaperRecord


MIN_TITLE_CHARS = 10
MIN_SUMMARY_CHARS = 80


def _parse_date(value: str) -> pd.Timestamp | None:
    """Doi chuoi ngay thanh Timestamp; hong thi tra ve None."""
    parsed = pd.to_datetime(value, errors="coerce")
    return None if pd.isna(parsed) else parsed


def _build_embedding_text(row: dict) -> str:
    """Gop cac truong quan trong thanh mot doan van ban de embed."""
    return (
        f"Title: {row['title']}\n"
        f"Authors: {row['authors_joined'] or 'unknown'}\n"
        f"Categories: {row['categories_joined'] or 'uncategorized'}\n"
        f"Published: {row['published']}\n"
        f"Summary: {row['summary']}"
    )


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    if not records:
        raise ValueError("Khong co raw record nao de lam sach.")

    run_day = run_date.date()
    rows: list[dict] = []

    for record in records:
        title = normalize_whitespace(record.title)
        summary = normalize_whitespace(record.summary)
        published = _parse_date(record.published)

        if not record.paper_id or not title or not summary or published is None:
            continue
        if len(title) < MIN_TITLE_CHARS or len(summary) < MIN_SUMMARY_CHARS:
            continue

        authors = [normalize_whitespace(a) for a in record.authors if normalize_whitespace(a)]
        categories = [normalize_whitespace(c) for c in record.categories if normalize_whitespace(c)]
        updated = _parse_date(record.updated) or published

        row = {
            "paper_id": record.paper_id.strip(),
            "title": title,
            "summary": summary,
            "authors_joined": compact_join(authors),
            "categories_joined": compact_join(categories),
            "primary_category": normalize_whitespace(record.primary_category)
            or (categories[0] if categories else "uncategorized"),
            "published": published.date().isoformat(),
            "updated": updated.date().isoformat(),
            "abs_url": normalize_whitespace(record.abs_url),
            "pdf_url": normalize_whitespace(record.pdf_url),
            "comment": normalize_whitespace(record.comment),
            "age_days": (run_day - published.date()).days,
            "author_count": len(authors),
            "title_chars": len(title),
            "summary_chars": len(summary),
        }
        row["text_for_embedding"] = _build_embedding_text(row)
        rows.append(row)

    if not rows:
        raise ValueError("Tat ca record deu bi loai sau khi lam sach. Kiem tra lai buoc ingestion.")

    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset="paper_id", keep="first")
    df = df.loc[~df["title"].str.lower().duplicated(keep="first")]
    df = df.sort_values(["published", "paper_id"], ascending=[False, True])
    return df.reset_index(drop=True)