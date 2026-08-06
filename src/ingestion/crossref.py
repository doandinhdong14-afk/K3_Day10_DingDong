from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from html import unescape
from pathlib import Path
import os
import re
import time
from typing import Any

import requests

from core.config import Settings
from core.utils import compact_join, normalize_whitespace, read_json, write_json

CROSSREF_API_URL = "https://api.crossref.org/works"

RETRY_STATUS_CODES = {429, 500, 502, 503, 504}
MAX_ATTEMPTS = 5
BACKOFF_SECONDS = 2.0
REQUEST_TIMEOUT = 30

_TAG_PATTERN = re.compile(r"<[^>]+>")
# JATS abstract thuong mo dau bang <jats:title>Abstract</jats:title> hoac Summary.
_ABSTRACT_LABEL_PATTERN = re.compile(r"^\s*(abstract|summary)\b[:\s]*", flags=re.IGNORECASE)


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


def _strip_markup(value: str) -> str:
    """Crossref tra abstract duoi dang JATS XML, can bo tag truoc khi embed."""
    without_tags = _TAG_PATTERN.sub(" ", value or "")
    return normalize_whitespace(unescape(without_tags))


def _first_string(values: Any) -> str:
    if isinstance(values, list):
        for value in values:
            if isinstance(value, str) and value.strip():
                return value
        return ""
    if isinstance(values, str):
        return values
    return ""


def _parse_date_parts(node: Any) -> str:
    """`{"date-parts": [[2025, 3, 1]]}` -> `2025-03-01`."""
    if not isinstance(node, dict):
        return ""
    parts = node.get("date-parts") or []
    if not parts or not isinstance(parts[0], list) or not parts[0]:
        return ""
    numbers = [int(part) for part in parts[0] if isinstance(part, (int, float))]
    if not numbers:
        return ""
    year = numbers[0]
    month = numbers[1] if len(numbers) > 1 else 1
    day = numbers[2] if len(numbers) > 2 else 1
    try:
        return datetime(year, month, day, tzinfo=UTC).date().isoformat()
    except ValueError:
        return ""


def _parse_date_time(node: Any) -> str:
    if not isinstance(node, dict):
        return ""
    raw = node.get("date-time")
    if isinstance(raw, str) and raw:
        return raw[:10]
    return _parse_date_parts(node)


def _parse_authors(item: dict) -> list[str]:
    authors: list[str] = []
    for author in item.get("author") or []:
        if not isinstance(author, dict):
            continue
        name = compact_join(
            [normalize_whitespace(author.get("given", "")), normalize_whitespace(author.get("family", ""))],
            sep=" ",
        )
        name = name or normalize_whitespace(author.get("name", ""))
        if name:
            authors.append(name)
    return authors


def _parse_categories(item: dict) -> list[str]:
    """Crossref `subject` thuong rong, nen fallback sang container-title va type."""
    categories = [normalize_whitespace(subject) for subject in item.get("subject") or [] if subject]
    if not categories:
        container = normalize_whitespace(_first_string(item.get("container-title")))
        if container:
            categories.append(container)
    doc_type = normalize_whitespace(item.get("type", ""))
    if doc_type and doc_type not in categories:
        categories.append(doc_type)
    return categories


def _parse_pdf_url(item: dict) -> str:
    for link in item.get("link") or []:
        if not isinstance(link, dict):
            continue
        if "pdf" in str(link.get("content-type", "")).lower() and link.get("URL"):
            return str(link["URL"])
    return ""


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref payload thanh list `PaperRecord` da chuan hoa."""
    items = (payload or {}).get("message", {}).get("items", []) or []
    records: list[PaperRecord] = []
    seen_ids: set[str] = set()

    for item in items:
        if not isinstance(item, dict):
            continue

        doi = normalize_whitespace(str(item.get("DOI", ""))).lower()
        title = _strip_markup(_first_string(item.get("title")))
        summary = _ABSTRACT_LABEL_PATTERN.sub("", _strip_markup(item.get("abstract", "")))
        published = _parse_date_parts(item.get("published") or item.get("issued") or item.get("created"))

        # Record khong co DOI/title/abstract/ngay xuat ban thi khong dung duoc cho RAG.
        if not doi or not title or not summary or not published:
            continue
        if doi in seen_ids:
            continue
        seen_ids.add(doi)

        categories = _parse_categories(item)
        updated = _parse_date_time(item.get("indexed") or item.get("deposited")) or published
        comment = compact_join(
            [
                normalize_whitespace(item.get("type", "")),
                normalize_whitespace(_first_string(item.get("container-title"))),
                normalize_whitespace(item.get("publisher", "")),
            ],
            sep=" | ",
        )

        records.append(
            PaperRecord(
                paper_id=doi,
                title=title,
                summary=summary,
                authors=_parse_authors(item),
                categories=categories,
                primary_category=categories[0] if categories else "uncategorized",
                published=published,
                updated=updated,
                abs_url=str(item.get("URL", "") or f"https://doi.org/{doi}"),
                pdf_url=_parse_pdf_url(item),
                comment=comment,
            )
        )

    return records


def _request_with_retry(params: dict[str, Any], headers: dict[str, str]) -> dict:
    last_error: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.get(CROSSREF_API_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
            if response.status_code in RETRY_STATUS_CODES:
                raise requests.HTTPError(f"Retryable status {response.status_code}", response=response)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as error:
            last_error = error
            if attempt == MAX_ATTEMPTS:
                break
            delay = BACKOFF_SECONDS * (2 ** (attempt - 1))
            retry_after = getattr(getattr(error, "response", None), "headers", {}).get("Retry-After")
            if retry_after:
                try:
                    delay = max(delay, float(retry_after))
                except ValueError:
                    pass
            print(f"[crossref] attempt {attempt}/{MAX_ATTEMPTS} failed ({error}); retry sau {delay:.1f}s")
            time.sleep(delay)
    raise RuntimeError(f"Crossref request that bai sau {MAX_ATTEMPTS} lan thu: {last_error}")


def effective_source_filter(settings: Settings) -> str:
    """Filter that su duoc gui len Crossref.

    Crossref co nhieu record "forthcoming" voi published date o tuong lai; chan lai
    ngay tu filter de corpus khong co `age_days` am.
    """
    today = datetime.now(UTC).date().isoformat()
    return f"{settings.source_filter},until-pub-date:{today}"


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Goi Crossref, luu raw response va raw records vao `data/raw/`."""
    source_filter = effective_source_filter(settings)

    # Over-fetch vi mot phan item se bi loai o buoc parse (thieu abstract/ngay).
    params: dict[str, Any] = {
        "query.bibliographic": settings.source_query,
        "filter": source_filter,
        "rows": settings.max_results * 3,
        # Sort theo relevance: `sort=published` se ghi de xep hang relevance va tra ve
        # cac paper moi nhat bat ke chu de, lam corpus lech khoi query.
        "sort": "relevance",
        "order": "desc",
    }
    mailto = os.getenv("CROSSREF_MAILTO", "").strip()
    if mailto:
        params["mailto"] = mailto
    headers = {"User-Agent": f"day10-data-observability-lab/0.1 (+{settings.source_api})"}

    print(f"[crossref] GET {CROSSREF_API_URL} query={settings.source_query!r} filter={source_filter!r}")
    payload = _request_with_retry(params, headers)

    write_json(settings.paths.raw_api_response, payload)
    records = parse_crossref_payload(payload)[: settings.max_results]
    write_json(settings.paths.raw_records_json, [asdict(record) for record in records])
    print(f"[crossref] luu {len(records)} raw records -> {settings.paths.raw_records_json}")
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Doc JSON snapshot trong `data/raw/` va map lai thanh `PaperRecord`."""
    payload = read_json(path)
    records: list[PaperRecord] = []
    for item in payload:
        records.append(
            PaperRecord(
                paper_id=str(item.get("paper_id", "")),
                title=str(item.get("title", "")),
                summary=str(item.get("summary", "")),
                authors=list(item.get("authors") or []),
                categories=list(item.get("categories") or []),
                primary_category=str(item.get("primary_category", "")),
                published=str(item.get("published", "")),
                updated=str(item.get("updated", "")),
                abs_url=str(item.get("abs_url", "")),
                pdf_url=str(item.get("pdf_url", "")),
                comment=str(item.get("comment", "")),
            )
        )
    return records
