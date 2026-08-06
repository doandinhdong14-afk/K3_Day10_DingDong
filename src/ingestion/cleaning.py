from datetime import UTC, datetime
import re
import pandas as pd

from ingestion.crossref import PaperRecord


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw records into a standardized DataFrame ready for embedding and indexing."""
    if not records:
        return pd.DataFrame(
            columns=[
                "paper_id",
                "title",
                "summary",
                "authors",
                "categories",
                "primary_category",
                "published",
                "updated",
                "abs_url",
                "pdf_url",
                "comment",
                "authors_joined",
                "categories_joined",
                "summary_chars",
                "age_days",
                "text_for_embedding",
            ]
        )

    data = []
    run_date_naive = run_date.astimezone(UTC).replace(tzinfo=None) if run_date.tzinfo else run_date

    for r in records:
        paper_id = (r.paper_id or "").strip()
        title = (r.title or "").strip()
        summary = (r.summary or "").strip()

        # Filter out bad/invalid rows
        if not paper_id or not title or len(title) < 3 or not summary or len(summary) < 10:
            continue

        # Clean whitespace
        title = re.sub(r"\s+", " ", title)
        summary = re.sub(r"\s+", " ", summary)

        authors = r.authors if isinstance(r.authors, list) else []
        categories = r.categories if isinstance(r.categories, list) else []
        primary_category = (r.primary_category or (categories[0] if categories else "")).strip()

        published_str = (r.published or "").strip()
        updated_str = (r.updated or published_str).strip()

        # Date parsing and freshness calculation
        try:
            pub_dt = pd.to_datetime(published_str, errors="coerce")
            if pd.isna(pub_dt):
                pub_dt = pd.Timestamp(run_date_naive)
                published_str = pub_dt.strftime("%Y-%m-%d")
        except Exception:
            pub_dt = pd.Timestamp(run_date_naive)
            published_str = pub_dt.strftime("%Y-%m-%d")

        pub_dt_naive = pub_dt.tz_localize(None) if pub_dt.tzinfo else pub_dt
        age_days = max(0, (run_date_naive - pub_dt_naive).days)

        authors_joined = ", ".join(authors) if authors else "Unknown"
        categories_joined = ", ".join(categories) if categories else "Uncategorized"
        summary_chars = len(summary)

        text_for_embedding = (
            f"Title: {title}\n"
            f"Summary: {summary}\n"
            f"Authors: {authors_joined}\n"
            f"Categories: {categories_joined}"
        )

        data.append(
            {
                "paper_id": paper_id,
                "title": title,
                "summary": summary,
                "authors": authors,
                "categories": categories,
                "primary_category": primary_category,
                "published": published_str,
                "updated": updated_str,
                "abs_url": (r.abs_url or f"https://doi.org/{paper_id}").strip(),
                "pdf_url": (r.pdf_url or "").strip(),
                "comment": (r.comment or "").strip(),
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "summary_chars": summary_chars,
                "age_days": age_days,
                "text_for_embedding": text_for_embedding,
            }
        )

    df = pd.DataFrame(data)
    if df.empty:
        return df

    # Remove duplicates
    df = df.drop_duplicates(subset=["paper_id"], keep="first")
    df = df.drop_duplicates(subset=["title"], keep="first")

    # Sort descending by publication date
    df = df.sort_values(by=["published", "paper_id"], ascending=[False, True]).reset_index(drop=True)

    return df

