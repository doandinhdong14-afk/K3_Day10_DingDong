# Phase 1 - Baseline Report

_Generated: 2026-08-06 05:17:03 UTC_

## 1. Nguon du lieu

| Truong | Gia tri |
| --- | --- |
| source_api | Crossref REST API |
| source_mode | raw snapshot |
| source_query | agentic retrieval augmented generation large language model |
| source_filter | from-pub-date:2026-02-07,has-abstract:true |
| max_results | 24 |
| raw_records | 24 |
| clean_rows | 24 |
| embedding_model | sentence-transformers/all-MiniLM-L6-v2 |
| collection_name | papers-baseline |
| top_k | 4 |
| llm_provider | groq |
| llm_model | openai/gpt-oss-20b |
| raw_response_path | data/raw/crossref_response.json |
| raw_records_path | data/raw/crossref_records.json |
| clean_csv_path | data/clean/papers_clean.csv |
| generated_at | 2026-08-06T05:17:03.872158+00:00 |

## 2. Evaluation metrics

| Metric | Gia tri |
| --- | --- |
| samples | 20 |
| retrieval_hit_rate | 1.0000 |
| mean_token_f1 | 1.0000 |
| judge_accuracy | 1.0000 |
| mean_judge_score | 5.0000 |

- Ragas: bo qua - Set RUN_RAGAS=1 to enable the slower Ragas pass.

## 3. Data quality

- Tong quan: 12/12 check pass (ty le 1.0000), trang thai chung: PASS.

| Check | Dimension | Ket qua | Ky vong | Thuc te | So dong loi |
| --- | --- | --- | --- | --- | --- |
| row_count | completeness | PASS | row_count >= 10 | row_count = 24 | 0 |
| paper_id_not_null | completeness | PASS | every row has a non-empty 'paper_id' | 0 / 24 rows have a null/blank 'paper_id' | 0 |
| paper_id_unique | uniqueness | PASS | 'paper_id' is unique across all rows | 0 / 24 rows repeat an existing 'paper_id' | 0 |
| title_not_null | completeness | PASS | every row has a non-empty 'title' | 0 / 24 rows have a null/blank 'title' | 0 |
| title_min_length | validity | PASS | every row has title_chars >= 10 | 0 / 24 rows have title_chars < 10 or a non-numeric value | 0 |
| summary_not_empty | completeness | PASS | every row has a non-empty 'summary' | 0 / 24 rows have a null/blank 'summary' | 0 |
| summary_min_length | validity | PASS | every row has summary_chars >= 80 | 0 / 24 rows have summary_chars < 80 or a non-numeric value | 0 |
| text_for_embedding_present | completeness | PASS | every row has a non-empty 'text_for_embedding' | 0 / 24 rows have a null/blank 'text_for_embedding' | 0 |
| freshness_within_threshold | freshness | PASS | no row has age_days > 180 | 0 / 24 rows are older than 180 days | 0 |
| published_format_valid | validity | PASS | every 'published' value matches YYYY-MM-DD | 0 / 24 rows have a malformed 'published' value | 0 |
| title_chars_consistent | consistency | PASS | title_chars equals len(title) on every row | 0 / 24 rows have title_chars out of sync with 'title' | 0 |
| summary_chars_consistent | consistency | PASS | summary_chars equals len(summary) on every row | 0 / 24 rows have summary_chars out of sync with 'summary' | 0 |

## 4. Freshness

| Truong | Gia tri |
| --- | --- |
| generated_at | 2026-08-06T05:17:03.865145+00:00 |
| latest_published | 2026-08-01 |
| oldest_published | 2026-02-12 |
| stale_rows | 0 |
| total_rows | 24 |
| is_fresh | true |
| freshness_threshold_days | 180 |
| max_age_days | 175 |
| min_age_days | 5 |
| mean_age_days | 83.3300 |
| stale_ratio | 0.0000 |
| age_days_available | true |
| stale_paper_ids | n/a |

## 5. Nhan xet

- Data quality: 12/12 check pass (ty le 1.0000, trang thai chung PASS), tat ca check deu pass nen dataset dat chuan de dung cho retrieval.
- Freshness: dataset con moi, latest_published=2026-08-01, oldest_published=2026-02-12, 0/24 dong stale (ty le 0.0000).
- Retrieval: retrieval_hit_rate=1.0000 tren 20 cau hoi, muc do rat cao, con thieu 0.0000 so voi muc toi da 1.0000.
- Chat luong tra loi: mean_token_f1=1.0000, judge_accuracy=1.0000, mean_judge_score=5 -> muc rat cao.
- Ragas bi bo qua nen ket luan hien dua hoan toan vao token-F1 va LLM judge.
