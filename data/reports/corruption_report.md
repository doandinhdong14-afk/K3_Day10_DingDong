# Corruption Impact Report

_Generated: 2026-08-06 05:57:02 UTC_

## 1. Tom tat

Bao cao so sanh 4 metric chinh giua ba trang thai baseline / corrupted / repaired: corruption lam giam 4/4 metric, manh nhat la judge_accuracy (-0.3500, tuong duong 0.3500 lan gia tri baseline). Sau khi repair, 4/4 metric quay ve muc bang hoac cao hon baseline. Chi tiet tung metric, tung data quality check va tin hieu freshness nam o cac muc ben duoi.

## 2. So sanh metrics

| Metric | Baseline | Corrupted | Repaired | Thay doi do corruption | Muc phuc hoi |
| --- | --- | --- | --- | --- | --- |
| retrieval_hit_rate | 1.0000 | 0.8000 | 1.0000 | -0.2000 | +0.2000 (da ve muc baseline) |
| mean_token_f1 | 1.0000 | 0.6684 | 1.0000 | -0.3316 | +0.3316 (da ve muc baseline) |
| judge_accuracy | 1.0000 | 0.6500 | 1.0000 | -0.3500 | +0.3500 (da ve muc baseline) |
| mean_judge_score | 5.0000 | 3.6000 | 5.0000 | -1.4000 | +1.4000 (da ve muc baseline) |

## 3. Data quality theo trang thai

| Check | Corrupted | Repaired |
| --- | --- | --- |
| row_count | PASS | PASS |
| paper_id_not_null | PASS | PASS |
| paper_id_unique | FAIL | PASS |
| title_not_null | PASS | PASS |
| title_min_length | FAIL | PASS |
| summary_not_empty | FAIL | PASS |
| summary_min_length | FAIL | PASS |
| text_for_embedding_present | PASS | PASS |
| freshness_within_threshold | FAIL | PASS |
| published_format_valid | PASS | PASS |
| title_chars_consistent | PASS | PASS |
| summary_chars_consistent | PASS | PASS |

## 4. Freshness theo trang thai

| Truong | Corrupted | Repaired |
| --- | --- | --- |
| latest_published | 2026-07-03 | 2026-08-01 |
| oldest_published | 2023-02-26 | 2026-02-12 |
| stale_rows | 4 | 0 |
| total_rows | 23 | 24 |
| is_fresh | false | true |
| generated_at | 2026-08-06T05:55:56.347919+00:00 | 2026-08-06T05:57:02.102337+00:00 |
| freshness_threshold_days | 180 | 180 |
| max_age_days | 1256 | 175 |
| min_age_days | 34 | 5 |
| mean_age_days | 278.7000 | 83.3300 |
| stale_ratio | 0.1739 | 0.0000 |
| age_days_available | true | true |
| stale_paper_ids | 10.21079/11681/50309, 10.52060/juptik.v4i1.4318, 10.1093/sleep/zsag091.0346, 10.35314/3y9hy151 | n/a |

## 5. Ket luan

1. Corruption -> data quality corrupted 7/12 check pass (paper_id_unique, title_min_length, summary_not_empty, +2 check khac), freshness is_fresh=false voi stale_rows=4 -> judge_accuracy giam -0.3500 so voi baseline, chung to du lieu hong keo tut chat luong tra loi cua agent.
2. Repair -> data quality repaired 12/12 check pass, freshness is_fresh=true voi stale_rows=0 -> judge_accuracy phuc hoi +0.3500 va da ve bang hoac vuot baseline (1.0000 so voi baseline 1.0000).
3. Repair lam 5 check chuyen tu FAIL sang PASS (paper_id_unique, title_min_length, summary_not_empty), dua ty le pass tu 7/12 len 12/12.
4. Tin hieu freshness cung phuc hoi: stale_rows tu 4 ve 0 va is_fresh tro lai true sau khi repair tu raw source.
