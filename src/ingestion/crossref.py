from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
import os
import re
import time

import requests

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json


CROSSREF_API_URL = "https://api.crossref.org/works"
CONTACT_EMAIL = "doandinhdong14@gmail.com"
REQUEST_HEADERS = {"User-Agent": f"K3-Day10-DataPipeline/1.0 (mailto:{CONTACT_EMAIL})"}
RETRYABLE_STATUS = {429, 500, 502, 503, 504}
MIN_SUMMARY_CHARS = 80


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


def _strip_markup(value: object) -> str:
    """Bo the XML/HTML trong abstract roi gom khoang trang thua."""
    if not value:
        return ""
    text = re.sub(r"<[^>]+>", " ", str(value))
    for entity, char in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'")):
        text = text.replace(entity, char)
    text = normalize_whitespace(text)
    return re.sub(r"^(abstract|summary)\s*[:.\-]?\s*", "", text, flags=re.IGNORECASE)


def _first_string(value: object) -> str:
    """Crossref hay tra ve list cho title/container-title -> lay phan tu dau tien."""
    if isinstance(value, list):
        return next((normalize_whitespace(str(item)) for item in value if item), "")
    return normalize_whitespace(str(value)) if value else ""


def _format_date(node: object) -> str:
    """{'date-parts': [[2026, 6, 15]]} -> '2026-06-15'."""
    parts = (node or {}).get("date-parts") if isinstance(node, dict) else None
    if not parts or not parts[0]:
        return ""
    numbers = [int(part) for part in parts[0] if part is not None]
    if not numbers:
        return ""
    year = numbers[0]
    month = numbers[1] if len(numbers) > 1 else 1
    day = numbers[2] if len(numbers) > 2 else 1
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return date(year, 1, 1).isoformat()


def _format_authors(nodes: object) -> list[str]:
    """[{'given': 'Ben J.', 'family': 'Weber'}] -> ['Ben J. Weber']."""
    authors: list[str] = []
    for node in nodes or []:
        if not isinstance(node, dict):
            continue
        name = node.get("name") or " ".join(
            part for part in (node.get("given", ""), node.get("family", "")) if part
        )
        name = normalize_whitespace(name)
        if name and name not in authors:
            authors.append(name)
    return authors


def _format_categories(item: dict) -> list[str]:
    """Crossref hiem khi co `subject`, nen fallback sang venue/type/publisher."""
    categories = [normalize_whitespace(str(s)) for s in (item.get("subject") or []) if s]
    if not categories:
        journal = _first_string(item.get("container-title"))
        doc_type = normalize_whitespace(str(item.get("type") or "")).replace("-", " ")
        publisher = normalize_whitespace(str(item.get("publisher") or ""))
        categories = [value for value in (journal, doc_type, publisher) if value]
    return list(dict.fromkeys(categories)) or ["uncategorized"]


def _find_pdf_url(item: dict) -> str:
    """content-type thuong la 'unspecified' nen phai doan them tu duoi URL."""
    links = [link for link in (item.get("link") or []) if isinstance(link, dict) and link.get("URL")]
    for link in links:
        url = str(link["URL"])
        if link.get("content-type") == "application/pdf" or ".pdf" in url.lower():
            return url
    return str(links[0]["URL"]) if links else ""


def _looks_latin(text: str) -> bool:
    """Loai bai khong phai chu Latin vi embedding model chi manh o tieng Anh."""
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return False
    return sum(1 for char in letters if char.isascii()) / len(letters) >= 0.7


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    items = ((payload or {}).get("message") or {}).get("items") or []
    records: list[PaperRecord] = []
    seen_ids: set[str] = set()

    for item in items:
        if not isinstance(item, dict):
            continue
        paper_id = normalize_whitespace(str(item.get("DOI") or ""))
        title = _strip_markup(_first_string(item.get("title")))
        summary = _strip_markup(item.get("abstract"))
        published = _format_date(item.get("issued") or item.get("published") or item.get("created"))

        if not paper_id or not title or not published:
            continue
        if len(summary) < MIN_SUMMARY_CHARS:
            continue
        if not (_looks_latin(title) and _looks_latin(summary)):
            continue
        if paper_id.lower() in seen_ids:
            continue
        seen_ids.add(paper_id.lower())

        categories = _format_categories(item)
        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=summary,
                authors=_format_authors(item.get("author")),
                categories=categories,
                primary_category=categories[0],
                published=published,
                updated=_format_date(item.get("deposited") or item.get("indexed")) or published,
                abs_url=str(item.get("URL") or f"https://doi.org/{paper_id}"),
                pdf_url=_find_pdf_url(item),
                comment=normalize_whitespace(
                    f"{item.get('type', '')} in {_first_string(item.get('container-title')) or 'unknown venue'}"
                ),
            )
        )
    return records


def _get_with_retry(params: dict, max_attempts: int = 5, timeout: int = 60) -> dict:
    """Goi API, gap 429/5xx thi cho roi thu lai voi thoi gian tang gap doi."""
    verify = os.getenv("CROSSREF_CA_BUNDLE") or True
    delay = 1.0
    last_error = "unknown error"

    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(
                CROSSREF_API_URL, params=params, headers=REQUEST_HEADERS, timeout=timeout, verify=verify
            )
            if response.status_code in RETRYABLE_STATUS:
                last_error = f"HTTP {response.status_code}"
            else:
                response.raise_for_status()
                return response.json()
        except requests.RequestException as exc:
            last_error = f"{type(exc).__name__}: {exc}"

        if attempt == max_attempts:
            break
        print(f"[crossref] {last_error} -> thu lai sau {delay:.0f}s ({attempt}/{max_attempts})")
        time.sleep(delay)
        delay *= 2

    raise RuntimeError(f"Khong goi duoc Crossref sau {max_attempts} lan. Loi cuoi: {last_error}")


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results * 3,
        "mailto": CONTACT_EMAIL,
    }
    print(f"[crossref] GET {CROSSREF_API_URL} rows={params['rows']}")
    payload = _get_with_retry(params)

    write_json(settings.paths.raw_api_response, payload)
    print(f"[crossref] Da luu raw response -> {settings.paths.raw_api_response}")

    records = parse_crossref_payload(payload)[: settings.max_results]
    if not records:
        raise RuntimeError("Crossref khong tra ve record hop le nao. Kiem tra lai query/filter.")

    write_json(settings.paths.raw_records_json, [asdict(record) for record in records])
    print(f"[crossref] Da luu {len(records)} raw records -> {settings.paths.raw_records_json}")
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    payload = read_json(path)
    if isinstance(payload, dict):
        return parse_crossref_payload(payload)

    records: list[PaperRecord] = []
    for row in payload or []:
        if not isinstance(row, dict) or not row.get("paper_id") or not row.get("title"):
            continue
        categories = list(row.get("categories") or []) or ["uncategorized"]
        records.append(
            PaperRecord(
                paper_id=str(row["paper_id"]),
                title=str(row["title"]),
                summary=str(row.get("summary") or ""),
                authors=list(row.get("authors") or []),
                categories=categories,
                primary_category=str(row.get("primary_category") or categories[0]),
                published=str(row.get("published") or ""),
                updated=str(row.get("updated") or row.get("published") or ""),
                abs_url=str(row.get("abs_url") or ""),
                pdf_url=str(row.get("pdf_url") or ""),
                comment=str(row.get("comment") or ""),
            )
        )
    return records