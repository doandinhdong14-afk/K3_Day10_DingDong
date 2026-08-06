# Member Role Report — Day 10: Data Pipeline & Data Observability

> Báo cáo vai trò cá nhân của **Đặng Quang Minh (2A202601459)** — Observability owner của nhóm DingDong. Nội dung chỉ mô tả phần việc tôi trực tiếp thực hiện (khối 4 — data quality & freshness), không sao chép báo cáo nhóm hay báo cáo của thành viên khác.

> **Lưu ý về provider LLM:** run đã nộp chạy với `provider=groq`, `model=openai/gpt-oss-20b` (xác minh tại `data/reports/phase1_report.md`, mục 1: `llm_provider | groq`, `llm_model | openai/gpt-oss-20b`). Khối của tôi hoàn toàn không gọi LLM — 12 quality check và freshness report đều là phép tính tất định trên DataFrame. Nhưng các con số `judge_*` tôi trích ở mục 8 thì phụ thuộc vào LLM này, nên nếu nhóm chạy lại trên provider khác thì phải cập nhật hai trường provider/model.

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Đặng Quang Minh |
| MSSV               | 2A202601459 |
| Khóa/Lớp         | K3 |
| Tên nhóm         | DingDong (4 thành viên) |
| Vai trò chính    | Observability owner — khối 4 (data quality & freshness) |
| Repository         | https://github.com/doandinhdong14-afk/K3_Day10_DingDong |
| Ngày hoàn thành | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

### Danh mục 7 khối deliverable của project

Khối được **in đậm** là khối tôi trực tiếp làm.

| # | Khối deliverable           | File nguồn phụ trách                                              | Artifact phải bàn giao                                                                                       |
| -: | -------------------------- | ------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| 1 | Raw ingestion              | `src/ingestion/crossref.py`                                       | `data/raw/crossref_response.json`, `crossref_records.json` (24 raw records)                                   |
| 2 | Cleaning & data modeling   | `src/ingestion/cleaning.py`                                       | `data/clean/papers_clean.csv`, `papers_clean.json` (24 dòng × 16 cột)                                       |
| 3 | Evaluation set             | `src/evaluation/testset.py`                                       | `data/eval/test_set.json` (20 câu hỏi / 5 paper / 4 loại câu hỏi)                                        |
| **4** | **Quality & freshness** | **`src/observability/quality.py`**                                | **`data/quality/baseline_quality.json`, `corrupted_quality.json`, `repaired_quality.json` + 3 file `freshness_report*.json`** |
| 5 | Reporting                  | `src/observability/reporting.py`                                  | `data/reports/phase1_report.md`, `corruption_report.md`, `answer_diff.md`                                   |
| 6 | Baseline orchestration     | `src/pipelines/phase1.py`, `src/retrieval/index.py`               | `data/results/baseline_metrics.json`, `baseline_answers.json`, `data/embeddings/`, `data/chroma/`           |
| 7 | Corruption & repair        | `src/ingestion/corruption.py`, `src/pipelines/corruption_flow.py` | `data/results/corruption_log.json`, `corrupted_metrics.json`, `repaired_metrics.json`                       |

Phân công của nhóm (cấu hình 4 người theo [`README.md`](README.md) mục 5, có điều chỉnh: `reporting.py` được chuyển sang leader vì cả ba file report đều phải đọc output của hai flow do leader điều phối):

| Họ và tên | MSSV | Vai trò | Khối sở hữu |
| ----------- | ------ | --------- | ------------- |
| Trần Hoài Nam | 2A202601751 | Source owner | Khối 1 — `crossref.py` |
| Dương Hải Long | 2A202601607 | Data model & evaluation-set owner | Khối 2, 3 — `cleaning.py`, `testset.py` |
| **Đặng Quang Minh** | **2A202601459** | **Observability owner** | **Khối 4 — `quality.py`** |
| Đoàn Đình Đông (leader) | 2A202601900 | Reporting, orchestration & corruption owner | Khối 5, 6, 7 + điều phối tích hợp |

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | ------------ |
| Bộ 12 data quality check trên 5 dimension | `run_data_quality_checks()` và các hàm dựng check: `_row_count_check()`, `_not_null_check()`, `_unique_check()`, `_min_length_check()`, `_freshness_check()`, `_published_format_check()`, `_char_count_consistency_check()` | Clean/corrupted/repaired DataFrame + `settings` + `report_name` | `data/quality/baseline_quality.json` (3.430 B), `corrupted_quality.json` (3.577 B), `repaired_quality.json` (3.430 B) | Hoàn thành |
| Schema guard chống `KeyError` | `_missing_column_check()` + guard `if column in columns` cho từng check | DataFrame có thể thiếu cột | Check FAIL kèm tên cột thay vì exception | Hoàn thành |
| Freshness report | `build_freshness_report()`, `_stale_mask()`, `_published_bounds()` | Cột `age_days` và `published` + `freshness_threshold_days = 180` | `freshness_report.json`, `freshness_report_corrupted.json`, `freshness_report_repaired.json` (385/518/385 B) | Hoàn thành |
| Các hàm phụ trợ chịu lỗi kiểu dữ liệu | `_text_series()`, `_numeric_series()`, `_blank_mask()`, `_as_bool_mask()`, `_below_min_mask()` | Cột có thể chứa `NaN`, kiểu lẫn lộn | Không hàm nào ném exception trên frame hỏng | Hoàn thành |
| Phát hiện `inject_noise` lọt qua bộ check | phân tích đối chiếu `corrupted_quality.json` với `corrupted_answers.json` | Artifact của cả ba trạng thái | Blocker còn mở, ghi ở mục 6 | **Chưa hoàn thành** |

Chỉ nhận ownership cho phần tôi trực tiếp thực hiện. Tôi **không** viết `crossref.py`, `cleaning.py`, `testset.py`, `reporting.py`, `phase1.py`, `corruption.py` hay `corruption_flow.py`.

Thứ tự phụ thuộc thực tế giữa các khối — khối của tôi là **nhánh quan sát**, không nằm trên đường đi của dữ liệu:

```text
Khối 1 raw ingestion
   -> Khối 2 cleaning
   -> Khối 3 test set + Khối 6 index/baseline
   -> Khối 4 quality/freshness  <-- phần việc của tôi (đọc clean frame, KHÔNG sửa nó)
      + Khối 5 reporting        (đọc lại JSON của tôi để dựng bảng Markdown)
   -> Khối 7 corruption/repair  (gọi lại khối 4 hai lần nữa: trên frame corrupted và repaired)
```

Đặc điểm quan trọng của vị trí này: `run_data_quality_checks()` được gọi **ba lần** trong hai flow — bước 8/10 của `phase1.py` trên frame sạch 24 dòng, bước 6/10 của `corruption_flow.py` trên frame corrupted 23 dòng, và bước 8/10 trên frame repaired 24 dòng. Nghĩa là hàm của tôi phải chạy được trên cả dữ liệu *đã hỏng* — chính là lúc nó cần thiết nhất. Đây là ràng buộc chi phối toàn bộ cách tôi viết code (xem mục 5).

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| ------------ | -------------------------------- | ---------- |
| Xác nhận `pdf_url` phải là trường tùy chọn, không đặt check bắt buộc | Trần Hoài Nam — `crossref._find_pdf_url()` | 7/24 dòng có `pdf_url` rỗng. Nếu tôi thêm check `pdf_url_not_null` thì baseline sẽ FAIL giả 7 dòng và làm hỏng mốc so sánh |
| Yêu cầu cột đếm phải được tính lại từ text để check consistency có ý nghĩa | Dương Hải Long — `cleaning.build_clean_dataframe()` | `title_chars = len(title)` và `summary_chars = len(summary)` được tính trong cleaning, nhờ đó `title_chars_consistent`/`summary_chars_consistent` bắt được trường hợp text bị sửa ngầm |
| Cung cấp danh sách `failed_check_names` và `total_failed_rows` ở cấp cao nhất của payload | Đoàn Đình Đông — `reporting.generate_corruption_report()` | Report dựng được bảng so sánh PASS/FAIL 12 dòng cho hai trạng thái mà không phải duyệt vào mảng `checks` |
| Chỉ ra rằng `row_count >= 10` không đủ để bắt `drop_latest_records` | Đoàn Đình Đông — thiết kế corruption | Trên corrupted, 24 → 23 dòng nhưng `row_count` vẫn **PASS** vì ngưỡng chỉ là 10. Đây là giới hạn đã biết, được ghi rõ ở mục 8 thay vì để người đọc hiểu nhầm |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------------- | ----------------------------- | ------------------- | --------------- |
| Xây 12 check trên 5 dimension | `run_data_quality_checks()` | Baseline 12/12 PASS, `success = true`, `total_failed_rows = 0` trên 24 dòng | `python script/run_phase1.py` (bước 8/10); mở `data/quality/baseline_quality.json` |
| Check completeness (4 check) | `_row_count_check()` (`MIN_ROWS = 10`), `_not_null_check()` cho `paper_id`, `title`, `summary`, `text_for_embedding` | 0/24 dòng rỗng ở mọi cột bắt buộc | như trên |
| Check uniqueness (1 check) | `_unique_check(df, "paper_id", ...)` | Baseline PASS; corrupted FAIL 2 dòng do `duplicate_rows` | `baseline_quality.json` vs `corrupted_quality.json` |
| Check validity (3 check) | `_min_length_check()` với `MIN_TITLE_CHARS = 10`, `MIN_SUMMARY_CHARS = 80`; `_published_format_check()` với `PUBLISHED_DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"` | Baseline PASS; corrupted FAIL `title_min_length` 3 dòng, `summary_min_length` 3 dòng | như trên |
| Check consistency (2 check) | `_char_count_consistency_check()` cho cặp `title`/`title_chars` và `summary`/`summary_chars` | PASS ở cả ba trạng thái — kể cả corrupted (phân tích ở mục 6) | như trên |
| Check freshness (1 check) | `_freshness_check()` với `age_days > threshold` | Baseline 0/24 quá hạn; corrupted FAIL 4/23 dòng | `corrupted_quality.json` |
| Freshness report định lượng | `build_freshness_report()` | Baseline `is_fresh = true`, `stale_rows = 0/24`, `max_age_days = 175`, `min_age_days = 5`, `mean_age_days = 83.33`, `stale_ratio = 0.0` | `data/quality/freshness_report.json` |
| Truy vết dòng stale | `_stale_mask()` + `stale_paper_ids` (giới hạn `MAX_STALE_IDS = 20`) | Corrupted chỉ đích danh 4 DOI: `10.21079/11681/50309`, `10.52060/juptik.v4i1.4318`, `10.1093/sleep/zsag091.0346`, `10.35314/3y9hy151` | `data/quality/freshness_report_corrupted.json` |
| Chạy được trên frame khác số dòng và khác schema | schema guard + guard từng check | Cùng một hàm cho ra 12 check trên cả 3 frame (24 / 23 / 24 dòng) | So `total_rows` và `total_checks` trong 3 file quality |

### Lệnh xác minh thật của từng khối

| Khối | Lệnh chạy | Artifact phải mở để đối chiếu | Dấu hiệu đạt |
| ---- | ----------- | -------------------------------- | -------------- |
| Tiền đề cho mọi khối gọi LLM | `python script/check_llm.py` | stdout của script | 3 dòng `[OK  ]` cho *chat bình thường*, *structured output*, *tool calling*, kết thúc bằng `KET LUAN: provider san sang` |
| 1. Raw ingestion | `python script/run_phase1.py` (bước 2/10) | `data/raw/crossref_records.json` | 24 record, mỗi record đủ `paper_id/title/summary/authors/published` |
| 2. Cleaning | `python script/run_phase1.py` (bước 3–4/10) | `data/clean/papers_clean.csv` | 24 dòng, 16 cột, cột `text_for_embedding` không rỗng |
| 3. Evaluation set | `python script/run_phase1.py` (bước 6/10); ép tạo lại bằng `REFRESH_TEST_SET=1` | `data/eval/test_set.json` | 20 sample, 4 `question_type`, mỗi sample có đúng 1 `ground_truth_doc_ids` |
| **4. Quality & freshness (của tôi)** | `python script/run_phase1.py` (bước 8/10) và `python script/run_corruption_flow.py` (bước 6 và 8/10) | `data/quality/baseline_quality.json`, `corrupted_quality.json`, `repaired_quality.json`, `freshness_report*.json` | baseline 12/12 pass, corrupted 7/12 pass với 5 `failed_check_names`, repaired 12/12 pass |
| 5. Reporting | `python script/run_phase1.py` (bước 9/10), `python script/run_corruption_flow.py` (bước 9/10) | `data/reports/*.md` | bảng so sánh khớp với các file `*_metrics.json` |
| 6. Baseline orchestration | `python script/run_phase1.py` | `data/results/baseline_metrics.json` | `1.0 / 1.0 / 1.0 / 5`; mọi dòng artifact là `[OK]` |
| 7. Corruption & repair | `python script/run_corruption_flow.py` | `data/results/corruption_log.json` | 7 step, `source_rows=24`, `result_rows=23`, `deterministic=true` |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

**`data/quality/freshness_report_corrupted.json` (518 bytes)** là artifact nói lên rõ nhất giá trị của phần việc tôi làm, vì nó là file duy nhất trong toàn bộ pipeline *giải thích được bản chất* của một lỗi thay vì chỉ báo có lỗi. Trên trạng thái corrupted, bộ 12 check chỉ nói `freshness_within_threshold` FAIL trên 4/23 dòng — đúng nhưng vô nghĩa với người đi sửa. File freshness report thì ghi: `is_fresh = false`, `stale_rows = 4`, `stale_ratio = 0.1739`, `max_age_days = 1256` (baseline 175), `min_age_days = 34` (baseline 5), `mean_age_days = 278.7` (baseline 83.33), `latest_published = 2026-07-03` (baseline 2026-08-01), `oldest_published = 2023-02-26` (baseline 2026-02-12), kèm đích danh 4 `stale_paper_ids`. Từ cặp `oldest_published` 2026-02-12 → 2023-02-26 đọc ra ngay bản chất: **ngày bị đẩy lùi đúng 3 năm**, chứ không phải dữ liệu cũ dần theo thời gian. Leader dùng lại toàn bộ file này trong `generate_corruption_report()` để dựng mục 4 của `corruption_report.md`.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Khối của tôi phải trả lời hai câu hỏi khác nhau về cùng một dataset, và không được nhầm lẫn hai câu hỏi đó:

1. **"Dữ liệu có *đúng* không?"** — cần câu trả lời pass/fail để làm cổng chặn: có dòng nào rỗng, có `paper_id` trùng, `title_chars` có khớp `len(title)`, `published` có đúng định dạng.
2. **"Dữ liệu có *mới* không, và mới/cũ ở mức nào?"** — cần các đại lượng liên tục để theo dõi theo thời gian và để chẩn đoán.

Khó khăn thật nằm ở chỗ thứ ba, không hiển nhiên: hàm của tôi được gọi **ba lần trên ba frame khác nhau**, trong đó một frame là dữ liệu đã bị cố ý làm hỏng (23 dòng thay vì 24, có `paper_id` trùng, có `summary` rỗng). Một quality report chết vì `KeyError` đúng lúc dữ liệu hỏng thì hoàn toàn vô dụng.

### Cách triển khai

```text
DataFrame (24 | 23 | 24 dòng)
  -> run_data_quality_checks(df, settings, report_name)
       . Bước 0 — schema guard: với mỗi cột trong REQUIRED_COLUMNS mà thiếu
                  -> _missing_column_check(column, total_rows)  (FAIL, không raise)
       . completeness : _row_count_check(MIN_ROWS = 10)
                        _not_null_check  x4  (paper_id, title, summary, text_for_embedding)
       . uniqueness   : _unique_check(paper_id)
       . validity     : _min_length_check(title_chars >= 10)
                        _min_length_check(summary_chars >= 80)
                        _published_format_check(r"^\d{4}-\d{2}-\d{2}$")
       . freshness    : _freshness_check(age_days > 180)
       . consistency  : _char_count_consistency_check(title, title_chars)
                        _char_count_consistency_check(summary, summary_chars)
       -> payload: total_rows, total_checks, passed_checks, failed_checks,
                   success, failed_check_names, total_failed_rows, checks[]
       -> write_json(data/quality/{report_name}.json)

  -> build_freshness_report(df, settings, report_path)
       . _stale_mask(df, 180)          -> stale_rows, stale_ratio
       . _numeric_series("age_days")   -> max/min/mean_age_days
       . _published_bounds(df)         -> latest_published, oldest_published
                                          (chỉ lấy giá trị khớp PUBLISHED_DATE_PATTERN)
       . stale_paper_ids (tối đa MAX_STALE_IDS = 20)
       -> write_json(freshness_report[_corrupted|_repaired].json)
```

Bốn quyết định trong code của tôi mà tôi thấy đáng nói:

1. **Mỗi check được bọc trong `if column in columns`.** Không check nào giả định cột tồn tại. Cộng với `_missing_column_check()` ở bước 0, hàm không bao giờ ném `KeyError` — nó *báo cáo* việc thiếu cột như một kết quả FAIL có tên.
2. **Mọi phép so sánh đi qua các hàm ép kiểu chịu lỗi.** `_text_series()` ép về chuỗi, `_numeric_series()` dùng `pd.to_numeric(errors="coerce")`, `_as_bool_mask()` chuẩn hóa mask có `NaN`. Nhờ vậy một cột `summary_chars` chứa chuỗi thay vì số cũng chỉ làm check đó FAIL chứ không làm sập cả report.
3. **Payload có sẵn tầng tóm tắt ở cấp cao nhất.** `passed_checks`, `failed_checks`, `success`, `failed_check_names`, `total_failed_rows` được tính sẵn, không bắt người đọc phải duyệt mảng `checks`. Đây là lý do `reporting.py` dựng được bảng so sánh mà không cần biết cấu trúc bên trong từng check.
4. **`_published_bounds()` chỉ xét các giá trị khớp `PUBLISHED_DATE_PATTERN` rồi sắp xếp chuỗi.** Vì `published` là chuỗi `YYYY-MM-DD`, sắp xếp từ điển trùng với sắp xếp theo thời gian — không cần parse ngày, nên không có chỗ cho lỗi parse. Giá trị sai định dạng bị loại khỏi phép tính min/max thay vì làm hỏng nó.

### Input, output và contract

| Thành phần | Mô tả |
| ------------ | ------- |
| Input | DataFrame sạch/corrupted/repaired (16 cột) từ khối 2 và khối 7; `settings.freshness_threshold_days = 180`; `settings.paths.quality_dir`; tham số `report_name` để đặt tên file |
| Output | **Quality:** `data/quality/{report_name}.json` với các khóa `report_name`, `generated_at`, `total_rows`, `total_checks`, `passed_checks`, `failed_checks`, `success`, `failed_check_names`, `total_failed_rows`, `checks[]`; mỗi phần tử `checks[]` có `name`, `dimension`, `passed`, `expected`, `observed`, `failed_rows`. **Freshness:** `generated_at`, `latest_published`, `oldest_published`, `stale_rows`, `total_rows`, `is_fresh`, `freshness_threshold_days`, `max_age_days`, `min_age_days`, `mean_age_days`, `stale_ratio`, `age_days_available`, `stale_paper_ids` |
| Module phụ thuộc | `src/core/config.py` (`freshness_threshold_days`, `paths.quality_dir`), `src/core/utils.py` (`now_utc`, `write_json`), `pandas`. **Không** phụ thuộc vào LLM, mạng hay vector store |
| Module sử dụng output | `src/observability/reporting.py` (`generate_phase1_report()` mục 3–4, `generate_corruption_report()` mục 3–4), `src/pipelines/phase1.py` bước 8/10, `src/pipelines/corruption_flow.py` bước 6 và 8/10, `app/dashboard.py` |
| Điều kiện lỗi cần xử lý | Xem bảng bên dưới |

Các điều kiện lỗi **thực sự** được xử lý trong `quality.py`:

| Điều kiện lỗi | Vị trí xử lý | Cách xử lý |
| --------------- | -------------- | ------------ |
| DataFrame thiếu cột bắt buộc | `run_data_quality_checks()` bước 0 + `_missing_column_check()` | Sinh một check FAIL có tên `<column>_present` kèm mô tả, thay vì ném `KeyError`. Các check phụ thuộc cột đó bị bỏ qua nhờ guard `if column in columns` |
| Cột số chứa giá trị không phải số | `_numeric_series()` (`pd.to_numeric(errors="coerce")`), `_below_min_mask()` | Giá trị không ép được thành số bị tính là **vi phạm** (an toàn theo hướng bi quan), không làm sập check |
| Cột text chứa `NaN` | `_text_series()`, `_blank_mask()` | Ép về chuỗi rồi `strip()`; `NaN` được coi là rỗng |
| Mask chứa `NaN` sau phép so sánh | `_as_bool_mask()`, `_count_true()` | Chuẩn hóa về bool trước khi đếm, tránh đếm sai |
| DataFrame rỗng | `_published_bounds()` (`if "published" not in df.columns or df.empty`) | Trả `(None, None)` thay vì `IndexError` |
| Không có cột `age_days` | `build_freshness_report()` (`has_age_column`) | `is_fresh = false`, `age_days_available = false`, các đại lượng tuổi để `None` — báo rõ "không đo được" thay vì báo nhầm là "fresh" |
| `published` sai định dạng | `_published_bounds()` | Chỉ lấy giá trị khớp `^\d{4}-\d{2}-\d{2}$` để tính min/max; giá trị sai định dạng vẫn bị `published_format_valid` bắt riêng |
| Quá nhiều dòng stale khiến file phình to | `MAX_STALE_IDS = 20` | Chỉ ghi tối đa 20 `paper_id` đầu tiên |
| Frame corrupted có số dòng khác baseline | toàn bộ các check dùng `total_rows = len(df)` làm mẫu số | Mọi tỷ lệ được tính trên số dòng thực tế của frame đó (24 hoặc 23), không hard-code |

### Cách xác minh

```bash
python script/run_phase1.py            # bước 8/10 sinh baseline_quality.json + freshness_report.json
python script/run_corruption_flow.py   # bước 6/10 (corrupted) và bước 8/10 (repaired)
```

- **Kết quả mong đợi:** baseline 12/12 check PASS và `is_fresh = true`; corrupted rớt xuống 7/12 với 5 check FAIL và `is_fresh = false`; repaired quay lại 12/12 PASS và `is_fresh = true`.
- **Kết quả thực tế:** đúng như mong đợi. Baseline: `total_checks = 12`, `passed_checks = 12`, `success = true`, `total_failed_rows = 0` trên 24 dòng. Corrupted: `passed_checks = 7`, `failed_checks = 5`, `total_failed_rows = 15` trên 23 dòng. Repaired: `passed_checks = 12`, `total_failed_rows = 0` trên 24 dòng — `repaired_quality.json` và `baseline_quality.json` cùng 3.430 bytes và chỉ khác nhau ở `report_name` và `generated_at`.
- **Artifact/log:** `data/quality/baseline_quality.json`, `corrupted_quality.json`, `repaired_quality.json`, `freshness_report.json`, `freshness_report_corrupted.json`, `freshness_report_repaired.json`. Thư mục `data/quality/gx/` tồn tại nhưng **rỗng** — nhóm không dùng Great Expectations, toàn bộ bộ check được viết trực tiếp bằng pandas trong `quality.py`. Không file nào chứa API key; `.env` nằm trong `.gitignore`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** `run_data_quality_checks()` được gọi ba lần, trong đó lần thứ hai chạy trên **frame đã bị cố ý làm hỏng**. Bước corruption xóa dòng, làm rỗng `summary`, cắt `title`, nhân bản dòng — và về nguyên tắc nó có thể làm mất cả một cột. Câu hỏi thiết kế: khi frame không có cột mà check cần, hàm nên làm gì?

- **Các phương án đã cân nhắc:**
  - **Phương án A — giả định frame luôn đủ cột, để `KeyError` nổ:** viết `df["summary_chars"]` thẳng. Ưu điểm: code ngắn hơn đáng kể (không cần `_missing_column_check`, không cần guard `if column in columns` ở 11 chỗ), và lỗi nổ sớm nên dễ debug lúc phát triển. Đây cũng là cách "fail fast" thường được khuyến khích.
  - **Phương án B — schema guard: mỗi cột thiếu sinh ra một check FAIL có tên, mỗi check được bọc trong `if column in columns`:** hàm luôn chạy đến hết và luôn ghi ra file JSON.

- **Phương án đã chọn:** Phương án B.

- **Lý do:** một quality report chỉ có giá trị đúng vào lúc dữ liệu có vấn đề. Với phương án A, kịch bản xấu nhất là: frame corrupted mất một cột → `run_data_quality_checks()` ném `KeyError` → `corruption_flow` chết ở bước 6/10 → **không có `corrupted_quality.json` nào được ghi**, và người vận hành mất luôn thông tin về 11 check còn lại, trong đó có những check đã bắt được lỗi thật. Nói cách khác, "fail fast" đúng với code đang phát triển nhưng sai với công cụ quan sát: công cụ quan sát phải là thứ **cuối cùng** ngừng hoạt động, không phải thứ đầu tiên. Giá phải trả là code dài hơn và có 11 nhánh `if` trông lặp lại — tôi chấp nhận đánh đổi đó.

  Có một lý do thứ hai mang tính chẩn đoán: với B, thông tin "cột nào bị thiếu" trở thành **dữ liệu có cấu trúc** trong `failed_check_names`, đọc được bằng máy và so sánh được giữa các lần chạy. Với A nó chỉ là một dòng traceback trong terminal, mất ngay khi đóng cửa sổ.

- **Bằng chứng quyết định phù hợp:** cùng một hàm chạy được trên ba frame khác nhau và luôn cho ra đủ 12 check:

  | Trạng thái | `total_rows` | `total_checks` | `passed_checks` | `total_failed_rows` | `success` |
  | ------------ | ------------: | --------------: | ---------------: | -------------------: | ----------: |
  | baseline | 24 | 12 | 12 | 0 | `true` |
  | corrupted | **23** | 12 | **7** | **15** | `false` |
  | repaired | 24 | 12 | 12 | 0 | `true` |

  Điểm cần chú ý ở cột `total_rows`: frame corrupted có 23 dòng chứ không phải 24, và mọi tỷ lệ trong report đều tính trên mẫu số 23 — nếu tôi hard-code 24 ở bất kỳ đâu thì `stale_ratio` đã sai thành 4/24 = 0.1667 thay vì giá trị đúng 4/23 = 0.1739.

## 6. Một lỗi hoặc blocker đã xử lý

Blocker này tôi **chưa xử lý xong**, và tôi ghi lại nguyên trạng vì nó là phát hiện quan trọng nhất trong phần việc của mình.

- **Triệu chứng/lỗi nguyên văn:** không có exception, không có thông báo lỗi. Triệu chứng là một **mâu thuẫn giữa hai artifact**: `data/quality/corrupted_quality.json` liệt kê đúng 5 check FAIL —

  ```text
  "failed_check_names": ["paper_id_unique", "title_min_length",
                         "summary_not_empty", "summary_min_length",
                         "freshness_within_threshold"]
  ```

  — trong đó **không có check nào liên quan tới việc `summary` bị nhồi rác**. Nhưng trong `data/results/corrupted_answers.json`, câu `q012` trả về nguyên văn:

  ```text
  "LOREM IPSUM DOLOR ###### CORRUPTED PAYLOAD @@@@@@."
  ```

  với `retrieval_hit = true`, `token_f1 = 0.000`, judge 1/5. Tức là bộ check của tôi báo dữ liệu "ổn" ở đúng chỗ mà agent trả lời hoàn toàn sai.

- **Lệnh hoặc bước tái hiện:**

  ```bash
  python script/run_corruption_flow.py
  # Mở data/quality/corrupted_quality.json  -> đọc failed_check_names (5 tên, không có check nào về nội dung summary)
  # Mở data/results/corrupted_answers.json  -> tìm q012, đọc trường answer
  # Mở data/results/corruption_log.json     -> bước inject_noise chạm 3 dòng, trong đó có 10.21203/rs.3.rs-10012178/v1 (paper của q009-q012)
  ```

- **Nguyên nhân gốc:** bộ 12 check của tôi đo **hình dạng** dữ liệu, không đo **nội dung**. Cụ thể với `inject_noise` (nối 153 ký tự rác vào *đầu* `summary`):
  - `summary_not_empty` PASS — summary không rỗng, thậm chí còn dài hơn trước.
  - `summary_min_length` PASS — summary sau khi nhồi rác dài hơn 80 ký tự rất nhiều.
  - `summary_chars_consistent` PASS — đây là điểm tôi đã dự đoán sai. Tôi tin check này sẽ bắt được nhiễu, vì suy nghĩ ban đầu là "text bị sửa mà cột đếm không đổi thì consistency FAIL". Nhưng bước corruption **cập nhật luôn `summary_chars`** sau khi chèn rác, nên `summary_chars == len(summary)` vẫn đúng. Check consistency chỉ bắt được sửa đổi *lén lút*, không bắt được sửa đổi *trung thực nhưng sai nội dung*.

  Kết quả là toàn bộ 12 check im lặng, trong khi `first_sentence(summary)` của `qa.py` cắt trúng câu rác đứng đầu và trả thẳng nó cho người dùng.

- **Cách xử lý (mới ở mức phân tích, chưa viết code):** cần bổ sung nhóm check **nội dung**, khác về bản chất với 12 check hiện có:
  1. `summary_noise_ratio` — tỷ lệ ký tự không phải chữ-số-khoảng trắng trong `summary`; chuỗi rác `###### … @@@@@@` sẽ đẩy tỷ lệ này vọt lên so với phân bố bình thường của abstract học thuật.
  2. `summary_repeated_block` — phát hiện đoạn văn bản lặp lại nhiều lần trong cùng một `summary` (`NOISE_TOKEN` được lặp `NOISE_REPEAT = 3` lần).
  3. `summary_title_overlap` — độ tương đồng từ vựng giữa `summary` và `title`; abstract của một bài báo bao giờ cũng chia sẻ từ khóa với tiêu đề, còn chuỗi rác thì không.

- **Cách xác minh sau khi sửa (chưa chạy được):** chạy lại `python script/run_corruption_flow.py`, kỳ vọng `corrupted_quality.json` chuyển từ 7/12 sang 8/15 hoặc 9/15 với `failed_check_names` có thêm ít nhất `summary_noise_ratio`, và **`total_failed_rows` tăng thêm đúng 3** (số dòng mà `corruption_log.json` ghi cho bước `inject_noise`). Đồng thời `baseline_quality.json` phải giữ nguyên toàn PASS — nếu ba check mới báo FAIL trên dữ liệu sạch thì đó là báo động giả và ngưỡng phải chỉnh lại.

- **Điều học được:** một bộ check "12/12 PASS" không có nghĩa là dữ liệu tốt — nó chỉ có nghĩa là dữ liệu không vi phạm **những thứ tôi nghĩ ra để kiểm tra**. Trong lần chạy này, `inject_noise` là corruption *duy nhất* mà bộ check của tôi hoàn toàn bỏ lọt, và nó lại là một trong bốn corruption gây thiệt hại thật cho câu trả lời. Bài học rộng hơn: quality report và evaluation là **hai lưới lọc bổ sung cho nhau, không thay thế nhau** — evaluation bắt được cái mà check bỏ lọt (`inject_noise`), còn check bắt được cái mà evaluation không thấy (`duplicate_rows` làm `paper_id_unique` FAIL nhưng không đổi metric nào).

Phần chưa xử lý xong:

- **Phạm vi bị ảnh hưởng:** mọi lỗi thuộc dạng "dữ liệu đúng hình dạng nhưng sai nội dung" đều đang lọt qua bộ check hiện tại. Ngoài `inject_noise`, một trường hợp tương tự đã quan sát được là `stale_dates`: ngày bị đẩy lùi 3 năm nhưng `published_format_valid` vẫn PASS vì ngày sai *đúng định dạng* — may là chiều freshness bắt được, còn nội dung summary thì không có chiều nào tương đương.
- **Những gì đã loại trừ:** không phải lỗi của bước corruption (đối chiếu `corruption_log.json`: bước `inject_noise` ghi rõ 3 dòng bị chạm, đúng như thiết kế); không phải lỗi ghi file (mở trực tiếp `papers_clean_corrupted.csv` thấy chuỗi rác nằm đúng ở đầu cột `summary` của 3 dòng); không phải do check bị bỏ qua vì thiếu cột (`total_checks = 12` ở cả ba trạng thái, không check nào bị skip).
- **Bước tiếp theo:** viết `_content_noise_check()` trong `quality.py` với ngưỡng lấy từ phân bố thực tế của 24 abstract sạch (đo phân vị 95 của tỷ lệ ký tự không phải chữ-số trên baseline rồi cộng biên an toàn), thêm vào `run_data_quality_checks()`, rồi chạy lại cả hai flow và kiểm tra hai tiêu chí ở trên.

## 7. Hiểu biết về luồng end-to-end

**1. Từ Crossref đến vector index.** `fetch_source_records()` gọi `GET https://api.crossref.org/works` với query agentic RAG/LLM và filter `from-pub-date:2026-02-07,has-abstract:true`, xin dư `24 × 3 = 72` dòng, lưu payload thô rồi parse còn 71 record hợp lệ và cắt lấy 24 ghi vào `data/raw/crossref_records.json`. `build_clean_dataframe()` biến 24 record đó thành frame 16 cột, tính thêm `age_days`, `title_chars`, `summary_chars`, khử trùng hai lượt, sắp xếp `published` giảm dần và ghép cột `text_for_embedding` = `title + authors + categories + published + summary`. `LocalEmbeddingIndex.build()` cho `all-MiniLM-L6-v2` mã hóa đúng cột đó rồi nạp vào ChromaDB (`PersistentClient` tại `data/chroma/`, khoảng cách cosine) với metadata gồm `paper_id`, `title`, `published`, `authors_joined`, `categories_joined`, `summary`, `abs_url`, `pdf_url`. Ba trạng thái dùng ba collection riêng: `papers-baseline`, `papers-corrupted`, `papers-repaired`. Khối của tôi đứng ngoài đường đi này — tôi đọc frame sạch nhưng không sửa nó, nên quality report không bao giờ là nguyên nhân làm đổi kết quả.

**2. Test set và ground-truth document IDs.** `build_test_set()` chọn 5 paper trải đều (`df.iloc[::4]`) rồi sinh 4 câu hỏi mỗi paper — `authors`, `date`, `categories`, `summary` — thành 20 sample. Mỗi sample lưu `ground_truth` lấy từ frame sạch và `ground_truth_doc_ids` chứa đúng một `paper_id`. Khi chấm, `evaluate_pipeline()` gọi `answer_question()` lấy `top_k = 4` rồi tính hai loại chỉ số tách biệt: `retrieval_hit = any(doc_id in ground_truth_doc_ids for doc_id in retrieved_doc_ids)` chỉ hỏi "document đúng có nằm trong top-4 không", còn `token_f1` và LLM judge (structured output: `score` 1–5, `correct`, `reasoning`) chấm nội dung. Nhờ tách đôi mà phân biệt được "lấy nhầm tài liệu" (q001, `retrieval_hit = false`) với "lấy đúng tài liệu nhưng nội dung đã hỏng" (q008 và q012, `retrieval_hit = true` nhưng `token_f1 = 0.000`) — và trường hợp thứ hai chính là loại lỗi mà bộ check của tôi phải bắt được, vì evaluation chỉ phát hiện nó *sau khi* người dùng đã nhận câu trả lời sai.

**3. Quality checks khác freshness monitoring.** Đây là phần của tôi, và sự khác nhau là chủ ý thiết kế chứ không phải trùng lặp. `run_data_quality_checks()` chạy **12 check trên 5 chiều** và trả lời "dữ liệu có *đúng* không" bằng pass/fail theo dòng — dạng tín hiệu để **chặn**. `build_freshness_report()` trả lời "dữ liệu có *mới* không" bằng các đại lượng liên tục (`latest_published`, `oldest_published`, `stale_rows`, `stale_ratio`, `max/min/mean_age_days`, `is_fresh`, `stale_paper_ids`) — dạng tín hiệu để **quan sát xu hướng**. Hai thứ giao nhau ở đúng một điểm: check `freshness_within_threshold` (`age_days > 180`) là ảnh chụp nhị phân của cùng tín hiệu mà freshness report mô tả chi tiết. Trên dữ liệu corrupted, check chỉ nói "FAIL, 4/23 dòng", còn report nói thêm rằng `mean_age_days` nhảy từ **83.33 lên 278.7**, `max_age_days` từ **175 lên 1256**, `oldest_published` tụt từ **2026-02-12 về 2023-02-26**, và chỉ đích danh 4 `paper_id`. Chỉ nhìn check thì biết "có dòng quá hạn"; phải mở report mới biết **ngày bị đẩy lùi 3 năm** chứ không phải dữ liệu cũ dần. Gate cần pass/fail, chẩn đoán cần số liệu liên tục.

**4. Vì sao phải dùng cùng test set cho cả ba trạng thái.** Vì test set và `ground_truth` được sinh **từ dữ liệu sạch**. Nếu sinh lại từ frame corrupted thì `ground_truth` của câu hỏi summary sẽ chính là chuỗi rỗng hoặc chuỗi rác, câu hỏi ngày tháng sẽ lấy đúng ngày đã bị đẩy lùi — agent trả về rác vẫn được chấm 5/5, tức phép đo tự phá chính nó. Trong code, `phase1._load_or_build_test_set()` đọc lại `data/eval/test_set.json` nếu đã có và chỉ tạo mới khi bật `REFRESH_TEST_SET`; `corruption_flow` truyền thẳng `settings.paths.eval_testset` cho cả hai lần đánh giá của nó và nạp lại `baseline_metrics.json` thay vì chấm lại baseline. Một điều đáng chú ý ở phía tôi: bộ check **không** cần ràng buộc này, vì nó chấm trực tiếp trên frame chứ không qua một test set — đó cũng là lý do quality signal là bằng chứng độc lập với metric của agent, chứ không phải một cách diễn đạt khác của cùng một thứ.

**5. Repair thành công dựa trên artifact và metric nào.** Repair không vá frame hỏng mà **dựng lại từ snapshot nguồn**: `corruption_flow` bước 7 gọi `load_raw_records(data/raw/crossref_records.json)` rồi `build_clean_dataframe()` lại từ đầu — đúng con đường baseline đã đi. Kết luận thành công dựa trên ba nhóm bằng chứng độc lập, trong đó **nhóm thứ hai là của tôi**: (a) **số dòng** — `papers_clean_repaired.csv` có 24 dòng, trùng khít từng byte với `papers_clean.csv`; (b) **tín hiệu dữ liệu** — `repaired_quality.json` báo `passed_checks = 12`, `failed_checks = 0`, `failed_check_names = []`, `total_failed_rows = 0`, và `freshness_report_repaired.json` báo `is_fresh = true`, `stale_rows = 0`, `stale_ratio = 0.0`, `max_age_days = 175`, `mean_age_days = 83.33` — **trùng khít từng con số** với freshness report của baseline; (c) **metric của agent** — `repaired_metrics.json` cho 1.0 / 1.0 / 1.0 / 5 trên đúng 20 sample cũ. Ba nhóm phải cùng phục hồi mới kết luận được: nếu chỉ metric hồi mà quality vẫn FAIL thì nhiều khả năng lỗi nằm ở phép đo chứ không phải dữ liệu đã lành.

## 8. Phân tích kết quả

### Metrics chính

Số liệu đọc trực tiếp từ `data/results/*.json` và `data/quality/*.json` của lần chạy nộp bài.

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------- | -------: | --------: | -------: | ---------------------- |
| `retrieval_hit_rate` | 1.0000 | 0.8000 | 1.0000 | 4/20 câu mất hit, toàn bộ thuộc paper `10.2118/234689-pa` bị `drop_latest_records` xóa. Đáng lo với tôi: **không check nào của tôi bắt được việc mất 3 dòng**, vì `row_count` chỉ yêu cầu `>= 10` |
| `mean_token_f1` | 1.0000 | 0.6684 | 1.0000 | Giảm 0.3316. Theo loại câu hỏi: summary 0.4190, date 0.6000, authors 0.8000, categories 0.8545 |
| `judge_accuracy` | 1.0000 | 0.6500 | 1.0000 | 7/20 câu bị chấm sai: q001–q004, q008, q012, q018 |
| `mean_judge_score` | 5.0000 | 3.6000 | 5.0000 | 13 câu giữ 5/5, 7 câu còn lại đều 1/5 |
| **Quality checks** | **12/12** | **7/12** | **12/12** | Artifact của tôi. 5 check FAIL: `paper_id_unique` (2 dòng), `title_min_length` (3), `summary_not_empty` (3), `summary_min_length` (3), `freshness_within_threshold` (4). `total_failed_rows` 0 → **15** → 0 |
| **Freshness status** | fresh (0/24 stale) | **NOT fresh** (4/23 stale) | fresh (0/24 stale) | Artifact của tôi. `stale_ratio` 0.0 → 0.1739 → 0.0; `mean_age_days` 83.33 → 278.7 → 83.33; `max_age_days` 175 → 1256 → 175; `min_age_days` 5 → 34 → 5; `latest_published` 2026-08-01 → 2026-07-03 → 2026-08-01; `oldest_published` 2026-02-12 → 2023-02-26 → 2026-02-12 |

Số dòng: baseline **24** → corrupted **23** (xóa 3, thêm 2 bản trùng) → repaired **24**. Cả ba trạng thái chấm trên cùng `data/eval/test_set.json` (20 câu / 5 paper / 4 loại).

Đối chiếu từng loại corruption với tín hiệu quality — bảng này là phần phân tích chính của khối tôi:

| Loại corruption | Dòng bị chạm | Check của tôi bắt được? | Số câu hỏi bị hỏng |
| ----------------- | -------------: | ------------------------- | ---------------------: |
| `drop_latest_records` | 3 | **KHÔNG** — `row_count` chỉ yêu cầu `>= 10`, 23 dòng vẫn PASS | **4/20** |
| `blank_summary` | 3 | CÓ — `summary_not_empty` FAIL 3, `summary_min_length` FAIL 3 | 1/20 |
| `inject_noise` | 3 | **KHÔNG** — không check nào FAIL (phân tích ở mục 6) | 1/20 |
| `truncate_title` | 3 | CÓ — `title_min_length` FAIL 3 | **0/20** |
| `stale_dates` | 4 | CÓ — `freshness_within_threshold` FAIL 4; `published_format_valid` vẫn PASS | 1/20 |
| `duplicate_rows` | 2 | CÓ — `paper_id_unique` FAIL 2 | **0/20** |

### Kết luận từ số liệu

1. **Corruption → tín hiệu quality/freshness → metric agent.** `corrupt_clean_dataframe()` chạy 7 bước → `corrupted_quality.json` rớt từ 12/12 xuống **7/12** với 5 check FAIL trên 15 dòng lỗi, `freshness_report_corrupted.json` chuyển `is_fresh` từ `true` sang **`false`** với `stale_rows = 4/23` và `mean_age_days` tăng gấp 3.3 lần → `corrupted_metrics.json` cho **0.8000 / 0.6684 / 0.6500 / 3.6000**.

2. **Repair → tín hiệu quality/freshness phục hồi → metric agent phục hồi.** Bước 7 dựng lại frame từ raw snapshot → `repaired_quality.json` quay lại **12/12 pass**, `failed_check_names = []`, `total_failed_rows = 0`; `freshness_report_repaired.json` quay lại `is_fresh = true`, `stale_rows = 0`, `mean_age_days = 83.33` — **trùng khít từng con số** với baseline → `repaired_metrics.json` quay lại **1.0000 / 1.0000 / 1.0000 / 5.0000**. Điểm tôi muốn nhấn: hai file quality của baseline và repaired có **cùng kích thước 3.430 bytes** và chỉ khác nhau ở `report_name` và `generated_at` — đây là bằng chứng độc lập với metric, vì nó được tính thẳng trên dữ liệu chứ không qua LLM hay vector store.

Corruption nào ảnh hưởng rõ nhất và vì sao?

**`drop_latest_records` gây hại nhiều nhất cho agent (4/20 câu) nhưng lại là loại mà bộ check của tôi hoàn toàn không bắt được** — đây là kết luận quan trọng nhất tôi rút ra từ khối của mình. Lý do: check duy nhất liên quan tới số dòng là `row_count` với ngưỡng `MIN_ROWS = 10`, mà 23 dòng thì vẫn thoải mái vượt ngưỡng. Trong khi đó, mất 3 dòng đồng nghĩa rút hẳn document ra khỏi corpus: với q001–q004, top-4 trả về `10.55041/isjem07213` và `10.21203/rs.3.rs-9882260/v1` — agent trả lời tự tin bằng tài liệu của bài báo khác, hỏi tác giả bài SafeRAG thì nhận `"Dr. Sumalatha P, Manoj Kumar"` thay vì `"Qianwen Cao, Chiyu Zhang, Junxiong Ning, Gongru Li"`.

Freshness report thì bắt được *dấu vết gián tiếp* của việc này: `latest_published` lùi từ `2026-08-01` về `2026-07-03`, tức bài mới nhất đã biến mất. Nhưng đó chỉ là dấu vết, không phải cảnh báo — `is_fresh` vẫn sẽ là `true` nếu chỉ có mình `drop_latest_records` xảy ra, vì các dòng còn lại đều trong ngưỡng 180 ngày.

Kết quả nào khác với kỳ vọng ban đầu?

**Hai check FAIL của tôi hóa ra không có hệ quả đo được nào ở đầu ra, và một corruption gây hại thật thì không check nào bắt.** Cụ thể:

- `truncate_title` làm `title_min_length` FAIL trên 3 dòng, `duplicate_rows` làm `paper_id_unique` FAIL trên 2 dòng — nhưng **cả hai đều không làm dịch chuyển bất kỳ metric nào**. Với `truncate_title`, tôi đã kiểm tra bằng cách mở `corrupted_answers.json` lọc riêng q013–q016 (4 câu của paper bị cắt tiêu đề): cả 4 vẫn `retrieval_hit = true`, `token_f1 = 1.000`, judge 5/5. Nguyên nhân: `answer_question()` chạy song song `lookup()` và `search()`; tra cứu chính xác theo tiêu đề trượt nhưng semantic search vẫn xếp đúng bài lên hạng 1, vì `text_for_embedding` còn nguyên authors/categories/published/summary.
- Ngược lại, `inject_noise` không bị check nào bắt nhưng làm q012 trả về nguyên chuỗi rác với `token_f1 = 0.000` (chi tiết ở mục 6).

Nói cách khác: **2 trong 5 check FAIL không có hệ quả đo được, và 1 corruption gây hại thật thì 12/12 check im lặng.** Điều này ban đầu làm tôi nghĩ bộ check của mình kém hiệu quả, nhưng đọc kỹ thì kết luận đúng phải là: quan hệ giữa data quality và chất lượng agent **không phải một-một**, và hai lưới lọc này bổ sung cho nhau. `title_min_length` FAIL vẫn là thông tin đúng và có giá trị — tiêu đề cụt sẽ hiển thị sai cho người dùng dù metric không đổi. Cái sai là suy diễn: không được suy từ "check FAIL" ra "agent chắc chắn tệ đi", cũng không được suy từ "12/12 PASS" ra "dữ liệu chắc chắn ổn".

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về data pipeline: công cụ quan sát phải chịu được chính loại hỏng mà nó đi quan sát.** `run_data_quality_checks()` được gọi ba lần, và lần quan trọng nhất là lần chạy trên frame đã bị làm hỏng có 23 dòng thay vì 24. Nếu tôi viết theo lối "fail fast" thì một cột bị thiếu sẽ làm cả report chết và mất luôn thông tin về 11 check còn lại. Vì vậy `_missing_column_check()` báo FAIL kèm tên cột thay vì ném `KeyError`, và mọi phép so sánh đi qua `_numeric_series()`/`_text_series()` chịu được kiểu dữ liệu lẫn lộn. Đây là nguyên tắc tôi sẽ mang sang mọi hệ thống monitoring khác: thứ đo lường phải là thứ cuối cùng ngừng hoạt động.

2. **Về data quality/observability: pass/fail và số liệu liên tục trả lời hai câu hỏi khác nhau, và tôi cần cả hai.** 12 check trả lời "dữ liệu có đúng không" (corrupted: 7/12, 15 dòng lỗi) — đủ để chặn nhưng không đủ để chẩn đoán. Freshness report trả lời "dữ liệu mới/cũ ở mức nào" (`mean_age_days` 83.33 → 278.7, `max_age_days` 175 → 1256, `stale_ratio` 0 → 0.1739, kèm 4 `paper_id` cụ thể) — đủ để chẩn đoán nhưng không dùng làm cổng chặn được. Ví dụ rõ nhất: check chỉ nói "4 dòng quá hạn", còn report cho thấy `oldest_published` tụt từ 2026-02-12 về 2023-02-26 — từ đó mới đọc ra bản chất là **ngày bị đẩy lùi 3 năm**, chứ không phải corpus cũ dần theo thời gian. Hai kết luận đó dẫn tới hai hành động sửa hoàn toàn khác nhau.

3. **Về ảnh hưởng của data đến RAG agent: "12/12 PASS" chỉ có nghĩa là dữ liệu không vi phạm những thứ tôi nghĩ ra để kiểm tra.** `inject_noise` đi qua toàn bộ 12 check mà không kích hoạt một FAIL nào, rồi làm q012 trả về `"LOREM IPSUM DOLOR ###### CORRUPTED PAYLOAD @@@@@@."` cho người dùng. Không exception nào được ném ra trong suốt lần chạy corrupted — flow chạy hết 10/10 bước và trả về đủ 20/20 câu trả lời. Đây là lý do tôi không coi quality report là "bằng chứng dữ liệu tốt" mà chỉ là "bằng chứng dữ liệu không sai theo N cách đã biết", và là lý do bộ check phải được mở rộng chứ không được đóng băng.

### Nếu có thêm thời gian

**Cải thiện đề xuất: bổ sung nhóm check *nội dung* và một check *biến động số dòng*, để bịt đúng hai lỗ hổng đã đo được ở mục 8.**

Hai lỗ hổng không phải giả định mà là số đo: `inject_noise` (3 dòng, 1 câu hỏi hỏng) và `drop_latest_records` (3 dòng, 4 câu hỏi hỏng) đều đi qua bộ 12 check hiện tại mà không kích hoạt FAIL nào.

Cách làm — thêm 4 check, nâng bộ từ 12 lên 16:

1. `summary_noise_ratio` — tỷ lệ ký tự không phải chữ-số-khoảng trắng trong `summary` vượt ngưỡng.
2. `summary_repeated_block` — có đoạn văn bản lặp lại nhiều lần trong cùng một `summary`.
3. `summary_title_overlap` — độ tương đồng từ vựng giữa `summary` và `title` dưới ngưỡng.
4. `row_count_drift` — so `total_rows` với số dòng của lần chạy trước (đọc từ `baseline_quality.json`), FAIL nếu lệch quá 5%. Đây là check khác về bản chất với 12 check hiện tại: nó **có trạng thái**, so với lịch sử chứ không chỉ nhìn frame hiện tại.

Ngưỡng của 3 check đầu không đặt tùy tiện mà lấy từ phân bố thực tế của 24 abstract sạch: đo phân vị 95 trên baseline rồi cộng biên an toàn, để bảo đảm không có báo động giả.

**Cách đo cải thiện** (có tiêu chí đạt/không đạt rõ ràng, chạy lại được):

1. Chạy `python script/run_phase1.py` trên dữ liệu sạch. **Tiêu chí đạt:** `baseline_quality.json` có `total_checks = 16` và `passed_checks = 16` — tức 4 check mới **không** gây báo động giả trên dữ liệu tốt. Nếu bất kỳ check nào FAIL ở đây thì ngưỡng sai và phải chỉnh lại trước khi đi tiếp.
2. Chạy `python script/run_corruption_flow.py`. **Tiêu chí đạt cho lỗ hổng nội dung:** `corrupted_quality.json` có `summary_noise_ratio` trong `failed_check_names` với `failed_rows = 3`, khớp đúng số dòng mà `corruption_log.json` ghi cho bước `inject_noise`.
3. **Tiêu chí đạt cho lỗ hổng số dòng:** `row_count_drift` FAIL trên trạng thái corrupted (23 so với 24 là lệch 4.2%… — nếu ngưỡng 5% không bắt được thì phải hạ xuống 2%, và đây chính là phần cần đo lại chứ không đoán trước).
4. **Chỉ số theo dõi:** *tỷ lệ corruption bị bắt* — hiện tại là **4/6** (`blank_summary`, `truncate_title`, `stale_dates`, `duplicate_rows` bắt được; `inject_noise` và `drop_latest_records` bỏ lọt). Mục tiêu là 6/6. Đây là con số đếm trực tiếp được bằng cách đối chiếu `corruption_log.json` với `failed_check_names` trong `corrupted_quality.json`, không cần suy diễn.
5. **Chỉ số theo dõi thứ hai:** `total_failed_rows` trên trạng thái corrupted, hiện là **15**. Sau cải thiện, con số này phải tăng lên ít nhất 18 (thêm 3 dòng của `inject_noise`), và mọi dòng tăng thêm phải truy được về một bước cụ thể trong `corruption_log.json`.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [ ] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [ ] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [ ] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [ ] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [ ] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [ ] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Đặng Quang Minh
**Ngày xác nhận:** 2026-08-06
