from __future__ import annotations



import pandas as pd
import json
import random
from typing import Any, List



def build_test_set(
    df: pd.DataFrame,
    output_path: str,
    min_docs: int = 5,
    sample_size: int = 10,
    seed: int = 42,
) -> List[dict[str, Any]]:
    """Tạo bộ evaluation set từ cleaned dataframe để benchmark RAG pipeline.

    Pseudo-code:
    1. Kiểm tra số lượng document tối thiểu.
    2. Chọn một số paper đại diện.
    3. Tạo nhiều loại câu hỏi:
        - summary
        - authors
        - date
        - categories
    4. Mỗi row cần có:
        - id
        - question_type
        - question
        - ground_truth
        - ground_truth_doc_ids
    5. Ghi file JSON vào output_path.
    """
    # -------------------------------------------------------------------------
    # Bước 1: Kiểm tra số lượng document tối thiểu
    # -------------------------------------------------------------------------
    if df is None or len(df) < min_docs:
        raise ValueError(
            f"Dataframe phải chứa ít nhất {min_docs} tài liệu. Số lượng hiện tại: {len(df) if df is not None else 0}"
        )

    random.seed(seed)
    test_set: List[dict[str, Any]] = []

    # -------------------------------------------------------------------------
    # Bước 2: Chọn một số paper đại diện
    # -------------------------------------------------------------------------
    num_to_sample = min(sample_size, len(df))
    # Ưu tiên lấy các bài báo có đầy đủ thông tin nhất
    sample_df = df.sample(n=num_to_sample, random_state=seed).reset_index(
        drop=True
    )

    q_counter = 1  # Đếm ID câu hỏi: eval_001, eval_002,...

    # -------------------------------------------------------------------------
    # Bước 3 & 4: Tạo nhiều loại câu hỏi và đóng gói cấu trúc row chuẩn
    # -------------------------------------------------------------------------
    for _, row in sample_df.iterrows():
        # Lấy doc_id (ưu tiên paper_id, fallback về title nếu không có)
        doc_id = str(row.get("paper_id", row.get("title")))
        title = str(row.get("title", "")).strip()

        # ---------------------------------------------------------------------
        # Loại 1: Question về Summary / Nội dung chính
        # ---------------------------------------------------------------------
        summary = str(row.get("summary", "")).strip()
        if summary:
            test_set.append({
                "id": f"eval_{q_counter:03d}",
                "question_type": "summary",
                "question": f"Tóm tắt nội dung chính và đóng góp của nghiên cứu '{title}' là gì?",
                "ground_truth": summary,
                "ground_truth_doc_ids": [doc_id],
            })
            q_counter += 1

        # ---------------------------------------------------------------------
        # Loại 2: Question về Authors / Tác giả
        # ---------------------------------------------------------------------
        authors = row.get("authors_joined", "")
        if not authors and isinstance(row.get("authors"), list):
            authors = ", ".join(row["authors"])

        if authors:
            test_set.append({
                "id": f"eval_{q_counter:03d}",
                "question_type": "authors",
                "question": f"Ai là tác giả của bài báo khoa học '{title}'?",
                "ground_truth": str(authors),
                "ground_truth_doc_ids": [doc_id],
            })
            q_counter += 1

        # ---------------------------------------------------------------------
        # Loại 3: Question về Date / Thời gian xuất bản
        # ---------------------------------------------------------------------
        pub_date = row.get("published")
        if pd.notna(pub_date):
            # Format ngày về dạng chuỗi YYYY-MM-DD
            date_str = (
                pub_date.strftime("%Y-%m-%d")
                if hasattr(pub_date, "strftime")
                else str(pub_date)[:10]
            )
            test_set.append({
                "id": f"eval_{q_counter:03d}",
                "question_type": "date",
                "question": f"Bài báo '{title}' được xuất bản/đăng tải vào thời gian nào?",
                "ground_truth": date_str,
                "ground_truth_doc_ids": [doc_id],
            })
            q_counter += 1

        # ---------------------------------------------------------------------
        # Loại 4: Question về Categories / Lĩnh vực nghiên cứu
        # ---------------------------------------------------------------------
        categories = row.get("categories_joined", "")
        if not categories and isinstance(row.get("categories"), list):
            categories = ", ".join(row["categories"])

        if categories:
            test_set.append({
                "id": f"eval_{q_counter:03d}",
                "question_type": "categories",
                "question": f"Nghiên cứu '{title}' thuộc các danh mục/chủ đề khoa học nào?",
                "ground_truth": str(categories),
                "ground_truth_doc_ids": [doc_id],
            })
            q_counter += 1

    # -------------------------------------------------------------------------
    # Bước 5: Ghi file JSON vào output_path
    # -------------------------------------------------------------------------
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(test_set, f, indent=2, ensure_ascii=False)

    return test_set




