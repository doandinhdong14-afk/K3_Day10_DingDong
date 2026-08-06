from __future__ import annotations

from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json

MIN_DOCUMENTS = 4
TARGET_PAPERS = 5

# Cach dat cau hoi phai khop voi router trong `retrieval/qa.py::_extract_answer`
# ("who authored", "when was", "what categories", con lai -> summary).
QUESTION_TEMPLATES: list[tuple[str, str, str]] = [
    ("summary", "What is the main contribution of the paper titled '{title}'?", "summary"),
    ("authors", "Who authored the paper titled '{title}'?", "authors_joined"),
    ("date", "When was the paper titled '{title}' published?", "published"),
    ("categories", "What categories are assigned to the paper titled '{title}'?", "categories_joined"),
]


def _select_papers(df: pd.DataFrame, target: int) -> pd.DataFrame:
    """Chon paper trai deu tu moi den cu de test set phu ca hai dau cua freshness."""
    # `qa.answer_question` tim title trong dau nhay don, nen bo title co ky tu ' de tranh match sai.
    candidates = df[~df["title"].str.contains("'", regex=False)]
    if len(candidates) < MIN_DOCUMENTS:
        candidates = df

    count = min(target, len(candidates))
    step = max(len(candidates) // count, 1)
    positions = sorted({min(index * step, len(candidates) - 1) for index in range(count)})
    return candidates.iloc[positions]


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Sinh evaluation set factual tu cleaned dataframe va ghi ra `data/eval/`."""
    if len(df) < MIN_DOCUMENTS:
        raise ValueError(f"Can it nhat {MIN_DOCUMENTS} document de tao test set, hien co {len(df)}.")

    selected = _select_papers(df, TARGET_PAPERS)

    test_set: list[dict[str, Any]] = []
    for paper_index, (_, row) in enumerate(selected.iterrows(), start=1):
        for question_type, template, source_column in QUESTION_TEMPLATES:
            value = str(row[source_column]).strip()
            if not value:
                continue
            ground_truth = first_sentence(value) if question_type == "summary" else value
            test_set.append(
                {
                    "id": f"q{paper_index:02d}-{question_type}",
                    "question_type": question_type,
                    "question": template.format(title=row["title"]),
                    "ground_truth": ground_truth,
                    "ground_truth_doc_ids": [row["paper_id"]],
                    "source_title": row["title"],
                    "source_published": row["published"],
                }
            )

    if not test_set:
        raise ValueError("Khong sinh duoc cau hoi nao tu cleaned dataframe.")

    write_json(output_path, test_set)
    print(f"[testset] tao {len(test_set)} cau hoi tu {len(selected)} paper -> {output_path}")
    return test_set
