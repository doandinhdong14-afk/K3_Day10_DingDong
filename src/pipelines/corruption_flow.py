from datetime import UTC, datetime
import logging
import pandas as pd

from core.config import load_settings
from core.utils import read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import load_raw_records
from ingestion.corruption import corrupt_clean_dataframe
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("--- Starting Corruption, Evaluation, Repair & Comparison Flow ---")
    settings = load_settings()
    run_date = datetime.now(UTC)

    # 1. Load baseline metrics and cleaned dataset
    if not settings.paths.baseline_metrics.exists() or not settings.paths.clean_json.exists():
        raise RuntimeError("Baseline artifacts not found. Please run Phase 1 baseline pipeline first.")

    baseline_metrics = read_json(settings.paths.baseline_metrics)
    clean_df = pd.read_json(settings.paths.clean_json)
    logger.info("Loaded baseline cleaned dataset (%d rows).", len(clean_df))

    # 2. Create corrupted DataFrame and save artifacts
    logger.info("Corrupting dataset...")
    corrupted_df = corrupt_clean_dataframe(clean_df, settings.paths.corruption_log)
    write_csv(corrupted_df, settings.paths.corrupted_clean_csv)
    write_json(settings.paths.corrupted_clean_json, corrupted_df.to_dict(orient="records"))
    logger.info("Corrupted dataset saved (%d rows).", len(corrupted_df))

    # 3. Build corrupted Chroma index & evaluate
    logger.info("Building ChromaDB index for corrupted dataset...")
    corrupted_index = LocalEmbeddingIndex.build(corrupted_df, settings, settings.paths.corrupted_embeddings_json)
    
    logger.info("Evaluating RAG pipeline on corrupted dataset...")
    corrupted_bundle = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )
    logger.info("Corrupted Metrics: %s", corrupted_bundle.summary)

    # 4. Run Data Quality Checks & Freshness Report on corrupted dataset
    corrupted_quality = run_data_quality_checks(corrupted_df, settings, "corrupted_quality")
    corrupted_freshness_path = settings.paths.quality_dir / "corrupted_freshness.json"
    corrupted_freshness = build_freshness_report(corrupted_df, settings, corrupted_freshness_path)

    # 5. Repair dataset from raw records
    logger.info("Repairing dataset from raw source records...")
    raw_records = load_raw_records(settings.paths.raw_records_json)
    repaired_df = build_clean_dataframe(raw_records, run_date)
    write_csv(repaired_df, settings.paths.repaired_clean_csv)
    write_json(settings.paths.repaired_clean_json, repaired_df.to_dict(orient="records"))
    logger.info("Repaired dataset saved (%d rows).", len(repaired_df))

    # 6. Build repaired Chroma index & evaluate
    logger.info("Building ChromaDB index for repaired dataset...")
    repaired_index = LocalEmbeddingIndex.build(repaired_df, settings, settings.paths.repaired_embeddings_json)

    logger.info("Evaluating RAG pipeline on repaired dataset...")
    repaired_bundle = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    logger.info("Repaired Metrics: %s", repaired_bundle.summary)

    # 7. Run Data Quality Checks & Freshness Report on repaired dataset
    repaired_quality = run_data_quality_checks(repaired_df, settings, "repaired_quality")
    repaired_freshness_path = settings.paths.quality_dir / "repaired_freshness.json"
    repaired_freshness = build_freshness_report(repaired_df, settings, repaired_freshness_path)

    # 8. Generate Markdown Comparison Report
    logger.info("Generating Corruption & Repair Comparison Report...")
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_bundle.summary,
        repaired_metrics=repaired_bundle.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )
    logger.info("Comparison Report saved to %s", settings.paths.comparison_report)
    logger.info("--- Corruption & Repair Flow Completed Successfully! ---")

