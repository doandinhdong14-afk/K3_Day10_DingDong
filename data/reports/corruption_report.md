# Corruption flow - baseline vs corrupted vs repaired

Generated at: `2026-08-06T09:29:04.035899+00:00`

Ca ba trang thai duoc danh gia tren **cung mot evaluation set** va cung cau hinh retrieval.

## 1. Metrics

| Metric | Baseline | Corrupted | Repaired | Corrupted vs baseline | Repaired vs baseline |
| --- | --- | --- | --- | --- | --- |
| Retrieval hit rate | 1.0000 | 0.8000 | 1.0000 | -0.2000 v | +0.0000 = |
| Mean token F1 | 1.0000 | 0.7137 | 1.0000 | -0.2863 v | +0.0000 = |
| Judge accuracy | 1.0000 | 0.7000 | 1.0000 | -0.3000 v | +0.0000 = |
| Mean judge score (1-5) | 5.0000 | 3.9000 | 5.0000 | -1.1000 v | +0.0000 = |

Judge duoc dung: baseline = `LLM judge (20/20)`, corrupted = `LLM judge (20/20)`, repaired = `LLM judge (20/20)`.

## 2. Data quality va freshness

| Signal | Baseline | Corrupted | Repaired |
| --- | --- | --- | --- |
| Quality suite | PASS (9/9 checks) | FAIL (6/9 checks) | PASS (9/9 checks) |
| Failed checks | - | paper_id_unique, summary_length_minimum, age_days_within_freshness_threshold | - |
| Freshness | FRESH (0 stale rows) | STALE (3 stale rows) | FRESH (0 stale rows) |
| Latest published | 2026-08-01 | 2026-07-03 | 2026-08-01 |
| Rows | 24 | 23 | 24 |

## 3. Cac loi da inject

Row: 24 -> 23 (-1)

| Loai loi | So dong | Mo ta |
| --- | --- | --- |
| `drop_latest_records` | 3 | Xoa 3 paper moi nhat de mo phong batch ingestion bi mat. |
| `blank_summary` | 3 | Xoa rong summary cua 3 paper de mo phong loi parse abstract. |
| `inject_noise` | 3 | Chen noise/markup rac vao summary cua 3 paper. |
| `truncate_title` | 2 | Cat title cua 2 paper con 12 ky tu. |
| `stale_publication_date` | 3 | Lui published date cua 3 paper ve 4 nam truoc. |
| `duplicate_rows` | 2 | Nhan doi 2 row de mo phong ingestion job chay trung. |

## 4. Ket luan

- Corruption lam giam retrieval hit rate (1.0000 -> 0.8000).
- Repair tu raw records khoi phuc duoc muc baseline (0.8000 -> 1.0000).
- Data quality suite phat hien loi ngay o buoc dataset, truoc khi cau tra loi sai den tay nguoi dung.
