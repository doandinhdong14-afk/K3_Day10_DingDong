from dataclasses import dataclass
import json
import logging
from pathlib import Path
import re
import time
import requests

from core.config import Settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _clean_abstract(raw_abstract: str) -> str:
    """Clean JATS XML / HTML tags from Crossref abstract."""
    if not raw_abstract:
        return ""
    cleaned = re.sub(r"<[^>]+>", " ", raw_abstract)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _format_date(date_dict: dict) -> str:
    """Format Crossref date-parts into YYYY-MM-DD string."""
    try:
        parts = date_dict.get("date-parts", [[]])[0]
        if not parts:
            return ""
        year = parts[0] if len(parts) > 0 else 2000
        month = parts[1] if len(parts) > 1 else 1
        day = parts[2] if len(parts) > 2 else 1
        return f"{year:04d}-{month:02d}-{day:02d}"
    except Exception:
        return ""


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref API payload into list of PaperRecord objects."""
    items = payload.get("message", {}).get("items", [])
    records: list[PaperRecord] = []

    for item in items:
        doi = item.get("DOI", "").strip()
        if not doi:
            continue

        # Extract title
        titles = item.get("title", [])
        title = titles[0].strip() if isinstance(titles, list) and titles else str(titles).strip()
        if not title:
            continue

        # Extract and clean abstract
        raw_abstract = item.get("abstract", "")
        summary = _clean_abstract(raw_abstract)

        # Extract authors
        authors = []
        for a in item.get("author", []):
            given = a.get("given", "").strip()
            family = a.get("family", "").strip()
            name = f"{given} {family}".strip() if given or family else a.get("name", "").strip()
            if name:
                authors.append(name)

        # Extract categories/subjects
        categories = [str(c).strip() for c in item.get("subject", []) if str(c).strip()]
        primary_category = categories[0] if categories else ""

        # Extract dates
        published = (
            _format_date(item.get("published-online", {}))
            or _format_date(item.get("published-print", {}))
            or _format_date(item.get("created", {}))
        )
        updated = _format_date(item.get("deposited", {})) or published

        # Extract URLs
        abs_url = item.get("URL", f"https://doi.org/{doi}")
        pdf_url = ""
        for link in item.get("link", []):
            if "pdf" in link.get("content-type", "").lower() or link.get("URL", "").endswith(".pdf"):
                pdf_url = link.get("URL", "")
                break

        comment = str(item.get("publisher", "")).strip()

        record = PaperRecord(
            paper_id=doi,
            title=title,
            summary=summary,
            authors=authors,
            categories=categories,
            primary_category=primary_category,
            published=published,
            updated=updated,
            abs_url=abs_url,
            pdf_url=pdf_url,
            comment=comment,
        )
        records.append(record)

    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Fetch records from Crossref API, save raw response, and return parsed PaperRecords."""
    url = "https://api.crossref.org/works"
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
    }
    headers = {
        "User-Agent": "Day10DataObservabilityLab/1.0 (mailto:student@example.com)"
    }

    max_retries = 3
    backoff = 2.0
    response_data = None

    for attempt in range(1, max_retries + 1):
        try:
            logger.info("Fetching Crossref API (attempt %d/%d)...", attempt, max_retries)
            resp = requests.get(url, params=params, headers=headers, timeout=30)
            if resp.status_code == 200:
                response_data = resp.json()
                break
            elif resp.status_code in {429, 503, 504}:
                logger.warning("HTTP %d received from Crossref API. Retrying in %.1f s...", resp.status_code, backoff)
                time.sleep(backoff)
                backoff *= 2
            else:
                resp.raise_for_status()
        except requests.RequestException as exc:
            if attempt == max_retries:
                raise RuntimeError(f"Failed to fetch Crossref data after {max_retries} attempts: {exc}") from exc
            time.sleep(backoff)
            backoff *= 2

    if not response_data:
        raise RuntimeError("Empty response received from Crossref API.")

    # Save raw API response
    raw_api_path = settings.paths.raw_api_response
    raw_api_path.parent.mkdir(parents=True, exist_ok=True)
    with open(raw_api_path, "w", encoding="utf-8") as f:
        json.dump(response_data, f, ensure_ascii=False, indent=2)
    logger.info("Saved raw API response to %s", raw_api_path)

    # Parse payload into PaperRecord list
    records = parse_crossref_payload(response_data)

    # Save raw records as JSON list
    raw_records_path = settings.paths.raw_records_json
    raw_records_path.parent.mkdir(parents=True, exist_ok=True)
    records_dict_list = [record.__dict__ for record in records]
    with open(raw_records_path, "w", encoding="utf-8") as f:
        json.dump(records_dict_list, f, ensure_ascii=False, indent=2)
    logger.info("Saved %d parsed records to %s", len(records), raw_records_path)

    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Load JSON snapshot from disk and map into list of PaperRecord objects."""
    if not path.exists():
        raise FileNotFoundError(f"Raw records file not found at {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    records = [PaperRecord(**item) for item in data]
    return records

