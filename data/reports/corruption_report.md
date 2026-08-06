# Data Corruption, Repair & Impact Comparison Report

## 1. Overview & Objectives
This report evaluates the direct impact of intentional data corruption on AI Agent / RAG performance, and demonstrates the effectiveness of automated data repair from raw artifacts.

## 2. End-to-End Metrics Comparison Table

| Metric | Baseline (Clean) | Corrupted (Lỗi) | Repaired (Đã sửa) | Impact Analysis |
| :--- | :---: | :---: | :---: | :--- |
| **Retrieval Hit Rate** | 1.0000 | **0.7500** | **1.0000** | Retrieval performance drops during corruption & recovers after repair |
| **Mean Token F1** | 0.4389 | **0.2744** | **0.4389** | Answer quality drops with corrupted text & restores post-repair |
| **LLM Judge Accuracy** | 0.3750 | **0.2500** | **0.3750** | LLM correctness evaluation score tracking |
| **Mean LLM Judge Score** | 2.42 / 5.0 | **1.92 / 5.0** | **2.42 / 5.0** | Average grade out of 5 |

## 3. Data Quality & Freshness Comparison

| Observability Metric | Corrupted Dataset | Repaired Dataset |
| :--- | :---: | :---: |
| **Quality Status** | `FAILED` | `PASSED` |
| **Duplicate Rows** | 2 | 0 |
| **Short/Empty Summaries** | 8 | 0 |
| **Freshness Status** | `STALE` | `FRESH` |
| **Stale Rows** | 2 | 0 |

## 4. Key Findings & Conclusion
- **Data Quality Impact**: Corrupted data (blank summaries, noise, duplicates, stale dates) directly causes retrieval failures and incorrect AI Agent answers.
- **Data Observability**: Data quality checks successfully catch missing fields, duplicates, and stale records before users receive incorrect answers.
- **Data Repair**: Rebuilding the cleaned dataset from the raw source artifacts restores 100% of pipeline performance.
