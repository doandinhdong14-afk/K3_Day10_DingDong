from pathlib import Path

import pandas as pd

from core.utils import write_json


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path: Path | str) -> pd.DataFrame:
    """Simulate data corruption by introducing missing summaries, noise, duplicates, and stale dates."""
    if df.empty:
        write_json(Path(output_log_path), {"log": [], "status": "empty_dataframe"})
        return df.copy()

    corrupted_df = df.copy()
    corruption_log: list[dict] = []

    # 1. Drop top latest records (e.g. drop top 2 rows)
    if len(corrupted_df) > 5:
        dropped_ids = list(corrupted_df.iloc[:2]["paper_id"])
        corrupted_df = corrupted_df.iloc[2:].reset_index(drop=True)
        corruption_log.append({"action": "drop_latest_records", "count": 2, "dropped_paper_ids": dropped_ids})

    # 2. Blank summary on selected rows (e.g. indices 0, 1)
    if len(corrupted_df) > 2:
        corrupted_df.loc[0, "summary"] = ""
        corrupted_df.loc[1, "summary"] = ""
        corruption_log.append({"action": "blank_summary", "affected_indices": [0, 1]})

    # 3. Inject noise text into summary (e.g. indices 2, 3)
    if len(corrupted_df) > 4:
        for idx in [2, 3]:
            corrupted_df.loc[idx, "summary"] = "GARBAGE_NOISE_CORRUPTED_TEXT " * 3 + str(corrupted_df.loc[idx, "summary"])
        corruption_log.append({"action": "inject_noise", "affected_indices": [2, 3]})

    # 4. Truncate title (e.g. index 4)
    if len(corrupted_df) > 4:
        corrupted_df.loc[4, "title"] = str(corrupted_df.loc[4, "title"])[:5]
        corruption_log.append({"action": "truncate_title", "affected_indices": [4]})

    # 5. Make published date stale (e.g. indices 5, 6)
    if len(corrupted_df) > 6:
        for idx in [5, 6]:
            corrupted_df.loc[idx, "published"] = "2020-01-01"
            corrupted_df.loc[idx, "age_days"] = 1500
        corruption_log.append({"action": "make_stale_dates", "affected_indices": [5, 6]})

    # 6. Add duplicate rows (duplicate first 2 rows)
    if len(corrupted_df) > 2:
        duplicates = corrupted_df.iloc[:2].copy()
        corrupted_df = pd.concat([corrupted_df, duplicates], ignore_index=True)
        corruption_log.append({"action": "add_duplicate_rows", "count": 2})

    # 7. Rebuild helper columns and text_for_embedding
    corrupted_df["summary_chars"] = corrupted_df["summary"].str.len()
    corrupted_df["text_for_embedding"] = (
        "Title: " + corrupted_df["title"].astype(str) + "\n"
        "Summary: " + corrupted_df["summary"].astype(str) + "\n"
        "Authors: " + corrupted_df["authors_joined"].astype(str) + "\n"
        "Categories: " + corrupted_df["categories_joined"].astype(str)
    )

    # 8. Save corruption log
    write_json(Path(output_log_path), {"log": corruption_log, "total_corrupted_rows": len(corrupted_df)})
    return corrupted_df

