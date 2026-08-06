# Member Role Report — Day 10: Data Pipeline & Data Observability

> Báo cáo vai trò cá nhân của **Dương Hải Long (2A202601607)** — Data model & evaluation-set owner của nhóm DingDong. Nội dung chỉ mô tả phần việc tôi trực tiếp thực hiện (khối 2 — cleaning và khối 3 — evaluation set), không sao chép báo cáo nhóm hay báo cáo của thành viên khác.

> **Lưu ý về provider LLM:** run đã nộp chạy với `provider=groq`, `model=openai/gpt-oss-20b` (xác minh tại `data/reports/phase1_report.md`, mục 1: `llm_provider | groq`, `llm_model | openai/gpt-oss-20b`). Test set do tôi sinh ra được chấm bởi LLM judge này; nếu nhóm chạy lại trên provider khác thì `judge_accuracy` và `mean_judge_score` sẽ đổi và phải cập nhật lại hai trường provider/model.

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Dương Hải Long |
| MSSV               | 2A202601607 |
| Khóa/Lớp         | K3 |
| Tên nhóm         | DingDong (4 thành viên) |
| Vai trò chính    | Data model & evaluation-set owner — khối 2 (cleaning) và khối 3 (test set) |
| Repository         | https://github.com/doandinhdong14-afk/K3_Day10_DingDong |
| Ngày hoàn thành | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

### Danh mục 7 khối deliverable của project

Khối được **in đậm** là khối tôi trực tiếp làm.

| # | Khối deliverable           | File nguồn phụ trách                                              | Artifact phải bàn giao                                                                                       |
| -: | -------------------------- | ------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| 1 | Raw ingestion              | `src/ingestion/crossref.py`                                       | `data/raw/crossref_response.json`, `crossref_records.json` (24 raw records)                                   |
| **2** | **Cleaning & data modeling** | **`src/ingestion/cleaning.py`**                               | **`data/clean/papers_clean.csv`, `papers_clean.json` (24 dòng × 16 cột, có `text_for_embedding`)**        |
| **3** | **Evaluation set**     | **`src/evaluation/testset.py`**                                   | **`data/eval/test_set.json` (20 câu hỏi / 5 paper / 4 loại câu hỏi)**                                   |
| 4 | Quality & freshness        | `src/observability/quality.py`                                    | `data/quality/*.json` (3 quality + 3 freshness report)                                                        |
| 5 | Reporting                  | `src/observability/reporting.py`                                  | `data/reports/phase1_report.md`, `corruption_report.md`, `answer_diff.md`                                   |
| 6 | Baseline orchestration     | `src/pipelines/phase1.py`, `src/retrieval/index.py`               | `data/results/baseline_metrics.json`, `baseline_answers.json`, `data/embeddings/`, `data/chroma/`           |
| 7 | Corruption & repair        | `src/ingestion/corruption.py`, `src/pipelines/corruption_flow.py` | `data/results/corruption_log.json`, `corrupted_metrics.json`, `repaired_metrics.json`                       |

Phân công của nhóm (cấu hình 4 người theo [`README.md`](README.md) mục 5):

| Họ và tên | MSSV | Vai trò | Khối sở hữu |
| ----------- | ------ | --------- | ------------- |
| Trần Hoài Nam | 2A202601751 | Source owner | Khối 1 — `crossref.py` |
| **Dương Hải Long** | **2A202601607** | **Data model & evaluation-set owner** | **Khối 2, 3 — `cleaning.py`, `testset.py`** |
| Đặng Quang Minh | 2A202601459 | Observability owner | Khối 4 — `quality.py` |
| Đoàn Đình Đông (leader) | 2A202601900 | Reporting, orchestration & corruption owner | Khối 5, 6, 7 + điều phối tích hợp |

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | ------------ |
| Dựng clean frame 16 cột | `build_clean_dataframe()`, `_parse_date()` | 24 `PaperRecord` (11 trường) từ khối 1 + `run_date` | `data/clean/papers_clean.csv` (103.200 B, 24 dòng × 16 cột), `papers_clean.json` (111.916 B) | Hoàn thành |
| Dựng cột `text_for_embedding` | `_build_embedding_text()` | 5 trường đã chuẩn hóa của mỗi dòng | Cột duy nhất được embed ở bước index | Hoàn thành |
| Khử trùng hai lượt + sắp xếp ổn định | `build_clean_dataframe()` (`drop_duplicates(subset="paper_id")`, khử theo title viết thường, `sort_values(["published","paper_id"], ascending=[False,True])`) | 24 dòng thô | Baseline `paper_id_unique` PASS 24/24 | Hoàn thành |
| Sinh evaluation set 20 câu | `build_test_set()`, `_question_specs()` | Clean frame 24 dòng | `data/eval/test_set.json` (8.509 B, 20 sample `q001`–`q020`) | Hoàn thành |
| Chọn paper trải đều + lọc paper phá router | `_select_papers()`, `_is_usable()`, hằng `ROUTING_PHRASES` | Clean frame | 5 paper: `10.2118/234689-pa`, `10.3390/buildings16132637`, `10.21203/rs.3.rs-10012178/v1`, `10.22214/ijraset.2026.82233`, `10.1093/sleep/zsag091.0346` | Hoàn thành |

Chỉ nhận ownership cho phần tôi trực tiếp thực hiện. Tôi **không** viết `crossref.py`, `quality.py`, `reporting.py`, `phase1.py`, `index.py`, `corruption.py` hay `corruption_flow.py`.

Thứ tự phụ thuộc thực tế giữa các khối — khối của tôi nằm giữa và **là nút thắt**: mọi khối phía sau đều đọc frame sạch hoặc test set của tôi.

```text
Khối 1 raw ingestion
   -> Khối 2 cleaning        <-- phần việc của tôi (đọc data/raw/crossref_records.json)
   -> Khối 3 test set        <-- phần việc của tôi (đọc clean frame)
      + Khối 6 index/baseline (embed cột text_for_embedding của tôi)
   -> Khối 4 quality/freshness (12 check chạy trên các cột do tôi định nghĩa)
      + Khối 5 reporting
   -> Khối 7 corruption/repair (corruption kiểm tra 11 cột bắt buộc của tôi rồi mới làm hỏng;
      repair chạy LẠI build_clean_dataframe() của tôi)
```

Một hệ quả tôi phải chịu trách nhiệm: `build_clean_dataframe()` được gọi **hai lần** — một lần ở pha 1 để dựng baseline, một lần ở bước 7 của pha 2 để repair. Hàm này vì vậy phải hoàn toàn tất định: cùng input phải cho ra cùng output tới từng byte. Bằng chứng là `papers_clean_repaired.csv` trùng khít 103.200 B với `papers_clean.csv`.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| ------------ | -------------------------------- | ---------- |
| Chốt danh sách 11 cột bắt buộc mà bước corruption phải kiểm tra trước khi làm hỏng | Đoàn Đình Đông — `corruption._require_columns()` | `REQUIRED_COLUMNS` trong `corruption.py` khớp đúng schema của tôi; corruption raise `ValueError` liệt kê cột thiếu thay vì ném `KeyError` giữa chừng |
| Giải thích vì sao `summary_chars`/`title_chars` phải được tính lại từ text chứ không nhận từ ngoài | Đặng Quang Minh — `quality._char_count_consistency_check()` | Hai check `title_chars_consistent` và `summary_chars_consistent` mới có ý nghĩa; chúng bắt được trường hợp text bị sửa ngầm mà cột đếm không đổi |
| Báo lại cho tầng nguồn rằng `categories_joined` rỗng sẽ làm `_is_usable()` loại sạch mọi paper | Trần Hoài Nam — `crossref._format_categories()` | Sau khi có nhánh fallback: 24/24 paper `usable`, 0 paper bị loại; `build_test_set()` sinh đủ 20 câu |
| Kiểm tra `text_for_embedding` được dựng lại đúng khuôn sau khi corrupt | Đoàn Đình Đông — bước `rebuild_embedding_text` trong `corrupt_clean_dataframe()` | Bước này dùng lại đúng khuôn 5 dòng của `_build_embedding_text()`, nên index corrupted thực sự embed phần text đã hỏng chứ không phải text cũ |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------------- | ----------------------------- | ------------------- | --------------- |
| Chuẩn hóa khoảng trắng và ép ngưỡng độ dài | `build_clean_dataframe()` với `MIN_TITLE_CHARS = 10`, `MIN_SUMMARY_CHARS = 80` | 24/24 raw record đi qua, 0 dòng bị loại; `title_chars` nhỏ nhất **92**, `summary_chars` nhỏ nhất **826** | `python script/run_phase1.py` (bước 3–4/10); đọc `data/clean/papers_clean.csv` |
| Ghép `authors`/`categories` thành chuỗi | `compact_join()` → `authors_joined`, `categories_joined` | 0/24 dòng `authors_joined` rỗng, 0/24 dòng `categories_joined` rỗng | Đếm trực tiếp trên `papers_clean.csv` |
| Giữ `published`/`updated` ở kiểu chuỗi `YYYY-MM-DD` | `published.date().isoformat()` thay vì giữ `pd.Timestamp` | Check `published_format_valid` PASS 24/24 | `data/quality/baseline_quality.json` |
| Tính 4 cột dẫn xuất | `age_days`, `author_count`, `title_chars`, `summary_chars` | `age_days` từ 5 đến 175 ngày, `mean_age_days = 83.33` | `data/quality/freshness_report.json` |
| Dựng `text_for_embedding` theo khuôn cố định 5 dòng | `_build_embedding_text()` | Check `text_for_embedding_present` PASS 24/24 | `data/quality/baseline_quality.json` |
| Khử trùng hai lượt độc lập | theo `paper_id`, rồi theo `title` viết thường | 24 dòng vào → 24 dòng ra; `paper_id_unique` PASS | `papers_clean.csv` + `baseline_quality.json` |
| Sắp xếp ổn định để pipeline tất định | `sort_values(["published","paper_id"], ascending=[False,True])` | Dòng đầu `2026-08-01`, dòng cuối `2026-02-12` | Mở `papers_clean.csv` đọc cột `published` |
| Sinh 20 câu hỏi trên 5 paper × 4 loại | `build_test_set()`, `_question_specs()` | `data/eval/test_set.json` — `q001`–`q020`, mỗi sample có `ground_truth` và đúng 1 `ground_truth_doc_ids` | `python script/run_phase1.py` (bước 6/10); ép tạo lại bằng `REFRESH_TEST_SET=1` |
| Chọn paper trải đều thay vì lấy 5 dòng đầu | `_select_papers()` — `step = len(usable) // 5 = 4`, `usable.iloc[::4].head(5)` | 5 paper ở vị trí 0, 4, 8, 12, 16 của frame | So `test_set.json` với thứ tự dòng trong `papers_clean.csv` |

### Lệnh xác minh thật của từng khối

| Khối | Lệnh chạy | Artifact phải mở để đối chiếu | Dấu hiệu đạt |
| ---- | ----------- | -------------------------------- | -------------- |
| Tiền đề cho mọi khối gọi LLM | `python script/check_llm.py` | stdout của script | 3 dòng `[OK  ]` cho *chat bình thường*, *structured output*, *tool calling*, kết thúc bằng `KET LUAN: provider san sang` |
| 1. Raw ingestion | `python script/run_phase1.py` (bước 2/10) | `data/raw/crossref_records.json` | 24 record, mỗi record đủ `paper_id/title/summary/authors/published` |
| **2. Cleaning (của tôi)** | `python script/run_phase1.py` (bước 3–4/10) | `data/clean/papers_clean.csv` | 24 dòng, 16 cột, cột `text_for_embedding` không rỗng |
| **3. Evaluation set (của tôi)** | `python script/run_phase1.py` (bước 6/10); ép tạo lại bằng `REFRESH_TEST_SET=1` | `data/eval/test_set.json` | 20 sample, 4 `question_type`, mỗi sample có đúng 1 `ground_truth_doc_ids` |
| 4. Quality & freshness | `python script/run_phase1.py` (bước 8/10) và `python script/run_corruption_flow.py` (bước 6, 8/10) | `data/quality/*.json` | baseline 12/12 pass, corrupted 7/12 pass, repaired 12/12 pass |
| 5. Reporting | `python script/run_phase1.py` (bước 9/10), `python script/run_corruption_flow.py` (bước 9/10) | `data/reports/*.md` | bảng so sánh khớp với các file `*_metrics.json` |
| 6. Baseline orchestration | `python script/run_phase1.py` | `data/results/baseline_metrics.json` | `1.0 / 1.0 / 1.0 / 5`; mọi dòng artifact là `[OK]` |
| 7. Corruption & repair | `python script/run_corruption_flow.py` | `data/results/corruption_log.json` | 7 step, `source_rows=24`, `result_rows=23`, `deterministic=true` |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

**`data/eval/test_set.json` (8.509 bytes, 20 sample)** là artifact có ảnh hưởng lớn nhất trong phần việc của tôi, vì nó là **thước đo dùng chung cho cả ba trạng thái**. File gồm 20 sample `q001`–`q020`, mỗi sample có `id`, `question_type`, `question`, `ground_truth` và `ground_truth_doc_ids` (đúng một `paper_id`). Cấu trúc là 5 paper × 4 loại câu hỏi: `q001`–`q004` cho `10.2118/234689-pa`, `q005`–`q008` cho `10.3390/buildings16132637`, `q009`–`q012` cho `10.21203/rs.3.rs-10012178/v1`, `q013`–`q016` cho `10.22214/ijraset.2026.82233`, `q017`–`q020` cho `10.1093/sleep/zsag091.0346`. Điểm quan trọng: `ground_truth` được lấy **từ frame sạch tại thời điểm sinh**, rồi file được đóng băng — `phase1._load_or_build_test_set()` chỉ tạo lại khi bật `REFRESH_TEST_SET`, còn `corruption_flow` truyền thẳng đường dẫn này cho cả hai lần đánh giá của nó. Nhờ vậy chênh lệch `1.0000 → 0.6684 → 1.0000` của `mean_token_f1` chỉ có thể do dữ liệu, không do phép đo. Ngoài ra, cách tôi chọn 5 paper bằng `iloc[::4]` chính là căn cứ để leader canh offset corruption ở khối 7 — nếu tôi lấy 5 dòng đầu thay vì trải đều thì bước `drop_latest_records` (xóa 3 dòng đầu) sẽ xóa mất 3/5 paper được chấm và phép đo mất hết độ phân giải.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Khối của tôi phải giải hai bài toán tách biệt nhưng dính chặt vào nhau:

1. **Data modeling:** biến 24 `PaperRecord` thô thành một bảng mà ba nơi khác nhau dùng được cùng lúc — ChromaDB (chỉ nhận metadata kiểu nguyên thủy), bộ 12 quality check (cần các cột đếm để so sánh), và bước corruption (cần đúng 11 cột bắt buộc). Một quyết định sai về schema sẽ làm gãy ít nhất một trong ba.
2. **Evaluation set:** sinh câu hỏi có ground truth **đáng tin**, trên một tập paper được chọn sao cho phép đo còn ý nghĩa sau khi dữ liệu bị làm hỏng. Nếu ground truth sai thì cả bài lab sụp, vì mọi kết luận về nhân quả đều dựa trên nó.

### Cách triển khai

```text
24 PaperRecord (11 trường)
  -> build_clean_dataframe(records, run_date)
       . normalize_whitespace(title), normalize_whitespace(summary)
       . _parse_date(published)                     -> loại dòng nếu parse thất bại
       . lọc len(title) < 10 hoặc len(summary) < 80 -> loại dòng
       . compact_join(authors)    -> authors_joined       (list -> str)
       . compact_join(categories) -> categories_joined    (list -> str)
       . published.date().isoformat() -> str YYYY-MM-DD   (KHÔNG giữ Timestamp)
       . age_days = run_date - published (đơn vị ngày)
       . author_count, title_chars = len(title), summary_chars = len(summary)
       . _build_embedding_text(row) -> text_for_embedding
       . drop_duplicates(subset="paper_id", keep="first")     (lượt khử trùng 1)
       . loại title trùng khi viết thường (keep="first")      (lượt khử trùng 2)
       . sort_values(["published","paper_id"], [False, True])
  -> DataFrame 24 dòng x 16 cột -> papers_clean.{csv,json}
  -> build_test_set(df, output_path)
       . _is_usable(row)     : loại paper có dấu nháy đơn trong title,
                               loại paper chứa sẵn ROUTING_PHRASES,
                               yêu cầu authors_joined/categories_joined/summary khác rỗng
       . _select_papers()    : step = len(usable)//5 = 4 -> usable.iloc[::4].head(5)
       . _question_specs()   : 4 câu/paper (authors, date, categories, summary)
  -> 20 sample -> data/eval/test_set.json
```

Bốn quyết định trong code của tôi mà tôi thấy đáng nói:

1. **`published`/`updated` giữ nguyên kiểu chuỗi.** Tôi ghi `published.date().isoformat()` chứ không giữ `pd.Timestamp`, vì metadata của ChromaDB chỉ nhận `str/int/float/bool`. Cùng lý do đó, `authors` và `categories` (vốn là list) được ghép sẵn thành `authors_joined`/`categories_joined`. Ràng buộc này lan cả sang khối 7: `corruption._shift_year_back()` cũng phải luôn trả về string.
2. **`title_chars` và `summary_chars` luôn được tính lại từ chính text.** Tôi không nhận hai giá trị này từ đâu khác. Nhờ vậy hai check `title_chars_consistent` / `summary_chars_consistent` của khối 4 mới có ý nghĩa — chúng phát hiện trường hợp text bị sửa mà cột đếm không đổi.
3. **Khử trùng hai lượt độc lập.** Lượt một theo `paper_id` bắt DOI trùng; lượt hai theo `title` viết thường bắt trường hợp cùng một bài được đăng dưới hai DOI khác nhau (preprint và bản chính thức). Chỉ khử theo `paper_id` là chưa đủ.
4. **Câu hỏi phải viết đúng theo keyword router của `qa.py`.** `_extract_answer()` định tuyến bằng các cụm "who authored" → `authors_joined`, "when was" → `published`, "what categories" → `categories_joined`, còn lại → `first_sentence(summary)`. Vì vậy `_question_specs()` sinh câu hỏi bằng đúng các cụm đó, bọc tiêu đề trong dấu nháy đơn để regex `r"'([^']+)'"` của `answer_question()` bắt được, và `_is_usable()` loại các paper có tiêu đề chứa dấu nháy đơn hoặc chứa sẵn cụm routing.

### Input, output và contract

| Thành phần | Mô tả |
| ------------ | ------- |
| Input | **Khối 2:** `data/raw/crossref_records.json` — 24 `PaperRecord` (11 trường: `paper_id`, `title`, `summary`, `authors`, `categories`, `primary_category`, `published`, `updated`, `abs_url`, `pdf_url`, `comment`) cộng `run_date` (thời điểm chạy theo UTC). **Khối 3:** clean frame 24 dòng do chính khối 2 sinh ra |
| Output | **Khối 2:** `data/clean/papers_clean.csv` (103.200 B) và `papers_clean.json` (111.916 B) — 24 dòng × 16 cột: 11 trường gốc (đã gộp `authors`/`categories` thành `authors_joined`/`categories_joined`) cộng `age_days`, `author_count`, `title_chars`, `summary_chars`, `text_for_embedding`. **Khối 3:** `data/eval/test_set.json` (8.509 B, 20 sample) |
| Module phụ thuộc | `src/core/utils.py` (`normalize_whitespace`, `compact_join`, `first_sentence`, `write_json`), `src/ingestion/crossref.py` (kiểu `PaperRecord`), `pandas` |
| Module sử dụng output | `src/retrieval/index.py` (embed cột `text_for_embedding`, đọc metadata), `src/evaluation/metrics.py` (chấm trên `ground_truth` của tôi), `src/observability/quality.py` (12 check trên các cột của tôi), `src/ingestion/corruption.py` (kiểm 11 cột bắt buộc rồi mới làm hỏng), `src/pipelines/phase1.py` và `corruption_flow.py` |
| Điều kiện lỗi cần xử lý | Xem bảng bên dưới |

Các điều kiện lỗi **thực sự** được xử lý trong hai file của tôi:

| Điều kiện lỗi | Vị trí xử lý | Cách xử lý |
| --------------- | -------------- | ------------ |
| Không có raw record nào | `build_clean_dataframe()` | `raise ValueError("Khong co raw record nao de lam sach.")` ngay đầu hàm |
| Ngày không parse được | `_parse_date()` (`pd.to_datetime(errors="coerce")`) | Trả `None` → dòng bị loại, thay vì để `NaT` lọt xuống và làm hỏng `age_days` |
| Thiếu `paper_id`, `title` hoặc `summary` | `build_clean_dataframe()` | Bỏ dòng |
| Title < 10 hoặc summary < 80 ký tự | `build_clean_dataframe()` (kiểm tra lại lần hai sau `crossref.py`) | Bỏ dòng. Đo thực tế 0/24 dòng vi phạm — `title_chars` nhỏ nhất 92, `summary_chars` nhỏ nhất 826 |
| Tất cả record bị loại | `build_clean_dataframe()` | `raise ValueError("Tat ca record deu bi loai sau khi lam sach. Kiem tra lai buoc ingestion.")` — chỉ đích danh khối 1 thay vì trả về frame rỗng |
| ChromaDB không nhận list / `Timestamp` | `build_clean_dataframe()` | `compact_join()` cho `authors`/`categories`; `.date().isoformat()` cho `published`/`updated` |
| `primary_category` rỗng | `build_clean_dataframe()` | Lấy `categories[0]`, cuối cùng mới đến `"uncategorized"` |
| `updated` thiếu hoặc hỏng | `build_clean_dataframe()` | `_parse_date(record.updated) or published` — gán bằng `published` |
| Frame ít hơn 5 document | `build_test_set()` (`MIN_DOCUMENTS = 5`) | `raise ValueError` nêu rõ số document hiện có |
| Không paper nào đủ điều kiện sinh câu hỏi | `_select_papers()` | `raise ValueError("Khong co paper nao du dieu kien de tao cau hoi.")` thay vì ghi ra test set rỗng |
| Tiêu đề chứa dấu nháy đơn hoặc chứa cụm routing | `_is_usable()` | Loại paper đó khỏi tập ứng viên. Đo thực tế: 0 paper bị loại, 24/24 usable |
| Số paper usable nhỏ hơn số cần lấy | `_select_papers()` — `step = max(1, len(usable) // count)` | `max(1, ...)` chặn `step = 0` gây lỗi slice |

### Cách xác minh

```bash
python script/run_phase1.py                        # bước 3-4/10 sinh clean artifacts, bước 6/10 sinh test set
REFRESH_TEST_SET=1 python script/run_phase1.py     # ép sinh lại test set từ đầu
python script/run_corruption_flow.py               # bước 7 gọi lại build_clean_dataframe() của tôi để repair
```

- **Kết quả mong đợi:** bước 3–4/10 sinh `papers_clean.csv` 24 dòng × 16 cột; bước 6/10 sinh `test_set.json` 20 sample; bước 7 của pha 2 dựng lại frame giống hệt baseline.
- **Kết quả thực tế:** đúng như mong đợi. `papers_clean.csv` = 103.200 B / 24 dòng / 16 cột, `test_set.json` = 8.509 B / 20 sample / 4 `question_type` / 5 paper. `papers_clean_repaired.csv` trùng khít **từng byte** với `papers_clean.csv` (cùng 103.200 B, cùng MD5 `8fd54f38e963a48ab8881b4a8dfe3854`) — bằng chứng `build_clean_dataframe()` hoàn toàn tất định.
- **Artifact/log:** `data/clean/papers_clean.{csv,json}`, `data/clean/papers_clean_repaired.{csv,json}`, `data/eval/test_set.json`. Không file nào chứa API key; `.env` nằm trong `.gitignore`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** cột `text_for_embedding` là **văn bản duy nhất** được `LocalEmbeddingIndex.build()` đưa qua `all-MiniLM-L6-v2`. Mọi thứ không nằm trong cột này thì không tồn tại đối với semantic search. Trong khi đó test set có 3/4 loại câu hỏi là câu hỏi *metadata*: "who authored…", "when was… published", "what categories…" — chỉ 1/4 là câu hỏi về nội dung (summary).

- **Các phương án đã cân nhắc:**
  - **Phương án A — chỉ embed `summary`:** đây là cách làm quen thuộc trong RAG, vì abstract mới là "nội dung" thật của bài báo, còn tác giả/ngày/chủ đề là metadata nên để bộ lọc metadata của vector store xử lý. Ưu điểm: vector thuần ngữ nghĩa, không bị loãng bởi tên riêng và con số; tìm kiếm theo chủ đề chính xác hơn. Nhược điểm: 15/20 câu hỏi trong test set không có tín hiệu từ vựng nào trong vector — hỏi "who authored 'SafeRAG…'" mà vector chỉ chứa abstract thì việc xếp đúng bài lên hạng 1 gần như chỉ trông vào phần tiêu đề tình cờ lặp lại trong abstract.
  - **Phương án B — ghép 5 trường theo khuôn cố định:** `Title: … \n Authors: … \n Categories: … \n Published: … \n Summary: …`, trường rỗng thì ghi `unknown` / `uncategorized` để không tạo dòng cụt.

- **Phương án đã chọn:** Phương án B.

- **Lý do:** test set của bài lab này kiểm tra khả năng truy hồi *bản ghi đúng* để trả lời câu hỏi metadata, chứ không kiểm tra khả năng tìm bài theo chủ đề. Với A thì 15/20 câu hỏi bị thiệt một cách có hệ thống, và phần sụt đó sẽ bị hiểu nhầm thành "chất lượng dữ liệu kém" trong khi thật ra là do thiết kế embedding. Đổi lại, B có một tác dụng phụ mà tôi phải chấp nhận và ghi rõ: vì tiêu đề chỉ chiếm khoảng 1/5 nội dung vector, **một corruption chỉ chạm vào một trường sẽ không đủ làm lệch vector của cả document**. Ban đầu tôi coi đây thuần túy là nhược điểm; sau khi đọc kết quả pha 2 thì thấy nó vừa là nhược điểm vừa là bằng chứng cho tính bền của thiết kế (xem phân tích `truncate_title` ở mục 8).

- **Bằng chứng quyết định phù hợp:** đối chiếu `data/results/baseline_answers.json` với `corrupted_answers.json` trên 4 câu của paper bị cắt tiêu đề (`10.22214/ijraset.2026.82233`, title còn `"Hybrid G"`):

  | Câu hỏi | Loại | Baseline | Corrupted |
  | --------- | ------ | ---------: | ----------: |
  | q013 | authors | `token_f1 = 1.000`, hit | `token_f1 = 1.000`, hit |
  | q014 | date | `token_f1 = 1.000`, hit | `token_f1 = 1.000`, hit |
  | q015 | categories | `token_f1 = 1.000`, hit | `token_f1 = 1.000`, hit |
  | q016 | summary | `token_f1 = 1.000`, hit | `token_f1 = 1.000`, hit |

  Cả 4 câu vẫn `retrieval_hit = true` dù tra cứu chính xác theo tiêu đề đã trượt hoàn toàn — semantic search vẫn xếp đúng bài lên hạng 1 nhờ 4 thành phần còn lại của `text_for_embedding`. Với phương án A, mất tiêu đề đồng nghĩa mất luôn tín hiệu duy nhất nối câu hỏi với document, và nhiều khả năng cả 4 câu này đã hỏng.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** test set sinh ra bình thường, không có exception nào, nhưng khi chấm thì các câu hỏi rơi nhầm nhánh của router: câu hỏi loại `authors` lại nhận về câu đầu tiên của abstract thay vì danh sách tác giả, nên `token_f1` gần 0 dù `retrieval_hit = true`. Không có thông báo lỗi nào — đây là loại hỏng **im lặng**, chỉ lộ ra khi đọc từng dòng trong `baseline_answers.json`.

  Chuỗi định danh nằm ngay trong code của tôi, ghi nguyên văn từ `src/evaluation/testset.py`:

  ```python
  # Ham QA co san (retrieval/qa.py) dinh tuyen cau tra loi bang cac cum tu nay.
  # Neu tieu de bai bao vo tinh chua chung, cau hoi se bi hieu sai -> loai bai do ra.
  ROUTING_PHRASES = (
      "who authored", "list the authors", "when was",
      "publication date", "published on", "what categories",
  )
  ```

- **Lệnh hoặc bước tái hiện:**

  ```bash
  # Khi _question_specs() còn diễn đạt câu hỏi tự do (ví dụ "Which researchers wrote ...?")
  REFRESH_TEST_SET=1 python script/run_phase1.py
  # Mở data/results/baseline_answers.json và lọc các sample có question_type = "authors"
  ```

- **Nguyên nhân gốc:** lớp trả lời trong `src/retrieval/qa.py` **không phải reader sinh ngôn ngữ** mà là một keyword router: `_extract_answer()` so cụm từ trong câu hỏi rồi trả thẳng một trường metadata — "who authored"/"list the authors" → `authors_joined`, "when was"/"publication date"/"published on" → `published`, "what categories" → `categories_joined`, còn lại rơi vào nhánh mặc định `first_sentence(summary)`. Ngoài ra `answer_question()` dùng regex `r"'([^']+)'"` để bắt tiêu đề trong dấu nháy đơn rồi gọi `index.lookup()` tra cứu chính xác. Nghĩa là **câu chữ của test set là một phần của hợp đồng kỹ thuật**, không phải chuyện văn phong. Tôi đã viết câu hỏi theo cách tự nhiên nhất với người đọc, và đó chính là lỗi.

  Có một hệ quả thứ hai tinh vi hơn: nếu *tiêu đề bài báo* vô tình chứa một cụm routing, thì câu hỏi summary của bài đó sẽ bị router hiểu thành câu hỏi ngày tháng. Và nếu tiêu đề chứa dấu nháy đơn thì regex `'([^']+)'` cắt sai, khiến `lookup()` tra nhầm.

- **Cách xử lý:** hai thay đổi trong `testset.py`, cả hai đều nằm trong khối của tôi chứ không sửa `qa.py` của người khác:

  1. `_question_specs()` sinh câu hỏi bằng **đúng** các cụm mà router nhận, và bọc tiêu đề trong dấu nháy đơn: `f"Who authored the paper '{title}'?"`, `f"When was the paper '{title}' published?"`, `f"What categories are assigned to the paper '{title}'?"`, `f"Give a one sentence summary of the paper '{title}'."`
  2. `_is_usable()` loại trước những paper sẽ phá router: có dấu nháy đơn trong tiêu đề, hoặc tiêu đề chứa sẵn một cụm trong `ROUTING_PHRASES`.

- **Cách xác minh sau khi sửa:**

  ```bash
  REFRESH_TEST_SET=1 python script/run_phase1.py
  ```

  `data/eval/test_set.json` sinh đủ 20 sample với 4 `question_type` đều 5 câu. Trong `data/results/baseline_metrics.json`: `mean_token_f1 = 1.0000` trên cả 20 câu (F1 nhỏ nhất của từng câu cũng là 1.0000), `retrieval_hit_rate = 1.0000`. Đo thêm trên dataset này: **0 paper bị `_is_usable()` loại, 24/24 usable** — tức bộ lọc chưa phải cắt bài nào, nhưng nó vẫn cần thiết vì corpus đổi mỗi lần refresh.

- **Điều học được:** ground truth chỉ đáng tin khi **câu hỏi được viết theo đúng cơ chế mà hệ thống dùng để trả lời**. Bài học rộng hơn: một evaluation set sai không làm pipeline gãy — nó làm pipeline *báo sai*, và điều đó nguy hiểm hơn nhiều so với một exception. Tôi cũng học được rằng khi phát hiện coupling giữa hai module, nên sửa ở phía mình sở hữu và ghi rõ ràng buộc ra, thay vì đi sửa module của người khác cho "tiện".

Phần cần ghi rõ giới hạn còn lại:

- **Phạm vi bị ảnh hưởng:** ràng buộc này là **ngầm** — nó chỉ được ghi bằng comment trong `testset.py`, không có test tự động nào bảo vệ. Ai đó đổi cách diễn đạt câu hỏi mà không đọc comment sẽ tái tạo lại đúng lỗi này, và metric sẽ tụt mà không có lỗi dữ liệu nào.
- **Những gì đã loại trừ:** không phải lỗi embedding (`retrieval_hit` vẫn true trong khi `token_f1` gần 0, chứng tỏ tìm đúng bài nhưng trả sai trường); không phải lỗi ground truth (đối chiếu tay với `papers_clean.csv` thấy khớp); không phải lỗi LLM judge (judge chấm đúng rằng câu trả lời sai).
- **Bước tiếp theo:** thêm một assert trong `build_test_set()` kiểm tra mỗi `question` sinh ra có chứa ít nhất một cụm trong `ROUTING_PHRASES` (trừ loại `summary`), để ràng buộc này gãy ngay lúc sinh test set chứ không gãy âm thầm ở lúc chấm.

## 7. Hiểu biết về luồng end-to-end

**1. Từ Crossref đến vector index.** `fetch_source_records()` gọi Crossref với query agentic RAG/LLM và filter `from-pub-date:2026-02-07,has-abstract:true`, xin dư 72 dòng rồi lọc còn 24 record ghi vào `data/raw/crossref_records.json`. Từ đó là phần của tôi: `build_clean_dataframe()` chuẩn hóa khoảng trắng, ép ngưỡng độ dài, ghép list thành chuỗi, tính 4 cột dẫn xuất, khử trùng hai lượt, sắp xếp `published` giảm dần và dựng cột `text_for_embedding`. Kết quả là frame 24 dòng × 16 cột. `LocalEmbeddingIndex.build()` sau đó cho `all-MiniLM-L6-v2` mã hóa **đúng cột `text_for_embedding`** rồi `add()` vào ChromaDB (`PersistentClient` tại `data/chroma/`, khoảng cách cosine), kèm metadata gồm `paper_id`, `title`, `published`, `authors_joined`, `categories_joined`, `summary`, `abs_url`, `pdf_url` — toàn bộ đều là cột do tôi định nghĩa. Ba trạng thái dùng ba collection riêng: `papers-baseline`, `papers-corrupted`, `papers-repaired`.

**2. Test set và ground-truth document IDs.** Đây là phần tôi làm. `build_test_set()` chọn 5 paper trải đều bằng `usable.iloc[::4].head(5)` — trải đều chứ không lấy 5 dòng đầu, vì frame được sắp mới nhất trước nên 5 dòng đầu sẽ nằm gọn trong vùng mà `drop_latest_records` xóa. Mỗi paper sinh 4 câu qua `_question_specs()`, thành 20 sample. `ground_truth` lấy trực tiếp từ chính dòng frame sạch: `authors_joined` cho câu authors, `published` cho câu date, `categories_joined` cho câu categories, `first_sentence(summary)` cho câu summary — tức ground truth và giá trị mà router trả về là **cùng một trường**, nên baseline đạt 1.0 là do thiết kế chứ không phải do mô hình giỏi. `ground_truth_doc_ids` chứa đúng một `paper_id`. Khi chấm, `evaluate_pipeline()` lấy `top_k = 4` rồi tính `retrieval_hit` (document đúng có nằm trong top-4 không) tách biệt với `token_f1` và LLM judge (nội dung câu trả lời đúng không). Tách đôi như vậy mới phân biệt được "lấy nhầm tài liệu" với "lấy đúng tài liệu nhưng nội dung tài liệu đã hỏng".

**3. Quality checks khác freshness monitoring.** `run_data_quality_checks()` chạy 12 check trên 5 chiều — completeness, uniqueness, validity, consistency, freshness — trả lời "dữ liệu có *đúng* không" bằng pass/fail theo dòng. Đáng chú ý với tôi: nhiều check chạy trên các cột dẫn xuất mà tôi tính (`title_chars`, `summary_chars`, `age_days`, `text_for_embedding`), và 2 check consistency tồn tại chỉ vì tôi tính lại cột đếm từ text thay vì nhận từ ngoài. `build_freshness_report()` thì trả lời "dữ liệu có *mới* không" bằng các đại lượng liên tục: `latest_published`, `oldest_published`, `stale_rows`, `stale_ratio`, `max/min/mean_age_days`, `is_fresh` — tất cả đều suy ra từ cột `age_days` của tôi. Hai thứ giao nhau ở đúng một điểm: check `freshness_within_threshold` (`age_days > 180`) là ảnh chụp nhị phân của cùng tín hiệu mà freshness report mô tả chi tiết.

**4. Vì sao phải dùng cùng test set cho cả ba trạng thái.** Đây là điểm sống còn của khối 3. `ground_truth` được sinh **từ dữ liệu sạch tại thời điểm sinh**. Nếu sinh lại test set từ frame corrupted thì: câu hỏi summary của paper bị `blank_summary` sẽ có ground truth là chuỗi rỗng; câu hỏi date của paper bị `stale_dates` sẽ lấy đúng ngày đã bị đẩy lùi 3 năm làm "đáp án đúng"; paper bị `drop_latest_records` xóa thì không còn câu hỏi nào. Agent trả về rác mà vẫn được chấm 5/5 — metric *đẹp lên* trên dữ liệu hỏng. Trong code, `phase1._load_or_build_test_set()` cố tình đọc lại `data/eval/test_set.json` nếu đã tồn tại và chỉ tạo mới khi bật `REFRESH_TEST_SET`; `corruption_flow` truyền thẳng `settings.paths.eval_testset` cho cả hai lần đánh giá của nó và nạp lại `baseline_metrics.json` thay vì chấm lại baseline. Nhờ vậy cả ba trạng thái là **20 sample giống hệt**.

**5. Repair thành công dựa trên artifact và metric nào.** Repair không vá frame hỏng mà **dựng lại từ snapshot nguồn**: `corruption_flow` bước 7 gọi `load_raw_records(data/raw/crossref_records.json)` rồi chạy lại **chính `build_clean_dataframe()` của tôi** — cùng đường đi mà baseline đã dùng. Kết luận thành công dựa trên ba nhóm bằng chứng độc lập: **số dòng** (`papers_clean_repaired.csv` 24 dòng, trùng khít từng byte và cùng MD5 với `papers_clean.csv` — bằng chứng trực tiếp nhất cho việc hàm của tôi tất định); **tín hiệu dữ liệu** (`repaired_quality.json` 12/12 pass, `total_failed_rows = 0`; `freshness_report_repaired.json` `is_fresh = true`, `stale_rows = 0`, `mean_age_days = 83.33`); và **metric của agent** (`repaired_metrics.json` cho 1.0 / 1.0 / 1.0 / 5 trên đúng 20 sample cũ). Ba nhóm phải cùng phục hồi mới kết luận được.

## 8. Phân tích kết quả

### Metrics chính

Số liệu đọc trực tiếp từ `data/results/*.json` và `data/quality/*.json` của lần chạy nộp bài.

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------- | -------: | --------: | -------: | ---------------------- |
| `retrieval_hit_rate` | 1.0000 | 0.8000 | 1.0000 | Giảm đúng 0.2000 = 4/20 câu. Vì test set của tôi là 5 paper × 4 câu, mất một paper là mất trọn 4 câu — đây là hệ quả trực tiếp của cách tôi cấu trúc test set |
| `mean_token_f1` | 1.0000 | 0.6684 | 1.0000 | Giảm 0.3316. Tách theo **loại câu hỏi tôi thiết kế**: summary 0.4190, date 0.6000, authors 0.8000, categories 0.8545. Loại `summary` chịu thiệt nặng nhất vì bị cả `blank_summary` lẫn `inject_noise` đánh vào |
| `judge_accuracy` | 1.0000 | 0.6500 | 1.0000 | 7/20 câu bị chấm sai: q001–q004 (mất paper), q008 (summary rỗng), q012 (summary rác), q018 (ngày sai) |
| `mean_judge_score` | 5.0000 | 3.6000 | 5.0000 | Theo loại câu hỏi: summary 2.60, date 3.40, authors 4.20, categories 4.20. 13 câu giữ 5/5, 7 câu còn lại đều 1/5 |
| Quality checks | 12/12 | 7/12 | 12/12 | 5 check FAIL trên corrupted: `paper_id_unique` (2 dòng), `title_min_length` (3), `summary_not_empty` (3), `summary_min_length` (3), `freshness_within_threshold` (4); `total_failed_rows = 15` |
| Freshness status | fresh (0/24 stale) | **NOT fresh** (4/23 stale) | fresh (0/24 stale) | `mean_age_days` 83.33 → 278.7 → 83.33; `max_age_days` 175 → 1256 → 175 — cả ba đều tính từ cột `age_days` của tôi |

Số dòng: baseline **24** → corrupted **23** (xóa 3, thêm 2 bản trùng) → repaired **24**. Cả ba trạng thái chấm trên cùng `data/eval/test_set.json` (20 câu / 5 paper / 4 loại).

### Kết luận từ số liệu

1. **Corruption → tín hiệu quality/freshness → metric agent.** `corrupt_clean_dataframe()` chạy 7 bước trên frame sạch của tôi → `corrupted_quality.json` rớt từ 12/12 xuống **7/12** với 15 dòng lỗi, `freshness_report_corrupted.json` chuyển `is_fresh` sang **`false`** (`stale_rows = 4/23`, `mean_age_days` tăng 3.3 lần) → `corrupted_metrics.json` cho **0.8000 / 0.6684 / 0.6500 / 3.6000**. Đáng chú ý: cả 5 check FAIL đều nằm trên các cột do tôi định nghĩa (`paper_id`, `title_chars`, `summary`, `summary_chars`, `age_days`), cho thấy schema của khối 2 chính là bề mặt mà observability quan sát.

2. **Repair → tín hiệu phục hồi → metric phục hồi.** Bước 7 chạy lại `build_clean_dataframe()` của tôi trên raw snapshot thay vì vá frame hỏng → `repaired_quality.json` quay lại 12/12 pass, `freshness_report_repaired.json` quay lại `is_fresh = true` với `mean_age_days = 83.33` trùng khít baseline → `repaired_metrics.json` quay lại **1.0000 / 1.0000 / 1.0000 / 5.0000**. Bằng chứng mạnh nhất cho phần việc của tôi: `papers_clean_repaired.csv` trùng khít **từng byte** với `papers_clean.csv`. Nếu hàm của tôi có bất kỳ yếu tố không tất định nào — thứ tự dòng phụ thuộc hash, dấu thời gian, RNG — thì hai file đã khác nhau và không thể kết luận repair hoàn toàn.

Corruption nào ảnh hưởng rõ nhất và vì sao?

**`drop_latest_records` (xóa 3 dòng mới nhất) là loại gây hại rõ nhất**, và cấu trúc test set của tôi là lý do nó nặng đến vậy:

| Loại corruption | Số câu hỏi bị hỏng | Metric bị ảnh hưởng |
| ----------------- | ---------------------: | --------------------- |
| `drop_latest_records` | **4/20** (q001–q004) | cả 4 metric, và là **nguyên nhân duy nhất** làm `retrieval_hit_rate` giảm |
| `blank_summary` | 1/20 (q008) | `token_f1`, `judge_*` |
| `inject_noise` | 1/20 (q012) | `token_f1`, `judge_*` |
| `stale_dates` | 1/20 (q018) | `token_f1`, `judge_*` |
| `truncate_title` | **0/20** | không metric nào |
| `duplicate_rows` | **0/20** | không metric nào (chỉ làm `paper_id_unique` FAIL) |

Lý do gấp đôi: (a) các loại khác chỉ **làm bẩn** một document vẫn còn trong index, nên retrieval vẫn tìm đúng `paper_id`, chỉ nội dung trả lời sai; xóa dòng thì **rút hẳn document khỏi corpus**; (b) trong test set của tôi, một paper gánh **cả 4 loại câu hỏi**, nên xóa một paper là mất trọn 4/20 câu, trong khi các corruption khác chỉ phá được đúng một loại câu hỏi của paper mà nó chạm. Với q001–q004, top-4 trả về `10.55041/isjem07213` và `10.21203/rs.3.rs-9882260/v1` — agent trả lời trôi chảy bằng tài liệu của bài báo khác, không hề báo lỗi.

Kết quả nào khác với kỳ vọng ban đầu?

**`truncate_title` không gây thiệt hại đo được nào — trái hẳn dự đoán của tôi.** Giả thuyết ban đầu: cắt tiêu đề của `10.22214/ijraset.2026.82233` còn 8 ký tự (`"Hybrid G"`) sẽ phá cơ chế tra cứu chính xác trong `answer_question()`, vì hàm này bắt tiêu đề trong dấu nháy đơn bằng regex `r"'([^']+)'"` rồi gọi `index.lookup()` — mà `documents_by_title` giờ chỉ còn khóa `"hybrid g"`, không khớp được tiêu đề đầy đủ trong câu hỏi. Tôi dự đoán 4 câu q013–q016 sẽ hỏng, và điều đó đáng lo với tôi vì chính tôi là người quyết định bọc tiêu đề trong dấu nháy đơn.

Cách kiểm tra: mở `data/results/corrupted_answers.json`, lọc riêng q013–q016. Kết quả thực tế: cả 4 câu vẫn `retrieval_hit = true`, `token_f1 = 1.000`, judge `correct = true` với score 5. Nguyên nhân: `lookup()` đúng là thất bại, nhưng `answer_question()` **luôn chạy song song** `index.search(question)` và chỉ ưu tiên kết quả `lookup` khi nó có giá trị. Ở đây semantic search vẫn xếp đúng bài lên hạng 1, vì `text_for_embedding` còn nguyên 4 thành phần khác (authors, categories, published, summary).

Đây chính là lúc quyết định ở mục 5 được đền đáp theo cách tôi không lường trước: tôi chọn ghép 5 trường để *tăng khả năng trả lời câu hỏi metadata*, nhưng tác dụng thật lớn hơn là nó tạo ra **dự phòng** — hỏng một thành phần thì bốn thành phần còn lại vẫn giữ được document đúng ở hạng 1. Bài học ngược lại cũng quan trọng: chính cơ chế dự phòng đó khiến `truncate_title` làm FAIL check `title_min_length` trên 3 dòng mà **không** làm suy giảm bất kỳ metric nào — nên không được suy từ "check FAIL" ra "agent chắc chắn tệ đi".

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về data pipeline: schema là hợp đồng, và hợp đồng đó bị ràng buộc bởi những thứ nằm ngoài file của mình.** Tôi không được tự do chọn kiểu dữ liệu cho `published`: ChromaDB chỉ nhận `str/int/float/bool` nên nó phải là chuỗi `YYYY-MM-DD`; `authors` và `categories` là list nên phải ghép sẵn thành `authors_joined`/`categories_joined`. Ràng buộc này còn lan sang khối 7 — `corruption._shift_year_back()` cũng buộc phải luôn trả về string, nếu không thì frame corrupted không index được và cả pha 2 sụp. Nói cách khác, một quyết định về kiểu dữ liệu ở khối 2 quyết định luôn cách viết code ở khối 7.

2. **Về data quality/observability: chất lượng dữ liệu chỉ đo được nếu schema chuẩn bị sẵn chỗ để đo.** Nhiều check trong bộ 12 chạy trên các cột dẫn xuất mà tôi tính, và 2 check consistency (`title_chars_consistent`, `summary_chars_consistent`) chỉ tồn tại được vì tôi *tính lại* cột đếm từ chính text thay vì nhận giá trị từ ngoài. Nếu tôi nhận `summary_chars` như một trường sẵn có, hai check đó sẽ luôn PASS một cách vô nghĩa. Đây là kiểu đóng góp không hiện lên trong bất kỳ metric nào nhưng lại quyết định việc observability có thật hay không.

3. **Về ảnh hưởng của data đến RAG agent: một evaluation set sai không làm pipeline gãy — nó làm pipeline báo sai.** Nếu test set được sinh lại từ dữ liệu corrupted thì cả bốn metric sẽ **đẹp lên** đúng vào lúc dữ liệu tệ nhất, vì ground truth cũng hỏng theo. Không có exception nào, không check nào FAIL. Đây là lý do `phase1._load_or_build_test_set()` phải đóng băng test set thay vì tiện tay sinh lại mỗi lần chạy — và cũng là lý do tôi coi `test_set.json` là artifact quan trọng hơn cả `papers_clean.csv` trong phần việc của mình.

### Nếu có thêm thời gian

**Cải thiện đề xuất: mở rộng test set từ 20 câu / 5 paper lên 60 câu / 15 paper, và bổ sung câu hỏi phủ định (negative sample).**

Test set hiện tại quá nhỏ để đo tin cậy: mỗi câu nặng đúng 5% giá trị metric, nên mọi con số đều nhảy theo bước 0.05. Cụ thể, `retrieval_hit_rate` giảm 0.2000 nghe như một sụt giảm lớn, nhưng thực chất chỉ là "mất một paper trong năm paper" — không đủ độ phân giải để phân biệt "mất một paper" với "hệ thống retrieval kém đi". Ngoài ra, 100% câu hỏi hiện tại đều có đáp án nằm trong corpus, nên test set **không đo được khả năng từ chối trả lời** khi tài liệu không tồn tại — đúng vào tình huống mà `drop_latest_records` tạo ra và agent đã trả lời sai một cách trôi chảy.

Cách làm: nâng `PAPERS_PER_TEST_SET` từ 5 lên 15 (đồng thời `max_results` từ 24 lên 100–200 để `_select_papers()` còn chỗ trải đều), và thêm một `question_type` thứ năm — `unanswerable` — sinh từ các paper **không** có trong corpus, với `ground_truth` là chuỗi báo không tìm thấy và `ground_truth_doc_ids = []`.

**Cách đo cải thiện** (có tiêu chí đạt/không đạt rõ ràng, chạy lại được):

1. Chạy `REFRESH_TEST_SET=1 python script/run_phase1.py` với `PAPERS_PER_TEST_SET = 15`. **Tiêu chí đạt:** `test_set.json` có 60 sample, mỗi `question_type` đúng 15 câu, mỗi sample vẫn có đúng 1 `ground_truth_doc_ids`.
2. **Tiêu chí đạt về độ phân giải:** chạy lại corruption flow với cùng bộ 6 corruption. Mức sụt của `retrieval_hit_rate` phải nhỏ hơn 0.2000 hiện tại (dự kiến quanh 0.05–0.07), chứng minh metric không còn bị một paper chi phối.
3. **Tiêu chí đạt về câu hỏi phủ định:** trên baseline, nhóm câu `unanswerable` hiện sẽ cho `token_f1` gần 0 vì agent luôn trả về tài liệu gần nhất thay vì nói không tìm thấy. Con số đó là mốc để đo cải thiện sau khi thêm ngưỡng khoảng cách cosine cho `index.search()`.
4. **Chỉ số theo dõi:** khoảng dao động của bốn metric giữa hai lần chạy baseline liên tiếp. Hiện tại là 0 (pipeline tất định), nhưng đó là do lớp trả lời là router chứ không phải do test set đủ lớn; với reader sinh ngôn ngữ thì test set 20 câu sẽ dao động mạnh, còn 60 câu thì ổn định hơn nhiều.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [ ] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [ ] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [ ] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [ ] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [ ] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [ ] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Dương Hải Long
**Ngày xác nhận:** 2026-08-06
