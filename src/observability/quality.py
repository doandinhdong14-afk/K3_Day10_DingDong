from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import now_utc, write_json


# Nguong toi thieu cho cac check chat luong
MIN_ROWS = 10
MIN_TITLE_CHARS = 10
MIN_SUMMARY_CHARS = 80

# So paper_id stale toi da duoc liet ke trong freshness report
MAX_STALE_IDS = 20

# published/updated phai la chuoi ngay dang YYYY-MM-DD
PUBLISHED_DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"

# Cac cot bat buoc phai co de chay duoc bo check
REQUIRED_COLUMNS: tuple[str, ...] = (
    "paper_id",
    "title",
    "summary",
    "published",
    "age_days",
    "title_chars",
    "summary_chars",
    "text_for_embedding",
)


def _check(
    name: str,
    dimension: str,
    passed: bool,
    expectation: str,
    observed: str,
    failed_rows: int = 0,
) -> dict[str, Any]:
    """Chuan hoa ket qua mot check thanh dict co cung bo key."""
    passed = bool(passed)
    return {
        "name": name,
        "dimension": dimension,
        "passed": passed,
        "expectation": expectation,
        "observed": observed,
        "failed_rows": 0 if passed else int(failed_rows),
    }


def _as_bool_mask(mask: pd.Series) -> pd.Series:
    """Doi mask nullable boolean thanh mask bool thuan de dem/loc an toan."""
    if len(mask) == 0:
        return pd.Series([], dtype=bool)
    return mask.fillna(False).astype(bool)


def _count_true(mask: pd.Series) -> int:
    """Dem so dong vi pham trong mot mask."""
    return int(_as_bool_mask(mask).sum())


def _text_series(df: pd.DataFrame, column: str) -> pd.Series:
    """Lay mot cot duoi dang chuoi (nullable string) de kiem tra text."""
    return df[column].astype("string")


def _blank_mask(df: pd.DataFrame, column: str) -> pd.Series:
    """Mask cac dong null hoac chi chua khoang trang o cot text."""
    values = _text_series(df, column)
    return _as_bool_mask(values.isna() | (values.str.strip() == ""))


def _numeric_series(df: pd.DataFrame, column: str) -> pd.Series:
    """Ep cot ve numeric; gia tri khong parse duoc thanh NaN."""
    return pd.to_numeric(df[column], errors="coerce")


def _below_min_mask(df: pd.DataFrame, column: str, minimum: int) -> pd.Series:
    """Mask cac dong co gia tri numeric nho hon nguong (NaN cung tinh la fail)."""
    values = _numeric_series(df, column)
    return _as_bool_mask(values.isna() | (values < minimum))


def _rows_observed(failed_rows: int, total_rows: int, label: str) -> str:
    """Tao chuoi observed dang '3 / 24 rows <label>'."""
    return f"{failed_rows} / {total_rows} rows {label}"


def _missing_column_check(column: str, total_rows: int) -> dict[str, Any]:
    """Check that bai khi dataframe thieu mot cot bat buoc."""
    return _check(
        name=f"schema_{column}_present",
        dimension="consistency",
        passed=False,
        expectation=f"column '{column}' exists in the dataframe",
        observed=f"column '{column}' is missing",
        failed_rows=total_rows,
    )


def _row_count_check(total_rows: int) -> dict[str, Any]:
    """Check so luong dong toi thieu cua dataset."""
    passed = total_rows >= MIN_ROWS
    return _check(
        name="row_count",
        dimension="completeness",
        passed=passed,
        expectation=f"row_count >= {MIN_ROWS}",
        observed=f"row_count = {total_rows}",
        failed_rows=max(MIN_ROWS - total_rows, 0),
    )


def _not_null_check(
    df: pd.DataFrame,
    column: str,
    name: str,
    total_rows: int,
) -> dict[str, Any]:
    """Check mot cot text khong duoc null hoac rong."""
    failed_rows = _count_true(_blank_mask(df, column))
    return _check(
        name=name,
        dimension="completeness",
        passed=failed_rows == 0,
        expectation=f"every row has a non-empty '{column}'",
        observed=_rows_observed(failed_rows, total_rows, f"have a null/blank '{column}'"),
        failed_rows=failed_rows,
    )


def _min_length_check(
    df: pd.DataFrame,
    column: str,
    name: str,
    minimum: int,
    total_rows: int,
) -> dict[str, Any]:
    """Check do dai toi thieu dua tren cot dem ky tu."""
    failed_rows = _count_true(_below_min_mask(df, column, minimum))
    return _check(
        name=name,
        dimension="validity",
        passed=failed_rows == 0,
        expectation=f"every row has {column} >= {minimum}",
        observed=_rows_observed(failed_rows, total_rows, f"have {column} < {minimum} or a non-numeric value"),
        failed_rows=failed_rows,
    )


def _char_count_consistency_check(
    df: pd.DataFrame,
    text_column: str,
    count_column: str,
    name: str,
    total_rows: int,
) -> dict[str, Any]:
    """Check cot dem ky tu con khop voi do dai text thuc te."""
    lengths = _text_series(df, text_column).fillna("").str.len()
    declared = _numeric_series(df, count_column)
    failed_rows = _count_true(declared.isna() | (declared != lengths))
    return _check(
        name=name,
        dimension="consistency",
        passed=failed_rows == 0,
        expectation=f"{count_column} equals len({text_column}) on every row",
        observed=_rows_observed(failed_rows, total_rows, f"have {count_column} out of sync with '{text_column}'"),
        failed_rows=failed_rows,
    )


def _unique_check(df: pd.DataFrame, column: str, name: str, total_rows: int) -> dict[str, Any]:
    """Check khoa chinh khong bi trung."""
    duplicated = _as_bool_mask(df[column].duplicated(keep="first"))
    failed_rows = int(duplicated.sum())
    return _check(
        name=name,
        dimension="uniqueness",
        passed=failed_rows == 0,
        expectation=f"'{column}' is unique across all rows",
        observed=_rows_observed(failed_rows, total_rows, f"repeat an existing '{column}'"),
        failed_rows=failed_rows,
    )


def _stale_mask(df: pd.DataFrame, threshold_days: int) -> pd.Series:
    """Mask cac dong co age_days vuot nguong freshness."""
    if "age_days" not in df.columns:
        return pd.Series([False] * len(df), index=df.index, dtype=bool)
    return _as_bool_mask(_numeric_series(df, "age_days") > threshold_days)


def _freshness_check(df: pd.DataFrame, threshold_days: int, total_rows: int) -> dict[str, Any]:
    """Check khong con dong nao cu hon nguong freshness."""
    failed_rows = _count_true(_stale_mask(df, threshold_days))
    return _check(
        name="freshness_within_threshold",
        dimension="freshness",
        passed=failed_rows == 0,
        expectation=f"no row has age_days > {threshold_days}",
        observed=_rows_observed(failed_rows, total_rows, f"are older than {threshold_days} days"),
        failed_rows=failed_rows,
    )


def _published_format_check(df: pd.DataFrame, total_rows: int) -> dict[str, Any]:
    """Check dinh dang ngay published la YYYY-MM-DD."""
    values = _text_series(df, "published")
    matched = _as_bool_mask(values.str.match(PUBLISHED_DATE_PATTERN, na=False))
    failed_rows = int(len(values) - matched.sum()) if len(values) else 0
    return _check(
        name="published_format_valid",
        dimension="validity",
        passed=failed_rows == 0,
        expectation="every 'published' value matches YYYY-MM-DD",
        observed=_rows_observed(failed_rows, total_rows, "have a malformed 'published' value"),
        failed_rows=failed_rows,
    )


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Chay bo data quality checks, ghi JSON vao data/quality va tra ve ket qua."""
    total_rows = int(len(df))
    columns = set(df.columns)
    checks: list[dict[str, Any]] = []

    # 0. Schema guard: thieu cot nao thi bao fail thay vi raise KeyError
    for column in REQUIRED_COLUMNS:
        if column not in columns:
            checks.append(_missing_column_check(column, total_rows))

    # 1. So dong toi thieu
    checks.append(_row_count_check(total_rows))

    # 2 + 3. paper_id khong rong va khong trung
    if "paper_id" in columns:
        checks.append(_not_null_check(df, "paper_id", "paper_id_not_null", total_rows))
        checks.append(_unique_check(df, "paper_id", "paper_id_unique", total_rows))

    # 4. title khong rong
    if "title" in columns:
        checks.append(_not_null_check(df, "title", "title_not_null", total_rows))

    # 5. title du dai
    if "title_chars" in columns:
        checks.append(
            _min_length_check(df, "title_chars", "title_min_length", MIN_TITLE_CHARS, total_rows)
        )

    # 6. summary khong rong
    if "summary" in columns:
        checks.append(_not_null_check(df, "summary", "summary_not_empty", total_rows))

    # 7. summary du dai
    if "summary_chars" in columns:
        checks.append(
            _min_length_check(df, "summary_chars", "summary_min_length", MIN_SUMMARY_CHARS, total_rows)
        )

    # 8. text_for_embedding phai co san cho buoc index
    if "text_for_embedding" in columns:
        checks.append(
            _not_null_check(df, "text_for_embedding", "text_for_embedding_present", total_rows)
        )

    # 9. Freshness theo age_days
    if "age_days" in columns:
        checks.append(_freshness_check(df, settings.freshness_threshold_days, total_rows))

    # 10. Dinh dang ngay published
    if "published" in columns:
        checks.append(_published_format_check(df, total_rows))

    # 11 + 12. Cot dem ky tu con khop voi text (bat truong hop text bi sua ngam)
    if {"title", "title_chars"} <= columns:
        checks.append(
            _char_count_consistency_check(df, "title", "title_chars", "title_chars_consistent", total_rows)
        )
    if {"summary", "summary_chars"} <= columns:
        checks.append(
            _char_count_consistency_check(
                df, "summary", "summary_chars", "summary_chars_consistent", total_rows
            )
        )

    failed_check_names = [check["name"] for check in checks if not check["passed"]]
    passed_checks = len(checks) - len(failed_check_names)

    payload: dict[str, Any] = {
        "report_name": report_name,
        "generated_at": now_utc().isoformat(),
        "total_rows": total_rows,
        "total_checks": len(checks),
        "passed_checks": passed_checks,
        "failed_checks": len(failed_check_names),
        "success": not failed_check_names,
        "failed_check_names": failed_check_names,
        "total_failed_rows": sum(int(check["failed_rows"]) for check in checks),
        "checks": checks,
    }

    write_json(Path(settings.paths.quality_dir) / f"{report_name}.json", payload)
    return payload


def _published_bounds(df: pd.DataFrame) -> tuple[str | None, str | None]:
    """Tim ngay published moi nhat va cu nhat (chuoi YYYY-MM-DD hop le)."""
    if "published" not in df.columns or df.empty:
        return None, None

    values = _text_series(df, "published")
    valid = values[_as_bool_mask(values.str.match(PUBLISHED_DATE_PATTERN, na=False))]
    if valid.empty:
        return None, None

    ordered = sorted(str(value) for value in valid.tolist())
    return ordered[-1], ordered[0]


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Tong hop freshness report, ghi JSON ra report_path va tra ve payload."""
    threshold_days = int(settings.freshness_threshold_days)
    total_rows = int(len(df))
    has_age_column = "age_days" in df.columns

    stale_mask = _stale_mask(df, threshold_days)
    stale_rows = int(stale_mask.sum()) if len(stale_mask) else 0

    stale_paper_ids: list[str] = []
    if stale_rows and "paper_id" in df.columns:
        stale_paper_ids = [str(value) for value in df.loc[stale_mask, "paper_id"].head(MAX_STALE_IDS)]

    ages = _numeric_series(df, "age_days").dropna() if has_age_column else pd.Series([], dtype=float)
    max_age_days = int(ages.max()) if not ages.empty else None
    min_age_days = int(ages.min()) if not ages.empty else None
    mean_age_days = round(float(ages.mean()), 2) if not ages.empty else None

    latest_published, oldest_published = _published_bounds(df)

    payload: dict[str, Any] = {
        "generated_at": now_utc().isoformat(),
        "latest_published": latest_published,
        "oldest_published": oldest_published,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "is_fresh": bool(stale_rows == 0 and total_rows > 0 and has_age_column),
        "freshness_threshold_days": threshold_days,
        "max_age_days": max_age_days,
        "min_age_days": min_age_days,
        "mean_age_days": mean_age_days,
        "stale_ratio": round(stale_rows / total_rows, 4) if total_rows else 0.0,
        "age_days_available": has_age_column,
        "stale_paper_ids": stale_paper_ids,
    }

    write_json(Path(report_path), payload)
    return payload
