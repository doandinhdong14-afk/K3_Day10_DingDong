from __future__ import annotations

import re
from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import now_utc, write_json

MIN_ROWS = 5
MIN_TITLE_CHARS = 8
MIN_SUMMARY_CHARS = 40
MIN_EMBEDDING_TEXT_CHARS = 80
ISO_DATE_REGEX = r"^\d{4}-\d{2}-\d{2}$"


def _check_specs(settings: Settings) -> list[dict[str, Any]]:
    """Mot bo spec duy nhat, dung chung cho ca Great Expectations lan fallback pandas."""
    return [
        {"name": "row_count_minimum", "type": "table_row_count_between", "min": MIN_ROWS},
        {"name": "paper_id_not_null", "type": "column_not_null", "column": "paper_id"},
        {"name": "paper_id_unique", "type": "column_unique", "column": "paper_id"},
        {"name": "title_not_null", "type": "column_not_null", "column": "title"},
        {"name": "title_length_minimum", "type": "column_length_between", "column": "title", "min": MIN_TITLE_CHARS},
        {
            "name": "summary_length_minimum",
            "type": "column_length_between",
            "column": "summary",
            "min": MIN_SUMMARY_CHARS,
        },
        {"name": "published_is_iso_date", "type": "column_matches_regex", "column": "published", "regex": ISO_DATE_REGEX},
        {
            "name": "text_for_embedding_length_minimum",
            "type": "column_length_between",
            "column": "text_for_embedding",
            "min": MIN_EMBEDDING_TEXT_CHARS,
        },
        {
            "name": "age_days_within_freshness_threshold",
            "type": "column_values_between",
            "column": "age_days",
            "min": 0,
            "max": settings.freshness_threshold_days,
        },
    ]


def _observed(element_count: int, unexpected_count: int) -> dict[str, Any]:
    percent = (unexpected_count / element_count * 100.0) if element_count else 0.0
    return {
        "element_count": element_count,
        "unexpected_count": unexpected_count,
        "unexpected_percent": round(percent, 2),
    }


def _run_pandas_check(df: pd.DataFrame, spec: dict[str, Any]) -> dict[str, Any]:
    check_type = spec["type"]
    column = spec.get("column")

    if check_type == "table_row_count_between":
        return {"success": len(df) >= spec["min"], "observed": {"row_count": len(df)}}

    if column not in df.columns:
        return {"success": False, "observed": {"error": f"missing column: {column}"}}

    series = df[column]
    if check_type == "column_not_null":
        unexpected = int(series.isna().sum() + (series.astype(str).str.strip() == "").sum())
    elif check_type == "column_unique":
        unexpected = int(series.duplicated(keep=False).sum())
    elif check_type == "column_length_between":
        lengths = series.fillna("").astype(str).str.len()
        unexpected = int((lengths < spec["min"]).sum())
    elif check_type == "column_matches_regex":
        pattern = re.compile(spec["regex"])
        unexpected = int((~series.fillna("").astype(str).str.match(pattern)).sum())
    elif check_type == "column_values_between":
        numeric = pd.to_numeric(series, errors="coerce")
        unexpected = int((numeric.isna() | (numeric < spec["min"]) | (numeric > spec["max"])).sum())
    else:
        return {"success": False, "observed": {"error": f"unsupported check type: {check_type}"}}

    return {"success": unexpected == 0, "observed": _observed(len(df), unexpected)}


def _to_gx_expectation(spec: dict[str, Any]):
    import great_expectations.expectations as gxe

    check_type = spec["type"]
    if check_type == "table_row_count_between":
        return gxe.ExpectTableRowCountToBeBetween(min_value=spec["min"])
    if check_type == "column_not_null":
        return gxe.ExpectColumnValuesToNotBeNull(column=spec["column"])
    if check_type == "column_unique":
        return gxe.ExpectColumnValuesToBeUnique(column=spec["column"])
    if check_type == "column_length_between":
        return gxe.ExpectColumnValueLengthsToBeBetween(column=spec["column"], min_value=spec["min"])
    if check_type == "column_matches_regex":
        return gxe.ExpectColumnValuesToMatchRegex(column=spec["column"], regex=spec["regex"])
    if check_type == "column_values_between":
        return gxe.ExpectColumnValuesToBeBetween(column=spec["column"], min_value=spec["min"], max_value=spec["max"])
    raise ValueError(f"unsupported check type: {check_type}")


def _run_with_great_expectations(
    df: pd.DataFrame,
    settings: Settings,
    report_name: str,
    specs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Chay suite bang Great Expectations va luu raw validation result vao `data/quality/gx/`."""
    import great_expectations as gx

    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas(name=f"{report_name}_pandas")
    data_asset = data_source.add_dataframe_asset(name=f"{report_name}_asset")
    batch_definition = data_asset.add_batch_definition_whole_dataframe(f"{report_name}_batch")

    suite = context.suites.add(gx.ExpectationSuite(name=f"{report_name}_suite"))
    for spec in specs:
        suite.add_expectation(_to_gx_expectation(spec))

    validation_definition = context.validation_definitions.add(
        gx.ValidationDefinition(data=batch_definition, suite=suite, name=f"{report_name}_validation")
    )
    raw_result = validation_definition.run(batch_parameters={"dataframe": df})
    payload = raw_result.to_json_dict()
    write_json(settings.paths.gx_dir / f"{report_name}_gx_validation.json", payload)

    checks: list[dict[str, Any]] = []
    for spec, result in zip(specs, payload.get("results", []), strict=True):
        result_body = result.get("result", {}) or {}
        checks.append(
            {
                "name": spec["name"],
                "type": spec["type"],
                "column": spec.get("column"),
                "success": bool(result.get("success")),
                "observed": {
                    key: result_body[key]
                    for key in ("element_count", "unexpected_count", "unexpected_percent", "observed_value")
                    if key in result_body
                },
            }
        )
    return checks


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Chay data quality suite tren mot dataset va ghi ket qua vao `data/quality/`."""
    specs = _check_specs(settings)
    engine = "great_expectations"
    engine_note = ""

    try:
        checks = _run_with_great_expectations(df, settings, report_name, specs)
    except Exception as error:  # Great Expectations doi API kha nhanh -> luon co duong lui.
        engine = "pandas"
        engine_note = f"Great Expectations khong chay duoc, dung fallback pandas: {error}"
        print(f"[quality] {engine_note}")
        checks = [
            {"name": spec["name"], "type": spec["type"], "column": spec.get("column"), **_run_pandas_check(df, spec)}
            for spec in specs
        ]

    failed = [check["name"] for check in checks if not check["success"]]
    payload = {
        "report_name": report_name,
        "engine": engine,
        "engine_note": engine_note,
        "generated_at": now_utc().isoformat(),
        "rows": int(len(df)),
        "columns": list(df.columns),
        "success": not failed,
        "summary": {"total": len(checks), "passed": len(checks) - len(failed), "failed": len(failed)},
        "failed_checks": failed,
        "checks": checks,
    }

    output_path = settings.paths.quality_dir / f"{report_name}_quality.json"
    write_json(output_path, payload)
    status = "PASS" if payload["success"] else "FAIL"
    print(f"[quality] {report_name}: {status} ({payload['summary']['passed']}/{len(checks)} checks) -> {output_path}")
    return payload


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Tong hop freshness signal cua dataset va ghi JSON report."""
    threshold = settings.freshness_threshold_days
    published = df["published"].fillna("").astype(str)
    age_days = pd.to_numeric(df["age_days"], errors="coerce")

    valid_published = published[published.str.match(ISO_DATE_REGEX)]
    stale_mask = age_days.isna() | (age_days > threshold)
    stale_rows = int(stale_mask.sum())
    total_rows = int(len(df))

    payload = {
        "generated_at": now_utc().isoformat(),
        "freshness_threshold_days": threshold,
        "total_rows": total_rows,
        "latest_published": valid_published.max() if not valid_published.empty else None,
        "oldest_published": valid_published.min() if not valid_published.empty else None,
        "min_age_days": int(age_days.min()) if age_days.notna().any() else None,
        "max_age_days": int(age_days.max()) if age_days.notna().any() else None,
        "median_age_days": float(age_days.median()) if age_days.notna().any() else None,
        "stale_rows": stale_rows,
        "stale_ratio": round(stale_rows / total_rows, 4) if total_rows else 0.0,
        "is_fresh": stale_rows == 0,
        "status": "FRESH" if stale_rows == 0 else "STALE",
    }

    write_json(report_path, payload)
    print(
        f"[freshness] {payload['status']}: {stale_rows}/{total_rows} row qua {threshold} ngay "
        f"(latest={payload['latest_published']}) -> {report_path}"
    )
    return payload
