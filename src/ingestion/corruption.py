from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import now_utc, write_json


# So dong toi thieu cua clean dataset de con y nghia khi lam hong.
MIN_SOURCE_ROWS = 8

# Cac tham so corruption: tat ca deu co dinh de lab chay lai cho ket qua giong nhau.
DROP_LATEST = 3
BLANK_COUNT = 3
NOISE_COUNT = 3
TRUNCATE_COUNT = 3
# Cat con 8 ky tu (ngan hon nguong title_min_length = 10) de quality check bat duoc loi nay.
TRUNCATE_CHARS = 8
STALE_COUNT = 4
STALE_YEARS = 3
DAYS_PER_YEAR = 365
DUPLICATE_COUNT = 2

# evaluation/testset.py chon paper duoc cham diem theo buoc nhay TESTSET_STRIDE, bat dau tu dong 0.
# Sau khi xoa DROP_LATEST dong dau, cac paper do doi ve lan vi tri bat dau tu EVAL_LANE_START.
# Moi loai corruption duoc gan mot diem xuat phat khac nhau tren lan do, nen moi loai deu cham
# dung MOT paper dang duoc cham diem -> tac dong cua tung loai deu do duoc rieng biet.
TESTSET_STRIDE = 4
EVAL_LANE_START = (-DROP_LATEST) % TESTSET_STRIDE
# Buoc nhay lech pha voi lan test set, nen cac dong con lai roi vao paper khong duoc cham.
SELECTION_STRIDE = TESTSET_STRIDE + 1

BLANK_OFFSET = EVAL_LANE_START + 0 * TESTSET_STRIDE
NOISE_OFFSET = EVAL_LANE_START + 1 * TESTSET_STRIDE
TRUNCATE_OFFSET = EVAL_LANE_START + 2 * TESTSET_STRIDE
STALE_OFFSET = EVAL_LANE_START + 3 * TESTSET_STRIDE
DUPLICATE_OFFSET = 0

# Chuoi rac ASCII de nhoi vao summary. Ket thuc bang dau cham de no tu tao thanh mot "cau",
# nhu vay first_sentence() se tra ve rac thay vi cau tom tat that -> do duoc bang token_f1.
NOISE_TOKEN = "LOREM IPSUM DOLOR ###### CORRUPTED PAYLOAD @@@@@@. "
NOISE_REPEAT = 3
NOISE_BLOB = NOISE_TOKEN * NOISE_REPEAT

# Gioi han so paper_id ghi vao log cho moi buoc.
MAX_LOGGED_IDS = 25

REQUIRED_COLUMNS = (
    "paper_id",
    "title",
    "summary",
    "authors_joined",
    "categories_joined",
    "published",
    "updated",
    "age_days",
    "title_chars",
    "summary_chars",
    "text_for_embedding",
)


def _require_columns(df: pd.DataFrame) -> None:
    """Bao loi som neu clean dataframe thieu cot can thiet."""
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Clean dataframe thieu cac cot bat buoc: {', '.join(missing)}.")


def _pick_positions(n_rows: int, count: int, offset: int, stride: int = 4) -> list[int]:
    """Chon toi da `count` vi tri khac nhau, bat dau tu `offset` va nhay theo `stride`.

    Khi chay qua cuoi frame thi quay vong bang modulo. Neu vi tri da duoc chon roi
    thi day them 1 buoc de khong bi lap vo han khi stride chia het n_rows.
    """
    if n_rows <= 0 or count <= 0:
        return []

    step = max(1, stride)
    target = min(count, n_rows)
    cursor = offset % n_rows
    picked: list[int] = []
    seen: set[int] = set()
    guard = 0
    max_iterations = n_rows * (step + 1) + n_rows

    while len(picked) < target and guard < max_iterations:
        if cursor not in seen:
            seen.add(cursor)
            picked.append(cursor)
            cursor = (cursor + step) % n_rows
        else:
            cursor = (cursor + 1) % n_rows
        guard += 1

    return sorted(picked)


def _cap_ids(paper_ids: list[str]) -> list[str]:
    """Cat bot danh sach paper_id de log khong phinh to."""
    return paper_ids[:MAX_LOGGED_IDS]


def _ids_at(df: pd.DataFrame, positions: list[int]) -> list[str]:
    """Lay paper_id tai cac vi tri (index da duoc reset nen label trung vi tri)."""
    return [str(df.at[position, "paper_id"]) for position in positions]


def _step_entry(
    name: str,
    description: str,
    paper_ids: list[str],
    details: dict[str, Any],
) -> dict[str, Any]:
    """Dong goi mot buoc corruption thanh entry cho log."""
    return {
        "name": name,
        "description": description,
        "affected_rows": len(paper_ids),
        "affected_paper_ids": _cap_ids(paper_ids),
        "details": details,
    }


def _parse_iso_date(value: Any) -> date | None:
    """Doc chuoi ngay dang YYYY-MM-DD; hong thi tra ve None."""
    text = str(value or "").strip()[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _shift_year_back(value: Any, years: int) -> str:
    """Lui chuoi ngay ve truoc `years` nam, luon tra ve string (khong tra Timestamp)."""
    parsed = _parse_iso_date(value)
    if parsed is None:
        return str(value or "")
    try:
        shifted = parsed.replace(year=parsed.year - years)
    except ValueError:
        # 29/02 khong ton tai o nam khong nhuan -> lui ve 28/02
        shifted = parsed.replace(year=parsed.year - years, day=28)
    return shifted.isoformat()


def _build_embedding_text(row: Any) -> str:
    """Gop lai text_for_embedding theo dung format cua buoc cleaning."""
    return (
        f"Title: {row['title']}\n"
        f"Authors: {row['authors_joined'] or 'unknown'}\n"
        f"Categories: {row['categories_joined'] or 'uncategorized'}\n"
        f"Published: {row['published']}\n"
        f"Summary: {row['summary']}"
    )


def _drop_latest_records(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Buoc 1: xoa cac dong moi nhat (frame sort newest-first) nhu incremental load loi."""
    rows_before = len(df)
    drop_count = min(DROP_LATEST, max(0, rows_before - 1))
    positions = list(range(drop_count))
    dropped_ids = _ids_at(df, positions)

    remaining = df.drop(index=positions).reset_index(drop=True)
    details = {
        "dropped_positions": positions,
        "rows_before": rows_before,
        "rows_after": len(remaining),
        "note": "mat cac paper moi nhat nen freshness va retrieval deu giam",
    }
    step = _step_entry(
        "drop_latest_records",
        f"Xoa {len(positions)} dong moi nhat o dau frame de gia lap incremental load that bai.",
        dropped_ids,
        details,
    )
    return remaining, step


def _blank_summaries(df: pd.DataFrame) -> dict[str, Any]:
    """Buoc 2: xoa trang summary tren mot so dong."""
    positions = _pick_positions(len(df), BLANK_COUNT, BLANK_OFFSET, SELECTION_STRIDE)
    affected_ids = _ids_at(df, positions)

    for position in positions:
        df.at[position, "summary"] = ""
        df.at[position, "summary_chars"] = 0

    details = {
        "positions": positions,
        "offset": BLANK_OFFSET,
        "stride": SELECTION_STRIDE,
        "note": "summary rong lam cau hoi dang summary mat hoan toan ground truth",
    }
    return _step_entry(
        "blank_summary",
        f"Dat summary = '' va summary_chars = 0 tren {len(positions)} dong.",
        affected_ids,
        details,
    )


def _inject_noise(df: pd.DataFrame) -> dict[str, Any]:
    """Buoc 3: noi them chuoi rac vao cuoi summary."""
    positions = _pick_positions(len(df), NOISE_COUNT, NOISE_OFFSET, SELECTION_STRIDE)
    affected_ids = _ids_at(df, positions)

    for position in positions:
        # Nhoi rac vao DAU summary: mo phong loi encoding/boilerplate bi ghep truoc noi dung that,
        # dong thoi lam hong luon cau dau tien ma qa.py dung lam cau tra loi.
        polluted = f"{NOISE_BLOB}{df.at[position, 'summary']}"
        df.at[position, "summary"] = polluted
        df.at[position, "summary_chars"] = len(polluted)

    details = {
        "positions": positions,
        "offset": NOISE_OFFSET,
        "stride": SELECTION_STRIDE,
        "noise_token": NOISE_TOKEN,
        "noise_repeat": NOISE_REPEAT,
        "noise_chars": len(NOISE_BLOB),
    }
    return _step_entry(
        "inject_noise",
        f"Noi {len(NOISE_BLOB)} ky tu rac vao summary cua {len(positions)} dong.",
        affected_ids,
        details,
    )


def _truncate_titles(df: pd.DataFrame) -> dict[str, Any]:
    """Buoc 4: cat cut title con TRUNCATE_CHARS ky tu dau."""
    positions = _pick_positions(len(df), TRUNCATE_COUNT, TRUNCATE_OFFSET, SELECTION_STRIDE)
    affected_ids = _ids_at(df, positions)
    truncated: list[str] = []

    for position in positions:
        short_title = str(df.at[position, "title"])[:TRUNCATE_CHARS]
        df.at[position, "title"] = short_title
        df.at[position, "title_chars"] = len(short_title)
        truncated.append(short_title)

    details = {
        "positions": positions,
        "offset": TRUNCATE_OFFSET,
        "stride": SELECTION_STRIDE,
        "keep_chars": TRUNCATE_CHARS,
        "new_titles": truncated[:MAX_LOGGED_IDS],
        "note": "title cut lam cau hoi trich dan tieu de khong con khop document",
    }
    return _step_entry(
        "truncate_title",
        f"Cat title con {TRUNCATE_CHARS} ky tu dau tren {len(positions)} dong.",
        affected_ids,
        details,
    )


def _stale_dates(df: pd.DataFrame) -> dict[str, Any]:
    """Buoc 5: day published/updated lui STALE_YEARS nam va cong them age_days."""
    positions = _pick_positions(len(df), STALE_COUNT, STALE_OFFSET, SELECTION_STRIDE)
    affected_ids = _ids_at(df, positions)
    extra_days = DAYS_PER_YEAR * STALE_YEARS
    shifts: list[dict[str, str]] = []

    for position in positions:
        old_published = str(df.at[position, "published"])
        new_published = _shift_year_back(old_published, STALE_YEARS)
        new_updated = _shift_year_back(df.at[position, "updated"], STALE_YEARS)

        # Giu nguyen kieu string cho published/updated vi ChromaDB metadata chi nhan primitive.
        df.at[position, "published"] = new_published
        df.at[position, "updated"] = new_updated
        df.at[position, "age_days"] = int(df.at[position, "age_days"]) + extra_days
        shifts.append({"from": old_published, "to": new_published})

    details = {
        "positions": positions,
        "offset": STALE_OFFSET,
        "stride": SELECTION_STRIDE,
        "years_back": STALE_YEARS,
        "extra_age_days": extra_days,
        "shifts": shifts[:MAX_LOGGED_IDS],
    }
    return _step_entry(
        "stale_dates",
        f"Lui published/updated {STALE_YEARS} nam va cong {extra_days} vao age_days tren {len(positions)} dong.",
        affected_ids,
        details,
    )


def _duplicate_rows(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Buoc 6: them ban sao y het cua mot so dong de pha check unique paper_id."""
    positions = _pick_positions(len(df), DUPLICATE_COUNT, DUPLICATE_OFFSET, SELECTION_STRIDE)
    affected_ids = _ids_at(df, positions)

    duplicated = df.iloc[positions].copy()
    result = pd.concat([df, duplicated], ignore_index=True)

    details = {
        "source_positions": positions,
        "appended_positions": list(range(len(df), len(result))),
        "rows_before": len(df),
        "rows_after": len(result),
        "note": "paper_id bi lap lam uniqueness check that bai",
    }
    step = _step_entry(
        "duplicate_rows",
        f"Them {len(duplicated)} dong trung lap vao cuoi frame.",
        affected_ids,
        details,
    )
    return result, step


def _rebuild_embedding_text(df: pd.DataFrame) -> dict[str, Any]:
    """Buoc 7: dung lai text_for_embedding tu cac cot da bi lam hong."""
    df["text_for_embedding"] = df.apply(_build_embedding_text, axis=1)
    affected_ids = [str(value) for value in df["paper_id"].tolist()]

    details = {
        "rows": len(df),
        "note": "index corrupted se embed dung phan text da hong",
    }
    return _step_entry(
        "rebuild_embedding_text",
        "Dung lai text_for_embedding cho toan bo dong sau khi da lam hong du lieu.",
        affected_ids,
        details,
    )


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """Lam hong clean dataset mot cach co chu dich va ghi corruption log.

    Cac buoc chay theo dung thu tu: drop latest -> blank summary -> inject noise ->
    truncate title -> stale dates -> duplicate rows -> rebuild text_for_embedding.
    Toan bo viec chon dong deu deterministic (khong dung random) de lab lap lai duoc.
    """
    if df is None or len(df) < MIN_SOURCE_ROWS:
        current = 0 if df is None else len(df)
        raise ValueError(
            f"Can it nhat {MIN_SOURCE_ROWS} dong clean data de tao corrupted dataset, hien chi co {current}."
        )

    _require_columns(df)

    # Copy de khong dung vao dataframe cua caller.
    working = df.copy().reset_index(drop=True)
    source_rows = len(working)
    steps: list[dict[str, Any]] = []

    working, drop_step = _drop_latest_records(working)
    steps.append(drop_step)

    steps.append(_blank_summaries(working))
    steps.append(_inject_noise(working))
    steps.append(_truncate_titles(working))
    steps.append(_stale_dates(working))

    working, duplicate_step = _duplicate_rows(working)
    steps.append(duplicate_step)

    rebuild_step = _rebuild_embedding_text(working)
    steps.append(rebuild_step)

    # Buoc rebuild cham vao moi dong nen khong tinh vao tong so dong bi lam hong.
    total_affected_rows = sum(
        step["affected_rows"] for step in steps if step["name"] != rebuild_step["name"]
    )

    log = {
        "generated_at": now_utc().isoformat(),
        "source_rows": source_rows,
        "result_rows": len(working),
        "parameters": {
            "min_source_rows": MIN_SOURCE_ROWS,
            "drop_latest": DROP_LATEST,
            "blank_count": BLANK_COUNT,
            "noise_count": NOISE_COUNT,
            "noise_token": NOISE_TOKEN,
            "noise_repeat": NOISE_REPEAT,
            "truncate_count": TRUNCATE_COUNT,
            "truncate_chars": TRUNCATE_CHARS,
            "stale_count": STALE_COUNT,
            "stale_years": STALE_YEARS,
            "days_per_year": DAYS_PER_YEAR,
            "duplicate_count": DUPLICATE_COUNT,
            "selection_stride": SELECTION_STRIDE,
            "offsets": {
                "blank_summary": BLANK_OFFSET,
                "inject_noise": NOISE_OFFSET,
                "truncate_title": TRUNCATE_OFFSET,
                "stale_dates": STALE_OFFSET,
                "duplicate_rows": DUPLICATE_OFFSET,
            },
            "max_logged_ids": MAX_LOGGED_IDS,
            "deterministic": True,
        },
        "steps": steps,
        "total_affected_rows": total_affected_rows,
    }
    write_json(Path(output_log_path), log)

    return working
