from __future__ import annotations

from datetime import datetime

import pandas as pd

from ingestion.crossref import PaperRecord

from dataclasses import dataclass
from typing import List, Optional
import numpy as np


import re
from pydantic import BaseModel


class PaperRecord(BaseModel):
    paper_id: str
    title: str
    summary: str
    authors: List[str]
    categories: List[str]
    published: datetime  # hoặc str
    updated: Optional[datetime] = None




def build_clean_dataframe(
    records: list[PaperRecord], run_date: datetime
) -> pd.DataFrame:
    """Clean raw records thành dataframe sẵn sàng để embed.

    Pseudo-code:
    1. Normalize title, summary, authors, categories.
    2. Parse published/updated date.
    3. Tính age_days.
    4. Tạo cột helper:
        - authors_joined
        - categories_joined
        - summary_chars
        - text_for_embedding
    5. Drop duplicates và filter row xấu.
    6. Sort dataframe và return.
    """
    if not records:
        return pd.DataFrame()

    # Chuyển list objects/dicts thành DataFrame
    data = [r.dict() if hasattr(r, "dict") else r.__dict__ for r in records]
    df = pd.DataFrame(data)

    # -------------------------------------------------------------------------
    # Bước 1: Normalize title, summary, authors, categories
    # -------------------------------------------------------------------------
    def clean_text(text: str) -> str:
        if not isinstance(text, str) or not text:
            return ""
        # Xóa xuống dòng, khoảng trắng thừa, và chuẩn hóa space
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    df["title"] = df["title"].apply(clean_text)
    df["summary"] = df["summary"].apply(clean_text)

    # Format danh sách tác giả & categories (làm sạch từng phần tử)
    def clean_list(items) -> list:
        if isinstance(items, list):
            return [clean_text(i) for i in items if clean_text(i)]
        return []

    df["authors"] = df["authors"].apply(clean_list)
    df["categories"] = df["categories"].apply(clean_list)

    # -------------------------------------------------------------------------
    # Bước 2: Parse published/updated date
    # -------------------------------------------------------------------------
    df["published"] = pd.to_datetime(df["published"], errors="coerce", utc=True)
    df["updated"] = pd.to_datetime(df["updated"], errors="coerce", utc=True)

    # Chuẩn hóa run_date sang timezone UTC để tính toán chính xác
    run_date_utc = pd.to_datetime(run_date, utc=True)

    # -------------------------------------------------------------------------
    # Bước 3: Tính age_days
    # -------------------------------------------------------------------------
    # Tính khoảng cách ngày từ ngày xuất bản (published) tới run_date
    df["age_days"] = (run_date_utc - df["published"]).dt.total_seconds() / (
        24 * 3600
    )
    df["age_days"] = df["age_days"].round(1)

    # -------------------------------------------------------------------------
    # Bước 4: Tạo các cột helper
    # -------------------------------------------------------------------------
    # - authors_joined: "Author A, Author B"
    df["authors_joined"] = df["authors"].apply(
        lambda x: ", ".join(x) if x else ""
    )

    # - categories_joined: "cs.CL, cs.AI"
    df["categories_joined"] = df["categories"].apply(
        lambda x: ", ".join(x) if x else ""
    )

    # - summary_chars: Độ dài tóm tắt theo ký tự
    df["summary_chars"] = df["summary"].str.len()

    # - text_for_embedding: Tạo chuỗi văn bản hoàn chỉnh để truyền vào Embedding Model
    # Ví dụ format: "Title: ... | Categories: ... | Authors: ... \nAbstract: ..."
    df["text_for_embedding"] = (
        "Title: "
        + df["title"]
        + " | Categories: "
        + df["categories_joined"]
        + "\nAbstract: "
        + df["summary"]
    )

    # -------------------------------------------------------------------------
    # Bước 5: Drop duplicates và filter row xấu
    # -------------------------------------------------------------------------
    # Xóa dòng bị lặp lại dựa trên paper_id hoặc title
    id_col = "paper_id" if "paper_id" in df.columns else "title"
    df.drop_duplicates(subset=[id_col], keep="first", inplace=True)

    # Filter row xấu:
    # - Title bị rỗng
    # - Summary quá ngắn (thường < 50 ký tự không phải là bài báo hợp lệ)
    # - Ngày xuất bản bị lỗi (NaT) hoặc tuổi âm (published trong tương lai)
    valid_mask = (
        (df["title"].str.len() > 5)
        & (df["summary_chars"] >= 50)
        & (df["published"].notna())
        & (df["age_days"] >= 0)
    )
    df = df[valid_mask].copy()

    # -------------------------------------------------------------------------
    # Bước 6: Sort dataframe và return
    # -------------------------------------------------------------------------
    # Ưu tiên xếp bài báo mới xuất bản lên đầu
    df.sort_values(by="published", ascending=False, inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df