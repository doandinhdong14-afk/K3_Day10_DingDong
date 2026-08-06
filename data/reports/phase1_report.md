# Phase 1 - Baseline pipeline report

Generated at: `2026-08-06T09:25:56.279473+00:00`

## 1. Nguon du lieu

| Field | Value |
| --- | --- |
| source_api | Crossref REST API |
| source_mode | reused cached snapshot in data/raw/ |
| query | agentic retrieval augmented generation large language model |
| filter | from-pub-date:2026-02-07,has-abstract:true,until-pub-date:2026-08-06 |
| max_results | 24 |
| raw_records | 24 |
| clean_rows | 24 |
| embedding_model | sentence-transformers/all-MiniLM-L6-v2 |
| collection_name | papers-baseline |
| top_k | 4 |
| llm_provider | gemini |
| llm_model | gemini-3.5-flash-lite |
| judge_mode | LLM judge (20/20) |
| run_started_at | 2026-08-06T09:24:58.427585+00:00 |

## 2. Evaluation metrics (du lieu sach)

Test set: **20** cau hoi, dung chung cho ca 3 trang thai.

| Metric | Value |
| --- | --- |
| Retrieval hit rate | 1.0000 |
| Mean token F1 | 1.0000 |
| Judge accuracy | 1.0000 |
| Mean judge score (1-5) | 5.0000 |

> Ragas: Set RUN_RAGAS=1 to enable the slower Ragas pass.

## 3. Data quality

- Engine: `great_expectations`
- Ket qua: **PASS (9/9 checks)**
- Check that bai: -
- So dong kiem tra: 24

| Check | Column | Success | Observed |
| --- | --- | --- | --- |
| `row_count_minimum` | `-` | PASS | `{'observed_value': 24}` |
| `paper_id_not_null` | `paper_id` | PASS | `{'element_count': 24, 'unexpected_count': 0, 'unexpected_percent': 0.0}` |
| `paper_id_unique` | `paper_id` | PASS | `{'element_count': 24, 'unexpected_count': 0, 'unexpected_percent': 0.0}` |
| `title_not_null` | `title` | PASS | `{'element_count': 24, 'unexpected_count': 0, 'unexpected_percent': 0.0}` |
| `title_length_minimum` | `title` | PASS | `{'element_count': 24, 'unexpected_count': 0, 'unexpected_percent': 0.0}` |
| `summary_length_minimum` | `summary` | PASS | `{'element_count': 24, 'unexpected_count': 0, 'unexpected_percent': 0.0}` |
| `published_is_iso_date` | `published` | PASS | `{'element_count': 24, 'unexpected_count': 0, 'unexpected_percent': 0.0}` |
| `text_for_embedding_length_minimum` | `text_for_embedding` | PASS | `{'element_count': 24, 'unexpected_count': 0, 'unexpected_percent': 0.0}` |
| `age_days_within_freshness_threshold` | `age_days` | PASS | `{'element_count': 24, 'unexpected_count': 0, 'unexpected_percent': 0.0}` |

## 4. Freshness

| Field | Value |
| --- | --- |
| generated_at | 2026-08-06T09:25:56.277209+00:00 |
| freshness_threshold_days | 180 |
| total_rows | 24 |
| latest_published | 2026-08-01 |
| oldest_published | 2026-02-12 |
| min_age_days | 5 |
| max_age_days | 175 |
| median_age_days | 66.0000 |
| stale_rows | 0 |
| stale_ratio | 0.0000 |
| is_fresh | yes |
| status | FRESH |

## 5. Doc ket qua

- `retrieval_hit_rate` cho biet retriever co lay dung paper chua ground truth hay khong.
- `mean_token_f1` do do trung lexical giua cau tra loi va ground truth.
- `judge_accuracy` / `mean_judge_score` la danh gia cua LLM judge tren cung cau hoi.
- Data quality va freshness la tin hieu chan truoc: neu chung FAIL thi metrics phia sau khong dang tin.
