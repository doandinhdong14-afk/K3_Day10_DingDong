from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Run data quality checks on DataFrame and write output JSON report."""
    total_rows = len(df)
    paper_id_nulls = int(df["paper_id"].isnull().sum() + (df["paper_id"] == "").sum()) if total_rows > 0 else 0
    paper_id_unique_count = int(df["paper_id"].nunique()) if total_rows > 0 else 0
    duplicate_paper_ids = max(0, total_rows - paper_id_unique_count)

    title_nulls = int(df["title"].isnull().sum() + (df["title"] == "").sum()) if total_rows > 0 else 0
    summary_nulls = int(df["summary"].isnull().sum() + (df["summary"] == "").sum()) if total_rows > 0 else 0
    short_summaries = int((df["summary"].str.len() < 20).sum()) if total_rows > 0 else 0

    stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum()) if total_rows > 0 and "age_days" in df.columns else 0

    success = (
        total_rows > 0
        and paper_id_nulls == 0
        and duplicate_paper_ids == 0
        and title_nulls == 0
        and summary_nulls == 0
        and short_summaries == 0
    )

    report = {
        "report_name": report_name,
        "success": success,
        "checks": {
            "total_rows": total_rows,
            "paper_id_nulls": paper_id_nulls,
            "duplicate_paper_ids": duplicate_paper_ids,
            "title_nulls": title_nulls,
            "summary_nulls": summary_nulls,
            "short_summaries": short_summaries,
            "stale_rows": stale_rows,
        },
    }

    report_file = settings.paths.quality_dir / f"{report_name}.json"
    write_json(report_file, report)
    return report


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path: Path | str) -> dict[str, Any]:
    """Build and save freshness monitoring report."""
    total_rows = len(df)
    if total_rows > 0 and "published" in df.columns:
        latest_published = str(df["published"].max())
        oldest_published = str(df["published"].min())
        stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum())
    else:
        latest_published = "N/A"
        oldest_published = "N/A"
        stale_rows = 0

    fresh_ratio = float((total_rows - stale_rows) / total_rows) if total_rows > 0 else 0.0
    is_fresh = (stale_rows == 0) and (total_rows > 0)

    report = {
        "latest_published": latest_published,
        "oldest_published": oldest_published,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "fresh_ratio": fresh_ratio,
        "is_fresh": is_fresh,
        "threshold_days": settings.freshness_threshold_days,
    }

    write_json(Path(report_path), report)
    return report

