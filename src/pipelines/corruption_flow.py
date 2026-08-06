from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings, load_settings, require_llm_credentials
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_answer_diff_report, generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


# 4 metric chinh dung de so sanh baseline / corrupted / repaired
HEADLINE_METRICS = (
    "retrieval_hit_rate",
    "mean_token_f1",
    "judge_accuracy",
    "mean_judge_score",
)
TOTAL_STEPS = 10


def _step(number: int, message: str) -> None:
    """In mot dong tien trinh co danh so."""
    print(f"[{number}/{TOTAL_STEPS}] {message}")


def _detail(message: str) -> None:
    """In dong phu, thut le cho de doc duoi moi step."""
    print(f"        {message}")


def _require_phase1_artifacts(settings: Settings) -> dict[str, Any]:
    """Bat buoc phase 1 phai chay xong, roi tra ve baseline metrics da nap."""
    required = {
        "baseline metrics": settings.paths.baseline_metrics,
        "clean dataset": settings.paths.clean_json,
        "evaluation test set": settings.paths.eval_testset,
        "raw records snapshot": settings.paths.raw_records_json,
    }
    missing = [f"{label} ({path})" for label, path in required.items() if not path.exists()]
    if missing:
        raise RuntimeError(
            "Thieu artifact cua phase 1: "
            + "; ".join(missing)
            + ". Hay chay script/run_phase1.py truoc khi chay corruption flow."
        )
    return read_json(settings.paths.baseline_metrics)


def _save_frame(df: pd.DataFrame, csv_path: Path, json_path: Path) -> None:
    """Ghi dataframe ra ca CSV va JSON de cac buoc sau doc lai duoc."""
    write_csv(df, csv_path)
    write_json(json_path, df.to_dict(orient="records"))


def _metric_value(metrics: dict[str, Any], key: str) -> float | None:
    """Lay metric dang so; neu thieu hoac sai kieu thi tra ve None."""
    value = metrics.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _format_metric(value: float | None) -> str:
    """Format metric ve chuoi 4 chu so thap phan, thieu thi ghi n/a."""
    return "n/a" if value is None else f"{value:.4f}"


def _freshness_line(freshness: dict[str, Any]) -> str:
    """Tom tat freshness report thanh mot dong ngan."""
    latest = freshness.get("latest_published", "?")
    stale = freshness.get("stale_rows", "?")
    total = freshness.get("total_rows", "?")
    is_fresh = freshness.get("is_fresh", "?")
    return f"latest={latest} stale={stale}/{total} is_fresh={is_fresh}"


def _quality_artifact(quality: dict[str, Any], settings: Settings, report_name: str) -> str:
    """Lay duong dan file quality tu ket qua tra ve, khong co thi doan theo ten mac dinh."""
    for key in ("report_path", "output_path", "path"):
        value = quality.get(key)
        if value:
            return str(value)
    return str(settings.paths.quality_dir / f"{report_name}.json")


def _print_comparison_table(
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
) -> None:
    """In bang so sanh 4 metric chinh giua 3 trang thai du lieu."""
    headers = ("metric", "baseline", "corrupted", "repaired")
    rows = [
        (
            key,
            _format_metric(_metric_value(baseline_metrics, key)),
            _format_metric(_metric_value(corrupted_metrics, key)),
            _format_metric(_metric_value(repaired_metrics, key)),
        )
        for key in HEADLINE_METRICS
    ]

    widths = [max([len(header)] + [len(row[column]) for row in rows]) for column, header in enumerate(headers)]
    print("  ".join(header.ljust(widths[column]) for column, header in enumerate(headers)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(cell.ljust(widths[column]) for column, cell in enumerate(row)))


def main() -> None:
    """Phase 2: corrupt -> evaluate -> repair -> evaluate -> compare."""
    _step(1, "Nap settings va kiem tra credentials cua LLM provider.")
    settings = load_settings()
    require_llm_credentials(settings)
    _detail(f"provider={settings.llm_provider} model={settings.model_name} top_k={settings.top_k}")

    _step(2, "Kiem tra artifact cua phase 1 va nap baseline metrics.")
    baseline_metrics = _require_phase1_artifacts(settings)
    _detail(f"baseline metrics <- {settings.paths.baseline_metrics}")

    _step(3, "Nap clean dataframe goc de lam moc so sanh.")
    baseline_df = pd.DataFrame(read_json(settings.paths.clean_json))
    _detail(f"baseline rows = {len(baseline_df)}")

    _step(4, "Tao corrupted dataframe va ghi corruption log.")
    corrupted_df = corrupt_clean_dataframe(baseline_df, settings.paths.corruption_log)
    _save_frame(corrupted_df, settings.paths.corrupted_clean_csv, settings.paths.corrupted_clean_json)
    _detail(f"corrupted rows = {len(corrupted_df)} (baseline {len(baseline_df)})")
    _detail(f"corruption log -> {settings.paths.corruption_log}")

    _step(5, "Build index corrupted va evaluate (buoc nay cham vi phai goi LLM).")
    corrupted_index = LocalEmbeddingIndex.build(
        corrupted_df, settings, settings.paths.corrupted_embeddings_json
    )
    # Dung lai dung test set cua phase 1 cho ca 3 trang thai de so sanh cong bang.
    corrupted_bundle = evaluate_pipeline(
        settings,
        corrupted_index,
        settings.paths.eval_testset,
        settings.paths.corrupted_metrics,
        settings.paths.corrupted_answers,
    )
    _detail(f"samples = {corrupted_bundle.summary.get('samples', '?')}")

    _step(6, "Chay data quality checks va freshness report tren du lieu corrupted.")
    corrupted_quality = run_data_quality_checks(corrupted_df, settings, "corrupted_quality")
    corrupted_freshness = build_freshness_report(
        corrupted_df, settings, settings.paths.quality_dir / "freshness_report_corrupted.json"
    )
    _detail(f"freshness corrupted: {_freshness_line(corrupted_freshness)}")

    _step(7, "Repair: dung lai tu raw snapshot dang tin cay thay vi va du lieu corrupted.")
    records = load_raw_records(settings.paths.raw_records_json)
    repaired_df = build_clean_dataframe(records, run_date=now_utc())
    _save_frame(repaired_df, settings.paths.repaired_clean_csv, settings.paths.repaired_clean_json)
    _detail(f"repaired rows = {len(repaired_df)} tu {len(records)} raw records")

    _step(8, "Build index repaired, evaluate va chay lai quality/freshness.")
    repaired_index = LocalEmbeddingIndex.build(
        repaired_df, settings, settings.paths.repaired_embeddings_json
    )
    repaired_bundle = evaluate_pipeline(
        settings,
        repaired_index,
        settings.paths.eval_testset,
        settings.paths.repaired_metrics,
        settings.paths.repaired_answers,
    )
    repaired_quality = run_data_quality_checks(repaired_df, settings, "repaired_quality")
    repaired_freshness = build_freshness_report(
        repaired_df, settings, settings.paths.quality_dir / "freshness_report_repaired.json"
    )
    _detail(f"freshness repaired: {_freshness_line(repaired_freshness)}")

    _step(9, "Sinh markdown report so sanh baseline / corrupted / repaired.")
    generate_corruption_report(
        settings.paths.comparison_report,
        baseline_metrics,
        corrupted_bundle.summary,
        repaired_bundle.summary,
        corrupted_quality,
        repaired_quality,
        corrupted_freshness,
        repaired_freshness,
    )
    _detail(f"report -> {settings.paths.comparison_report}")

    # Bang chung o muc OUTPUT: cung mot cau hoi, agent tra loi khac nhau tuy chat luong du lieu.
    answer_diff_path = settings.paths.comparison_report.parent / "answer_diff.md"
    generate_answer_diff_report(
        answer_diff_path,
        read_json(settings.paths.baseline_answers),
        corrupted_bundle.answers,
        repaired_bundle.answers,
    )
    _detail(f"doi chieu cau tra loi -> {answer_diff_path}")

    _step(10, "Tong ket ket qua.")
    print()
    print("=== So sanh metric ===")
    _print_comparison_table(baseline_metrics, corrupted_bundle.summary, repaired_bundle.summary)

    print()
    print("=== So dong du lieu ===")
    print(f"baseline={len(baseline_df)}  corrupted={len(corrupted_df)}  repaired={len(repaired_df)}")

    artifacts: list[tuple[str, str]] = [
        ("corruption log", str(settings.paths.corruption_log)),
        ("corrupted csv", str(settings.paths.corrupted_clean_csv)),
        ("corrupted json", str(settings.paths.corrupted_clean_json)),
        ("corrupted embeddings", str(settings.paths.corrupted_embeddings_json)),
        ("corrupted metrics", str(settings.paths.corrupted_metrics)),
        ("corrupted answers", str(settings.paths.corrupted_answers)),
        ("corrupted quality", _quality_artifact(corrupted_quality, settings, "corrupted_quality")),
        ("corrupted freshness", str(settings.paths.quality_dir / "freshness_report_corrupted.json")),
        ("repaired csv", str(settings.paths.repaired_clean_csv)),
        ("repaired json", str(settings.paths.repaired_clean_json)),
        ("repaired embeddings", str(settings.paths.repaired_embeddings_json)),
        ("repaired metrics", str(settings.paths.repaired_metrics)),
        ("repaired answers", str(settings.paths.repaired_answers)),
        ("repaired quality", _quality_artifact(repaired_quality, settings, "repaired_quality")),
        ("repaired freshness", str(settings.paths.quality_dir / "freshness_report_repaired.json")),
        ("comparison report", str(settings.paths.comparison_report)),
        ("answer diff report", str(settings.paths.comparison_report.parent / "answer_diff.md")),
    ]
    label_width = max(len(label) for label, _ in artifacts)

    print()
    print("=== Artifact da ghi ===")
    for label, path in artifacts:
        print(f"{label.ljust(label_width)}  {path}")
