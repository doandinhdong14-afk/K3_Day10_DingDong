from __future__ import annotations

import re
import time
from typing import Any

from core.config import Settings, load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import effective_source_filter, fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import describe_judge_mode, generate_phase1_report
from retrieval.index import LocalEmbeddingIndex

DEMO_QUESTION_COUNT = 3
AGENT_MAX_ATTEMPTS = 8
AGENT_BACKOFF_SECONDS = 15.0
AGENT_MAX_BACKOFF_SECONDS = 90.0

# Provider rate-limit thuong kem goi y thoi gian cho, vd "Please retry in 59.9s".
_RETRY_HINT_PATTERN = re.compile(r"retry in ([0-9.]+)s", flags=re.IGNORECASE)


def _step(number: int, title: str) -> None:
    print(f"\n=== [{number}/8] {title} ===")


def _retry_delay(error: Exception, attempt: int) -> float:
    """Uu tien thoi gian cho ma provider goi y, neu khong thi exponential backoff."""
    hint = _RETRY_HINT_PATTERN.search(str(error))
    if hint:
        return min(float(hint.group(1)) + 1.0, AGENT_MAX_BACKOFF_SECONDS)
    return min(AGENT_BACKOFF_SECONDS * (2 ** (attempt - 1)), AGENT_MAX_BACKOFF_SECONDS)


def _ask_agent(agent: Any, question: str, run_agent_question) -> str:
    """Agent goi LLM nhieu lan cho moi cau hoi nen rat de cham rate limit -> can retry."""
    last_error: Exception | None = None
    for attempt in range(1, AGENT_MAX_ATTEMPTS + 1):
        try:
            return run_agent_question(agent, question)
        except Exception as error:
            last_error = error
            if attempt == AGENT_MAX_ATTEMPTS:
                break
            delay = _retry_delay(error, attempt)
            print(f"[agent] attempt {attempt}/{AGENT_MAX_ATTEMPTS} bi loi rate limit; retry sau {delay:.0f}s")
            time.sleep(delay)
    raise RuntimeError(f"Agent khong tra loi duoc sau {AGENT_MAX_ATTEMPTS} lan thu: {last_error}")


def _run_agent_demo(settings: Settings, index: LocalEmbeddingIndex, test_set: list[dict[str, Any]]) -> None:
    """Demo agent tren vai cau hoi. Khong co LLM credential thi ghi lai ly do, khong lam fail pipeline."""
    questions = [item["question"] for item in test_set[:DEMO_QUESTION_COUNT]]
    try:
        from retrieval.agent import build_agent, run_agent_question

        agent = build_agent(settings=settings, index=index)
    except Exception as error:
        write_json(
            settings.paths.demo_answers,
            {"skipped": f"Khong khoi tao duoc agent: {error}", "questions": questions},
        )
        print(f"[agent] bo qua demo: {error}")
        return

    # Ghi ket qua theo tung cau: mot cau that bai khong lam mat cac cau da tra loi duoc.
    answers: list[dict[str, Any]] = []
    for question in questions:
        try:
            answers.append({"question": question, "answer": _ask_agent(agent, question, run_agent_question)})
        except Exception as error:
            answers.append({"question": question, "error": str(error)})

    answered = sum(1 for item in answers if "answer" in item)
    write_json(settings.paths.demo_answers, answers)
    print(f"[agent] tra loi {answered}/{len(answers)} cau hoi demo -> {settings.paths.demo_answers}")


def main() -> None:
    """Baseline pipeline: Crossref -> clean -> index -> evaluate -> quality/freshness -> report."""
    settings = load_settings()
    paths = settings.paths
    run_started_at = now_utc()

    _step(1, "Raw ingestion")
    if settings.refresh_source or not paths.raw_records_json.exists():
        records = fetch_source_records(settings)
        source_mode = "fetched from Crossref"
    else:
        records = load_raw_records(paths.raw_records_json)
        source_mode = "reused cached snapshot in data/raw/"
        print(f"[crossref] dung snapshot co san: {len(records)} records ({paths.raw_records_json})")
        print("           dat REFRESH_SOURCE=1 neu muon goi lai Crossref.")

    _step(2, "Cleaning va data modeling")
    df = build_clean_dataframe(records, run_started_at)
    write_csv(df, paths.clean_csv)
    write_json(paths.clean_json, df.to_dict(orient="records"))
    print(f"[clean] {len(records)} raw -> {len(df)} clean row; {len(df.columns)} cot -> {paths.clean_csv}")

    _step(3, "Embedding va vector store")
    index = LocalEmbeddingIndex.build(df, settings, paths.embeddings_json)
    print(f"[index] collection '{index.collection_name}' voi {len(index.documents)} document ({settings.embedding_model})")

    _step(4, "Evaluation set")
    if settings.refresh_test_set or not paths.eval_testset.exists():
        test_set = build_test_set(df, paths.eval_testset)
    else:
        test_set = read_json(paths.eval_testset)
        print(f"[testset] dung test set co san: {len(test_set)} cau hoi ({paths.eval_testset})")

    _step(5, "Evaluate baseline")
    bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=paths.eval_testset,
        metrics_output_path=paths.baseline_metrics,
        answers_output_path=paths.baseline_answers,
    )
    for key in ("retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score"):
        print(f"[metrics] {key}: {bundle.summary[key]:.4f}")

    _step(6, "Data quality checks")
    quality = run_data_quality_checks(df, settings, "baseline")

    _step(7, "Freshness report")
    freshness = build_freshness_report(df, settings, paths.freshness_report)

    _step(8, "Markdown report")
    source_summary = {
        "source_api": settings.source_api,
        "source_mode": source_mode,
        "query": settings.source_query,
        "filter": effective_source_filter(settings),
        "max_results": settings.max_results,
        "raw_records": len(records),
        "clean_rows": len(df),
        "embedding_model": settings.embedding_model,
        "collection_name": index.collection_name,
        "top_k": settings.top_k,
        "llm_provider": settings.llm_provider,
        "llm_model": settings.model_name,
        "judge_mode": describe_judge_mode(bundle.answers),
        "run_started_at": run_started_at.isoformat(),
    }
    generate_phase1_report(
        report_path=paths.baseline_report,
        source_summary=source_summary,
        metrics=bundle.summary,
        quality=quality,
        freshness=freshness,
    )

    _run_agent_demo(settings, index, test_set)

    print("\nBaseline pipeline hoan tat.")
    print(f"  metrics : {paths.baseline_metrics}")
    print(f"  report  : {paths.baseline_report}")
    print("  buoc tiep theo: python script/run_corruption_flow.py")
