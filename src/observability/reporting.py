from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from core.utils import compact_join, normalize_whitespace, now_utc, write_text

# Gia tri hien thi khi thieu du lieu, khong bao gio hardcode con so that
_NA = "n/a"

# Cac metric duoc so sanh giua baseline / corrupted / repaired
_METRIC_KEYS: tuple[str, ...] = (
    "retrieval_hit_rate",
    "mean_token_f1",
    "judge_accuracy",
    "mean_judge_score",
)

# Cac truong freshness duoc uu tien hien thi truoc
_FRESHNESS_KEYS: tuple[str, ...] = (
    "latest_published",
    "oldest_published",
    "stale_rows",
    "total_rows",
    "is_fresh",
)

# Sai so cho phep khi so sanh float
_EPS = 5e-5


# ---------------------------------------------------------------------------
# Helper format
# ---------------------------------------------------------------------------
def _fmt_number(value: Any) -> str:
    """Format so: float 4 chu so thap phan, int de nguyen, None -> n/a."""
    if value is None:
        return _NA
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value != value:  # NaN
            return _NA
        return f"{value:.4f}"
    return str(value)


def _fmt_metric(value: Any) -> str:
    """Format gia tri metric: luon 4 chu so thap phan de cac cot trong bang thang hang.

    Vi du mean_judge_score = 5 (int) van hien thi la 5.0000 thay vi 5.
    """
    if isinstance(value, bool) or value is None:
        return _fmt_number(value)
    if isinstance(value, (int, float)):
        if value != value:  # NaN
            return _NA
        return f"{float(value):.4f}"
    return _fmt_number(value)


def _fmt_value(value: Any) -> str:
    """Format bat ky gia tri nao thanh chuoi an toan cho markdown."""
    if value is None:
        return _NA
    if isinstance(value, (bool, int, float)):
        return _fmt_number(value)
    if isinstance(value, Mapping):
        parts = [f"{key}={_fmt_value(item)}" for key, item in value.items()]
        return compact_join(parts, "; ") or _NA
    if isinstance(value, (list, tuple, set)):
        parts = [_fmt_value(item) for item in value]
        return compact_join(parts, ", ") or _NA
    text = normalize_whitespace(str(value))
    return text or _NA


def _truncate(text: str, limit: int = 200) -> str:
    """Cat bot chuoi qua dai de bang markdown van doc duoc."""
    cleaned = normalize_whitespace(text)
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: max(limit - 3, 1)].rstrip() + "..."


def _cell(value: Any) -> str:
    """Chuan bi mot o trong bang markdown (escape dau gach dung)."""
    return _truncate(_fmt_value(value)).replace("|", "\\|")


def _signed(delta: float | None) -> str:
    """Format delta co dau, them dau + khi tang."""
    if delta is None:
        return _NA
    if abs(delta) < _EPS:
        return "0.0000"
    if delta > 0:
        return f"+{delta:.4f}"
    return f"{delta:.4f}"


def _md_table(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> str:
    """Dung bang markdown tu header va cac dong du lieu."""
    lines = [
        "| " + " | ".join(str(head) for head in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    count = 0
    for row in rows:
        lines.append("| " + " | ".join(_cell(cell) for cell in row) + " |")
        count += 1
    if count == 0:
        lines.append("| " + " | ".join(_NA for _ in headers) + " |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helper doc payload mot cach an toan
# ---------------------------------------------------------------------------
def _items(payload: Any) -> list[tuple[str, Any]]:
    """Lay danh sach (key, value) tu mot mapping, rong neu payload khong hop le."""
    if not isinstance(payload, Mapping):
        return []
    return [(str(key), value) for key, value in payload.items()]


def _pick(payload: Any, keys: Sequence[str], default: Any = None) -> Any:
    """Lay gia tri dau tien khong None theo danh sach ten key thay the."""
    if not isinstance(payload, Mapping):
        return default
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return default


def _as_bool(value: Any) -> bool | None:
    """Ep gia tri ve bool, tra None neu khong hieu duoc."""
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"true", "pass", "passed", "success", "succeeded", "ok", "yes", "1"}:
        return True
    if text in {"false", "fail", "failed", "failure", "error", "no", "0"}:
        return False
    return None


def _pass_label(flag: bool | None) -> str:
    """Doi bool thanh nhan PASS / FAIL."""
    if flag is None:
        return _NA
    return "PASS" if flag else "FAIL"


def _num(payload: Any, key: str) -> float | None:
    """Doc mot metric dang so tu payload, tra None neu thieu hoac khong parse duoc."""
    if not isinstance(payload, Mapping):
        return None
    value = payload.get(key)
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        return None if number != number else number
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _delta(new: float | None, old: float | None) -> float | None:
    """Tinh chenh lech new - old, None neu thieu mot dau."""
    if new is None or old is None:
        return None
    return new - old


def _relative(delta: float | None, base: float | None) -> float | None:
    """Chuan hoa delta theo do lon baseline de so sanh cac metric khac thang do."""
    if delta is None:
        return None
    if base is None or abs(base) < _EPS:
        return delta
    return delta / abs(base)


def _raw_metric(payload: Any, key: str) -> str:
    """Format metric tu gia tri goc de khop voi bang so sanh."""
    return _fmt_number(payload.get(key) if isinstance(payload, Mapping) else None)


# ---------------------------------------------------------------------------
# Helper doc data quality payload
# ---------------------------------------------------------------------------
def _iter_checks(quality: Any) -> list[dict[str, Any]]:
    """Chuan hoa danh sach check ve list[dict] du payload la list hay dict."""
    raw = _pick(quality, ("checks", "results", "expectations", "validations"), default=[])
    checks: list[dict[str, Any]] = []
    if isinstance(raw, Mapping):
        for name, item in raw.items():
            if isinstance(item, Mapping):
                merged = dict(item)
                merged.setdefault("name", name)
                checks.append(merged)
            else:
                checks.append({"name": name, "success": item})
    elif isinstance(raw, (list, tuple)):
        for item in raw:
            if isinstance(item, Mapping):
                checks.append(dict(item))
    return checks


def _check_name(check: Mapping[str, Any]) -> str:
    return str(_pick(check, ("name", "check", "check_name", "expectation_type", "id"), default="unnamed"))


def _check_success(check: Mapping[str, Any]) -> bool | None:
    return _as_bool(_pick(check, ("success", "passed", "ok", "is_success", "status", "result")))


def _check_dimension(check: Mapping[str, Any]) -> Any:
    return _pick(check, ("dimension", "quality_dimension", "category", "type"))


def _check_expected(check: Mapping[str, Any]) -> Any:
    return _pick(check, ("expected", "expectation", "threshold", "expected_value", "rule"))


def _check_actual(check: Mapping[str, Any]) -> Any:
    return _pick(check, ("actual", "observed", "actual_value", "value", "result_value"))


def _check_failed_rows(check: Mapping[str, Any]) -> Any:
    return _pick(
        check,
        ("failed_rows", "unexpected_count", "failed_count", "error_rows", "bad_rows", "violations"),
    )


def _quality_summary(quality: Any) -> tuple[int, int, bool | None]:
    """Tra ve (so check pass, tong so check, trang thai chung)."""
    checks = _iter_checks(quality)
    computed_total = len(checks)
    computed_passed = sum(1 for check in checks if _check_success(check) is True)

    raw_passed = _pick(quality, ("passed", "passed_checks", "success_count", "n_passed"))
    raw_total = _pick(quality, ("total", "total_checks", "n_checks", "checks_count"))
    passed = raw_passed if isinstance(raw_passed, int) and not isinstance(raw_passed, bool) else computed_passed
    total = raw_total if isinstance(raw_total, int) and not isinstance(raw_total, bool) else computed_total

    success = _as_bool(_pick(quality, ("success", "overall_success", "is_success", "all_passed")))
    if success is None and total > 0:
        success = passed == total
    return passed, total, success


def _check_map(quality: Any) -> dict[str, bool | None]:
    """Map ten check -> trang thai pass/fail."""
    return {_check_name(check): _check_success(check) for check in _iter_checks(quality)}


def _failed_names(quality: Any, limit: int = 3) -> str:
    """Liet ke ten cac check bi fail de dua vao cau nhan xet."""
    names = [name for name, flag in _check_map(quality).items() if flag is False]
    if not names:
        return "khong co check nao fail"
    shown = ", ".join(names[:limit])
    if len(names) > limit:
        shown = f"{shown}, +{len(names) - limit} check khac"
    return shown


def _freshness_fields(*payloads: Any) -> list[str]:
    """Lay danh sach truong freshness: uu tien truong chuan roi den truong phat sinh."""
    fields = [key for key in _FRESHNESS_KEYS]
    for payload in payloads:
        for key, _ in _items(payload):
            if key not in fields:
                fields.append(key)
    return fields


# ---------------------------------------------------------------------------
# Helper sinh nhan xet
# ---------------------------------------------------------------------------
def _ragas_lines(ragas: Any) -> list[str]:
    """Sinh cac dong mo ta ket qua Ragas (co the la skipped / error / diem so)."""
    if ragas is None:
        return [f"- Ragas: {_NA} (metrics khong co khoa 'ragas')."]
    if isinstance(ragas, Mapping):
        if not ragas:
            return [f"- Ragas: {_NA} (payload rong)."]
        if "skipped" in ragas:
            return [f"- Ragas: bo qua - {_truncate(_fmt_value(ragas['skipped']))}"]
        if "error" in ragas:
            return [f"- Ragas: loi - {_truncate(_fmt_value(ragas['error']))}"]
        return [f"- Ragas.{key}: {_fmt_value(value)}" for key, value in ragas.items()]
    return [f"- Ragas: {_truncate(_fmt_value(ragas))}"]


def _level_label(value: float | None) -> str:
    """Doi diem so 0..1 thanh nhan dinh tinh."""
    if value is None:
        return _NA
    if value >= 0.9:
        return "rat cao"
    if value >= 0.7:
        return "kha"
    if value >= 0.5:
        return "trung binh"
    return "thap"


def _phase1_notes(metrics: Any, quality: Any, freshness: Any) -> list[str]:
    """Sinh 3-6 nhan xet duoc tinh tu chinh cac con so trong artifact."""
    notes: list[str] = []

    passed, total, success = _quality_summary(quality)
    if total > 0:
        ratio = passed / total
        if passed == total:
            verdict = "tat ca check deu pass nen dataset dat chuan de dung cho retrieval"
        else:
            verdict = f"con {total - passed} check fail ({_failed_names(quality)}) nen can xu ly truoc khi tin ket qua"
        notes.append(
            f"Data quality: {passed}/{total} check pass (ty le {ratio:.4f}, trang thai chung "
            f"{_pass_label(success)}), {verdict}."
        )
    else:
        notes.append("Data quality: chua ghi nhan check nao trong payload nen chua the ket luan ve chat luong du lieu.")

    is_fresh = _as_bool(_pick(freshness, ("is_fresh", "fresh", "passed")))
    latest = _pick(freshness, ("latest_published", "newest_published", "max_published"))
    oldest = _pick(freshness, ("oldest_published", "min_published"))
    stale_rows = _pick(freshness, ("stale_rows", "stale_count"))
    total_rows = _pick(freshness, ("total_rows", "row_count", "rows"))
    stale_ratio = None
    if isinstance(stale_rows, (int, float)) and isinstance(total_rows, (int, float)) and total_rows:
        stale_ratio = float(stale_rows) / float(total_rows)
    stale_text = f"{_fmt_value(stale_rows)}/{_fmt_value(total_rows)} dong stale"
    if stale_ratio is not None:
        stale_text = f"{stale_text} (ty le {stale_ratio:.4f})"
    if is_fresh is True:
        notes.append(
            f"Freshness: dataset con moi, latest_published={_fmt_value(latest)}, "
            f"oldest_published={_fmt_value(oldest)}, {stale_text}."
        )
    elif is_fresh is False:
        notes.append(
            f"Freshness: dataset da qua han, latest_published={_fmt_value(latest)} voi {stale_text}, "
            "nen refresh lai nguon truoc khi danh gia agent."
        )
    else:
        notes.append(
            f"Freshness: thieu tin hieu is_fresh, chi biet latest_published={_fmt_value(latest)} va {stale_text}."
        )

    samples = _num(metrics, "samples")
    hit_rate = _num(metrics, "retrieval_hit_rate")
    sample_text = f" tren {int(samples)} cau hoi" if samples is not None else ""
    if hit_rate is None:
        notes.append(f"Retrieval: metrics khong co retrieval_hit_rate{sample_text} nen chua danh gia duoc khau tim kiem.")
    else:
        gap = 1.0 - hit_rate
        notes.append(
            f"Retrieval: retrieval_hit_rate={hit_rate:.4f}{sample_text}, muc do {_level_label(hit_rate)}, "
            f"con thieu {gap:.4f} so voi muc toi da 1.0000."
        )

    token_f1 = _num(metrics, "mean_token_f1")
    judge_acc = _num(metrics, "judge_accuracy")
    judge_score = _num(metrics, "mean_judge_score")
    parts = []
    if token_f1 is not None:
        parts.append(f"mean_token_f1={token_f1:.4f}")
    if judge_acc is not None:
        parts.append(f"judge_accuracy={judge_acc:.4f}")
    if judge_score is not None:
        parts.append(f"mean_judge_score={_fmt_number(judge_score if judge_score % 1 else int(judge_score))}")
    if parts:
        level_source = judge_acc if judge_acc is not None else token_f1
        notes.append(f"Chat luong tra loi: {', '.join(parts)} -> muc {_level_label(level_source)}.")
    else:
        notes.append("Chat luong tra loi: khong co mean_token_f1 / judge_accuracy trong metrics de nhan xet.")

    ragas = metrics.get("ragas") if isinstance(metrics, Mapping) else None
    if isinstance(ragas, Mapping) and "skipped" in ragas:
        notes.append("Ragas bi bo qua nen ket luan hien dua hoan toan vao token-F1 va LLM judge.")
    elif isinstance(ragas, Mapping) and "error" in ragas:
        notes.append(f"Ragas chay loi ({_truncate(_fmt_value(ragas['error']), 80)}) nen chi so nay chua dung de doi chieu.")
    elif isinstance(ragas, Mapping) and ragas:
        notes.append(f"Ragas co ket qua bo sung: {_truncate(_fmt_value(ragas), 160)}.")

    return notes[:6]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Viet markdown report cho baseline phase tu cac artifact da sinh ra.

    Moi con so trong report deu duoc doc tu 4 payload dau vao, khong hardcode.
    """
    generated = now_utc().strftime("%Y-%m-%d %H:%M:%S UTC")
    lines: list[str] = [
        "# Phase 1 - Baseline Report",
        "",
        f"_Generated: {generated}_",
        "",
        "## 1. Nguon du lieu",
        "",
        _md_table(("Truong", "Gia tri"), ((key, value) for key, value in _items(source_summary))),
        "",
        "## 2. Evaluation metrics",
        "",
        _md_table(
            ("Metric", "Gia tri"),
            (
                (
                    key,
                    (_fmt_number if key == "samples" else _fmt_metric)(metrics.get(key))
                    if isinstance(metrics, Mapping)
                    else _NA,
                )
                for key in ("samples", *_METRIC_KEYS)
            ),
        ),
        "",
    ]
    lines.extend(_ragas_lines(metrics.get("ragas") if isinstance(metrics, Mapping) else None))
    lines.append("")

    passed, total, success = _quality_summary(quality)
    checks = _iter_checks(quality)
    ratio_text = f"{passed / total:.4f}" if total > 0 else _NA
    lines.extend(
        [
            "## 3. Data quality",
            "",
            f"- Tong quan: {passed}/{total} check pass (ty le {ratio_text}), trang thai chung: {_pass_label(success)}.",
            "",
            _md_table(
                ("Check", "Dimension", "Ket qua", "Ky vong", "Thuc te", "So dong loi"),
                (
                    (
                        _check_name(check),
                        _check_dimension(check),
                        _pass_label(_check_success(check)),
                        _check_expected(check),
                        _check_actual(check),
                        _check_failed_rows(check),
                    )
                    for check in checks
                ),
            ),
            "",
            "## 4. Freshness",
            "",
            _md_table(("Truong", "Gia tri"), ((key, value) for key, value in _items(freshness))),
            "",
            "## 5. Nhan xet",
            "",
        ]
    )
    lines.extend(f"- {note}" for note in _phase1_notes(metrics, quality, freshness))

    write_text(report_path, "\n".join(lines).rstrip() + "\n")


def _corruption_summary_paragraph(
    baseline_metrics: Any,
    corrupted_metrics: Any,
    repaired_metrics: Any,
) -> str:
    """Sinh doan tom tat duoc tinh tu delta giua ba trang thai."""
    tracked = 0
    dropped: list[tuple[str, float, float]] = []
    recovered = 0
    for key in _METRIC_KEYS:
        base = _num(baseline_metrics, key)
        corrupt = _num(corrupted_metrics, key)
        repair = _num(repaired_metrics, key)
        drop = _delta(corrupt, base)
        if drop is None:
            continue
        tracked += 1
        if drop < -_EPS:
            dropped.append((key, drop, _relative(drop, base) or drop))
        if repair is not None and base is not None and repair >= base - _EPS:
            recovered += 1

    if tracked == 0:
        return (
            "Khong doc duoc metric chung nao giua baseline, corrupted va repaired nen chua the "
            "dinh luong tac dong cua corruption."
        )

    if dropped:
        worst_key, worst_delta, worst_rel = min(dropped, key=lambda item: item[2])
        impact = (
            f"corruption lam giam {len(dropped)}/{tracked} metric, manh nhat la {worst_key} "
            f"({_signed(worst_delta)}, tuong duong {abs(worst_rel):.4f} lan gia tri baseline)"
        )
    else:
        impact = f"corruption khong lam giam metric nao trong {tracked} metric duoc theo doi"

    return (
        f"Bao cao so sanh {tracked} metric chinh giua ba trang thai baseline / corrupted / repaired: "
        f"{impact}. Sau khi repair, {recovered}/{tracked} metric quay ve muc bang hoac cao hon baseline. "
        f"Chi tiet tung metric, tung data quality check va tin hieu freshness nam o cac muc ben duoi."
    )


def _corruption_conclusions(
    baseline_metrics: Any,
    corrupted_metrics: Any,
    repaired_metrics: Any,
    corrupted_quality: Any,
    repaired_quality: Any,
    corrupted_freshness: Any,
    repaired_freshness: Any,
) -> list[str]:
    """Sinh cac chuoi nhan qua corruption -> tin hieu -> metric, tinh tu so lieu."""
    corrupt_passed, corrupt_total, _ = _quality_summary(corrupted_quality)
    repair_passed, repair_total, _ = _quality_summary(repaired_quality)
    corrupt_fresh = _as_bool(_pick(corrupted_freshness, ("is_fresh", "fresh", "passed")))
    repair_fresh = _as_bool(_pick(repaired_freshness, ("is_fresh", "fresh", "passed")))
    corrupt_stale = _pick(corrupted_freshness, ("stale_rows", "stale_count"))
    repair_stale = _pick(repaired_freshness, ("stale_rows", "stale_count"))

    changes: list[tuple[str, float, float]] = []
    for key in _METRIC_KEYS:
        base = _num(baseline_metrics, key)
        drop = _delta(_num(corrupted_metrics, key), base)
        if drop is not None:
            changes.append((key, drop, _relative(drop, base) or drop))

    notes: list[str] = []
    signal_text = (
        f"data quality corrupted {corrupt_passed}/{corrupt_total} check pass "
        f"({_failed_names(corrupted_quality)}), freshness is_fresh={_fmt_value(corrupt_fresh)} "
        f"voi stale_rows={_fmt_value(corrupt_stale)}"
    )

    if not changes:
        notes.append(
            f"Corruption -> {signal_text} -> khong doc duoc metric nao de do tac dong, "
            "nen chua the ket luan corruption anh huong den agent."
        )
        focus_key = None
    else:
        worst_key, worst_delta, _worst_rel = min(changes, key=lambda item: item[2])
        focus_key = worst_key
        if worst_delta < -_EPS:
            notes.append(
                f"Corruption -> {signal_text} -> {worst_key} giam {_signed(worst_delta)} so voi baseline, "
                "chung to du lieu hong keo tut chat luong tra loi cua agent."
            )
        else:
            notes.append(
                f"Corruption -> {signal_text} -> khong metric nao giam (thay doi xau nhat la {worst_key} "
                f"{_signed(worst_delta)}), nen tren test set nay corruption chua lam hong ket qua agent."
            )

    repair_signal = (
        f"data quality repaired {repair_passed}/{repair_total} check pass, "
        f"freshness is_fresh={_fmt_value(repair_fresh)} voi stale_rows={_fmt_value(repair_stale)}"
    )
    if focus_key is None:
        notes.append(f"Repair -> {repair_signal} -> khong co metric de doi chieu muc phuc hoi.")
    else:
        base = _num(baseline_metrics, focus_key)
        corrupt = _num(corrupted_metrics, focus_key)
        repair = _num(repaired_metrics, focus_key)
        recovery = _delta(repair, corrupt)
        if recovery is None:
            notes.append(f"Repair -> {repair_signal} -> thieu gia tri {focus_key} sau repair nen chua do duoc phuc hoi.")
        elif recovery > _EPS:
            compare = (
                f"{_raw_metric(repaired_metrics, focus_key)} so voi baseline "
                f"{_raw_metric(baseline_metrics, focus_key)}"
            )
            if base is not None and repair is not None and repair >= base - _EPS:
                tail = f"va da ve bang hoac vuot baseline ({compare})"
            else:
                tail = f"nhung van thap hon baseline ({compare})"
            notes.append(f"Repair -> {repair_signal} -> {focus_key} phuc hoi {_signed(recovery)} {tail}.")
        else:
            notes.append(
                f"Repair -> {repair_signal} -> {focus_key} thay doi {_signed(recovery)} so voi corrupted, "
                "tuc la buoc repair chua tao ra phuc hoi do duoc tren metric nay."
            )

    corrupt_map = _check_map(corrupted_quality)
    repair_map = _check_map(repaired_quality)
    flipped = [name for name, flag in corrupt_map.items() if flag is False and repair_map.get(name) is True]
    still_failing = [name for name, flag in repair_map.items() if flag is False]
    if flipped:
        notes.append(
            f"Repair lam {len(flipped)} check chuyen tu FAIL sang PASS ({', '.join(flipped[:3])}), "
            f"dua ty le pass tu {corrupt_passed}/{corrupt_total} len {repair_passed}/{repair_total}."
        )
    elif still_failing:
        notes.append(
            f"Sau repair van con {len(still_failing)} check fail ({', '.join(still_failing[:3])}), "
            "nen tin hieu quality chua tro lai trang thai baseline."
        )
    elif repair_total > 0:
        notes.append(
            f"Cac check quality sau repair deu o trang thai {repair_passed}/{repair_total} pass, "
            "khop voi ky vong du lieu da duoc khoi phuc."
        )
    else:
        notes.append("Khong co data quality check nao duoc ghi nhan nen chua co bang chung ve viec khoi phuc du lieu.")

    if corrupt_fresh is False and repair_fresh is True:
        notes.append(
            f"Tin hieu freshness cung phuc hoi: stale_rows tu {_fmt_value(corrupt_stale)} ve "
            f"{_fmt_value(repair_stale)} va is_fresh tro lai true sau khi repair tu raw source."
        )

    return notes


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """Viet markdown report so sanh baseline / corrupted / repaired."""
    generated = now_utc().strftime("%Y-%m-%d %H:%M:%S UTC")

    metric_rows: list[tuple[Any, ...]] = []
    for key in _METRIC_KEYS:
        base = _num(baseline_metrics, key)
        corrupt = _num(corrupted_metrics, key)
        repair = _num(repaired_metrics, key)
        drop = _delta(corrupt, base)
        recovery = _delta(repair, corrupt)
        recovery_text = _signed(recovery)
        if repair is not None and base is not None and repair >= base - _EPS:
            recovery_text = f"{recovery_text} (da ve muc baseline)"
        metric_rows.append(
            (
                key,
                _fmt_metric(baseline_metrics.get(key) if isinstance(baseline_metrics, Mapping) else None),
                _fmt_metric(corrupted_metrics.get(key) if isinstance(corrupted_metrics, Mapping) else None),
                _fmt_metric(repaired_metrics.get(key) if isinstance(repaired_metrics, Mapping) else None),
                _signed(drop),
                recovery_text,
            )
        )

    corrupt_map = _check_map(corrupted_quality)
    repair_map = _check_map(repaired_quality)
    check_names = list(corrupt_map.keys())
    check_names.extend(name for name in repair_map if name not in corrupt_map)
    quality_rows = [
        (name, _pass_label(corrupt_map.get(name)), _pass_label(repair_map.get(name))) for name in check_names
    ]

    freshness_rows = [
        (
            field,
            _pick(corrupted_freshness, (field,)),
            _pick(repaired_freshness, (field,)),
        )
        for field in _freshness_fields(corrupted_freshness, repaired_freshness)
    ]

    lines: list[str] = [
        "# Corruption Impact Report",
        "",
        f"_Generated: {generated}_",
        "",
        "## 1. Tom tat",
        "",
        _corruption_summary_paragraph(baseline_metrics, corrupted_metrics, repaired_metrics),
        "",
        "## 2. So sanh metrics",
        "",
        _md_table(
            (
                "Metric",
                "Baseline",
                "Corrupted",
                "Repaired",
                "Thay doi do corruption",
                "Muc phuc hoi",
            ),
            metric_rows,
        ),
        "",
        "## 3. Data quality theo trang thai",
        "",
        _md_table(("Check", "Corrupted", "Repaired"), quality_rows),
        "",
        "## 4. Freshness theo trang thai",
        "",
        _md_table(("Truong", "Corrupted", "Repaired"), freshness_rows),
        "",
        "## 5. Ket luan",
        "",
    ]
    lines.extend(
        f"{index}. {note}"
        for index, note in enumerate(
            _corruption_conclusions(
                baseline_metrics,
                corrupted_metrics,
                repaired_metrics,
                corrupted_quality,
                repaired_quality,
                corrupted_freshness,
                repaired_freshness,
            ),
            start=1,
        )
    )

    write_text(report_path, "\n".join(lines).rstrip() + "\n")


# ---------------------------------------------------------------------------
# Bao cao doi chieu CAU TRA LOI THAT giua ba trang thai
# ---------------------------------------------------------------------------
_ANSWER_PREVIEW_CHARS = 160


def _answers_by_id(answers: Any) -> dict[str, Mapping[str, Any]]:
    """Danh index cac cau tra loi theo id de doi chieu ba trang thai."""
    if not isinstance(answers, Sequence):
        return {}
    return {str(item.get("id")): item for item in answers if isinstance(item, Mapping) and item.get("id")}


def _preview(text: Any) -> str:
    """Rut gon cau tra loi de dua vao bang, giu nguyen y nghia."""
    value = normalize_whitespace(str(text or ""))
    if not value:
        return "(rong)"
    return value if len(value) <= _ANSWER_PREVIEW_CHARS else value[:_ANSWER_PREVIEW_CHARS] + "..."


def _verdict(item: Mapping[str, Any] | None) -> str:
    """Tom tat ket qua cham diem cua mot cau."""
    if not isinstance(item, Mapping):
        return _NA
    judge = item.get("judge") if isinstance(item.get("judge"), Mapping) else {}
    return (
        f"judge {_fmt_number(judge.get('score'))}/5, "
        f"F1 {_fmt_number(item.get('token_f1'))}, "
        f"tim dung bai: {'co' if item.get('retrieval_hit') else 'khong'}"
    )


def generate_answer_diff_report(
    report_path,
    baseline_answers: Any,
    corrupted_answers: Any,
    repaired_answers: Any,
) -> None:
    """Doi chieu cau tra loi that cua agent giua baseline / corrupted / repaired.

    Muc dich: chung minh anh huong cua data quality bang chinh OUTPUT ma nguoi dung nhan duoc,
    khong chi bang metric. Day la bang chung truc quan nhat cho ket luan cua bai lab.
    """
    base = _answers_by_id(baseline_answers)
    corrupt = _answers_by_id(corrupted_answers)
    repair = _answers_by_id(repaired_answers)

    changed = [qid for qid in base if _preview(base[qid].get("answer")) != _preview(corrupt.get(qid, {}).get("answer"))]
    recovered = [qid for qid in changed if _preview(base[qid].get("answer")) == _preview(repair.get(qid, {}).get("answer"))]

    lines: list[str] = [
        "# Doi chieu cau tra loi cua agent theo trang thai du lieu",
        "",
        f"_Generated: {now_utc().strftime('%Y-%m-%d %H:%M:%S')} UTC_",
        "",
        "## 1. Tong quan",
        "",
        f"- Tong so cau hoi: **{len(base)}** (cung mot evaluation set cho ca ba trang thai).",
        f"- So cau bi DOI cau tra loi khi du lieu bi corrupt: **{len(changed)}/{len(base)}**.",
        f"- So cau QUAY VE dung cau tra loi baseline sau khi repair: **{len(recovered)}/{len(changed)}**.",
        "",
        "## 2. Cac cau co output khac nhau",
        "",
    ]

    if not changed:
        lines.append("Khong co cau nao doi cau tra loi: corruption chua tac dong den output cua agent.")
    else:
        for qid in changed:
            b, c, r = base.get(qid), corrupt.get(qid), repair.get(qid)
            lines.extend(
                [
                    f"### {qid} - loai `{(b or {}).get('question_type', _NA)}`",
                    "",
                    f"**Cau hoi:** {_preview((b or {}).get('question'))}",
                    "",
                    _md_table(
                        ("Trang thai", "Cau tra loi cua agent", "Ket qua cham"),
                        (
                            ("Baseline (du lieu sach)", _preview((b or {}).get("answer")), _verdict(b)),
                            ("Corrupted (du lieu hong)", _preview((c or {}).get("answer")), _verdict(c)),
                            ("Repaired (da sua)", _preview((r or {}).get("answer")), _verdict(r)),
                        ),
                    ),
                    "",
                ]
            )

    unchanged = [qid for qid in base if qid not in changed]
    lines.extend(
        [
            "## 3. Cac cau khong doi output",
            "",
            f"{len(unchanged)}/{len(base)} cau giu nguyen cau tra loi vi corruption khong cham vao "
            "paper tuong ung hoac khong cham vao truong du lieu ma cau hoi do can:",
            "",
            ", ".join(f"`{qid}`" for qid in unchanged) or _NA,
            "",
            "## 4. Ket luan",
            "",
        ]
    )

    if changed and len(recovered) == len(changed):
        lines.append(
            f"Du lieu hong lam **{len(changed)}/{len(base)}** cau tra loi sai lech so voi baseline, "
            f"va repair tu raw snapshot dua **toan bo {len(recovered)}** cau ve dung cau tra loi ban dau. "
            "Day la bang chung truc tiep o muc output, doc lap voi cac chi so tong hop."
        )
    elif changed:
        lines.append(
            f"Du lieu hong lam **{len(changed)}/{len(base)}** cau tra loi sai lech, "
            f"repair khoi phuc duoc **{len(recovered)}/{len(changed)}** cau. "
            "Cac cau chua khoi phuc can duoc dieu tra them."
        )
    else:
        lines.append(
            "Corruption khong lam thay doi output nao cua agent. Can xem lai muc do hoac vi tri corruption "
            "truoc khi ket luan ve anh huong cua data quality."
        )

    write_text(report_path, "\n".join(lines).rstrip() + "\n")
