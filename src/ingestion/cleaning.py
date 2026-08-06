from __future__ import annotations

from datetime import UTC, date, datetime

import pandas as pd

from core.utils import compact_join, normalize_whitespace, read_json
from ingestion.crossref import PaperRecord

MIN_SUMMARY_CHARS = 40
MIN_TITLE_CHARS = 8

CLEAN_COLUMNS = [
    "paper_id",
    "title",
    "summary",
    "authors_joined",
    "author_count",
    "categories_joined",
    "primary_category",
    "published",
    "updated",
    "age_days",
    "title_chars",
    "summary_chars",
    "abs_url",
    "pdf_url",
    "comment",
    "text_for_embedding",
]


def build_text_for_embedding(row) -> str:
    """Mot document text duy nhat, dung chung cho baseline/corrupted/repaired index."""
    return (
        f"Title: {row['title']}\n"
        f"Authors: {row['authors_joined']}\n"
        f"Categories: {row['categories_joined']}\n"
        f"Published: {row['published']}\n"
        f"Summary: {row['summary']}"
    )


def compute_age_days(published: str, run_date: date) -> int | None:
    """Tuoi cua record tinh bang ngay. Gia tri am = published date o tuong lai (metadata sai)."""
    try:
        return (run_date - date.fromisoformat(str(published)[:10])).days
    except ValueError:
        return None


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Chuan hoa raw records thanh dataframe san sang embed."""
    as_of = run_date.astimezone(UTC).date() if run_date.tzinfo else run_date.date()

    rows: list[dict] = []
    for record in records:
        title = normalize_whitespace(record.title)
        summary = normalize_whitespace(record.summary)
        authors = [normalize_whitespace(author) for author in record.authors if normalize_whitespace(author)]
        categories = [normalize_whitespace(category) for category in record.categories if normalize_whitespace(category)]
        published = str(record.published)[:10]
        age_days = compute_age_days(published, as_of)
        if age_days is None:
            continue  # Ngay xuat ban khong parse duoc -> khong tinh duoc freshness.

        rows.append(
            {
                "paper_id": normalize_whitespace(record.paper_id).lower(),
                "title": title,
                "summary": summary,
                "authors_joined": compact_join(authors),
                "author_count": len(authors),
                "categories_joined": compact_join(categories),
                "primary_category": categories[0] if categories else "uncategorized",
                "published": published,
                "updated": str(record.updated)[:10] or published,
                "age_days": age_days,
                "title_chars": len(title),
                "summary_chars": len(summary),
                "abs_url": record.abs_url,
                "pdf_url": record.pdf_url,
                "comment": record.comment,
            }
        )

    df = pd.DataFrame(rows, columns=[column for column in CLEAN_COLUMNS if column != "text_for_embedding"])
    if df.empty:
        raise ValueError("Khong co record nao sau khi clean. Kiem tra lai buoc ingestion.")

    # Loai bo row khong dung duoc cho retrieval.
    df = df[df["paper_id"].str.len() > 0]
    df = df[df["title_chars"] >= MIN_TITLE_CHARS]
    df = df[df["summary_chars"] >= MIN_SUMMARY_CHARS]
    df = df[df["age_days"] >= 0]  # Bo record co published date o tuong lai (forthcoming).

    df = df.drop_duplicates(subset=["paper_id"], keep="first")
    df = df.drop_duplicates(subset=["title"], keep="first")

    if df.empty:
        raise ValueError("Tat ca record deu bi loai o buoc cleaning. Kiem tra lai filter.")

    df = df.sort_values(["published", "paper_id"], ascending=[False, True]).reset_index(drop=True)
    df["text_for_embedding"] = df.apply(build_text_for_embedding, axis=1)
    return df[CLEAN_COLUMNS]


def load_clean_dataframe(path) -> pd.DataFrame:
    """Doc lai cleaned dataset tu JSON snapshot (giu nguyen kieu du lieu, khong bien '' thanh NaN)."""
    df = pd.DataFrame(read_json(path))
    for column in CLEAN_COLUMNS:
        if column not in df.columns:
            raise ValueError(f"Cleaned dataset thieu cot bat buoc: {column}")
    for column in ("age_days", "author_count", "title_chars", "summary_chars"):
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(-1).astype(int)
    for column in set(CLEAN_COLUMNS) - {"age_days", "author_count", "title_chars", "summary_chars"}:
        df[column] = df[column].fillna("").astype(str)
    return df[CLEAN_COLUMNS]
