from datetime import UTC, datetime
import logging

from core.config import load_settings
from core.utils import write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("--- Starting Phase 1 Baseline Data Pipeline ---")
    settings = load_settings()
    run_date = datetime.now(UTC)

    # 1. Load or fetch raw records
    if settings.refresh_source or not settings.paths.raw_records_json.exists():
        logger.info("Fetching raw records from Crossref API...")
        raw_records = fetch_source_records(settings)
    else:
        logger.info("Loading cached raw records from %s...", settings.paths.raw_records_json)
        raw_records = load_raw_records(settings.paths.raw_records_json)

    raw_count = len(raw_records)

    # 2. Clean data
    logger.info("Cleaning raw records into DataFrame...")
    clean_df = build_clean_dataframe(raw_records, run_date)
    cleaned_count = len(clean_df)

    # 3. Save clean CSV & JSON
    logger.info("Saving cleaned dataset to CSV and JSON...")
    write_csv(clean_df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, clean_df.to_dict(orient="records"))

    # 4. Build Chroma Vector Index
    logger.info("Building ChromaDB embedding index...")
    index = LocalEmbeddingIndex.build(clean_df, settings, settings.paths.embeddings_json)

    # 5. Create or load evaluation test set
    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        logger.info("Building new evaluation test set...")
        build_test_set(clean_df, settings.paths.eval_testset)
    else:
        logger.info("Evaluation test set already exists at %s", settings.paths.eval_testset)

    # 6. Evaluate baseline RAG pipeline
    logger.info("Evaluating baseline RAG pipeline...")
    bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )
    logger.info("Baseline Metrics: %s", bundle.summary)

    # 7. Run Data Quality Checks & Freshness Report
    logger.info("Running Data Quality Checks & Freshness Monitoring...")
    quality_report = run_data_quality_checks(clean_df, settings, "baseline_quality")
    freshness_report = build_freshness_report(clean_df, settings, settings.paths.freshness_report)

    # 8. Generate Phase 1 Markdown Report
    logger.info("Generating Phase 1 Markdown Report...")
    source_summary = {
        "source_api": settings.source_api,
        "source_query": settings.source_query,
        "source_filter": settings.source_filter,
        "raw_records_count": raw_count,
        "cleaned_records_count": cleaned_count,
    }
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=bundle.summary,
        quality=quality_report,
        freshness=freshness_report,
    )
    logger.info("Phase 1 Baseline Report saved to %s", settings.paths.baseline_report)
    logger.info("--- Phase 1 Baseline Data Pipeline Completed Successfully! ---")

