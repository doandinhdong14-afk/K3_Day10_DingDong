# Member Role Report — Day 10: Data Pipeline & Data Observability

> Báo cáo vai trò cá nhân của **Trần Hoài Nam (2A202601751)** — Source owner của nhóm DingDong. Nội dung chỉ mô tả phần việc tôi trực tiếp thực hiện (khối 1 — raw ingestion), không sao chép báo cáo nhóm hay báo cáo của thành viên khác.

> **Lưu ý về provider LLM:** run đã nộp chạy với `provider=groq`, `model=openai/gpt-oss-20b` (xác minh tại `data/reports/phase1_report.md`, mục 1: `llm_provider | groq`, `llm_model | openai/gpt-oss-20b`). Khối của tôi không gọi LLM, nhưng mọi con số `judge_*` tôi trích ở mục 8 đều do LLM này chấm; nếu nhóm chạy lại trên provider khác thì phải cập nhật lại hai trường đó.

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Trần Hoài Nam |
| MSSV               | 2A202601751 |
| Khóa/Lớp         | K3 |
| Tên nhóm         | DingDong (4 thành viên) |
| Vai trò chính    | Source owner — khối 1 (raw ingestion từ Crossref) |
| Repository         | https://github.com/doandinhdong14-afk/K3_Day10_DingDong |
| Ngày hoàn thành | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

### Danh mục 7 khối deliverable của project

Khối được **in đậm** là khối tôi trực tiếp làm.

| # | Khối deliverable           | File nguồn phụ trách                                              | Artifact phải bàn giao                                                                                       |
| -: | -------------------------- | ------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| **1** | **Raw ingestion**      | **`src/ingestion/crossref.py`**                                   | **`data/raw/crossref_response.json`, `data/raw/crossref_records.json` (24 raw records)**                      |
| 2 | Cleaning & data modeling   | `src/ingestion/cleaning.py`                                       | `data/clean/papers_clean.csv`, `papers_clean.json` (24 dòng × 16 cột)                                       |
| 3 | Evaluation set             | `src/evaluation/testset.py`                                       | `data/eval/test_set.json` (20 câu hỏi / 5 paper / 4 loại câu hỏi)                                        |
| 4 | Quality & freshness        | `src/observability/quality.py`                                    | `data/quality/*.json` (3 quality + 3 freshness report)                                                        |
| 5 | Reporting                  | `src/observability/reporting.py`                                  | `data/reports/phase1_report.md`, `corruption_report.md`, `answer_diff.md`                                   |
| 6 | Baseline orchestration     | `src/pipelines/phase1.py`, `src/retrieval/index.py`               | `data/results/baseline_metrics.json`, `baseline_answers.json`, `data/embeddings/`, `data/chroma/`           |
| 7 | Corruption & repair        | `src/ingestion/corruption.py`, `src/pipelines/corruption_flow.py` | `data/results/corruption_log.json`, `corrupted_metrics.json`, `repaired_metrics.json`                       |

Phân công của nhóm (cấu hình 4 người theo [`README.md`](README.md) mục 5):

| Họ và tên | MSSV | Vai trò | Khối sở hữu |
| ----------- | ------ | --------- | ------------- |
| **Trần Hoài Nam** | **2A202601751** | **Source owner** | **Khối 1 — `crossref.py`** |
| Dương Hải Long | 2A202601607 | Data model & evaluation-set owner | Khối 2, 3 — `cleaning.py`, `testset.py` |
| Đặng Quang Minh | 2A202601459 | Observability owner | Khối 4 — `quality.py` |
| Đoàn Đình Đông (leader) | 2A202601900 | Reporting, orchestration & corruption owner | Khối 5, 6, 7 + điều phối tích hợp |

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | ------------ |
| Gọi Crossref REST API có retry/backoff | `fetch_source_records()`, `_get_with_retry()` | `source_query`, `source_filter`, `max_results=24` từ `src/core/config.py` | `data/raw/crossref_response.json` (1.070.143 B, 72 item) | Hoàn thành |
| Parse và lọc payload thành `PaperRecord` | `parse_crossref_payload()`, `_strip_markup()`, `_format_date()`, `_format_authors()`, `_format_categories()`, `_find_pdf_url()`, `_looks_latin()` | Payload thô 72 item | `data/raw/crossref_records.json` (60.391 B, 24 record × 11 trường) | Hoàn thành |
| Nạp lại snapshot thô để repair | `load_raw_records()` | `data/raw/crossref_records.json` | `list[PaperRecord]` cho `corruption_flow` bước 7 | Hoàn thành |
| Định nghĩa raw schema | dataclass `PaperRecord` (11 trường) | — | Contract đầu vào cho `cleaning.py` | Hoàn thành |

Chỉ nhận ownership cho phần tôi trực tiếp thực hiện. Tôi **không** viết `cleaning.py`, `testset.py`, `quality.py`, `reporting.py`, `phase1.py`, `corruption.py` hay `corruption_flow.py`.

Thứ tự phụ thuộc thực tế giữa các khối — khối của tôi đứng đầu chuỗi, nên mọi lỗi ở đây lan xuống toàn bộ pipeline:

```text
Khối 1 raw ingestion  <-- phần việc của tôi
   -> Khối 2 cleaning (đọc data/raw/crossref_records.json)
   -> Khối 3 test set + Khối 6 index/baseline (đọc data/clean/papers_clean.json)
   -> Khối 4 quality/freshness + Khối 5 reporting
   -> Khối 7 corruption/repair (repair đọc LẠI data/raw/crossref_records.json của tôi)
```

Điểm đáng chú ý: `data/raw/crossref_records.json` được dùng **hai lần** — một lần ở pha 1 để dựng baseline, một lần ở pha 2 bước 7 để repair. Vì vậy file này phải bất biến trong suốt hai flow; nếu bước corruption ghi đè lên nó thì repair sẽ tái tạo lại chính dữ liệu đã hỏng.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| ------------ | -------------------------------- | ---------- |
| Bàn giao và giải thích raw schema (`PaperRecord`, 11 trường) để cleaning không phải đoán kiểu dữ liệu | Dương Hải Long — `src/ingestion/cleaning.py` | `build_clean_dataframe()` đọc thẳng `record.published`, `record.categories`… không cần lớp chuyển đổi trung gian. Bằng chứng: 24/24 raw record đi qua cleaning mà không dòng nào bị loại |
| Xác nhận với leader rằng `crossref_records.json` không bị bước corruption ghi vào, để repair dùng lại được | Đoàn Đình Đông — `src/pipelines/corruption_flow.py` bước 7 | `papers_clean_repaired.csv` trùng khít từng byte với `papers_clean.csv` (cùng 103.200 B) — chứng tỏ snapshot thô còn nguyên vẹn |
| Chỉ ra tại sao `pdf_url` phải là trường tùy chọn thay vì bắt buộc | Đặng Quang Minh — `src/observability/quality.py` | Đo thực tế 7/24 dòng có `pdf_url` rỗng. Bộ 12 check vì vậy **không** đặt check bắt buộc cho `pdf_url`; nếu đặt thì baseline sẽ FAIL giả 7 dòng |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------------- | ----------------------------- | ------------------- | --------------- |
| Gọi Crossref với polite pool và retry lũy thừa | `_get_with_retry()` (`max_attempts=5`, `timeout=60`, `RETRYABLE_STATUS = {429,500,502,503,504}`) | `crossref_response.json` — `total-results = 100934`, response chứa 72 item | `python script/run_phase1.py` (bước 2/10); mở file và đếm `message.items` |
| Over-fetch rồi lọc phía client | `fetch_source_records()` với `rows = max_results * 3 = 72` | 72 item → **71 record hợp lệ** sau parse → cắt còn 24 ghi ra `crossref_records.json` | Chạy lại `parse_crossref_payload()` trên `crossref_response.json` đã lưu, đếm kết quả |
| Bóc markup JATS/HTML trong `title` và `abstract` | `_strip_markup()` | Không còn thẻ `<jats:p>`/`<p>` trong `title`/`summary` của 24 record | So `crossref_response.json` với `crossref_records.json` trên cùng một DOI |
| Chuẩn hóa `date-parts` của Crossref thành `YYYY-MM-DD` | `_format_date()` (thiếu tháng/ngày → mặc định 1; ngày sai → lùi về `YYYY-01-01`) | 24/24 record có `published` đúng định dạng | Check `published_format_valid` PASS 24/24 trong `data/quality/baseline_quality.json` |
| Suy ra `categories` khi Crossref không có `subject` | `_format_categories()` — fallback `container-title` → `type` → `publisher` | 0/24 dòng `categories_joined` rỗng, 0/24 dòng rơi về `uncategorized`, trung bình **2.62** category/dòng | Đếm trực tiếp trên `data/clean/papers_clean.csv` |
| Loại bài không phải chữ Latin | `_looks_latin()` — yêu cầu ≥70% ký tự chữ cái là ASCII trên cả `title` lẫn `summary` | 72 item → 71 hợp lệ (1 item bị loại) | Chạy `parse_crossref_payload()` và so với `len(items)` |
| Khử DOI trùng ngay trong payload | `parse_crossref_payload()` với set `seen_ids` (so sánh chữ thường) | Baseline đạt `paper_id_unique` PASS 24/24 | `data/quality/baseline_quality.json` |
| Cho phép nạp lại snapshot mà không gọi API | `load_raw_records()`; `phase1._load_records()` chỉ gọi API khi thiếu file hoặc bật `REFRESH_SOURCE=1` | Chạy lại pipeline nhiều lần vẫn ra đúng 24 record cũ | Chạy `run_phase1.py` hai lần, kiểm tra `crossref_records.json` không đổi kích thước (60.391 B) |

### Lệnh xác minh thật của từng khối

| Khối | Lệnh chạy | Artifact phải mở để đối chiếu | Dấu hiệu đạt |
| ---- | ----------- | -------------------------------- | -------------- |
| Tiền đề cho mọi khối gọi LLM | `python script/check_llm.py` | stdout của script | 3 dòng `[OK  ]` cho *chat bình thường*, *structured output*, *tool calling*, kết thúc bằng `KET LUAN: provider san sang` |
| **1. Raw ingestion (của tôi)** | `python script/run_phase1.py` (bước 2/10) | `data/raw/crossref_records.json` | file có 24 record, mỗi record đủ `paper_id/title/summary/authors/published` |
| 2. Cleaning | `python script/run_phase1.py` (bước 3–4/10) | `data/clean/papers_clean.csv` | 24 dòng, 16 cột, cột `text_for_embedding` không rỗng |
| 3. Evaluation set | `python script/run_phase1.py` (bước 6/10); ép tạo lại bằng `REFRESH_TEST_SET=1` | `data/eval/test_set.json` | 20 sample, 4 `question_type`, mỗi sample có đúng 1 `ground_truth_doc_ids` |
| 4. Quality & freshness | `python script/run_phase1.py` (bước 8/10) và `python script/run_corruption_flow.py` (bước 6, 8/10) | `data/quality/*.json` | baseline 12/12 pass, corrupted 7/12 pass, repaired 12/12 pass |
| 5. Reporting | `python script/run_phase1.py` (bước 9/10), `python script/run_corruption_flow.py` (bước 9/10) | `data/reports/*.md` | bảng so sánh khớp với các file `*_metrics.json` |
| 6. Baseline orchestration | `python script/run_phase1.py` | `data/results/baseline_metrics.json` | `1.0 / 1.0 / 1.0 / 5`; mọi dòng artifact là `[OK]` |
| 7. Corruption & repair | `python script/run_corruption_flow.py` | `data/results/corruption_log.json` | 7 step, `source_rows=24`, `result_rows=23`, `deterministic=true` |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

**`data/raw/crossref_records.json` (60.391 bytes, 24 record)** là artifact chính của tôi. Mỗi record là một `PaperRecord` với đúng 11 trường: `paper_id` (DOI), `title`, `summary`, `authors`, `categories`, `primary_category`, `published`, `updated`, `abs_url`, `pdf_url`, `comment`. File này quan trọng hơn hẳn `crossref_response.json` ở chỗ nó đã qua toàn bộ bộ lọc chất lượng của tầng nguồn — 72 item Crossref trả về chỉ còn 71 sau khi loại bài không phải chữ Latin, rồi cắt còn 24 theo `max_results`. Hai người dùng lại output này: Dương Hải Long đọc nó ở `build_clean_dataframe()` để dựng frame sạch, và Đoàn Đình Đông đọc lại **đúng file này** ở bước 7 của `corruption_flow.py` để repair. Chính vì repair đọc lại snapshot của tôi chứ không vá frame hỏng mà `papers_clean_repaired.csv` ra đúng 103.200 bytes, trùng khít từng byte với `papers_clean.csv` của baseline.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Khối của tôi phải trả lời một câu hỏi tưởng đơn giản: *lấy 24 bài báo dùng được từ một API sống, theo cách lặp lại được*. Ba khó khăn thật:

1. **Crossref là nguồn sống.** `source_filter` được tính theo `hôm nay − 180 ngày` trong `src/core/config.py`, nên mỗi ngày gọi lại sẽ ra một tập bài khác. Nếu pipeline gọi API mỗi lần chạy thì không thể so sánh baseline với corrupted, vì corpus đã đổi giữa hai lần đo.
2. **Chất lượng metadata của Crossref rất không đều.** Abstract lưu dưới dạng XML JATS, `subject` thường không có, `content-type` của link thường là `unspecified`, ngày tháng có thể thiếu tháng hoặc thiếu ngày.
3. **Bộ lọc phía client loại bớt record**, nên không thể xin đúng số lượng cần.

### Cách triển khai

Luồng trong khối của tôi:

```text
GET https://api.crossref.org/works
    ?query=agentic retrieval augmented generation large language model
    &filter=from-pub-date:2026-02-07,has-abstract:true
    &rows=72                       (= max_results * 3)
    &mailto=<email liên hệ>        (polite pool)
  -> _get_with_retry()             : 5 lần thử, chờ 1 -> 2 -> 4 -> 8s
  -> write_json(raw_api_response)  : data/raw/crossref_response.json (72 item, ~1.07 MB)
  -> parse_crossref_payload()      : 72 item -> 71 record hợp lệ
       . _strip_markup()           : bóc thẻ JATS/HTML, giải mã entity
       . _format_date()            : date-parts -> YYYY-MM-DD
       . _format_authors()         : ghép given + family, khử trùng tên
       . _format_categories()      : subject -> container-title -> type -> publisher
       . _find_pdf_url()           : ưu tiên content-type=application/pdf, sau đó đoán theo ".pdf"
       . _looks_latin()            : loại bài < 70% ký tự ASCII
       . seen_ids                  : loại DOI trùng (so sánh chữ thường)
  -> [: max_results]               : cắt còn 24
  -> write_json(raw_records_json)  : data/raw/crossref_records.json (24 record)
```

Bốn chi tiết trong code của tôi mà tôi thấy đáng nói:

1. **`REQUEST_HEADERS` có `mailto` để vào polite pool của Crossref.** Crossref chia lưu lượng thành polite pool và anonymous pool; client khai báo email được ưu tiên và ít bị 429 hơn. Đây là lý do trong các lần chạy thật tôi không phải dùng tới nhánh retry — nhưng nhánh đó vẫn phải có, vì "chưa bao giờ bị rate limit" không đồng nghĩa với "sẽ không bao giờ bị".
2. **Retry chỉ áp cho lỗi tạm thời.** `RETRYABLE_STATUS = {429, 500, 502, 503, 504}`. Các mã khác đi thẳng vào `raise_for_status()` và ném ngay — thử lại một request 400 sai tham số chỉ tốn 15 giây rồi vẫn hỏng.
3. **`_looks_latin()` áp cho *cả* `title` lẫn `summary`.** Một bài có tiêu đề tiếng Anh nhưng abstract tiếng khác vẫn phải loại, vì cột được embed (`text_for_embedding`) chứa cả hai, mà `all-MiniLM-L6-v2` chỉ mạnh với tiếng Anh.
4. **Payload thô được ghi ra đĩa *trước* khi parse.** `write_json(settings.paths.raw_api_response, payload)` chạy ngay sau `_get_with_retry()`. Nhờ vậy khi bộ lọc của tôi có bug thì vẫn chạy lại `parse_crossref_payload()` được trên payload cũ mà không phải gọi API lần nữa — và đúng là tôi đã dùng cách này để đếm ra con số "0/72 item có `subject`" ở mục 6.

### Input, output và contract

| Thành phần | Mô tả |
| ------------ | ------- |
| Input | Tham số từ `src/core/config.py`: `source_query = "agentic retrieval augmented generation large language model"`, `source_filter = "from-pub-date:{hôm nay − 180 ngày},has-abstract:true"` (lần chạy nộp bài: `from-pub-date:2026-02-07`), `max_results = 24`. Khi chạy lại, `phase1._load_records()` ưu tiên đọc `data/raw/crossref_records.json` đã có; chỉ gọi API khi thiếu file hoặc bật `REFRESH_SOURCE=1` |
| Output | `data/raw/crossref_response.json` — payload thô nguyên trạng (72 item). `data/raw/crossref_records.json` — 24 `PaperRecord`, mỗi record 11 trường: `paper_id`, `title`, `summary`, `authors` (list), `categories` (list), `primary_category`, `published`, `updated`, `abs_url`, `pdf_url`, `comment` |
| Module phụ thuộc | `src/core/config.py` (query/filter/`max_results`), `src/core/utils.py` (`normalize_whitespace`, `write_json`, `read_json`), thư viện `requests` |
| Module sử dụng output | `src/ingestion/cleaning.py` (`build_clean_dataframe(records, run_date)`), `src/pipelines/phase1.py` (bước 2/10), `src/pipelines/corruption_flow.py` (bước 7 — repair gọi `load_raw_records`) |
| Điều kiện lỗi cần xử lý | Xem bảng bên dưới |

Các điều kiện lỗi **thực sự** được xử lý trong `crossref.py` (không phải giả định):

| Điều kiện lỗi | Vị trí xử lý | Cách xử lý |
| --------------- | -------------- | ------------ |
| HTTP 429/500/502/503/504 hoặc `requests.RequestException` | `_get_with_retry()` | Tối đa 5 lần thử; chờ 1s rồi nhân đôi sau mỗi lần (1→2→4→8s), in dòng `[crossref] {lỗi} -> thu lai sau {n}s ({attempt}/5)`. Hết lượt thì `raise RuntimeError` kèm lỗi cuối cùng |
| Chứng chỉ TLS của mạng nội bộ chặn request | `_get_with_retry()` | Cho phép trỏ CA bundle riêng qua biến môi trường `CROSSREF_CA_BUNDLE`, mặc định `verify=True` |
| Abstract dạng XML JATS | `_strip_markup()` | Bóc toàn bộ thẻ, giải mã HTML entity, gộp khoảng trắng, bỏ tiền tố "Abstract:"/"Summary:" |
| Abstract rỗng hoặc quá ngắn | `parse_crossref_payload()` — `MIN_SUMMARY_CHARS = 80` | Bỏ hẳn record. Đo thực tế: `summary_chars` nhỏ nhất trong dataset cuối là **826**, tức filter `has-abstract:true` đã chặn phần lớn từ phía server |
| Thiếu DOI, thiếu tiêu đề hoặc không parse được ngày | `parse_crossref_payload()` | Bỏ record; đo thực tế 0/72 item vi phạm |
| Ngày thiếu tháng/ngày hoặc không hợp lệ | `_format_date()` | Thiếu thì mặc định là 1; ngày không hợp lệ thì lùi về `YYYY-01-01`; không có `issued` thì thử `published` rồi `created` |
| Bài không phải chữ Latin | `_looks_latin()` | Yêu cầu ≥70% ký tự chữ cái là ASCII trên cả `title` lẫn `summary`. Đo thực tế: 1/72 item bị loại |
| Crossref không có trường `subject` | `_format_categories()` | Fallback `container-title` → `type` (thay `-` bằng khoảng trắng) → `publisher`, khử trùng theo thứ tự xuất hiện; cạn nguồn mới trả `["uncategorized"]`. **Đo thực tế: 0/72 item có `subject`** |
| `content-type` của link là `unspecified` | `_find_pdf_url()` | Ưu tiên link có `content-type == "application/pdf"`, sau đó đoán theo đuôi `.pdf` trong URL, cuối cùng lấy link đầu tiên; không có link nào thì trả chuỗi rỗng (7/24 dòng rơi vào trường hợp này) |
| DOI trùng trong cùng payload | `parse_crossref_payload()` — set `seen_ids` | So sánh DOI viết thường, giữ bản xuất hiện trước |
| Crossref trả về 0 record hợp lệ | `fetch_source_records()` | `raise RuntimeError("Crossref khong tra ve record hop le nao. Kiem tra lai query/filter.")` thay vì ghi ra file rỗng |

### Cách xác minh

```bash
python script/run_phase1.py            # bước 2/10 sinh cả hai file trong data/raw/
python script/run_corruption_flow.py   # bước 7 đọc lại crossref_records.json để repair
```

- **Kết quả mong đợi:** bước 2/10 in `[crossref] GET https://api.crossref.org/works rows=72`, lưu raw response rồi lưu 24 raw records; không có dòng retry nào.
- **Kết quả thực tế:** đúng như mong đợi. `crossref_response.json` = 1.070.143 B với 72 item và `total-results = 100934`; `crossref_records.json` = 60.391 B với 24 record. Chạy lại lần hai, pipeline đọc lại snapshot cũ nên hai file không đổi — đây là điều kiện để baseline và corrupted so sánh được với nhau.
- **Artifact/log:** `data/raw/crossref_response.json`, `data/raw/crossref_records.json`. Không file nào chứa API key; Crossref không cần key, chỉ cần email liên hệ trong `User-Agent`, và `.env` nằm trong `.gitignore`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** cần đúng 24 record dùng được, nhưng bộ lọc phía client (abstract < 80 ký tự, không phải chữ Latin, DOI trùng, thiếu DOI/tiêu đề/ngày) loại bớt một phần kết quả API trả về. Xin đúng `rows=24` thì sau khi lọc có thể thiếu, mà thiếu thì khối 3 sẽ gãy: `build_test_set()` yêu cầu tối thiểu 5 document (`MIN_DOCUMENTS = 5`) và `_select_papers()` cần đủ paper để lấy mẫu trải đều.

- **Các phương án đã cân nhắc:**
  - **Phương án A — vòng lặp phân trang cho tới khi đủ 24:** gọi `rows=24`, lọc, nếu thiếu thì gọi tiếp với `offset` tăng dần. Ưu điểm: tải về đúng lượng dữ liệu cần, tiết kiệm băng thông. Nhược điểm: số lần gọi API phụ thuộc tỷ lệ record bị loại, mà tỷ lệ đó thay đổi theo ngày → không tất định; `crossref_response.json` sẽ là bản ghép của nhiều response nên mất quan hệ "một request ↔ một payload"; và mỗi vòng lặp thêm là một cơ hội dính 429.
  - **Phương án B — over-fetch cố định `max_results × 3 = 72` trong một request rồi cắt:** một lần gọi duy nhất, lọc, rồi `[: max_results]`.

- **Phương án đã chọn:** Phương án B.

- **Lý do:** đây là bài lab về *khả năng truy vết*, nên "một request ↔ một file payload" đáng giá hơn vài trăm KB băng thông. Với B, `crossref_response.json` là bản chụp nguyên vẹn của đúng một lời gọi API — nhờ đó tôi chạy lại được `parse_crossref_payload()` trên file đã lưu để kiểm chứng mọi con số trong báo cáo này (72 → 71 → 24, và 0/72 item có `subject`) mà không phải gọi lại API. Hệ số 3 không phải con số tùy tiện: nó phải đủ lớn để chịu trường hợp xấu, và số đo thực tế cho thấy tỷ lệ loại chỉ 1/72 nên biên an toàn còn rất rộng. Đổi lại là tải ~1.07 MB cho 24 record thực dùng — chấp nhận được ở cỡ corpus này, nhưng phải xem lại nếu nâng `max_results` lên hàng trăm.

- **Bằng chứng quyết định phù hợp:** chạy lại `parse_crossref_payload()` trên `data/raw/crossref_response.json` đã lưu cho ra chuỗi số:

  | Giai đoạn | Số item | Nguồn kiểm chứng |
  | ----------- | --------: | ------------------ |
  | Crossref khớp query | 100.934 | `message.total-results` |
  | Trả về trong một request | 72 | `len(message.items)` |
  | Hợp lệ sau bộ lọc client | 71 | `len(parse_crossref_payload(payload))` |
  | Ghi ra `crossref_records.json` | 24 | cắt theo `max_results` |

  Nếu dùng phương án A với `rows=24` thì lần gọi đầu chỉ còn khoảng 23–24 record hợp lệ — sát ngưỡng đến mức chỉ thêm một bài không phải chữ Latin là phải gọi vòng thứ hai, và số vòng gọi sẽ khác nhau giữa các ngày.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** pipeline chạy qua ingestion và cleaning bình thường rồi chết ở bước 6/10 khi dựng test set:

  ```text
  ValueError: Khong co paper nao du dieu kien de tao cau hoi.
  ```

  (Chuỗi này lấy nguyên văn từ `src/evaluation/testset.py`, hàm `_select_papers()`. Log gốc không chứa secret.)

- **Lệnh hoặc bước tái hiện:**

  ```bash
  # Khi _format_categories() mới chỉ đọc item["subject"] và chưa có nhánh fallback
  python script/run_phase1.py     # chết ở bước 6/10 "Chuan bi evaluation test set"
  ```

- **Nguyên nhân gốc:** không phải lỗi của `testset.py` mà là lỗi ở tầng nguồn — tức khối của tôi. `subject` là trường **tùy chọn** trong metadata Crossref, chỉ một phần nhà xuất bản khai báo. Đo trực tiếp trên snapshot đã lưu `data/raw/crossref_response.json`: **0 trên 72 item** có trường `subject`. Hậu quả dây chuyền: `categories = []` trên mọi record → `categories_joined` rỗng trên 24/24 dòng clean → `_is_usable()` trong `testset.py` (yêu cầu `authors_joined`, `categories_joined` và `summary` đều khác rỗng) loại sạch mọi bài → `usable.empty` → `ValueError`. Giả định ban đầu của tôi là "mỗi bài báo đều có chủ đề" — đúng với arXiv (nơi `categories` luôn có) nhưng sai với Crossref.

- **Cách xử lý:** thêm chuỗi fallback trong `_format_categories()` thay vì nới lỏng điều kiện `_is_usable()` ở khối của người khác:

  ```python
  categories = [normalize_whitespace(str(s)) for s in (item.get("subject") or []) if s]
  if not categories:
      journal   = _first_string(item.get("container-title"))
      doc_type  = normalize_whitespace(str(item.get("type") or "")).replace("-", " ")
      publisher = normalize_whitespace(str(item.get("publisher") or ""))
      categories = [value for value in (journal, doc_type, publisher) if value]
  return list(dict.fromkeys(categories)) or ["uncategorized"]
  ```

  Tôi cố ý **không** chọn cách nới điều kiện `_is_usable()`. Nếu nới, 5/20 câu hỏi loại `categories` sẽ có ground truth là chuỗi rỗng, và `token_f1` của chúng bị ép về 0 theo đúng định nghĩa trong `metrics._token_f1` (`if not ref_tokens: return 0.0`) — metric sẽ tố cáo một lỗi dữ liệu không tồn tại, còn tầng nguồn thì vẫn sai y nguyên.

- **Cách xác minh sau khi sửa:**

  ```bash
  python script/run_phase1.py
  ```

  `data/clean/papers_clean.csv`: **0/24** dòng có `categories_joined` rỗng, **0/24** dòng rơi về giá trị mặc định `uncategorized`, trung bình **2.62** category mỗi dòng — ví dụ `SPE Journal, journal article, Society of Petroleum Engineers (SPE)`. `data/eval/test_set.json` sinh đủ 20 câu hỏi với 5 câu loại `categories`. Trong `data/results/baseline_answers.json`, năm câu `q003`, `q007`, `q011`, `q015`, `q019` đều có `token_f1 = 1.0` và judge 5/5.

- **Điều học được:** trường "tùy chọn" trong đặc tả API phải được coi là **luôn vắng mặt** cho tới khi đo trên dữ liệu thật, chứ không phải "thường có". Bài học thứ hai quan trọng hơn: lỗi nổ ở khối 3 nhưng nguyên nhân nằm ở khối 1 — nếu tôi sửa ở chỗ nó nổ thì đã che mất lỗi thật. Với vai trò owner của tầng nguồn, tôi phải chịu trách nhiệm cho cả những lỗi biểu hiện ở hạ nguồn.

Phần cần ghi rõ giới hạn của cách xử lý này:

- **Phạm vi bị ảnh hưởng về mặt ngữ nghĩa:** sau fallback, `categories` mô tả **nơi công bố** (tạp chí / loại tài liệu / nhà xuất bản) chứ không phải **lĩnh vực học thuật**. 5/20 câu hỏi loại `categories` vì vậy thực chất đang kiểm tra "bài này đăng ở đâu". Đây là đánh đổi có ý thức, tôi ghi ra để người đọc không hiểu nhầm ngữ nghĩa của cột.
- **Những gì đã loại trừ:** không phải lỗi mạng hay ngẫu nhiên (đo trên snapshot tĩnh, lặp lại 100%); không phải lỗi parse của tôi (kiểm tra thủ công trong `crossref_response.json`, không item nào có khóa `subject`); không phải do query hay filter (đổi query khác vẫn 0 item có `subject`).
- **Bước tiếp theo:** bổ sung nguồn chủ đề học thuật thật — OpenAlex concepts hoặc phân loại bằng LLM — rồi so `categories_joined` mới với bản hiện tại trên cùng 24 bài để đo mức chênh.

## 7. Hiểu biết về luồng end-to-end

**1. Từ Crossref đến vector index.** Đây là đoạn tôi trực tiếp làm phần đầu. `fetch_source_records()` gọi `GET https://api.crossref.org/works` với query về agentic RAG/LLM và filter `from-pub-date:2026-02-07,has-abstract:true`, xin dư 72 dòng, lưu payload thô rồi parse còn 71 record hợp lệ và cắt lấy 24 ghi vào `data/raw/crossref_records.json`. Từ đó `build_clean_dataframe()` dựng frame 16 cột và ghép cột `text_for_embedding` = `title + authors + categories + published + summary`. Cuối cùng `LocalEmbeddingIndex.build()` cho `sentence-transformers/all-MiniLM-L6-v2` mã hóa **đúng cột `text_for_embedding`** rồi nạp vào ChromaDB (`PersistentClient` tại `data/chroma/`, khoảng cách cosine), kèm metadata gồm `paper_id`, `title`, `published`, `authors_joined`, `categories_joined`, `summary`, `abs_url`, `pdf_url`. Ba trạng thái dùng ba collection riêng: `papers-baseline`, `papers-corrupted`, `papers-repaired`. Điều tôi phải nhớ khi làm tầng nguồn: bốn trong năm thành phần của `text_for_embedding` đến thẳng từ record của tôi, nên một trường bị parse sai sẽ đi thẳng vào vector chứ không dừng lại ở CSV.

**2. Test set và ground-truth document IDs.** `build_test_set()` chọn 5 paper trải đều (`df.iloc[::4]`) rồi sinh 4 câu hỏi mỗi paper — `authors`, `date`, `categories`, `summary` — thành 20 sample `q001`–`q020`. Mỗi sample lưu `ground_truth` lấy trực tiếp từ frame sạch và `ground_truth_doc_ids` chứa đúng một `paper_id`. Khi chấm, `evaluate_pipeline()` gọi `answer_question()` lấy `top_k = 4` rồi tính hai loại chỉ số tách biệt: `retrieval_hit` chỉ hỏi "document đúng có nằm trong top-4 không" (không quan tâm câu trả lời), còn `token_f1` và LLM judge chấm nội dung câu trả lời. Tách đôi như vậy mới phân biệt được "lấy nhầm tài liệu" với "lấy đúng tài liệu nhưng nội dung tài liệu đã hỏng".

**3. Quality checks khác freshness monitoring.** `run_data_quality_checks()` chạy 12 check trên 5 chiều (completeness, uniqueness, validity, consistency, freshness) và trả lời "dữ liệu có *đúng* không" bằng pass/fail theo dòng. `build_freshness_report()` trả lời "dữ liệu có *mới* không" bằng các đại lượng liên tục: `latest_published`, `oldest_published`, `stale_rows`, `stale_ratio`, `max/min/mean_age_days`, `is_fresh`, kèm `stale_paper_ids` để truy vết. Hai thứ giao nhau ở đúng một điểm — check `freshness_within_threshold` (`age_days > 180`) là ảnh chụp nhị phân của cùng tín hiệu mà freshness report mô tả chi tiết. Trên dữ liệu corrupted, check chỉ nói "FAIL, 4/23 dòng", còn report nói thêm `mean_age_days` nhảy từ 83.33 lên 278.7 và `max_age_days` từ 175 lên 1256.

**4. Vì sao phải dùng cùng test set cho cả ba trạng thái.** Vì test set và `ground_truth` được sinh **từ dữ liệu sạch**. Sinh lại từ frame corrupted thì ground truth của câu hỏi summary sẽ chính là chuỗi rỗng hoặc chuỗi rác, câu hỏi ngày tháng sẽ lấy đúng ngày đã bị đẩy lùi — agent trả về rác vẫn được chấm 5/5, tức phép đo tự phá chính nó. Trong code, `phase1._load_or_build_test_set()` đọc lại `data/eval/test_set.json` nếu đã có và chỉ tạo mới khi bật `REFRESH_TEST_SET`; `corruption_flow` truyền thẳng `settings.paths.eval_testset` cho cả hai lần đánh giá của nó và nạp lại `baseline_metrics.json` thay vì chấm lại baseline.

**5. Repair thành công dựa trên artifact và metric nào.** Đây là chỗ khối của tôi được dùng lần thứ hai: `corruption_flow` bước 7 gọi `load_raw_records(data/raw/crossref_records.json)` — hàm và file đều của tôi — rồi `build_clean_dataframe()` lại từ đầu, tức đi đúng con đường baseline đã đi, chứ không vá frame hỏng. Kết luận thành công dựa trên ba nhóm bằng chứng độc lập: **số dòng** (`papers_clean_repaired.csv` có 24 dòng, trùng khít từng byte với bản baseline); **tín hiệu dữ liệu** (`repaired_quality.json` 12/12 pass, `total_failed_rows = 0`; `freshness_report_repaired.json` `is_fresh = true`, `stale_rows = 0`, `mean_age_days = 83.33`); và **metric của agent** (`repaired_metrics.json` cho 1.0 / 1.0 / 1.0 / 5 trên đúng 20 sample cũ). Ba nhóm phải cùng phục hồi mới kết luận được.

## 8. Phân tích kết quả

### Metrics chính

Số liệu đọc trực tiếp từ `data/results/*.json` và `data/quality/*.json` của lần chạy nộp bài.

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------- | -------: | --------: | -------: | ---------------------- |
| `retrieval_hit_rate` | 1.0000 | 0.8000 | 1.0000 | Nhìn từ tầng nguồn thì đây là metric nói về tôi rõ nhất: nó chỉ giảm khi **bản ghi biến mất khỏi corpus**, không giảm vì nội dung bẩn. 4/20 câu trượt đều thuộc `10.2118/234689-pa` bị `drop_latest_records` xóa |
| `mean_token_f1` | 1.0000 | 0.6684 | 1.0000 | Giảm 0.3316. Theo loại câu hỏi: summary 0.4190, date 0.6000, authors 0.8000, categories 0.8545. Câu `categories` — loại phụ thuộc trực tiếp vào nhánh fallback của tôi — lại ít bị ảnh hưởng nhất |
| `judge_accuracy` | 1.0000 | 0.6500 | 1.0000 | 7/20 câu bị chấm sai: q001–q004 (mất bản ghi), q008 (summary rỗng), q012 (summary rác), q018 (ngày sai) |
| `mean_judge_score` | 5.0000 | 3.6000 | 5.0000 | 13 câu giữ 5/5, 7 câu còn lại đều bị chấm 1/5 — không có mức trung gian |
| Quality checks | 12/12 | 7/12 | 12/12 | 5 check FAIL trên corrupted: `paper_id_unique` (2 dòng), `title_min_length` (3), `summary_not_empty` (3), `summary_min_length` (3), `freshness_within_threshold` (4); `total_failed_rows = 15` |
| Freshness status | fresh (0/24 stale) | **NOT fresh** (4/23 stale) | fresh (0/24 stale) | `latest_published` 2026-08-01 → 2026-07-03 → 2026-08-01; `oldest_published` 2026-02-12 → 2023-02-26 → 2026-02-12 |

Số dòng: baseline **24** → corrupted **23** (xóa 3, thêm 2 bản trùng) → repaired **24**. Cả ba trạng thái chấm trên cùng `data/eval/test_set.json` (20 câu / 5 paper / 4 loại).

### Kết luận từ số liệu

1. **Corruption → tín hiệu quality/freshness → metric agent.** `corrupt_clean_dataframe()` chạy 7 bước trên frame sạch → `corrupted_quality.json` rớt từ 12/12 xuống **7/12** với 15 dòng lỗi, `freshness_report_corrupted.json` chuyển `is_fresh` sang **`false`** với `stale_rows = 4/23` và `mean_age_days` tăng gấp 3.3 lần → `corrupted_metrics.json` cho **0.8000 / 0.6684 / 0.6500 / 3.6000**.

2. **Repair từ snapshot thô → tín hiệu phục hồi → metric phục hồi.** Bước 7 dựng lại frame từ `data/raw/crossref_records.json` — **file của khối tôi** — thay vì vá frame hỏng → `repaired_quality.json` quay lại 12/12 pass, `freshness_report_repaired.json` quay lại `is_fresh = true` với `mean_age_days = 83.33` trùng khít baseline → `repaired_metrics.json` quay lại **1.0000 / 1.0000 / 1.0000 / 5.0000**. Đây là bằng chứng trực tiếp cho giá trị của việc ghi snapshot thô ra đĩa ở tầng nguồn: nếu tôi chỉ trả về `list[PaperRecord]` trong bộ nhớ mà không ghi file, bước repair sẽ không có gì để dựng lại.

Corruption nào ảnh hưởng rõ nhất và vì sao?

**`drop_latest_records` (xóa 3 dòng mới nhất) là loại gây hại rõ nhất**, và đây cũng là loại chạm thẳng vào mối quan tâm của tầng nguồn:

| Loại corruption | Số câu hỏi bị hỏng | Metric bị ảnh hưởng |
| ----------------- | ---------------------: | --------------------- |
| `drop_latest_records` | **4/20** (q001–q004) | cả 4 metric, và là **nguyên nhân duy nhất** làm `retrieval_hit_rate` giảm |
| `blank_summary` | 1/20 (q008) | `token_f1`, `judge_*` |
| `inject_noise` | 1/20 (q012) | `token_f1`, `judge_*` |
| `stale_dates` | 1/20 (q018) | `token_f1`, `judge_*` |
| `truncate_title` | **0/20** | không metric nào |
| `duplicate_rows` | **0/20** | không metric nào (chỉ làm `paper_id_unique` FAIL) |

Lý do: các loại khác chỉ **làm bẩn** một document vẫn còn trong index, nên retrieval vẫn tìm đúng `paper_id`, chỉ nội dung trả lời sai. Riêng xóa dòng thì **rút hẳn document khỏi corpus**. Với q001–q004, top-4 trả về `10.55041/isjem07213` và `10.21203/rs.3.rs-9882260/v1` — agent tự tin trả lời bằng tài liệu của bài báo khác: hỏi tác giả bài SafeRAG thì nhận `"Dr. Sumalatha P, Manoj Kumar"` thay vì `"Qianwen Cao, Chiyu Zhang, Junxiong Ning, Gongru Li"`. Với vai trò owner tầng nguồn, tôi rút ra: một bản ghi *thiếu* nguy hiểm hơn một bản ghi *bẩn*, vì bẩn thì check bắt được và người dùng còn thấy dấu vết, còn thiếu thì hệ thống im lặng thay thế bằng tài liệu khác.

Kết quả nào khác với kỳ vọng ban đầu?

**Bộ lọc `_looks_latin()` của tôi chỉ loại đúng 1/72 item — thấp hơn nhiều so với dự đoán.** Khi viết hàm này tôi đặt ngưỡng 70% ký tự ASCII và nghĩ rằng với nguồn Crossref đa ngôn ngữ, sẽ có khoảng 10–20% bài bị loại. Cách kiểm tra: chạy lại `parse_crossref_payload()` trên `crossref_response.json` đã lưu và đếm số record sống sót — kết quả 71/72, tức chỉ 1 item bị loại (và đó cũng có thể là do một điều kiện lọc khác chứ không hẳn do ngôn ngữ).

Nguyên nhân: filter `has-abstract:true` phía server đã chặn phần lớn record chất lượng thấp trước khi tới bộ lọc của tôi, còn query bằng tiếng Anh khiến xếp hạng relevance của Crossref ưu tiên bài tiếng Anh. Nói cách khác, **bộ lọc phía server làm gần hết việc, bộ lọc phía client chỉ là lưới an toàn**. Điều này không có nghĩa `_looks_latin()` thừa — nó vẫn phải có vì query có thể đổi và Crossref không bảo đảm ngôn ngữ — nhưng nó cho thấy hệ số over-fetch ×3 hiện rộng hơn cần thiết rất nhiều. Một quan sát liên quan: `summary_chars` nhỏ nhất trong dataset cuối là **826**, trong khi ngưỡng `MIN_SUMMARY_CHARS` chỉ là 80 — ngưỡng này cũng chưa từng phải cắt bài nào trong lần chạy này.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về data pipeline: ghi payload thô ra đĩa trước khi xử lý là quyết định rẻ nhất và có giá trị nhất trong toàn khối của tôi.** `write_json(raw_api_response, payload)` chạy ngay sau lời gọi API, trước cả bước parse. Nhờ đó (a) tôi kiểm chứng lại được mọi con số trong báo cáo này mà không gọi API lần nào nữa — chính cách này cho ra kết luận "0/72 item có `subject`"; (b) bước repair ở pha 2 có nguồn để tái tạo, đưa dataset về đúng 24/24 dòng và 12/12 check; (c) pipeline chạy lại được nhiều lần trên cùng corpus dù Crossref là nguồn sống. Nếu tôi chỉ trả về danh sách record trong bộ nhớ thì cả ba lợi ích trên đều mất.

2. **Về data quality/observability: chất lượng dữ liệu phải được đo ngay tại tầng nguồn, không đợi tới quality report.** Bộ 12 check ở khối 4 chạy trên frame *đã sạch*, nên nó không bao giờ thấy được rằng 0/72 item Crossref có trường `subject` — thông tin đó chỉ tồn tại ở payload thô. Trên báo cáo, `categories_joined` trông hoàn hảo (0/24 rỗng, 2.62 giá trị mỗi dòng), nhưng thực chất 100% giá trị đó đến từ nhánh fallback và mang ngữ nghĩa khác với tên cột. Đây là loại sai lệch mà không check nào ở hạ nguồn bắt được, vì dữ liệu *đúng hình dạng*.

3. **Về ảnh hưởng của data đến RAG agent: lỗi ở tầng nguồn không dừng lại ở tầng nguồn.** Một trường metadata vắng mặt (`subject`) đã đánh sập bước 6/10 của pipeline, ở một file mà tôi không viết. Ngược lại, việc mất 3 bản ghi trên corpus 24 tài liệu kéo `retrieval_hit_rate` xuống 0.2000 và làm agent trả lời sai *một cách trôi chảy* — không exception nào được ném ra trong suốt lần chạy corrupted. Với corpus nhỏ như thế này, mỗi bản ghi nặng khoảng 4% giá trị metric, nên độ đầy đủ của tầng nguồn không phải chuyện "nice to have".

### Nếu có thêm thời gian

**Cải thiện đề xuất: thêm một "source manifest" ghi lại các chỉ số của chính bước ingestion, để chất lượng tầng nguồn quan sát được thay vì phải suy ra từ hạ nguồn.**

Hiện tại `fetch_source_records()` chỉ ghi hai file dữ liệu và in vài dòng ra stdout; mọi thông tin về *quá trình lọc* biến mất khi terminal đóng. Muốn biết bao nhiêu item bị loại vì lý do gì, tôi phải viết script rời chạy lại trên payload đã lưu — đúng như tôi đã làm để viết báo cáo này.

Cách làm: ghi thêm `data/raw/source_manifest.json` ngay trong `fetch_source_records()`, gồm `query`, `filter`, `rows_requested`, `total_results`, `items_returned`, `records_valid`, `records_kept`, số item bị loại theo từng lý do (`dropped_missing_doi`, `dropped_short_abstract`, `dropped_non_latin`, `dropped_duplicate_doi`), `subject_coverage` (số item có trường `subject`), và `sha256` của `crossref_response.json`.

**Cách đo cải thiện** (có tiêu chí đạt/không đạt rõ ràng, chạy lại được):

1. Chạy `python script/run_phase1.py` với `REFRESH_SOURCE=1`. **Tiêu chí đạt:** `source_manifest.json` được sinh ra và các con số khớp đúng với những gì đo lại thủ công trên payload — với lần chạy hiện tại là `items_returned = 72`, `records_valid = 71`, `records_kept = 24`, `subject_coverage = 0`.
2. **Tiêu chí đạt về khả năng tái lập:** chạy `run_phase1.py` lần thứ hai mà không bật `REFRESH_SOURCE` thì `sha256` trong manifest không đổi, chứng minh pipeline đang dùng lại đúng snapshot cũ.
3. **Chỉ số theo dõi:** `subject_coverage`. Hiện tại là 0/72 và toàn bộ `categories_joined` đến từ fallback. Nếu con số này lớn hơn 0 ở một lần chạy sau, nghĩa là ngữ nghĩa của cột `categories` đã thay đổi giữa hai lần chạy — điều mà hiện nay hoàn toàn không ai phát hiện được.
4. **Chỉ số theo dõi thứ hai:** tỷ lệ loại của bộ lọc client, hiện là 1/72 ≈ 1.4%. Nếu tỷ lệ này vượt 50% thì hệ số over-fetch ×3 không còn đủ an toàn và phải nâng lên — hiện tại không có cách nào biết trước điều đó cho tới khi pipeline gãy.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [ ] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [ ] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [ ] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [ ] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [ ] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [ ] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Trần Hoài Nam
**Ngày xác nhận:** 2026-08-06
