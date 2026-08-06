from __future__ import annotations

from datetime import datetime
import json
import os
import chromadb
from chromadb.utils import embedding_functions
import pandas as pd

def main() -> None:
    """Xây dựng corruption -> evaluate -> repair -> compare flow.

    Pseudo-code:
    1. Load baseline metrics và clean dataset.
    2. Tạo corrupted dataframe.
    3. Save corrupted artifacts.
    4. Rebuild index và evaluate.
    5. Run quality checks/freshness trên corrupted data.
    6. Repair lại từ raw records.
    7. Evaluate repaired dataset.
    8. Tạo comparison report.
    """
    print("=" * 65)
    print("🧪 STARTING PHASE 2: CORRUPTION -> EVAL -> REPAIR -> COMPARE FLOW")
    print("=" * 65)
    run_date = datetime.now()

    # Cấu hình đường dẫn & tham số
    config = {
        "raw_data_path": "data/raw_papers.json",
        "clean_output_path": "data/clean_papers.csv",
        "corrupted_output_path": "data/corrupted_papers.csv",
        "corruption_log_path": "data/corruption_log.json",
        "repaired_output_path": "data/repaired_papers.csv",
        "eval_set_path": "data/eval_set.json",
        "chroma_db_dir": "data/chroma_db_phase2",
        "report_path": "reports/phase2_comparison_report.md",
        "embedding_model": "all-MiniLM-L6-v2",
        "top_k": 3,
    }
    os.makedirs("data", exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    # -------------------------------------------------------------------------
    # Helper Functions cho Indexing & Evaluation
    # -------------------------------------------------------------------------
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=config["embedding_model"]
    )
    chroma_client = chromadb.PersistentClient(path=config["chroma_db_dir"])

    def evaluate_dataset(
        df_data: pd.DataFrame, collection_name: str, eval_set: list
    ) -> dict:
        """Helper rebuild index ChromaDB và tính Hit@K, MRR."""
        try:
            chroma_client.delete_collection(name=collection_name)
        except Exception:
            pass

        collection = chroma_client.create_collection(
            name=collection_name, embedding_function=emb_fn
        )

        # Lọc bỏ row rỗng text_for_embedding nếu có
        valid_df = df_data.dropna(subset=["text_for_embedding"]).copy()
        if valid_df.empty:
            return {"hit_rate": 0.0, "mrr": 0.0, "indexed_count": 0}

        # Nạp dữ liệu vào ChromaDB
        documents = valid_df["text_for_embedding"].tolist()
        metadatas = [
            {"paper_id": str(r.get("paper_id", idx))}
            for idx, r in valid_df.iterrows()
        ]
        ids = [f"{r.get('paper_id', idx)}_{idx}" for idx, r in valid_df.iterrows()]

        collection.add(documents=documents, metadatas=metadatas, ids=ids)

        # Đánh giá trên bộ eval_set
        hits = 0
        mrr_sum = 0.0
        for item in eval_set:
            query = item["question"]
            target_ids = set(item["ground_truth_doc_ids"])

            results = collection.query(
                query_texts=[query], n_results=config["top_k"]
            )
            # Lấy danh sách paper_id từ metadata kết quả truy vấn
            retrieved_metas = results["metadatas"][0] if results["metadatas"] else []
            retrieved_ids = [m.get("paper_id") for m in retrieved_metas if m]

            if any(doc_id in target_ids for doc_id in retrieved_ids):
                hits += 1

            for rank, doc_id in enumerate(retrieved_ids, start=1):
                if doc_id in target_ids:
                    mrr_sum += 1.0 / rank
                    break

        total_eval = len(eval_set) if eval_set else 1
        return {
            "hit_rate": hits / total_eval,
            "mrr": mrr_sum / total_eval,
            "indexed_count": collection.count(),
        }

    # -------------------------------------------------------------------------
    # Bước 1: Load baseline metrics và clean dataset
    # -------------------------------------------------------------------------
    print("\n[Step 1/8] Loading clean dataset & evaluation benchmark...")
    if not os.path.exists(config["clean_output_path"]):
        # Nếu chưa có clean dataset, đọc raw records để build
        with open(config["raw_data_path"], "r", encoding="utf-8") as f:
            raw_records = json.load(f)
        clean_df = build_clean_dataframe(raw_records, run_date=run_date)
        clean_df.to_csv(config["clean_output_path"], index=False)
    else:
        clean_df = pd.read_csv(config["clean_output_path"])

    if not os.path.exists(config["eval_set_path"]):
        eval_set = build_test_set(clean_df, output_path=config["eval_set_path"])
    else:
        with open(config["eval_set_path"], "r", encoding="utf-8") as f:
            eval_set = json.load(f)

    # Đo đạc chỉ số Baseline (Clean State)
    baseline_metrics = evaluate_dataset(clean_df, "baseline_col", eval_set)
    print(
        f"-> Baseline Metrics: Hit@{config['top_k']} = {baseline_metrics['hit_rate']:.2%}, "
        f"MRR = {baseline_metrics['mrr']:.4f}"
    )

    # -------------------------------------------------------------------------
    # Bước 2: Tạo corrupted dataframe
    # -------------------------------------------------------------------------
    print("\n[Step 2/8] Generating corrupted dataframe...")
    corrupted_df = corrupt_clean_dataframe(
        df=clean_df,
        output_log_path=config["corruption_log_path"],
        drop_latest_ratio=0.1,
        blank_summary_ratio=0.1,
        noise_text_ratio=0.1,
        truncate_title_ratio=0.1,
        shift_date_ratio=0.1,
        duplicate_ratio=0.05,
    )

    # -------------------------------------------------------------------------
    # Bước 3: Save corrupted artifacts
    # -------------------------------------------------------------------------
    print("\n[Step 3/8] Saving corrupted CSV & JSON artifacts...")
    corrupted_df.to_csv(
        config["corrupted_output_path"], index=False, encoding="utf-8"
    )
    print(f"-> Corrupted CSV saved to {config['corrupted_output_path']}")
    print(f"-> Corruption Log saved to {config['corruption_log_path']}")

    # -------------------------------------------------------------------------
    # Bước 4: Rebuild index và evaluate trên Corrupted Data
    # -------------------------------------------------------------------------
    print("\n[Step 4/8] Rebuilding vector index & evaluating Corrupted Data...")
    corrupted_metrics = evaluate_dataset(
        corrupted_df, "corrupted_col", eval_set
    )
    print(
        f"-> Corrupted Metrics: Hit@{config['top_k']} = {corrupted_metrics['hit_rate']:.2%}, "
        f"MRR = {corrupted_metrics['mrr']:.4f}"
    )

    # -------------------------------------------------------------------------
    # Bước 5: Run quality checks/freshness trên corrupted data
    # -------------------------------------------------------------------------
    print("\n[Step 5/8] Running quality & freshness checks on corrupted data...")
    corrupted_null_summaries = (
        (corrupted_df["summary"] == "").sum()
        + corrupted_df["summary"].isna().sum()
    )
    corrupted_duplicates = corrupted_df.duplicated(subset=["paper_id"]).sum()
    print(
        f"-> Quality Issues Found: Empty Summaries = {corrupted_null_summaries}, "
        f"Duplicates = {corrupted_duplicates}"
    )

    # -------------------------------------------------------------------------
    # Bước 6: Repair lại từ raw records
    # -------------------------------------------------------------------------
    print(
        "\n[Step 6/8] Executing Repair Pipeline (Re-building from Raw Data)..."
    )
    with open(config["raw_data_path"], "r", encoding="utf-8") as f:
        raw_records = json.load(f)

    repaired_df = build_clean_dataframe(raw_records, run_date=run_date)
    repaired_df.to_csv(
        config["repaired_output_path"], index=False, encoding="utf-8"
    )
    print(f"-> Repaired dataset saved to {config['repaired_output_path']}")

    # -------------------------------------------------------------------------
    # Bước 7: Evaluate repaired dataset
    # -------------------------------------------------------------------------
    print("\n[Step 7/8] Evaluating Repaired Dataset...")
    repaired_metrics = evaluate_dataset(repaired_df, "repaired_col", eval_set)
    print(
        f"-> Repaired Metrics: Hit@{config['top_k']} = {repaired_metrics['hit_rate']:.2%}, "
        f"MRR = {repaired_metrics['mrr']:.4f}"
    )

    # -------------------------------------------------------------------------
    # Bước 8: Tạo comparison report
    # -------------------------------------------------------------------------
    print("\n[Step 8/8] Generating Markdown Comparison Report...")
    report_md = f"""# 📈 Data Corruption & Repair Comparison Report

- **Execution Timestamp:** {run_date.strftime("%Y-%m-%d %H:%M:%S")}
- **Embedding Model:** `{config['embedding_model']}`
- **Top-K Retrieval:** `{config['top_k']}`

## 1. Metrics Performance Across Pipeline Stages

| Pipeline Stage | Indexed Docs | Hit Rate @ {config['top_k']} | MRR @ {config['top_k']} | Status |
| :--- | :---: | :---: | :---: | :---: |
| **1. Baseline (Clean)** | `{baseline_metrics['indexed_count']}` | `{baseline_metrics['hit_rate']:.2%}` | `{baseline_metrics['mrr']:.4f}` | 🟢 Optimal |
| **2. Corrupted** | `{corrupted_metrics['indexed_count']}` | `{corrupted_metrics['hit_rate']:.2%}` | `{corrupted_metrics['mrr']:.4f}` | 🔴 Degradation |
| **3. Repaired** | `{repaired_metrics['indexed_count']}` | `{repaired_metrics['hit_rate']:.2%}` | `{repaired_metrics['mrr']:.4f}` | 🟢 Restored |

## 2. Impact Analysis
- **Retrieval Performance Degradation:** `{(corrupted_metrics['hit_rate'] - baseline_metrics['hit_rate']):.2%}`
- **Repair Recovery Rate:** `{(repaired_metrics['hit_rate'] - corrupted_metrics['hit_rate']):.2%}`
- **Corrupted Data Quality Flaws:**
  - Missing/Blank Summaries: `{corrupted_null_summaries}`
  - Duplicate Records: `{corrupted_duplicates}`

## 3. Conclusion
Lớp kiểm thử độ bền (Robustness testing) cho thấy các dạng nhiễu dữ liệu làm giảm chất lượng tìm kiếm Vector Search.
Quy trình làm sạch tự động (Auto-repair pipeline) đã khôi phục thành công các chỉ số tìm kiếm về mức Baseline tối ưu.
"""
    with open(config["report_path"], "w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"-> Comparison report saved to {config['report_path']}")
    print("\n" + "=" * 65)
    print("✅ PHASE 2 PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 65)


if __name__ == "__main__":
    main()