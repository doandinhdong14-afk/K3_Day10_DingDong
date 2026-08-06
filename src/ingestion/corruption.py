from __future__ import annotations

import pandas as pd


import json
import random
import pandas as pd
import numpy as np


from datetime import datetime, timedelta
import re




def corrupt_clean_dataframe(
    df: pd.DataFrame,
    output_log_path: str,
    drop_latest_ratio: float = 0.05,
    blank_summary_ratio: float = 0.05,
    noise_text_ratio: float = 0.05,
    truncate_title_ratio: float = 0.05,
    shift_date_ratio: float = 0.05,
    duplicate_ratio: float = 0.03,
    seed: int = 42,
) -> pd.DataFrame:
    """Simulate nhiều dạng data corruption dựa trên DataFrame sạch và ghi log.

    Pseudo-code:
    1. Drop một số latest records.
    2. Blank summary ở một số dòng.
    3. Inject noise vào text.
    4. Làm title bị truncate.
    5. Làm published date cũ đi.
    6. Add duplicate rows.
    7. Rebuild `text_for_embedding`.
    8. Ghi corruption log vào output_log_path.
    """
    if df.empty:
        # Nếu dataframe rỗng, ghi log rỗng và trả về
        with open(output_log_path, "w", encoding="utf-8") as f:
            json.dump({"summary": "Empty dataframe provided", "modifications": []}, f, indent=2)
        return df.copy()

    # Khởi tạo seed & copy dataframe
    np.random.seed(seed)
    random.seed(seed)
    corrupted_df = df.copy()
    logs = []

    # -------------------------------------------------------------------------
    # Bước 1: Drop một số latest records (các bài báo mới nhất)
    # -------------------------------------------------------------------------
    if "published" in corrupted_df.columns:
        # Sắp xếp để lấy bài mới nhất ở đầu
        corrupted_df.sort_values(by="published", ascending=False, inplace=True)
        corrupted_df.reset_index(drop=True, inplace=True)

    num_to_drop = int(len(corrupted_df) * drop_latest_ratio)
    if num_to_drop > 0:
        dropped_indices = list(range(num_to_drop))
        for idx in dropped_indices:
            logs.append({
                "step": "1_drop_latest_records",
                "row_index": idx,
                "paper_id": str(corrupted_df.at[idx, "paper_id"]) if "paper_id" in corrupted_df.columns else None,
                "action": "dropped_record",
                "original_published": str(corrupted_df.at[idx, "published"]) if "published" in corrupted_df.columns else None
            })
        corrupted_df.drop(index=dropped_indices, inplace=True)
        corrupted_df.reset_index(drop=True, inplace=True)

    num_rows = len(corrupted_df)

    # Helper pick random indices
    def get_random_indices(ratio: float) -> list[int]:
        count = int(num_rows * ratio)
        return random.sample(range(num_rows), min(count, num_rows))

    # -------------------------------------------------------------------------
    # Bước 2: Blank summary ở một số dòng
    # -------------------------------------------------------------------------
    if "summary" in corrupted_df.columns:
        blank_indices = get_random_indices(blank_summary_ratio)
        for idx in blank_indices:
            orig_val = corrupted_df.at[idx, "summary"]
            corrupted_df.at[idx, "summary"] = ""
            if "summary_chars" in corrupted_df.columns:
                corrupted_df.at[idx, "summary_chars"] = 0

            logs.append({
                "step": "2_blank_summary",
                "row_index": idx,
                "paper_id": str(corrupted_df.at[idx, "paper_id"]) if "paper_id" in corrupted_df.columns else None,
                "original_summary_snippet": str(orig_val)[:50],
                "new_summary": ""
            })

    # -------------------------------------------------------------------------
    # Bước 3: Inject noise vào text (Summary)
    # -------------------------------------------------------------------------
    if "summary" in corrupted_df.columns:
        noise_indices = get_random_indices(noise_text_ratio)
        for idx in noise_indices:
            orig_text = corrupted_df.at[idx, "summary"]
            if orig_text:
                # Chọn chiến thuật inject noise: typo, hoa/thường, chèn ký tự lạ
                noise_type = random.choice(["typo", "uppercase", "special_chars"])
                if noise_type == "uppercase":
                    noisy_text = orig_text.upper()
                elif noise_type == "special_chars":
                    noisy_text = f"@@ERR_NOISE@@ {orig_text} ###"
                else: # typo (tráo đổi 2 ký tự kề nhau)
                    words = orig_text.split()
                    if len(words) > 3:
                        target_w_idx = random.randint(0, len(words) - 1)
                        word = words[target_w_idx]
                        if len(word) > 2:
                            w_list = list(word)
                            w_list[0], w_list[1] = w_list[1], w_list[0]
                            words[target_w_idx] = "".join(w_list)
                        noisy_text = " ".join(words)
                    else:
                        noisy_text = orig_text + " [corrupted]"

                corrupted_df.at[idx, "summary"] = noisy_text
                logs.append({
                    "step": "3_inject_noise_text",
                    "row_index": idx,
                    "paper_id": str(corrupted_df.at[idx, "paper_id"]) if "paper_id" in corrupted_df.columns else None,
                    "noise_type": noise_type,
                    "original_text_snippet": orig_text[:50],
                    "corrupted_text_snippet": noisy_text[:50]
                })

    # -------------------------------------------------------------------------
    # Bước 4: Làm title bị truncate (cắt ngắn tiêu đề)
    # -------------------------------------------------------------------------
    if "title" in corrupted_df.columns:
        truncate_indices = get_random_indices(truncate_title_ratio)
        for idx in truncate_indices:
            orig_title = corrupted_df.at[idx, "title"]
            if orig_title and len(orig_title) > 10:
                # Cắt ngắn title chỉ còn 1/3 độ dài ban đầu
                trunc_len = max(5, len(orig_title) // 3)
                truncated_title = orig_title[:trunc_len] + "..."
                corrupted_df.at[idx, "title"] = truncated_title

                logs.append({
                    "step": "4_truncate_title",
                    "row_index": idx,
                    "paper_id": str(corrupted_df.at[idx, "paper_id"]) if "paper_id" in corrupted_df.columns else None,
                    "original_title": orig_title,
                    "truncated_title": truncated_title
                })

    # -------------------------------------------------------------------------
    # Bước 5: Làm published date cũ đi (Shift publication date back)
    # -------------------------------------------------------------------------
    if "published" in corrupted_df.columns:
        date_indices = get_random_indices(shift_date_ratio)
        for idx in date_indices:
            orig_date = corrupted_df.at[idx, "published"]
            if pd.notna(orig_date):
                # Lùi ngày xuất bản về quá khứ ngẫu nhiên từ 365 đến 3650 ngày (~1-10 năm)
                days_to_shift = random.randint(365, 3650)
                shifted_date = pd.to_datetime(orig_date) - timedelta(days=days_to_shift)
                corrupted_df.at[idx, "published"] = shifted_date

                # Cập nhật lại age_days nếu cột này có sẵn
                if "age_days" in corrupted_df.columns:
                    corrupted_df.at[idx, "age_days"] = float(corrupted_df.at[idx, "age_days"]) + days_to_shift

                logs.append({
                    "step": "5_make_published_date_older",
                    "row_index": idx,
                    "paper_id": str(corrupted_df.at[idx, "paper_id"]) if "paper_id" in corrupted_df.columns else None,
                    "days_shifted_back": days_to_shift,
                    "original_date": str(orig_date),
                    "new_date": str(shifted_date)
                })

    # -------------------------------------------------------------------------
    # Bước 6: Add duplicate rows (Nhân bản dòng)
    # -------------------------------------------------------------------------
    num_dups = int(num_rows * duplicate_ratio)
    if num_dups > 0:
        dup_source_indices = random.choices(range(num_rows), k=num_dups)
        dup_rows = corrupted_df.iloc[dup_source_indices].copy()
        
        # Nối các dòng lặp vào cuối DataFrame
        corrupted_df = pd.concat([corrupted_df, dup_rows], ignore_index=True)

        for src_idx in dup_source_indices:
            logs.append({
                "step": "6_add_duplicate_rows",
                "source_row_index": src_idx,
                "paper_id": str(corrupted_df.at[src_idx, "paper_id"]) if "paper_id" in corrupted_df.columns else None,
                "action": "duplicated_and_appended"
            })

    # -------------------------------------------------------------------------
    # Bước 7: Rebuild `text_for_embedding`
    # -------------------------------------------------------------------------
    # Vì title, summary hoặc categories đã bị thay đổi, cần build lại text_for_embedding
    if "text_for_embedding" in corrupted_df.columns:
        title_col = corrupted_df["title"].fillna("") if "title" in corrupted_df.columns else ""
        summary_col = corrupted_df["summary"].fillna("") if "summary" in corrupted_df.columns else ""
        cats_col = corrupted_df["categories_joined"].fillna("") if "categories_joined" in corrupted_df.columns else ""

        corrupted_df["text_for_embedding"] = (
            "Title: "
            + title_col
            + " | Categories: "
            + cats_col
            + "\nAbstract: "
            + summary_col
        )

    # -------------------------------------------------------------------------
    # Bước 8: Ghi corruption log vào output_log_path
    # -------------------------------------------------------------------------
    log_payload = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_corruptions_applied": len(logs),
            "final_rows_count": len(corrupted_df),
            "seed": seed
        },
        "modifications": logs
    }

    with open(output_log_path, "w", encoding="utf-8") as f:
        json.dump(log_payload, f, indent=2, ensure_ascii=False)

    return corrupted_df

