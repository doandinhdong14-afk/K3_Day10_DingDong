import json
from pathlib import Path
from typing import Any

import pandas as pd


def build_test_set(df: pd.DataFrame, output_path: Path | str) -> list[dict[str, Any]]:
    """Build a standard evaluation test set from the cleaned DataFrame."""
    if df.empty:
        raise ValueError("Cannot build test set from an empty DataFrame.")

    test_samples: list[dict[str, Any]] = []
    # Select top representative papers (up to 8 papers to keep evaluation balanced and fast)
    sample_df = df.head(8)

    for _, row in sample_df.iterrows():
        paper_id = str(row["paper_id"])
        title = str(row["title"])
        summary = str(row["summary"])
        authors_joined = str(row["authors_joined"])
        published = str(row["published"])

        # 1. Summary question
        test_samples.append(
            {
                "id": f"q_{len(test_samples) + 1:03d}",
                "question_type": "summary",
                "question": f"What is the main summary or abstract of the research paper '{title}'?",
                "ground_truth": summary,
                "ground_truth_doc_ids": [paper_id],
            }
        )

        # 2. Authors question
        if authors_joined and authors_joined != "Unknown":
            test_samples.append(
                {
                    "id": f"q_{len(test_samples) + 1:03d}",
                    "question_type": "authors",
                    "question": f"Who are the authors of the paper '{title}'?",
                    "ground_truth": authors_joined,
                    "ground_truth_doc_ids": [paper_id],
                }
            )

        # 3. Publication date question
        if published:
            test_samples.append(
                {
                    "id": f"q_{len(test_samples) + 1:03d}",
                    "question_type": "date",
                    "question": f"When was the paper '{title}' published?",
                    "ground_truth": published,
                    "ground_truth_doc_ids": [paper_id],
                }
            )

    output_p = Path(output_path)
    output_p.parent.mkdir(parents=True, exist_ok=True)
    with open(output_p, "w", encoding="utf-8") as f:
        json.dump(test_samples, f, ensure_ascii=False, indent=2)

    return test_samples

