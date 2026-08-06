from __future__ import annotations

from typing import Any

from core.utils import now_utc, write_text

FALLBACK_JUDGE_MARKER = "Fallback heuristic judge"

METRIC_LABELS: list[tuple[str, str]] = [
    ("retrieval_hit_rate", "Retrieval hit rate"),
    ("mean_token_f1", "Mean token F1"),
    ("judge_accuracy", "Judge accuracy"),
    ("mean_judge_score", "Mean judge score (1-5)"),
]


def describe_judge_mode(answers: list[dict[str, Any]]) -> str:
    """`judge_*` chi so sanh duoc khi ca ba trang thai dung cung mot judge, nen phai ghi ro."""
    if not answers:
        return "n/a"
    fallback = sum(1 for item in answers if FALLBACK_JUDGE_MARKER in item.get("judge", {}).get("reasoning", ""))
    if fallback == 0:
        return f"LLM judge ({len(answers)}/{len(answers)})"
    if fallback == len(answers):
        return f"heuristic judge ({fallback}/{len(answers)})"
    return f"mixed: {len(answers) - fallback} LLM / {fallback} heuristic"


def _fmt(value: Any, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, float)):
        return f"{value:.{digits}f}" if isinstance(value, float) else str(value)
    return str(value)


def _fmt_metric(value: Any, digits: int = 4) -> str:
    """Metric luon in dang thap phan de cot so thang hang, ke ca khi mean() tra ve int."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return _fmt(value, digits)
    return f"{float(value):.{digits}f}"


def _fmt_delta(current: Any, baseline: Any, digits: int = 4) -> str:
    if not isinstance(current, (int, float)) or not isinstance(baseline, (int, float)):
        return "n/a"
    delta = float(current) - float(baseline)
    arrow = "=" if abs(delta) < 1e-9 else ("v" if delta < 0 else "^")
    return f"{delta:+.{digits}f} {arrow}"


def _quality_status(quality: dict[str, Any] | None) -> str:
    if not quality:
        return "n/a"
    summary = quality.get("summary", {})
    status = "PASS" if quality.get("success") else "FAIL"
    return f"{status} ({summary.get('passed', '?')}/{summary.get('total', '?')} checks)"


def _failed_checks(quality: dict[str, Any] | None) -> str:
    if not quality:
        return "n/a"
    failed = quality.get("failed_checks") or []
    return ", ".join(failed) if failed else "-"


def _freshness_status(freshness: dict[str, Any] | None) -> str:
    if not freshness:
        return "n/a"
    return f"{freshness.get('status', '?')} ({freshness.get('stale_rows', '?')} stale rows)"


def _ragas_section(metrics: dict[str, Any]) -> list[str]:
    ragas = metrics.get("ragas")
    if not isinstance(ragas, dict):
        return []
    if "skipped" in ragas:
        return ["", f"> Ragas: {ragas['skipped']}"]
    if "error" in ragas:
        return ["", f"> Ragas: {ragas['error']}"]
    lines = ["", "### Ragas", "", "| Metric | Value |", "| --- | --- |"]
    lines += [f"| {key} | {_fmt(value)} |" for key, value in ragas.items()]
    return lines


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Viet markdown report cho baseline phase."""
    lines: list[str] = [
        "# Phase 1 - Baseline pipeline report",
        "",
        f"Generated at: `{now_utc().isoformat()}`",
        "",
        "## 1. Nguon du lieu",
        "",
        "| Field | Value |",
        "| --- | --- |",
    ]
    lines += [f"| {key} | {_fmt(value)} |" for key, value in source_summary.items()]

    lines += [
        "",
        "## 2. Evaluation metrics (du lieu sach)",
        "",
        f"Test set: **{metrics.get('samples', 'n/a')}** cau hoi, dung chung cho ca 3 trang thai.",
        "",
        "| Metric | Value |",
        "| --- | --- |",
    ]
    lines += [f"| {label} | {_fmt_metric(metrics.get(key))} |" for key, label in METRIC_LABELS]
    lines += _ragas_section(metrics)

    lines += [
        "",
        "## 3. Data quality",
        "",
        f"- Engine: `{quality.get('engine', 'n/a')}`",
        f"- Ket qua: **{_quality_status(quality)}**",
        f"- Check that bai: {_failed_checks(quality)}",
        f"- So dong kiem tra: {quality.get('rows', 'n/a')}",
        "",
        "| Check | Column | Success | Observed |",
        "| --- | --- | --- | --- |",
    ]
    for check in quality.get("checks", []):
        lines.append(
            f"| `{check.get('name')}` | `{check.get('column') or '-'}` | "
            f"{'PASS' if check.get('success') else 'FAIL'} | `{check.get('observed')}` |"
        )

    lines += [
        "",
        "## 4. Freshness",
        "",
        "| Field | Value |",
        "| --- | --- |",
    ]
    lines += [f"| {key} | {_fmt(value)} |" for key, value in freshness.items()]

    lines += [
        "",
        "## 5. Doc ket qua",
        "",
        "- `retrieval_hit_rate` cho biet retriever co lay dung paper chua ground truth hay khong.",
        "- `mean_token_f1` do do trung lexical giua cau tra loi va ground truth.",
        "- `judge_accuracy` / `mean_judge_score` la danh gia cua LLM judge tren cung cau hoi.",
        "- Data quality va freshness la tin hieu chan truoc: neu chung FAIL thi metrics phia sau khong dang tin.",
        "",
    ]

    write_text(report_path, "\n".join(lines))
    print(f"[report] baseline report -> {report_path}")


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
    baseline_quality: dict[str, Any] | None = None,
    baseline_freshness: dict[str, Any] | None = None,
    corruption_log: dict[str, Any] | None = None,
    judge_modes: dict[str, str] | None = None,
) -> None:
    """Viet markdown report so sanh baseline / corrupted / repaired."""
    lines: list[str] = [
        "# Corruption flow - baseline vs corrupted vs repaired",
        "",
        f"Generated at: `{now_utc().isoformat()}`",
        "",
        "Ca ba trang thai duoc danh gia tren **cung mot evaluation set** va cung cau hinh retrieval.",
        "",
        "## 1. Metrics",
        "",
        "| Metric | Baseline | Corrupted | Repaired | Corrupted vs baseline | Repaired vs baseline |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for key, label in METRIC_LABELS:
        baseline_value = baseline_metrics.get(key)
        corrupted_value = corrupted_metrics.get(key)
        repaired_value = repaired_metrics.get(key)
        lines.append(
            f"| {label} | {_fmt_metric(baseline_value)} | {_fmt_metric(corrupted_value)} | "
            f"{_fmt_metric(repaired_value)} | {_fmt_delta(corrupted_value, baseline_value)} | "
            f"{_fmt_delta(repaired_value, baseline_value)} |"
        )

    if judge_modes:
        modes = set(judge_modes.values())
        lines += [
            "",
            f"Judge duoc dung: baseline = `{judge_modes.get('baseline', 'n/a')}`, "
            f"corrupted = `{judge_modes.get('corrupted', 'n/a')}`, "
            f"repaired = `{judge_modes.get('repaired', 'n/a')}`.",
        ]
        if len(modes) > 1:
            lines.append(
                "> Canh bao: ba trang thai khong dung cung mot judge, nen chi `retrieval_hit_rate` "
                "va `mean_token_f1` la so sanh duoc truc tiep."
            )

    lines += [
        "",
        "## 2. Data quality va freshness",
        "",
        "| Signal | Baseline | Corrupted | Repaired |",
        "| --- | --- | --- | --- |",
        f"| Quality suite | {_quality_status(baseline_quality)} | {_quality_status(corrupted_quality)} | "
        f"{_quality_status(repaired_quality)} |",
        f"| Failed checks | {_failed_checks(baseline_quality)} | {_failed_checks(corrupted_quality)} | "
        f"{_failed_checks(repaired_quality)} |",
        f"| Freshness | {_freshness_status(baseline_freshness)} | {_freshness_status(corrupted_freshness)} | "
        f"{_freshness_status(repaired_freshness)} |",
        f"| Latest published | {_fmt((baseline_freshness or {}).get('latest_published'))} | "
        f"{_fmt(corrupted_freshness.get('latest_published'))} | {_fmt(repaired_freshness.get('latest_published'))} |",
        f"| Rows | {_fmt((baseline_freshness or {}).get('total_rows'))} | "
        f"{_fmt(corrupted_freshness.get('total_rows'))} | {_fmt(repaired_freshness.get('total_rows'))} |",
    ]

    if corruption_log:
        lines += [
            "",
            "## 3. Cac loi da inject",
            "",
            f"Row: {corruption_log.get('original_rows')} -> {corruption_log.get('corrupted_rows')} "
            f"({corruption_log.get('row_delta'):+d})",
            "",
            "| Loai loi | So dong | Mo ta |",
            "| --- | --- | --- |",
        ]
        for event in corruption_log.get("events", []):
            lines.append(f"| `{event.get('type')}` | {event.get('affected_rows')} | {event.get('description')} |")

    baseline_hit = baseline_metrics.get("retrieval_hit_rate")
    corrupted_hit = corrupted_metrics.get("retrieval_hit_rate")
    repaired_hit = repaired_metrics.get("retrieval_hit_rate")
    recovered = (
        isinstance(repaired_hit, (int, float))
        and isinstance(baseline_hit, (int, float))
        and repaired_hit >= baseline_hit - 1e-9
    )
    degraded = (
        isinstance(corrupted_hit, (int, float))
        and isinstance(baseline_hit, (int, float))
        and corrupted_hit < baseline_hit
    )

    lines += [
        "",
        "## 4. Ket luan",
        "",
        f"- Corruption {'lam giam' if degraded else 'khong lam giam'} retrieval hit rate "
        f"({_fmt_metric(baseline_hit)} -> {_fmt_metric(corrupted_hit)}).",
        f"- Repair tu raw records {'khoi phuc duoc' if recovered else 'chua khoi phuc duoc'} muc baseline "
        f"({_fmt_metric(corrupted_hit)} -> {_fmt_metric(repaired_hit)}).",
        "- Data quality suite phat hien loi ngay o buoc dataset, truoc khi cau tra loi sai den tay nguoi dung.",
        "",
    ]

    write_text(report_path, "\n".join(lines))
    print(f"[report] comparison report -> {report_path}")
