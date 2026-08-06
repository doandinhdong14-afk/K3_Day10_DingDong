from __future__ import annotations

from core.config import load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe, load_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import describe_judge_mode, generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def _step(number: int, title: str) -> None:
    print(f"\n=== [{number}/8] {title} ===")


def main() -> None:
    """Corruption -> evaluate -> repair tu raw -> evaluate -> so sanh 3 trang thai."""
    settings = load_settings()
    paths = settings.paths

    _step(1, "Kiem tra baseline artifacts")
    missing = [
        str(path)
        for path in (
            paths.baseline_metrics,
            paths.baseline_answers,
            paths.clean_json,
            paths.eval_testset,
            paths.raw_records_json,
        )
        if not path.exists()
    ]
    if missing:
        raise FileNotFoundError(
            "Thieu artifact cua Pha 1: " + ", ".join(missing) + ". Chay `python script/run_phase1.py` truoc."
        )
    baseline_metrics = read_json(paths.baseline_metrics)
    baseline_quality = read_json(paths.quality_dir / "baseline_quality.json")
    baseline_freshness = read_json(paths.freshness_report)
    clean_df = load_clean_dataframe(paths.clean_json)
    print(f"[baseline] {len(clean_df)} clean row, retrieval_hit_rate={baseline_metrics.get('retrieval_hit_rate')}")

    _step(2, "Tao corrupted dataset")
    corrupted_df = corrupt_clean_dataframe(clean_df, paths.corruption_log)
    write_csv(corrupted_df, paths.corrupted_clean_csv)
    write_json(paths.corrupted_clean_json, corrupted_df.to_dict(orient="records"))
    corruption_log = read_json(paths.corruption_log)

    _step(3, "Rebuild index tren corrupted data")
    corrupted_index = LocalEmbeddingIndex.build(corrupted_df, settings, paths.corrupted_embeddings_json)
    print(f"[index] collection '{corrupted_index.collection_name}' voi {len(corrupted_index.documents)} document")

    _step(4, "Evaluate corrupted (cung test set voi baseline)")
    corrupted_bundle = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=paths.eval_testset,
        metrics_output_path=paths.corrupted_metrics,
        answers_output_path=paths.corrupted_answers,
    )

    _step(5, "Quality va freshness tren corrupted data")
    corrupted_quality = run_data_quality_checks(corrupted_df, settings, "corrupted")
    corrupted_freshness = build_freshness_report(
        corrupted_df, settings, paths.quality_dir / "freshness_report_corrupted.json"
    )

    _step(6, "Repair tu raw records")
    records = load_raw_records(paths.raw_records_json)
    repaired_df = build_clean_dataframe(records, now_utc())
    write_csv(repaired_df, paths.repaired_clean_csv)
    write_json(paths.repaired_clean_json, repaired_df.to_dict(orient="records"))
    print(f"[repair] rebuild {len(repaired_df)} row tu {len(records)} raw record -> {paths.repaired_clean_csv}")
    repaired_index = LocalEmbeddingIndex.build(repaired_df, settings, paths.repaired_embeddings_json)

    _step(7, "Evaluate repaired")
    repaired_bundle = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=paths.eval_testset,
        metrics_output_path=paths.repaired_metrics,
        answers_output_path=paths.repaired_answers,
    )
    repaired_quality = run_data_quality_checks(repaired_df, settings, "repaired")
    repaired_freshness = build_freshness_report(
        repaired_df, settings, paths.quality_dir / "freshness_report_repaired.json"
    )

    _step(8, "Comparison report")
    generate_corruption_report(
        report_path=paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_bundle.summary,
        repaired_metrics=repaired_bundle.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
        baseline_quality=baseline_quality,
        baseline_freshness=baseline_freshness,
        corruption_log=corruption_log,
        judge_modes={
            "baseline": describe_judge_mode(read_json(paths.baseline_answers)),
            "corrupted": describe_judge_mode(corrupted_bundle.answers),
            "repaired": describe_judge_mode(repaired_bundle.answers),
        },
    )

    print("\nCorruption flow hoan tat.")
    for label, metrics in (
        ("baseline ", baseline_metrics),
        ("corrupted", corrupted_bundle.summary),
        ("repaired ", repaired_bundle.summary),
    ):
        print(
            f"  {label} | hit_rate={metrics['retrieval_hit_rate']:.4f} "
            f"token_f1={metrics['mean_token_f1']:.4f} "
            f"judge_acc={metrics['judge_accuracy']:.4f} "
            f"judge_score={metrics['mean_judge_score']:.4f}"
        )
    print(f"  report: {paths.comparison_report}")
