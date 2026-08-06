from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

import pandas as pd

from core.utils import now_utc, write_json
from ingestion.cleaning import build_text_for_embedding, compute_age_days

# Corruption duoc thiet ke deterministic (chon theo vi tri, khong random)
# de baseline/corrupted/repaired co the tai hien lai y het.
DROP_LATEST_COUNT = 3
BLANK_SUMMARY_COUNT = 3
NOISE_COUNT = 3
TRUNCATE_TITLE_COUNT = 2
STALE_DATE_COUNT = 3
DUPLICATE_COUNT = 2

TRUNCATED_TITLE_CHARS = 12
STALE_YEARS = 4
NOISE_TEXT = (
    "%%% RAW_DUMP_ERR 0x8f ??? lorem ipsum dolor sit amet consectetur "
    "&&&& <<UNPARSED>> \\x00\\x00 click here for casino bonus 12345 %%%"
)


def _positions(df: pd.DataFrame, start: int, count: int) -> list[int]:
    """Lay `count` vi tri lien tiep tu `start`, khong vuot qua so dong hien co."""
    return list(range(start, min(start + count, len(df))))


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """Mo phong 6 dang loi du lieu thuong gap trong mot pipeline that."""
    original_rows = len(df)
    working = df.copy().reset_index(drop=True)
    events: list[dict[str, Any]] = []

    def log(kind: str, description: str, paper_ids: list[str]) -> None:
        events.append(
            {
                "type": kind,
                "description": description,
                "affected_rows": len(paper_ids),
                "affected_paper_ids": paper_ids,
            }
        )

    # 1. Mat du lieu moi nhat: upstream job fail nen batch moi khong duoc nap.
    dropped = working.head(DROP_LATEST_COUNT)
    log(
        "drop_latest_records",
        f"Xoa {len(dropped)} paper moi nhat de mo phong batch ingestion bi mat.",
        dropped["paper_id"].tolist(),
    )
    working = working.iloc[len(dropped) :].reset_index(drop=True)

    # 2. Summary rong: field bi mat khi parse abstract.
    blank_positions = _positions(working, 0, BLANK_SUMMARY_COUNT)
    working.loc[blank_positions, "summary"] = ""
    log(
        "blank_summary",
        f"Xoa rong summary cua {len(blank_positions)} paper de mo phong loi parse abstract.",
        working.loc[blank_positions, "paper_id"].tolist(),
    )

    # 3. Text nhieu: raw markup/spam lot vao field summary.
    noise_positions = _positions(working, BLANK_SUMMARY_COUNT, NOISE_COUNT)
    working.loc[noise_positions, "summary"] = working.loc[noise_positions, "summary"] + " " + NOISE_TEXT
    log(
        "inject_noise",
        f"Chen noise/markup rac vao summary cua {len(noise_positions)} paper.",
        working.loc[noise_positions, "paper_id"].tolist(),
    )

    # 4. Title bi cat: loi truncate khi ghi vao cot co gioi han do dai.
    truncate_start = BLANK_SUMMARY_COUNT + NOISE_COUNT
    truncate_positions = _positions(working, truncate_start, TRUNCATE_TITLE_COUNT)
    working.loc[truncate_positions, "title"] = (
        working.loc[truncate_positions, "title"].str.slice(0, TRUNCATED_TITLE_CHARS) + "..."
    )
    log(
        "truncate_title",
        f"Cat title cua {len(truncate_positions)} paper con {TRUNCATED_TITLE_CHARS} ky tu.",
        working.loc[truncate_positions, "paper_id"].tolist(),
    )

    # 5. Ngay xuat ban bi lui lai: loi timezone/backfill lam du lieu trong nhu da cu.
    stale_start = truncate_start + TRUNCATE_TITLE_COUNT
    stale_positions = _positions(working, stale_start, STALE_DATE_COUNT)
    as_of: date = now_utc().astimezone(UTC).date()
    for position in stale_positions:
        try:
            original = date.fromisoformat(str(working.at[position, "published"])[:10])
        except ValueError:
            original = as_of
        stale_date = (original - timedelta(days=365 * STALE_YEARS)).isoformat()
        working.at[position, "published"] = stale_date
        working.at[position, "age_days"] = compute_age_days(stale_date, as_of)
    log(
        "stale_publication_date",
        f"Lui published date cua {len(stale_positions)} paper ve {STALE_YEARS} nam truoc.",
        working.loc[stale_positions, "paper_id"].tolist(),
    )

    # 6. Duplicate: job chay lai hai lan nen record bi nap trung.
    duplicate_positions = _positions(working, 0, DUPLICATE_COUNT)
    duplicates = working.iloc[duplicate_positions].copy()
    log(
        "duplicate_rows",
        f"Nhan doi {len(duplicates)} row de mo phong ingestion job chay trung.",
        duplicates["paper_id"].tolist(),
    )
    working = pd.concat([working, duplicates], ignore_index=True)

    # 7. Dong bo lai cac cot dan xuat de corrupted dataset van dung schema cua cleaning.
    working["title_chars"] = working["title"].str.len()
    working["summary_chars"] = working["summary"].str.len()
    working["text_for_embedding"] = working.apply(build_text_for_embedding, axis=1)

    log_payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "original_rows": original_rows,
        "corrupted_rows": len(working),
        "row_delta": len(working) - original_rows,
        "unique_paper_ids": int(working["paper_id"].nunique()),
        "corruption_types": [event["type"] for event in events],
        "events": events,
    }
    write_json(output_log_path, log_payload)
    print(
        f"[corruption] {original_rows} -> {len(working)} row, "
        f"{len(events)} loai loi -> {output_log_path}"
    )
    return working
