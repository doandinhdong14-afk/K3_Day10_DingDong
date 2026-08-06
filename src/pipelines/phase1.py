from __future__ import annotations


from datetime import datetime
import json
import os
from typing import Any, List
import chromadb
from chromadb.utils import embedding_functions
import pandas as pd




def main() -> None:
    """TODO(student): xay dung baseline pipeline end-to-end.

    Pseudo-code:
    1. Load settings.
    2. Load hoac fetch raw records.
    3. Clean data.
    4. Save clean CSV/JSON.
    5. Build Chroma index.
    6. Tao hoac load evaluation set.
    7. Evaluate.
    8. Run quality checks va freshness report.
    9. Tao markdown report.
    10. Co the demo agent tren vai sample question.
    """
    print("=" * 60)
    print("🚀 STARTING RAG PIPELINE BASELINE RUN")
    print("=" * 60)
    run_date = datetime.now()

    # -------------------------------------------------------------------------
    # Bước 1: Load settings
    # -------------------------------------------------------------------------
    print("\n[Step 1/10] Loading settings...")
    config = {
        "raw_data_path": "data/raw_papers.json",
        "clean_output_path": "data/clean_papers.csv",
        "eval_set_path": "data/eval_set.json",
        "chroma_db_dir": "data/chroma_db",
        "report_path": "reports/pipeline_report.md",
        "collection_name": "arxiv_papers",
        "embedding_model": "all-MiniLM-L6-v2",
        "top_k": 3
    }
    os.makedirs("data", exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    # -------------------------------------------------------------------------
    # Bước 2: Load hoặc fetch raw records
    # -------------------------------------------------------------------------
    print("\n[Step 2/10] Loading raw paper records...")
    # Giả lập load dữ liệu thô nếu không tìm thấy file
    if os.path.exists(config["raw_data_path"]):
        with open(config["raw_data_path"], "r", encoding="utf-8") as f:
            raw_records = json.load(f)
    else:
        # Fallback dummy sample data nếu chưa fetch từ ArXiv API
        raw_records = [
            {
                "paper_id": "2301.00001",
                "title": "  Advances in Large Language  Models ",
                "summary": "This paper reviews recent progress in LLM architectures and alignment techniques.",
                "authors": ["Alice Smith", "Bob Jones"],
                "categories": ["cs.CL", "cs.AI"],
                "published": "2023-01-01T10:00:00Z"
            },
            {
                "paper_id": "2302.00002",
                "title": "Vector Databases for Retrieval-Augmented Generation",
                "summary": "We benchmark performance of ANN search algorithms in RAG pipelines.",
                "authors": ["Charlie Brown"],
                "categories": ["cs.DB", "cs.IR"],
                "published": "2023-02-15T14:30:00Z"
            }
        ]

    # -------------------------------------------------------------------------
    # Bước 3: Clean data
    # -------------------------------------------------------------------------
    print("\n[Step 3/10] Cleaning raw data...")
    # Gọi hàm build_clean_dataframe đã viết ở bài trước
    clean_df = build_clean_dataframe(raw_records, run_date=run_date)
    print(f"-> Cleaned {len(clean_df)} valid paper records.")

    # -------------------------------------------------------------------------
    # Bước 4: Save clean CSV/JSON
    # -------------------------------------------------------------------------
    print("\n[Step 4/10] Saving clean dataset...")
    clean_df.to_csv(config["clean_output_path"], index=False, encoding="utf-8")
    print(f"-> Saved to {config['clean_output_path']}")

    # -------------------------------------------------------------------------
    # Bước 5: Build Chroma index
    # -------------------------------------------------------------------------
    print("\n[Step 5/10] Building Vector Database (ChromaDB)...")
    chroma_client = chromadb.PersistentClient(path=config["chroma_db_dir"])
    
    # Sử dụng embedding function mặc định hoặc Sentence-Transformers
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=config["embedding_model"]
    )
    
    # Xóa collection cũ nếu tồn tại để build lại index mới
    try:
        chroma_client.delete_collection(name=config["collection_name"])
    except Exception:
        pass

    collection = chroma_client.create_collection(
        name=config["collection_name"], 
        embedding_function=emb_fn
    )

    # Nạp dữ liệu vào Vector Database
    documents = clean_df["text_for_embedding"].tolist()
    metadatas = [
        {"paper_id": str(r["paper_id"]), "title": str(r["title"]), "published": str(r["published"])}
        for _, r in clean_df.iterrows()
    ]
    ids = [str(r["paper_id"]) for _, r in clean_df.iterrows()]

    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    print(f"-> Indexed {collection.count()} vectors into ChromaDB.")

    # -------------------------------------------------------------------------
    # Bước 6: Tạo hoặc load evaluation set
    # -------------------------------------------------------------------------
    print("\n[Step 6/10] Preparing evaluation benchmark set...")
    if os.path.exists(config["eval_set_path"]):
        with open(config["eval_set_path"], "r", encoding="utf-8") as f:
            eval_set = json.load(f)
    else:
        # Gọi hàm build_test_set đã viết ở bài trước
        eval_set = build_test_set(clean_df, output_path=config["eval_set_path"], sample_size=5)
    print(f"-> Loaded {len(eval_set)} evaluation test cases.")

    # -------------------------------------------------------------------------
    # Bước 7: Evaluate Retrieval System
    # -------------------------------------------------------------------------
    print("\n[Step 7/10] Evaluating Vector Search (Hit Rate & MRR)...")
    hits = 0
    mrr_sum = 0.0

    for item in eval_set:
        query = item["question"]
        target_ids = set(item["ground_truth_doc_ids"])

        results = collection.query(query_texts=[query], n_results=config["top_k"])
        retrieved_ids = results["ids"][0] if results["ids"] else []

        # Hit Rate @ K
        has_hit = any(doc_id in target_ids for doc_id in retrieved_ids)
        if has_hit:
            hits += 1

        # MRR (Mean Reciprocal Rank) @ K
        for rank, doc_id in enumerate(retrieved_ids, start=1):
            if doc_id in target_ids:
                mrr_sum += 1.0 / rank
                break

    eval_count = len(eval_set) if eval_set else 1
    hit_rate = hits / eval_count
    mrr = mrr_sum / eval_count
    print(f"-> Evaluation Results: Hit@{config['top_k']} = {hit_rate:.2%}, MRR@{config['top_k']} = {mrr:.4f}")

    # -------------------------------------------------------------------------
    # Bước 8: Run quality checks và freshness report
    # -------------------------------------------------------------------------
    print("\n[Step 8/10] Running Data Quality & Freshness checks...")
    null_summaries = clean_df["summary"].isna().sum()
    duplicate_titles = clean_df.duplicated(subset=["title"]).sum()
    avg_age_days = clean_df["age_days"].mean() if "age_days" in clean_df.columns else 0

    quality_passed = (null_summaries == 0) and (duplicate_titles == 0)

    # -------------------------------------------------------------------------
    # Bước 9: Tạo markdown report
    # -------------------------------------------------------------------------
    print("\n[Step 9/10] Generating pipeline execution report...")
    report_content = f"""# 📊 RAG Pipeline Execution & Quality Report

- **Run Date:** {run_date.strftime("%Y-%m-%d %H:%M:%S")}
- **Pipeline Status:** {"🟢 PASSED" if quality_passed else "🔴 WARNING"}

## 1. Data Processing Statistics
| Metric | Value |
| :--- | :--- |
| Total Documents Processed | `{len(clean_df)}` |
| Missing Summaries | `{null_summaries}` |
| Duplicate Titles | `{duplicate_titles}` |
| Average Paper Age (Days) | `{avg_age_days:.1f}` |

## 2. Vector DB Indexing
- **Collection Name:** `{config['collection_name']}`
- **Total Vectors Indexed:** `{collection.count()}`
- **Embedding Model:** `{config['embedding_model']}`

## 3. Retrieval Benchmark Metrics
- **Evaluated Samples:** `{len(eval_set)}`
- **Hit Rate @ {config['top_k']}:** `{hit_rate:.2%}`
- **MRR @ {config['top_k']}:** `{mrr:.4f}`
"""
    with open(config["report_path"], "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"-> Report saved to {config['report_path']}")

    # -------------------------------------------------------------------------
    # Bước 10: Demo agent trên vài sample question
    # -------------------------------------------------------------------------
    print("\n[Step 10/10] 🤖 Demo Agent Retrieval Inference:")
    demo_queries = [
        "What are the main advances in LLM architectures?",
        "Vector databases for retrieval search"
    ]

    for q in demo_queries:
        print(f"\n❓ User Question: '{q}'")
        res = collection.query(query_texts=[q], n_results=1)
        if res["documents"][0]:
            print(f"   📄 Top Retrieved Paper ID: {res['ids'][0][0]}")
            print(f"   📝 Content Snippet: {res['documents'][0][0][:120]}...")
        else:
            print("   ⚠️ No document found.")

    print("\n" + "=" * 60)
    print("✅ PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    main()


