from __future__ import annotations

from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json


MIN_DOCUMENTS = 5
PAPERS_PER_TEST_SET = 5

# Ham QA co san (retrieval/qa.py) dinh tuyen cau tra loi bang cac cum tu nay.
# Neu tieu de bai bao vo tinh chua chung, cau hoi se bi hieu sai -> loai bai do ra.
ROUTING_PHRASES = (
    "who authored",
    "list the authors",
    "when was",
    "publication date",
    "published on",
    "what categories",
)


def _question_specs(row: pd.Series) -> list[tuple[str, str, str]]:
    """Tra ve (question_type, question, ground_truth) cho tung loai cau hoi."""
    title = row["title"]
    return [
        ("authors", f"Who authored the paper '{title}'?", row["authors_joined"]),
        ("date", f"When was the paper '{title}' published?", row["published"]),
        ("categories", f"What categories are assigned to the paper '{title}'?", row["categories_joined"]),
        ("summary", f"Give a one sentence summary of the paper '{title}'.", first_sentence(row["summary"])),
    ]


def _is_usable(row: pd.Series) -> bool:
    """Loai cac paper se lam hong viec dinh tuyen hoac tra cuu chinh xac."""
    title = str(row.get("title") or "")
    if not row.get("paper_id") or not title:
        return False
    # Dau nhay don trong tieu de se pha regex tra cuu chinh xac cua qa.py
    if "'" in title:
        return False
    if any(phrase in title.lower() for phrase in ROUTING_PHRASES):
        return False
    return all(str(row.get(field) or "").strip() for field in ("authors_joined", "categories_joined", "summary"))


def _select_papers(df: pd.DataFrame, count: int) -> pd.DataFrame:
    """Chon paper trai deu tren toan bo dataset thay vi lay cac dong dau."""
    usable = df[df.apply(_is_usable, axis=1)]
    if usable.empty:
        raise ValueError("Khong co paper nao du dieu kien de tao cau hoi.")
    step = max(1, len(usable) // count)
    return usable.iloc[::step].head(count)


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    if df is None or len(df) < MIN_DOCUMENTS:
        raise ValueError(
            f"Can it nhat {MIN_DOCUMENTS} document de tao test set, hien co {0 if df is None else len(df)}."
        )

    samples: list[dict[str, Any]] = []
    for _, row in _select_papers(df, PAPERS_PER_TEST_SET).iterrows():
        for question_type, question, ground_truth in _question_specs(row):
            samples.append(
                {
                    "id": f"q{len(samples) + 1:03d}",
                    "question_type": question_type,
                    "question": question,
                    "ground_truth": str(ground_truth),
                    "ground_truth_doc_ids": [row["paper_id"]],
                }
            )

    if not samples:
        raise ValueError("Khong tao duoc cau hoi nao tu cleaned dataset.")

    write_json(output_path, samples)
    return samples
