from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings, load_settings, require_llm_credentials
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import PaperRecord, fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.agent import build_agent, run_agent_question
from retrieval.index import LocalEmbeddingIndex


TOTAL_STEPS = 10
QUALITY_REPORT_NAME = "baseline_quality"
DEMO_QUESTION_LIMIT = 2
DEMO_PREVIEW_CHARS = 160


def _step(number: int, message: str) -> None:
    """In dong tien trinh dang [n/10] cho tung buoc cua pipeline."""
    print(f"\n[{number}/{TOTAL_STEPS}] {message}")


def _detail(message: str) -> None:
    """In dong chi tiet thut le cho de doc duoi moi buoc."""
    print(f"      {message}")


def _format_metric(value: Any) -> str:
    """So thi lam tron 4 chu so, con lai giu nguyen dang chuoi."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return str(value)
    return f"{float(value):.4f}"


def _shorten(text: str, limit: int = DEMO_PREVIEW_CHARS) -> str:
    """Cat bot cau tra loi dai de log khong bi tran man hinh."""
    flat = " ".join(str(text).split())
    return flat if len(flat) <= limit else flat[: limit - 3] + "..."


def _load_records(settings: Settings) -> tuple[list[PaperRecord], str]:
    """Uu tien raw snapshot da luu; chi goi API khi thieu file hoac bat refresh."""
    raw_path = settings.paths.raw_records_json
    if raw_path.exists() and not settings.refresh_source:
        records = load_raw_records(raw_path)
        if records:
            _detail(f"dung lai raw snapshot: {raw_path}")
            return records, "raw snapshot"
        _detail("raw snapshot rong -> goi lai source API")
    return fetch_source_records(settings), settings.source_api


def _load_or_build_test_set(settings: Settings, df: pd.DataFrame) -> list[dict[str, Any]]:
    """Giu nguyen test set cu de so sanh cong bang, tru khi user yeu cau refresh."""
    testset_path = settings.paths.eval_testset
    if testset_path.exists() and not settings.refresh_test_set:
        test_set = read_json(testset_path)
        if test_set:
            _detail(f"dung lai test set co san: {len(test_set)} cau hoi ({testset_path})")
            return list(test_set)
        _detail("test set cu rong -> tao lai tu dataset sach")
    test_set = build_test_set(df, testset_path)
    _detail(f"da tao moi {len(test_set)} cau hoi -> {testset_path}")
    return test_set


def _quality_counts(quality: Any) -> tuple[int, int]:
    """Dem so check pass/fail, chap nhan nhieu dang payload khac nhau."""
    if not isinstance(quality, dict):
        return 0, 0

    def _is_count(value: Any) -> bool:
        return isinstance(value, int) and not isinstance(value, bool)

    for pass_key, fail_key in (
        ("passed_checks", "failed_checks"),
        ("passed", "failed"),
        ("success_count", "failure_count"),
    ):
        passed = quality.get(pass_key)
        failed = quality.get(fail_key)
        if _is_count(passed) and _is_count(failed):
            return passed, failed

    checks = quality.get("checks") or quality.get("results") or quality.get("expectations") or []
    if isinstance(checks, dict):
        checks = list(checks.values())

    passed_count = 0
    failed_count = 0
    for check in checks:
        if not isinstance(check, dict):
            continue
        flag = check.get("success")
        if flag is None:
            flag = check.get("passed")
        if flag is None:
            flag = check.get("ok")
        if flag is None:
            flag = str(check.get("status", "")).strip().lower() in {"pass", "passed", "ok", "success", "true"}
        if flag:
            passed_count += 1
        else:
            failed_count += 1
    return passed_count, failed_count


def _freshness_status(freshness: Any) -> str:
    """Gom trang thai freshness thanh mot dong ngan de in ra console."""
    if not isinstance(freshness, dict):
        return "KHONG RO"
    is_fresh = freshness.get("is_fresh")
    label = "KHONG RO" if is_fresh is None else ("FRESH" if is_fresh else "STALE")
    latest = freshness.get("latest_published", "?")
    oldest = freshness.get("oldest_published", "?")
    stale_rows = freshness.get("stale_rows", "?")
    total_rows = freshness.get("total_rows", "?")
    return f"{label} | latest={latest} | oldest={oldest} | stale={stale_rows}/{total_rows}"


def _relative_path(path: Path, project_dir: Path) -> str:
    """Doi duong dan tuyet doi thanh duong dan tuong doi so voi project.

    Bao cao nop bai khong nen lo duong dan tuyet doi cua may ca nhan (co ca ten user).
    """
    try:
        return path.resolve().relative_to(project_dir.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _build_source_summary(
    settings: Settings,
    records: list[PaperRecord],
    df: pd.DataFrame,
    source_mode: str,
) -> dict[str, Any]:
    """Metadata ve nguon du lieu de gan vao markdown report."""
    project_dir = settings.paths.project_dir
    return {
        "source_api": settings.source_api,
        "source_mode": source_mode,
        "source_query": settings.source_query,
        "source_filter": settings.source_filter,
        "max_results": settings.max_results,
        "raw_records": len(records),
        "clean_rows": len(df),
        "embedding_model": settings.embedding_model,
        "collection_name": settings.baseline_collection_name,
        "top_k": settings.top_k,
        "llm_provider": settings.llm_provider,
        "llm_model": settings.model_name,
        "raw_response_path": _relative_path(settings.paths.raw_api_response, project_dir),
        "raw_records_path": _relative_path(settings.paths.raw_records_json, project_dir),
        "clean_csv_path": _relative_path(settings.paths.clean_csv, project_dir),
        "generated_at": now_utc().isoformat(),
    }


def _run_agent_demo(settings: Settings, index: LocalEmbeddingIndex, test_set: list[dict[str, Any]]) -> None:
    """Demo agent tren vai cau hoi dau; loi LLM khong duoc lam hong pipeline."""
    try:
        agent = build_agent(settings, index)
        demo_rows: list[dict[str, Any]] = []
        for item in test_set[:DEMO_QUESTION_LIMIT]:
            question = str(item.get("question", ""))
            answer = run_agent_question(agent, question)
            demo_rows.append(
                {
                    "id": item.get("id"),
                    "question_type": item.get("question_type"),
                    "question": question,
                    "ground_truth": item.get("ground_truth"),
                    "agent_answer": answer,
                }
            )
            _detail(f"{item.get('id')}: {_shorten(answer)}")
        write_json(settings.paths.demo_answers, demo_rows)
        _detail(f"da luu {len(demo_rows)} demo answer -> {settings.paths.demo_answers}")
    except Exception as exc:  # LLM co the bi rate limit -> chi canh bao roi di tiep
        _detail(f"CANH BAO: agent demo that bai ({type(exc).__name__}: {exc})")
        _detail("bo qua demo, cac buoc truoc do van hop le")


def _artifact_paths(settings: Settings) -> list[tuple[str, Path]]:
    """Danh sach artifact ma phase 1 co the sinh ra, theo thu tu pipeline."""
    paths = settings.paths
    items: list[tuple[str, Path]] = [
        ("raw response", paths.raw_api_response),
        ("raw records", paths.raw_records_json),
        ("clean csv", paths.clean_csv),
        ("clean json", paths.clean_json),
        ("chroma dir", paths.chroma_dir),
        ("embeddings manifest", paths.embeddings_json),
        ("test set", paths.eval_testset),
        ("baseline metrics", paths.baseline_metrics),
        ("baseline answers", paths.baseline_answers),
    ]
    if paths.quality_dir.exists():
        for path in sorted(paths.quality_dir.glob("*.json")):
            if path != paths.freshness_report:
                items.append(("quality report", path))
    items.extend(
        [
            ("freshness report", paths.freshness_report),
            ("baseline report", paths.baseline_report),
            ("agent demo answers", paths.demo_answers),
        ]
    )
    return items


def _print_artifacts(settings: Settings) -> None:
    """In khoi tong ket cac artifact thuc su ton tai tren dia."""
    print("\n" + "=" * 72)
    print("TOM TAT ARTIFACT PHASE 1")
    print("=" * 72)
    for label, path in _artifact_paths(settings):
        if path.exists():
            print(f"  [OK]    {label:<20} {path}")
        else:
            print(f"  [THIEU] {label:<20} {path}")
    print("=" * 72)


def main() -> None:
    """Chay toan bo baseline pipeline: ingest -> clean -> index -> evaluate -> report."""
    print("=" * 72)
    print("PHASE 1 - BASELINE DATA PIPELINE")
    print("=" * 72)

    _step(1, "Load settings va kiem tra credential LLM...")
    settings = load_settings()
    require_llm_credentials(settings)
    _detail(f"provider={settings.llm_provider} | model={settings.model_name}")
    _detail(f"embedding model={settings.embedding_model}")
    _detail(f"project dir={settings.paths.project_dir}")

    _step(2, "Lay raw records tu source...")
    records, source_mode = _load_records(settings)
    _detail(f"nguon={source_mode} | so raw record={len(records)}")

    _step(3, "Lam sach du lieu...")
    df = build_clean_dataframe(records, run_date=now_utc())
    _detail(f"clean rows={len(df)} | columns={len(df.columns)}")
    _detail(f"published moi nhat={df['published'].iloc[0]} | cu nhat={df['published'].iloc[-1]}")

    _step(4, "Luu clean artifacts (CSV + JSON)...")
    write_csv(df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, df.to_dict(orient="records"))
    _detail(f"csv  -> {settings.paths.clean_csv}")
    _detail(f"json -> {settings.paths.clean_json}")

    _step(5, "Build embedding index (ChromaDB)...")
    index = LocalEmbeddingIndex.build(df, settings, settings.paths.embeddings_json)
    _detail(f"collection={index.collection_name} | documents={len(index.documents)}")
    _detail(f"persist -> {index.persist_path}")

    _step(6, "Chuan bi evaluation test set...")
    test_set = _load_or_build_test_set(settings, df)

    _step(7, "Evaluate pipeline tren test set...")
    bundle = evaluate_pipeline(
        settings,
        index,
        settings.paths.eval_testset,
        settings.paths.baseline_metrics,
        settings.paths.baseline_answers,
    )
    summary = bundle.summary
    _detail(f"samples            = {summary.get('samples')}")
    _detail(f"retrieval_hit_rate = {_format_metric(summary.get('retrieval_hit_rate'))}")
    _detail(f"mean_token_f1      = {_format_metric(summary.get('mean_token_f1'))}")
    _detail(f"judge_accuracy     = {_format_metric(summary.get('judge_accuracy'))}")
    _detail(f"mean_judge_score   = {_format_metric(summary.get('mean_judge_score'))}")

    _step(8, "Chay data quality checks va freshness report...")
    quality = run_data_quality_checks(df, settings, QUALITY_REPORT_NAME)
    freshness = build_freshness_report(df, settings, settings.paths.freshness_report)
    passed_count, failed_count = _quality_counts(quality)
    _detail(f"quality checks: pass={passed_count} | fail={failed_count}")
    _detail(f"freshness: {_freshness_status(freshness)}")

    _step(9, "Sinh markdown report cho phase 1...")
    source_summary = _build_source_summary(settings, records, df, source_mode)
    generate_phase1_report(settings.paths.baseline_report, source_summary, summary, quality, freshness)
    _detail(f"report -> {settings.paths.baseline_report}")

    _step(10, f"Demo agent tren {DEMO_QUESTION_LIMIT} cau hoi dau (best effort)...")
    _run_agent_demo(settings, index, test_set)

    _print_artifacts(settings)
    print("\nPHASE 1 hoan tat.")
