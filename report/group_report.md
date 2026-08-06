# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Khóa/Lớp         | K3 |
| Tên nhóm         | DingDong (4 thành viên) |
| Repository         | https://github.com/doandinhdong14-afk/K3_Day10_DingDong |
| Ngày hoàn thành | 2026-08-06 |

### Thành viên và phân công

Nhóm chia theo cấu hình 4 người khuyến nghị trong [`README.md`](README.md) mục 5, với một điều chỉnh: khối 5 (`reporting.py`) được tách khỏi Observability owner và chuyển sang nhóm trưởng, vì cả ba file report đều phải đọc output của hai flow do nhóm trưởng điều phối. Observability owner vì vậy giữ nguyên khối 4 (`quality.py`).

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu | Báo cáo cá nhân |
| --: | --- | --- | --- | --- | --- |
| 1 | Trần Hoài Nam | 2A202601751 | Source owner | Khối 1 — `src/ingestion/crossref.py`; artifact `data/raw/crossref_response.json`, `crossref_records.json` | [`2A202601751_TranHoaiNam.md`](2A202601751_TranHoaiNam.md) |
| 2 | Dương Hải Long | 2A202601607 | Data model & evaluation-set owner | Khối 2, 3 — `src/ingestion/cleaning.py`, `src/evaluation/testset.py`; artifact `data/clean/papers_clean.{csv,json}`, `data/eval/test_set.json` | [`2A202601607_DuongHaiLong.md`](2A202601607_DuongHaiLong.md) |
| 3 | Đặng Quang Minh | 2A202601459 | Observability owner | Khối 4 — `src/observability/quality.py`; artifact `data/quality/*_quality.json`, `freshness_report*.json` | [`2A202601459_DangQuangMinh.md`](2A202601459_DangQuangMinh.md) |
| 4 | **Đoàn Đình Đông** | **2A202601900** | **Nhóm trưởng** — reporting, orchestration & corruption owner | Khối 5, 6, 7 — `src/observability/reporting.py`, `src/pipelines/phase1.py`, `src/retrieval/index.py`, `src/ingestion/corruption.py`, `src/pipelines/corruption_flow.py`; thêm `app/dashboard.py` (ngoài yêu cầu) và điều phối tích hợp | [`2A202601900_DoanDinhDong.md`](2A202601900_DoanDinhDong.md) |

## 2. Tóm tắt kết quả

**Tóm tắt của nhóm:**

Nhóm đã hoàn thành cả hai pha của bài lab và chạy end-to-end trên dữ liệu thật. Pha 1 lấy 72 item từ Crossref REST API, giữ lại 24 raw record, làm sạch thành một bảng 24 dòng × 16 cột, embed bằng `sentence-transformers/all-MiniLM-L6-v2`, nạp vào ChromaDB (cosine, collection `papers-baseline`) và đánh giá trên test set 20 câu hỏi thuộc 4 loại (authors/date/categories/summary) trải trên 5 bài báo. Baseline đạt `retrieval_hit_rate` = 1.0000, `mean_token_f1` = 1.0000, `judge_accuracy` = 1.0000, `mean_judge_score` = 5.0000, data quality 12/12 check pass và freshness 0/24 dòng stale. Pha 2 tạo 6 loại corruption có chủ đích (xóa 3 bài mới nhất, làm rỗng summary, nhồi nhiễu, cắt title, lùi ngày 3 năm, nhân bản dòng) rồi đánh giá lại trên **cùng** test set. Corruption làm số dòng còn 23, quality tụt xuống 7/12 check pass, freshness chuyển sang NOT fresh (4/23 dòng stale) và bốn metric của agent giảm còn 0.8000 / 0.6684 / 0.6500 / 3.6000. Repair dựng lại dataset từ raw snapshot đáng tin cậy `data/raw/crossref_records.json` (không vá bảng đã hỏng) và đưa toàn bộ bốn metric, 12/12 quality check và freshness trở về đúng mức baseline. Giới hạn lớn nhất còn lại: lớp QA là một keyword router chứ không phải reader sinh ngôn ngữ, nên baseline hoàn hảo là do thiết kế, và corpus chỉ có 24 tài liệu.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref API
    -> raw response/raw records
    -> cleaning và data modeling
    -> embedding + ChromaDB index
    -> evaluation baseline
    -> quality/freshness reports
    -> corruption
    -> re-index và re-evaluate
    -> repair từ dữ liệu nguồn
    -> comparison report
```

### Trách nhiệm của từng khối

| Khối             | Input          | Xử lý chính             | Output/artifact          | Owner          |
| ----------------- | -------------- | -------------------------- | ------------------------ | -------------- |
| Ingestion         | Crossref REST API `https://api.crossref.org/works` với `query` + `filter` từ `src/core/config.py` | `src/ingestion/crossref.py`: over-fetch `max_results × 3 = 72` rows, retry/backoff lũy thừa trên 429/500/502/503/504, bóc thẻ XML/HTML trong abstract, loại bài không phải chữ Latin và abstract < 80 ký tự, fallback `categories` sang venue/type/publisher | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` (24 record) | Trần Hoài Nam |
| Cleaning          | 24 `PaperRecord` từ raw snapshot | `src/ingestion/cleaning.py`: chuẩn hóa khoảng trắng, ép ngưỡng title ≥ 10 và summary ≥ 80 ký tự, giữ `published`/`updated` ở dạng chuỗi, hai lượt dedupe (theo `paper_id` rồi theo title viết thường), tính `age_days`/`author_count`/`title_chars`/`summary_chars`, dựng `text_for_embedding` | `data/clean/papers_clean.csv`, `data/clean/papers_clean.json` (24 dòng × 16 cột) | Dương Hải Long |
| Embedding/index   | Cột `text_for_embedding` của clean frame | `src/retrieval/index.py`: MiniLM-L6-v2, ChromaDB `PersistentClient`, `create_collection(configuration={"hnsw": {"space": "cosine"}})`, id tài liệu = `"{paper_id}::{index}"`, metadata chỉ chứa giá trị nguyên thủy | `data/embeddings/papers_embeddings.json` (manifest), `data/chroma/` (collection `papers-baseline`) | Đoàn Đình Đông |
| Evaluation        | Clean frame + `data/eval/test_set.json` | `src/evaluation/testset.py` sinh 4 câu hỏi × 5 bài báo; `src/evaluation/metrics.py` chấm `retrieval_hit_rate`, `mean_token_f1` và LLM-as-judge (`score` 1–5 + `correct`) | `data/results/baseline_metrics.json`, `data/results/baseline_answers.json`, `data/results/agent_demo_answers.json` | Dương Hải Long (test set) + Đoàn Đình Đông (chạy evaluate) |
| Observability     | Clean/corrupted/repaired frame | `src/observability/quality.py`: 12 check trên 5 dimension (completeness, uniqueness, validity, consistency, freshness) + freshness report theo `age_days`; `src/observability/reporting.py` sinh markdown | `data/quality/*.json`, `data/reports/phase1_report.md` | Đặng Quang Minh (`quality.py`) + Đoàn Đình Đông (`reporting.py`) |
| Corruption/repair | `data/clean/papers_clean.json` (corrupt) và `data/raw/crossref_records.json` (repair) | `src/ingestion/corruption.py`: 6 loại corruption deterministic (không dùng RNG), offset lệch pha với stride của test set; repair chạy lại `load_raw_records` + `build_clean_dataframe` từ raw snapshot | `data/results/corruption_log.json`, `data/clean/papers_clean_corrupted.*`, `data/clean/papers_clean_repaired.*` | Đoàn Đình Đông |
| Orchestration     | Settings + artifact của pha trước | `script/run_phase1.py` → `src/pipelines/phase1.py` (10 bước); `script/run_corruption_flow.py` → `src/pipelines/corruption_flow.py` (10 bước, chặn chạy nếu thiếu artifact pha 1) | `data/results/{corrupted,repaired}_metrics.json`, `data/reports/corruption_report.md` | Đoàn Đình Đông |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER`             | `groq` |
| `LLM_MODEL`                | `openai/gpt-oss-20b` |
| Embedding model              | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | `max_results = 24` (API được gọi với `rows = 24 × 3 = 72` rồi mới lọc) |
| Retrieval `top_k`           | `4` |
| Freshness threshold          | `180` ngày |
| Random seed, nếu có        | Không có. Bước corruption hoàn toàn deterministic, không dùng RNG (`deterministic: true` trong `data/results/corruption_log.json`) |
| Vector store                 | ChromaDB persistent tại `data/chroma/`, khoảng cách cosine |
| Collection                   | `papers-baseline` / `papers-corrupted` / `papers-repaired` |
| `source_query`             | `agentic retrieval augmented generation large language model` |
| `source_filter`            | `from-pub-date:{hôm nay − 180 ngày},has-abstract:true` — lần chạy nộp bài là `from-pub-date:2026-02-07,has-abstract:true` |
| `RUN_RAGAS`                | Không bật (mặc định), nên khối `ragas` trong metrics ghi `skipped` |

> **Lưu ý về provider:** hai dòng `LLM_PROVIDER` và `LLM_MODEL` ở trên mô tả đúng lần chạy được nộp — đây cũng chính là giá trị mặc định trong `src/core/config.py` (`groq` / `openai/gpt-oss-20b`) và là giá trị `phase1_report.md` ghi lại. Groq là provider hạng nhất của project (`LLM_PROVIDER=groq`, `GROQ_API_KEY`, `GROQ_BASE_URL`); ngoài ra `config.py` còn hỗ trợ `openai`, `gemini`, `anthropic`, `openrouter`, `ollama` và `custom`. **Nếu chạy lại pipeline trên provider khác thì phải cập nhật lại đúng hai trường này** (và các chỗ nhắc tới provider/model ở mục 6 và mục 7), vì toàn bộ điểm judge đều do LLM đó sinh ra.

Không dán nội dung API key hoặc file `.env` vào báo cáo. File `.env` đã nằm trong `.gitignore`.

### Lệnh cài đặt

```bash
uv sync
```

Hoặc:

```bash
python -m pip install -e .
```

### Lệnh chạy

Baseline:

```bash
uv run python script/run_phase1.py
```

Hoặc với môi trường `pip` đã kích hoạt:

```bash
python script/run_phase1.py
```

Corruption flow:

```bash
uv run python script/run_corruption_flow.py
```

Hoặc với môi trường `pip` đã kích hoạt:

```bash
python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh             | Trạng thái                                    | Thời điểm chạy gần nhất | Bằng chứng                         |
| ----------------- | ----------------------------------------------- | ----------------------------- | ------------------------------------ |
| Baseline pipeline | Thành công (10/10 bước) | 2026-08-06 04:57:15 UTC (`generated_at` trong `data/reports/phase1_report.md`) | `data/raw/crossref_records.json`, `data/clean/papers_clean.csv`, `data/embeddings/papers_embeddings.json`, `data/eval/test_set.json`, `data/results/baseline_metrics.json`, `data/results/baseline_answers.json`, `data/quality/baseline_quality.json`, `data/quality/freshness_report.json`, `data/reports/phase1_report.md` |
| Corruption flow   | Thành công (10/10 bước) | 2026-08-06 04:58:19 UTC → 04:59:58 UTC (`generated_at` của `corruption_log.json` → `repaired_quality.json`) | `data/results/corruption_log.json`, `data/clean/papers_clean_corrupted.csv`, `data/results/corrupted_metrics.json`, `data/results/corrupted_answers.json`, `data/quality/corrupted_quality.json`, `data/quality/freshness_report_corrupted.json`, `data/clean/papers_clean_repaired.csv`, `data/results/repaired_metrics.json`, `data/quality/repaired_quality.json`, `data/quality/freshness_report_repaired.json`, `data/reports/corruption_report.md` |

Pipeline đã được chạy lại hai lần liên tiếp và cho ra **bộ số hoàn toàn giống nhau** ở cả bốn metric, 12 quality check và freshness report, xác nhận tính deterministic của corruption và của bước chấm điểm. Lưu ý phạm vi: thứ deterministic là các **con số**; riêng trường `judge.reasoning` (văn bản tự do do LLM sinh) có thể đổi cách diễn đạt giữa hai lần chạy mà không làm đổi `score` hay `correct` — xem chi tiết ở mục 9.

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính                | Giá trị                             |
| --------------------------- | ------------------------------------- |
| Source                      | Crossref REST API — `GET https://api.crossref.org/works` (`User-Agent` kèm mailto để dùng polite pool) |
| Query/filter                | `query=agentic retrieval augmented generation large language model`, `filter=from-pub-date:2026-02-07,has-abstract:true`, `rows=72` |
| Thời điểm lấy dữ liệu | Snapshot dùng cho bài nộp được đọc lại ở 2026-08-06 04:57 UTC (`data/raw/crossref_records.json`); pipeline chỉ gọi lại API khi thiếu file hoặc khi bật `REFRESH_SOURCE=1` |
| Số record nhận được    | API trả `total-results = 100934`, response chứa 72 item; sau khi lọc còn 71 item hợp lệ; cắt theo `max_results` giữ 24 record; cleaning giữ nguyên 24 dòng |
| Cơ chế retry/backoff      | Tối đa 5 lần thử, chờ 1s → 2s → 4s → 8s (nhân đôi sau mỗi lần), áp dụng cho HTTP 429/500/502/503/504 và mọi `requests.RequestException`; hết lượt thì raise `RuntimeError` kèm lỗi cuối |

### Raw và clean schema

Clean frame có đúng 16 cột (`data/clean/papers_clean.csv`, 24 dòng).

| Trường        | Kiểu dữ liệu | Bắt buộc?  | Ý nghĩa   | Xử lý khi thiếu/sai |
| --------------- | --------------- | ------------ | ----------- | ---------------------- |
| `paper_id` | string (DOI) | Có | Khóa chính, lấy từ trường `DOI` của Crossref | Không có DOI → loại record ngay ở bước parse; DOI trùng (không phân biệt hoa thường) → bỏ bản sau |
| `title` | string | Có | Tiêu đề đã bóc thẻ XML/HTML và gộp khoảng trắng | Rỗng hoặc < 10 ký tự → loại record; trùng title (viết thường) → giữ bản đầu |
| `summary` | string | Có | Abstract đã bóc markup, đã bỏ tiền tố "Abstract:"/"Summary:" | < 80 ký tự → loại record (áp dụng ở cả `crossref.py` và `cleaning.py`) |
| `authors_joined` | string | Có | Danh sách tác giả nối bằng `", "` — **cố ý nối sẵn** vì metadata ChromaDB không nhận list | Không có tác giả → chuỗi rỗng; `text_for_embedding` ghi `unknown` |
| `categories_joined` | string | Có | Chủ đề nối bằng `", "`; do Crossref không trả `subject` nên dùng fallback container-title / type / publisher | Không suy ra được giá trị nào → `uncategorized`. Thực tế 0/24 dòng phải dùng giá trị mặc định này |
| `primary_category` | string | Có | Phần tử đầu tiên của danh sách categories | Rỗng → lấy `categories[0]`, cuối cùng mới đến `uncategorized` |
| `published` | string `YYYY-MM-DD` | Có | Ngày xuất bản, ưu tiên `issued` → `published` → `created` | Không parse được ngày → loại record. **Giữ kiểu string** vì metadata ChromaDB từ chối `pandas.Timestamp` |
| `updated` | string `YYYY-MM-DD` | Có | Ngày `deposited`/`indexed` của Crossref | Thiếu hoặc hỏng → gán bằng `published`; cũng giữ kiểu string |
| `abs_url` | string | Có | URL landing page của bài báo | Thiếu → dựng `https://doi.org/{paper_id}` |
| `pdf_url` | string | Không | Link full-text nếu Crossref có khai báo | 7/24 dòng rỗng — giữ chuỗi rỗng, **không** loại record vì đây là trường tùy chọn |
| `comment` | string | Không | Chuỗi mô tả `"{type} in {container-title}"` | Không có venue → `unknown venue` |
| `age_days` | int | Có | `run_date − published` tính theo ngày; là đầu vào của freshness check | `published` luôn hợp lệ sau bước lọc nên luôn tính được |
| `author_count` | int | Có | Số tác giả sau khi khử trùng tên | Không có tác giả → `0` |
| `title_chars` | int | Có | `len(title)` — dùng cho check độ dài và check consistency | Luôn được tính lại từ `title` |
| `summary_chars` | int | Có | `len(summary)` — dùng cho check độ dài và check consistency | Luôn được tính lại từ `summary` |
| `text_for_embedding` | string | Có | Văn bản thực sự được embed (xem giải thích bên dưới) | Luôn dựng lại từ các cột đã làm sạch, không bao giờ rỗng (check `text_for_embedding_present`) |

### Quy tắc cleaning

Cột "Số record bị tác động" ghi rõ mẫu số: `/72` là trên các item Crossref trả về, `/24` là trên clean frame cuối cùng.

| Quy tắc                                 | Quality dimension liên quan | Số record bị tác động | Cách xác minh      |
| ---------------------------------------- | ---------------------------- | -------------------------: | -------------------- |
| Bóc thẻ XML/HTML, giải mã HTML entity và gộp khoảng trắng cho `title`/`summary` | Validity | 72/72 | So `data/raw/crossref_response.json` với `data/raw/crossref_records.json` |
| Loại record thiếu `DOI`, `title` hoặc ngày xuất bản | Completeness | 0/72 | Đếm lại trên raw response: 0 item vi phạm |
| Loại record có abstract < 80 ký tự | Completeness / Validity | 0/72 (filter `has-abstract:true` đã chặn trước) | `summary_chars` nhỏ nhất trong clean frame là 826 |
| Loại bài không phải chữ Latin (< 70% ký tự ASCII) | Validity | 1/72 | 72 item → 71 item hợp lệ sau bộ lọc |
| Bỏ DOI trùng ngay trong payload | Uniqueness | 0/72 | `paper_id_unique` pass 24/24 ở baseline |
| Cắt theo `max_results = 24` | Kiểm soát chi phí embedding | 47 record hợp lệ bị bỏ (71 → 24) | `raw_records = 24` trong `data/reports/phase1_report.md` |
| Fallback `categories` sang container-title / type / publisher khi Crossref không có `subject` | Completeness | 24/24 (đo được: **0/72 item** có trường `subject`) | `categories_joined` của mọi dòng đều là venue/type/publisher, ví dụ `SPE Journal, journal article, Society of Petroleum Engineers (SPE)`; trung bình 2.6 category/dòng |
| Loại record có `title` < 10 hoặc `summary` < 80 ký tự tại bước cleaning | Validity | 0/24 | `title_min_length` và `summary_min_length` pass 24/24 |
| Dedupe lượt 1 theo `paper_id` | Uniqueness | 0/24 | `paper_id_unique` pass |
| Dedupe lượt 2 theo title viết thường | Uniqueness | 0/24 | 24 dòng vào, 24 dòng ra |
| Sắp xếp `published` giảm dần rồi `paper_id` tăng dần | Consistency | 24/24 | Dòng đầu `2026-08-01`, dòng cuối `2026-02-12` trong `papers_clean.csv` |
| Giữ nguyên `pdf_url` rỗng (trường tùy chọn) | Completeness (không chặn) | 7/24 dòng có `pdf_url` rỗng | Đếm trực tiếp trên `papers_clean.csv` |

Giải thích cách nhóm tạo `text_for_embedding`, document ID và `age_days`:

- `text_for_embedding` được ghép từ 5 trường theo đúng một khuôn cố định: `Title: … \n Authors: … \n Categories: … \n Published: … \n Summary: …`. Ghép cả metadata (tác giả, chủ đề, ngày) vào chính văn bản được embed là có chủ đích: câu hỏi dạng "who authored…", "when was… published" hay "what categories…" nhờ đó có tín hiệu từ vựng ngay trong vector, thay vì chỉ dựa vào abstract. Khi tác giả hoặc chủ đề rỗng thì chuỗi ghi `unknown` / `uncategorized` để không tạo ra dòng cụt. Bước corruption cũng dựng lại chuỗi này bằng **đúng khuôn đó** sau khi làm hỏng dữ liệu, nhờ vậy index corrupted thực sự embed phần text đã hỏng chứ không phải text cũ.
- **Document ID:** khóa nghiệp vụ là `paper_id` (DOI). ID nạp vào ChromaDB là `record_id = "{paper_id}::{index}"` — có thêm chỉ số dòng vì frame corrupted cố ý chứa `paper_id` trùng, nếu dùng thẳng DOI làm ID thì Chroma sẽ ghi đè bản trùng và corruption "duplicate_rows" biến mất một cách âm thầm. Đối chiếu ground truth trong evaluation thì vẫn dùng `paper_id`.
- `age_days = run_date − published` (đơn vị ngày, `run_date` là thời điểm chạy pipeline theo UTC). Đây là cột nguồn duy nhất cho check `freshness_within_threshold` (`age_days > 180`) và cho toàn bộ freshness report (`max_age_days`, `mean_age_days`, `stale_ratio`).

## 6. Evaluation setup

| Thành phần                             | Cấu hình thực tế          |
| ---------------------------------------- | ----------------------------- |
| Số câu hỏi                            | 20 |
| Các `question_type`                    | `authors`, `date`, `categories`, `summary` — mỗi loại 5 câu, sinh từ 5 bài báo |
| Ground-truth document ID                 | `ground_truth_doc_ids = [paper_id]` của chính dòng sinh ra câu hỏi. 5 bài được chọn bằng cách lấy mẫu trải đều (`iloc[::step]`, `step = 24 // 5 = 4`) trên các bài "usable": `10.2118/234689-pa`, `10.3390/buildings16132637`, `10.21203/rs.3.rs-10012178/v1`, `10.22214/ijraset.2026.82233`, `10.1093/sleep/zsag091.0346`. `retrieval_hit` = true khi `paper_id` này nằm trong danh sách doc được truy hồi |
| Embedding model                          | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store/collection                  | ChromaDB persistent (`data/chroma/`), khoảng cách cosine; `papers-baseline`, `papers-corrupted`, `papers-repaired` |
| Retrieval `top_k`                       | 4 |
| LLM provider/model                       | `groq` / `openai/gpt-oss-20b`, dùng cho LLM-as-judge (`temperature=0.0`, structured output `score` 1–5 + `correct` + `reasoning`). **Phải cập nhật lại hai giá trị này nếu chạy lại trên provider khác, ví dụ Gemini hoặc OpenAI.** Trong lần chạy nộp bài, 0/20 câu ở cả ba trạng thái phải rơi về judge heuristic dự phòng — nghĩa là mọi điểm judge đều do LLM thật chấm |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json` (8509 bytes, 20 sample, id `q001`–`q020`) |

Giải thích vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:

Test set được sinh **một lần** từ dataset sạch rồi đóng băng. `src/pipelines/phase1.py` chỉ dựng lại test set khi file chưa tồn tại hoặc khi người chạy chủ động bật `REFRESH_TEST_SET=1`; `src/pipelines/corruption_flow.py` truyền thẳng `settings.paths.eval_testset` vào cả ba lần gọi `evaluate_pipeline`. Nếu sinh lại test set từ dữ liệu corrupted thì câu hỏi và ground truth sẽ được sinh **từ chính dữ liệu đã hỏng** — bài báo bị xóa sẽ không còn câu hỏi nào, summary rỗng sẽ trở thành ground truth "đúng", và metric sẽ đẹp lên một cách giả tạo trong khi dữ liệu thực sự tệ đi. Giữ nguyên test set là điều kiện để ba con số baseline/corrupted/repaired nằm trên cùng một thước đo, và cũng là cách duy nhất để chứng minh corruption gây hại thay vì chỉ làm thay đổi bài kiểm tra.

Một chi tiết quan trọng của thiết kế test set: câu chữ của câu hỏi được viết khớp với keyword router trong `src/retrieval/qa.py` ("who authored" / "when was" / "what categories" / còn lại là summary), và tiêu đề bài báo được bọc trong dấu nháy đơn để regex tra cứu chính xác của `qa.py` kích hoạt được. Vì vậy `testset.py` loại bỏ những bài có dấu nháy đơn trong tiêu đề hoặc có sẵn cụm từ định tuyến trong tiêu đề (đo được trên dataset này: 0 bài bị loại vì lý do đó, 24/24 bài đều usable).

## 7. Kết quả baseline

### Artifact checklist

Toàn bộ đường dẫn dưới đây đã được kiểm tra là tồn tại trên đĩa tại thời điểm viết báo cáo.

| Artifact                 | Đường dẫn thực tế                | Trạng thái | Ghi chú   |
| ------------------------ | -------------------------------------- | ------------ | ---------- |
| Raw response/records     | `data/raw/`                          | Có | `crossref_response.json` (72 item, ~1.07 MB) và `crossref_records.json` (24 record) |
| Cleaned dataset          | `data/clean/`                        | Có | `papers_clean.csv` + `papers_clean.json` (24 dòng × 16 cột); thư mục còn chứa bản `_corrupted` (23 dòng) và `_repaired` (24 dòng) |
| Embedding manifest/index | `data/embeddings/`                   | Có | 3 manifest (`papers_embeddings.json`, `_corrupted`, `_repaired`); index nhị phân nằm ở `data/chroma/` (`chroma.sqlite3` + thư mục HNSW) |
| Evaluation set           | `data/eval/`                         | Có | `test_set.json`, 20 câu hỏi |
| Baseline metrics         | `data/results/baseline_metrics.json` | Có | Kèm `baseline_answers.json` (20 câu trả lời đầy đủ) và `agent_demo_answers.json` (2 câu demo qua agent) |
| Quality/freshness        | `data/quality/`                      | Có | `baseline_quality.json`, `corrupted_quality.json`, `repaired_quality.json`, `freshness_report.json`, `freshness_report_corrupted.json`, `freshness_report_repaired.json`. Thư mục `data/quality/gx/` tồn tại nhưng rỗng — nhóm không dùng Great Expectations, bộ check được viết trực tiếp trong `src/observability/quality.py` |
| Baseline report          | `data/reports/phase1_report.md`      | Có | Sinh tự động lúc 2026-08-06 04:57:15 UTC; cùng thư mục có `corruption_report.md` |
| Đối chiếu câu trả lời  | `data/reports/answer_diff.md`        | Có | Sinh tự động bởi `generate_answer_diff_report()`. Đặt cạnh nhau **câu trả lời thật** của agent ở ba trạng thái cho từng câu hỏi: 7/20 câu đổi output khi dữ liệu hỏng, 7/7 câu quay về đúng sau repair. Đây là bằng chứng ở mức output, độc lập với các chỉ số tổng hợp |

### Baseline metrics

Nguồn: `data/results/baseline_metrics.json` (20 sample).

| Metric                 |       Giá trị | Diễn giải                             |
| ---------------------- | --------------: | --------------------------------------- |
| `retrieval_hit_rate` |     1.0000 | 20/20 câu truy hồi được đúng bài báo ground truth trong `top_k = 4`. Có phần đóng góp của bước tra cứu chính xác theo tiêu đề trong `qa.py`, nên đây là cận trên chứ không phải phép đo thuần túy của semantic search |
| `mean_token_f1`      |     1.0000 | Câu trả lời trùng khớp token với ground truth ở cả 20 câu (F1 nhỏ nhất trên từng câu cũng là 1.0000). Lý do: với dữ liệu sạch, router trả về đúng trường metadata đã dùng để sinh ground truth |
| `judge_accuracy`     |     1.0000 | LLM judge (`openai/gpt-oss-20b` qua Groq) đánh dấu `correct = true` cho 20/20 câu; 0 câu phải dùng judge heuristic dự phòng |
| `mean_judge_score`   |     5.0000 | Toàn bộ 20 câu được chấm 5/5 |
| Ragas, nếu có        | N/A | Không chạy. `data/results/baseline_metrics.json` ghi `"ragas": {"skipped": "Set RUN_RAGAS=1 to enable the slower Ragas pass."}`. Kết luận về chất lượng vì vậy chỉ dựa trên token-F1 và LLM judge |

Cần nói thẳng: bộ số 1.0000 / 1.0000 / 1.0000 / 5.0000 **không** chứng minh hệ thống mạnh. Nó là hệ quả của việc lớp trả lời là một keyword router đọc thẳng metadata, còn ground truth cũng được sinh từ chính metadata đó. Giá trị thật của baseline là làm mốc: mọi mức sụt sau đó đều quy được về dữ liệu chứ không về mô hình.

## 8. Data quality và freshness

### Quality checks

Nguồn: `data/quality/baseline_quality.json` — 12/12 check pass, `success = true`, `total_failed_rows = 0` trên 24 dòng.

| Check        | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline      | Bằng chứng |
| ------------ | ----------------- | ------------------ | ----------------------- | ------------ |
| `row_count` | completeness | `row_count >= 10` | Pass — `row_count = 24` | `data/quality/baseline_quality.json` |
| `paper_id_not_null` | completeness | mọi dòng có `paper_id` khác rỗng | Pass — 0/24 dòng rỗng | như trên |
| `paper_id_unique` | uniqueness | `paper_id` duy nhất trên toàn bộ dòng | Pass — 0/24 dòng lặp | như trên |
| `title_not_null` | completeness | mọi dòng có `title` khác rỗng | Pass — 0/24 dòng rỗng | như trên |
| `title_min_length` | validity | `title_chars >= 10` | Pass — 0/24 dòng vi phạm | như trên |
| `summary_not_empty` | completeness | mọi dòng có `summary` khác rỗng | Pass — 0/24 dòng rỗng | như trên |
| `summary_min_length` | validity | `summary_chars >= 80` | Pass — 0/24 dòng vi phạm | như trên |
| `text_for_embedding_present` | completeness | mọi dòng có `text_for_embedding` khác rỗng | Pass — 0/24 dòng rỗng | như trên |
| `freshness_within_threshold` | freshness | không dòng nào có `age_days > 180` | Pass — 0/24 dòng quá hạn | như trên + `data/quality/freshness_report.json` |
| `published_format_valid` | validity | `published` khớp `YYYY-MM-DD` | Pass — 0/24 dòng sai định dạng | `data/quality/baseline_quality.json` |
| `title_chars_consistent` | consistency | `title_chars == len(title)` | Pass — 0/24 dòng lệch | như trên |
| `summary_chars_consistent` | consistency | `summary_chars == len(summary)` | Pass — 0/24 dòng lệch | như trên |

### Freshness

| Thuộc tính               | Giá trị                           |
| -------------------------- | ----------------------------------- |
| Freshness được đo tại | Clean dataset (`data/clean/papers_clean.json`), qua cột `age_days`; báo cáo ghi ra `data/quality/freshness_report.json` |
| Timestamp mới nhất       | `latest_published = 2026-08-01` (bài cũ nhất `oldest_published = 2026-02-12`) |
| Ngưỡng freshness         | 180 ngày (`freshness_threshold_days`) |
| Trạng thái baseline      | Fresh (`is_fresh = true`) |
| Lý do                     | `stale_rows = 0 / 24`, `stale_ratio = 0.0`, `max_age_days = 175` vẫn dưới ngưỡng 180, `min_age_days = 5`, `mean_age_days = 83.33`. Dữ liệu mới là do `source_filter` đã chặn `from-pub-date` đúng bằng mốc 180 ngày trước ngày chạy, nên corpus không thể chứa bài cũ hơn ngưỡng ngay từ đầu |

## 9. Corruption scenarios và repair

Nguồn: `data/results/corruption_log.json` — 24 dòng vào, 23 dòng ra, `total_affected_rows = 18` (không tính bước dựng lại `text_for_embedding` vì bước này chạm mọi dòng). Mỗi loại corruption được canh offset lệch pha với stride của test set nên **chạm đúng một bài báo đang được chấm điểm**, nhờ vậy tác động của từng loại đo được riêng rẽ.

| Corruption         | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair   |
| ------------------ | ---------- | ---------------------: | ------------------------ | --------------------- | -------------- |
| `drop_latest_records` | Xóa 3 dòng đầu frame (frame sắp xếp mới nhất trước) để giả lập incremental load thất bại | 3 — `10.2118/234689-pa`, `10.1007/s10278-026-02086-9`, `10.21203/rs.3.rs-10178277/v1` | `row_count` giảm, freshness mất mốc mới nhất | **Nặng nhất.** Bài `10.2118/234689-pa` nằm trong test set → 4 câu `q001`–`q004` đều `retrieval_hit = false`, judge chấm 1 điểm, `correct = false`. Đây là toàn bộ phần sụt của `retrieval_hit_rate` (16/20 = 0.8000). `latest_published` lùi từ `2026-08-01` về `2026-07-03`. Lưu ý: `row_count` vẫn PASS vì ngưỡng chỉ là ≥ 10 | Dựng lại frame từ `data/raw/crossref_records.json` → 3 bài quay lại |
| `blank_summary` | Đặt `summary = ""` và `summary_chars = 0` tại các vị trí 1, 6, 11 | 3 — `10.3390/buildings16132637`, `10.21203/rs.3.rs-9882260/v1`, `10.32473/flairs.39.1.141782` | `summary_not_empty` FAIL, `summary_min_length` FAIL | Đúng như kỳ vọng: 2 check FAIL, mỗi check 3 dòng. Câu `q008` (bài `10.3390/buildings16132637`) trả về chuỗi rỗng → `token_f1 = 0`, judge 1/5, dù `retrieval_hit` vẫn true | Dựng lại từ raw snapshot |
| `inject_noise` | Nối 153 ký tự rác (`LOREM IPSUM DOLOR ###### CORRUPTED PAYLOAD @@@@@@. ` × 3) vào **đầu** `summary` tại các vị trí 5, 10, 15 | 3 — `10.21203/rs.3.rs-10012178/v1`, `10.21203/rs.3.rs-9770645/v1`, `10.70121/001c.158711` | Kỳ vọng ban đầu: `summary_chars_consistent` sẽ bắt được | **Không check nào bắt được.** Vì corruption cập nhật luôn `summary_chars` nên check consistency vẫn PASS, summary vẫn dài hơn 80 ký tự nên hai check độ dài cũng PASS. Chỉ evaluation phát hiện: `q012` trả về đúng chuỗi rác (`first_sentence` cắt trúng câu rác đứng đầu) → `token_f1 = 0`, judge 1/5 | Dựng lại từ raw snapshot |
| `truncate_title` | Cắt `title` còn 8 ký tự đầu tại các vị trí 9, 14, 19 (`"Hybrid G"`, `"Retrieva"`, `"Developm"`) | 3 — `10.22214/ijraset.2026.82233`, `10.20944/preprints202604.0339.v1`, `10.1097/hc9.0000000000000895` | `title_min_length` FAIL (8 < ngưỡng 10) | Quality bắt đúng: `title_min_length` FAIL 3 dòng. **Nhưng metric của agent không đổi**: 4 câu `q013`–`q016` của bài `10.22214/ijraset.2026.82233` vẫn `retrieval_hit = true` và `token_f1 = 1.0000`. Lý do: tra cứu chính xác theo tiêu đề trong `qa.py` trượt, song semantic search vẫn xếp bài đó hạng 1 nhờ `text_for_embedding` còn nguyên tác giả/chủ đề/summary | Dựng lại từ raw snapshot |
| `stale_dates` | Lùi `published`/`updated` 3 năm và cộng 1095 vào `age_days` tại các vị trí 2, 7, 13, 18 | 4 — `10.21079/11681/50309`, `10.52060/juptik.v4i1.4318`, `10.1093/sleep/zsag091.0346`, `10.35314/3y9hy151` | `freshness_within_threshold` FAIL, freshness report chuyển NOT fresh | Đúng như kỳ vọng: 4/23 dòng stale, `is_fresh = false`, `max_age_days` 175 → 1256, `mean_age_days` 83.33 → 278.70, `stale_ratio = 0.1739`. Câu `q018` trả `2023-05-01` thay vì `2026-05-01` → `token_f1 = 0`, judge 1/5. `published_format_valid` vẫn PASS vì ngày sai nhưng đúng định dạng | Dựng lại từ raw snapshot |
| `duplicate_rows` | Nối thêm 2 bản sao y hệt của các dòng 0 và 5 vào cuối frame | 2 — `10.2196/preprints.106157`, `10.21203/rs.3.rs-10012178/v1` | `paper_id_unique` FAIL | Quality bắt đúng: `paper_id_unique` FAIL 2 dòng. **Không có metric agent nào thay đổi vì lý do này** — bản sao giống hệt bản gốc nên xếp hạng truy hồi không đổi | Dựng lại từ raw snapshot (dedupe hai lượt chạy lại) |
| `rebuild_embedding_text` | Dựng lại `text_for_embedding` cho toàn bộ 23 dòng bằng đúng khuôn của bước cleaning | 23 (mọi dòng — không tính vào `total_affected_rows`) | Không phải lỗi dữ liệu, mà là điều kiện để corruption thật sự đi vào index | Index `papers-corrupted` embed đúng phần text đã hỏng. Nếu bỏ bước này thì corruption chỉ nằm trong CSV còn vector vẫn sạch, và toàn bộ phép đo sẽ vô nghĩa | Không cần repair riêng; bản repaired dựng `text_for_embedding` từ dữ liệu sạch |

Corruption log:

- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có (5879 bytes, `generated_at = 2026-08-06T04:58:19Z`)
- Nhận xét: Log đủ dùng để tái hiện và để audit. Nó ghi `source_rows = 24`, `result_rows = 23`, `total_affected_rows = 18`, toàn bộ tham số (`drop_latest`, `blank_count`, `noise_token`, `truncate_chars`, `stale_years`, `duplicate_count`, `selection_stride`, các `offsets`) kèm cờ `deterministic: true`, và với **từng bước** ghi tên, mô tả, số dòng bị tác động, danh sách `paper_id` cụ thể và chi tiết riêng (vị trí dòng, tiêu đề mới sau khi cắt, cặp ngày `from`/`to` khi lùi ngày). Từ log này có thể chỉ đích danh câu hỏi nào trong test set bị ảnh hưởng mà không cần chạy lại pipeline.

Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy thay vì chỉ che kết quả lỗi:

Bước repair trong `src/pipelines/corruption_flow.py` **không chạm vào frame corrupted**. Nó gọi `load_raw_records(settings.paths.raw_records_json)` để đọc lại snapshot thô `data/raw/crossref_records.json` — file được ghi ở pha 1 ngay sau khi gọi Crossref và không hề bị bước corruption sửa — rồi chạy lại đúng `build_clean_dataframe()` mà baseline đã dùng. Nghĩa là dataset repaired được **tái tạo từ nguồn**, không phải được vá bằng cách điền lại ô trống hay lọc bỏ dòng xấu. Cách này quan trọng vì vá tại chỗ chỉ sửa được những lỗi mình biết trước; những lỗi bộ check không bắt được (điển hình là `inject_noise` ở trên — 12/12 check đều im lặng) sẽ sống sót qua bước vá và tiếp tục đầu độc index. Bằng chứng cho thấy repair là tái tạo thật chứ không phải làm đẹp số: `data/clean/papers_clean_repaired.csv` trùng khít từng byte với `data/clean/papers_clean.csv` (cùng 103.200 bytes, cùng MD5 `8fd54f38e963a48ab8881b4a8dfe3854`). Với `data/results/repaired_answers.json` (199.149 bytes) so với `data/results/baseline_answers.json` (199.075 bytes): hai file **không** trùng byte, nhưng toàn bộ phần xác định kết quả thì trùng khớp tuyệt đối — 20/20 câu giống nhau ở `answer`, `retrieval_hit`, `token_f1` và `retrieved_doc_ids`. Khác biệt duy nhất nằm ở câu chữ tự do trong `judge.reasoning` của 5 câu (`q004`, `q005`, `q007`, `q015`, `q016`), tức là do LLM judge diễn đạt lại ở lần gọi thứ hai chứ không phải do dữ liệu khác nhau; điểm `score` và cờ `correct` của cả 20 câu vẫn y hệt (5/5 và `true`).

## 10. So sánh baseline, corrupted và repaired

Nguồn: `data/results/{baseline,corrupted,repaired}_metrics.json`, `data/quality/*.json`.

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét   |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ------------ |
| `retrieval_hit_rate`   |      1.0000 |       0.8000 |      1.0000 |                      −0.2000 |             +0.2000 (về đúng baseline) | Đúng 4 câu trượt, tất cả thuộc bài `10.2118/234689-pa` bị xóa ở bước `drop_latest_records`. Không có bài nào bị trượt vì lý do khác |
| `mean_token_f1`        |      1.0000 |       0.6684 |      1.0000 |                      −0.3316 |             +0.3316 (về đúng baseline) | 7/20 câu tụt: 4 câu do mất bài, 1 do summary rỗng (`q008`), 1 do nhiễu (`q012`), 1 do lùi ngày (`q018`) |
| `judge_accuracy`       |      1.0000 |       0.6500 |      1.0000 |                      −0.3500 |             +0.3500 (về đúng baseline) | Đúng 13/20 câu được judge chấm `correct`; 7 câu sai trùng khớp với 7 câu tụt F1 ở trên |
| `mean_judge_score`     |      5.0000 |       3.6000 |      5.0000 |                      −1.4000 |             +1.4000 (về đúng baseline) | 13 câu giữ 5/5; 7 câu còn lại đều bị chấm 1/5 — không có câu nào rơi vào mức điểm trung gian |
| Quality checks pass/fail |      12/12 pass |       7/12 pass (5 FAIL) |      12/12 pass |                      −5 check | +5 check (về đúng baseline) | 5 check FAIL: `paper_id_unique` (2 dòng), `title_min_length` (3), `summary_not_empty` (3), `summary_min_length` (3), `freshness_within_threshold` (4). Tổng `total_failed_rows` 0 → 15 → 0 |
| Freshness status         |      Fresh (0/24 stale) |       NOT fresh (4/23 stale) |      Fresh (0/24 stale) |                      `is_fresh` true → false | `is_fresh` về true | `max_age_days` 175 → 1256 → 175; `mean_age_days` 83.33 → 278.70 → 83.33; `latest_published` `2026-08-01` → `2026-07-03` → `2026-08-01` |
| Số dòng dataset       |      24 |       23 |      24 |                      −1 (xóa 3, thêm 2 bản sao) | +1 | `source_rows = 24`, `result_rows = 23` trong corruption log |

Nêu ít nhất hai kết luận có quan hệ nhân quả được hỗ trợ bởi artifacts:

1. **Mất bản ghi → freshness và completeness suy giảm → sập cả retrieval lẫn answer metric.** `drop_latest_records` xóa `10.2118/234689-pa` (`corruption_log.json`) → `freshness_report_corrupted.json` ghi `latest_published` lùi từ `2026-08-01` về `2026-07-03` → trong `corrupted_answers.json`, cả bốn câu `q001`–`q004` có `retrieval_hit = false` (bài đơn giản không còn trong index) → `retrieval_hit_rate` rơi từ 1.0000 xuống 0.8000 và cả bốn câu đó đều bị judge chấm 1 điểm. Đây là chuỗi nhân quả duy nhất làm dịch chuyển `retrieval_hit_rate`.
2. **Repair từ nguồn → quality và freshness hồi phục → metric của agent hồi phục theo.** `corruption_flow.py` dựng lại frame từ `data/raw/crossref_records.json` → `repaired_quality.json` trở lại 12/12 check pass với `total_failed_rows = 0` và `freshness_report_repaired.json` trở lại `is_fresh = true`, `stale_rows = 0/24` → `repaired_metrics.json` trở lại 1.0000 / 1.0000 / 1.0000 / 5.0000, và `repaired_answers.json` khớp với `baseline_answers.json` ở toàn bộ 20 câu trên `answer`, `retrieval_hit` và `token_f1` (chỉ khác câu chữ `judge.reasoning` ở 5 câu). Hồi phục đạt 100% chứ không phải một phần.
3. **Lùi ngày → freshness FAIL → sai nội dung câu trả lời, trong khi check định dạng vẫn im lặng.** `stale_dates` đẩy `10.1093/sleep/zsag091.0346` từ `2026-05-01` về `2023-05-01` → `freshness_within_threshold` FAIL 4/23 dòng và `is_fresh = false` → câu `q018` trả lời `2023-05-01` trong khi ground truth là `2026-05-01`, `token_f1 = 0`, judge 1/5. Đáng chú ý: `published_format_valid` vẫn PASS — dữ liệu sai nhưng **hợp lệ về hình thức**, nên chỉ chiều freshness mới bắt được lỗi này.
4. **Có corruption làm hỏng quality nhưng không làm suy giảm metric, và ngược lại.** Hai trường hợp này được nêu ra vì số liệu không cho phép kết luận "có tác động":
   - `truncate_title` và `duplicate_rows` làm 2 check FAIL (`title_min_length` 3 dòng, `paper_id_unique` 2 dòng) nhưng **không** làm dịch chuyển bất kỳ metric nào của agent — bốn câu `q013`–`q016` của bài bị cắt tiêu đề vẫn đạt `retrieval_hit = true` và `token_f1 = 1.0000`, vì semantic search dựa trên `text_for_embedding` (còn nguyên tác giả, chủ đề, summary) chứ không chỉ dựa vào tiêu đề.
   - Ngược lại, `inject_noise` **không bị bất kỳ check nào trong 12 check bắt được** (corruption cập nhật luôn `summary_chars` nên check consistency vẫn PASS) nhưng lại làm câu `q012` trả về nguyên chuỗi rác, `token_f1 = 0`, judge 1/5. Giả thuyết của nhóm — rằng check consistency sẽ bắt được nhiễu — đã bị chính artifact bác bỏ; cách kiểm tra là đối chiếu `corrupted_quality.json` (12 check, chỉ 5 FAIL, không có check nào liên quan tới nội dung summary bị nhiễu) với `corrupted_answers.json` (`q012`). Kết luận: bộ check hiện tại đo *hình dạng* dữ liệu chứ chưa đo *nội dung*, nên quality report và evaluation là hai lưới lọc bổ sung cho nhau, không thay thế nhau.

## 11. Vấn đề tích hợp quan trọng

Vấn đề chính: **Crossref không bao giờ trả về trường `subject`, làm gãy toàn bộ nhánh câu hỏi `categories`.**

- **Triệu chứng:** Khi ingestion mới chỉ đọc `item["subject"]` để lấy chủ đề bài báo, mọi record đều có `categories = []`. Hậu quả dây chuyền: `categories_joined` rỗng trên 24/24 dòng → hàm `_is_usable()` trong `src/evaluation/testset.py` (yêu cầu `authors_joined`, `categories_joined` và `summary` đều khác rỗng) loại sạch mọi bài → `build_test_set()` ném `ValueError: Khong co paper nao du dieu kien de tao cau hoi.` và pha 1 dừng ngay tại bước 6. Nếu nới điều kiện đó ra thay vì sửa gốc thì 5/20 câu hỏi (loại `categories`, tức 25% test set) sẽ có ground truth là chuỗi rỗng, và `token_f1` của chúng bị ép về 0 theo đúng định nghĩa trong `_token_f1` (`if not ref_tokens: return 0.0`) — nghĩa là metric sẽ tố cáo một lỗi dữ liệu không tồn tại.
- **Nguyên nhân:** `subject` là trường tùy chọn trong metadata Crossref, chỉ một số nhà xuất bản khai báo. Đo trực tiếp trên snapshot đã lưu `data/raw/crossref_response.json`: **0 trên 72 item** có trường `subject`. Đây không phải lỗi ngẫu nhiên hay lỗi mạng, mà là một khác biệt hợp đồng dữ liệu giữa Crossref và giả định ban đầu của pipeline (giả định vốn được mượn từ arXiv, nơi `categories` luôn có).
- **Cách xử lý:** Thêm chuỗi fallback trong `_format_categories()` (`src/ingestion/crossref.py`): nếu `subject` rỗng thì suy chủ đề từ `container-title` (tên tạp chí/hội nghị) → `type` (ví dụ `journal-article`, `posted-content`) → `publisher`, khử trùng lặp theo thứ tự xuất hiện, và chỉ khi cả ba đều rỗng mới trả `["uncategorized"]`. `primary_category` lấy phần tử đầu của danh sách này. Chủ đề vì thế mô tả *nơi công bố* thay vì *lĩnh vực học thuật* — đây là một đánh đổi có ý thức, và cần được ghi rõ để người đọc không hiểu nhầm ngữ nghĩa của cột.
- **Cách xác minh:** Chạy `uv run python script/run_phase1.py` rồi kiểm tra `data/clean/papers_clean.csv`: 0/24 dòng có `categories_joined` rỗng, 0/24 dòng rơi về giá trị mặc định `uncategorized`, trung bình 2.6 category mỗi dòng, ví dụ `SPE Journal, journal article, Society of Petroleum Engineers (SPE)`. `data/eval/test_set.json` sinh đủ 20 câu hỏi với 5 câu loại `categories`. Trong `data/results/baseline_answers.json`, năm câu `q003`, `q007`, `q011`, `q015`, `q019` đều có `token_f1 = 1.0` và judge 5/5.

Hai vấn đề tích hợp khác cũng đã gặp thật và đang được xử lý trong code (ghi lại ngắn để không lặp lại ở lần chạy sau):

- **ChromaDB từ chối metadata dạng list và `Timestamp`.** Collection chỉ nhận giá trị nguyên thủy, nên `authors` và `categories` phải được nối sẵn thành chuỗi (`authors_joined`, `categories_joined`) ngay từ bước cleaning, còn `published`/`updated` phải giữ nguyên kiểu string `YYYY-MM-DD` thay vì đổi sang `pandas.Timestamp`. Ràng buộc này lan cả sang bước corruption: `_shift_year_back()` được viết để **luôn** trả về string, nếu không thì frame corrupted sẽ không index được và cả pha 2 sụp đổ.
- **Câu chữ của test set phải khớp keyword router trong `qa.py`.** `_extract_answer()` định tuyến bằng các cụm "who authored" / "list the authors" / "when was" / "publication date" / "published on" / "what categories", còn lại rơi vào nhánh summary; ngoài ra `answer_question()` dùng regex `'([^']+)'` để tra cứu chính xác theo tiêu đề. Vì vậy `testset.py` phải sinh câu hỏi bằng đúng các cụm đó, bọc tiêu đề trong dấu nháy đơn, và loại những bài có dấu nháy đơn hoặc có sẵn cụm định tuyến trong tiêu đề (trên dataset này: 0 bài bị loại, 24/24 usable). Nếu đổi cách diễn đạt câu hỏi mà không đổi router, câu hỏi sẽ rơi nhầm nhánh và `retrieval_hit_rate` cùng `token_f1` sụt ngay mà không hề có lỗi dữ liệu nào.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng   | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| Lớp trả lời trong `src/retrieval/qa.py` là **keyword router đọc thẳng metadata**, không phải reader sinh ngôn ngữ | Baseline đạt 1.0000/1.0000/1.0000/5.0000 gần như **do thiết kế**: ground truth được sinh từ chính các trường mà router trả về. Metric vì thế đo được "dữ liệu có đúng không" nhưng gần như không đo được "mô hình đọc hiểu tốt không" | Thay `_extract_answer()` bằng một reader sinh câu trả lời từ context truy hồi, chạy lại cùng test set và báo cáo baseline mới; kỳ vọng baseline tụt xuống dưới 1.0 và chênh lệch baseline−corrupted trở nên có ý nghĩa hơn |
| Corpus chỉ có **24 tài liệu**, test set 20 câu trên 5 bài | Mỗi câu hỏi nặng 5% giá trị metric, nên một bài bị xóa đã kéo `retrieval_hit_rate` đi 0.2000. `top_k = 4` trên 24 tài liệu là điều kiện quá dễ cho retrieval | Nâng `max_results` lên 100–200, sinh test set 60–100 câu, chạy lại và so khoảng dao động của metric giữa các lần chạy |
| Bộ 12 quality check chỉ đo **hình dạng** dữ liệu (rỗng, độ dài, trùng, định dạng, tuổi), không đo nội dung | Đã đo được: `inject_noise` làm hỏng câu trả lời `q012` nhưng **không check nào FAIL**. Dữ liệu có thể "sạch" theo báo cáo mà vẫn đầu độc agent | Bổ sung check nội dung: tỷ lệ ký tự không phải chữ/số trong `summary`, phát hiện đoạn lặp, so độ tương đồng giữa `summary` và `title`; kiểm chứng bằng cách chạy lại corruption flow và xác nhận `inject_noise` bị bắt |
| LLM judge chạy trên **free tier**, dễ dính rate limit | Nếu bị chặn, `_judge_answer()` âm thầm rơi về judge heuristic dựa trên token-F1 → `judge_accuracy` mất tính độc lập với `mean_token_f1`. Lần chạy nộp bài may mắn có 0/20 câu phải dùng fallback ở cả ba trạng thái, nhưng đây không phải bảo đảm | Ghi thẳng số câu dùng fallback vào file metrics (hiện chỉ thấy được khi đọc `reasoning` trong file answers), và thêm retry/backoff cho lời gọi judge |
| Crossref là **nguồn sống**, `source_filter` lại tính theo `hôm nay − 180 ngày` | Mỗi nhóm (và mỗi lần chạy cách nhau vài ngày) sẽ lấy về tập bài báo khác nhau, nên tuyệt đối không thể so số tuyệt đối giữa các nhóm. Việc pipeline ưu tiên đọc lại `data/raw/crossref_records.json` là thứ duy nhất giữ cho lần chạy này tái hiện được | Cố định snapshot bằng cách commit `data/raw/crossref_records.json` và chỉ refresh khi bật `REFRESH_SOURCE=1`; ghi thêm hash của snapshot vào báo cáo để đối chiếu |
| `categories` không phải chủ đề học thuật thật mà là venue/type/publisher (hệ quả của việc Crossref thiếu `subject`) | 5/20 câu hỏi loại `categories` thực chất đang kiểm tra "bài này đăng ở đâu", không phải "bài này thuộc lĩnh vực gì" | Bổ sung nguồn chủ đề khác (OpenAlex concepts, hoặc phân loại chủ đề bằng LLM), rồi so `categories_joined` mới với bản hiện tại trên cùng 24 bài |
| Ragas bị bỏ qua (`RUN_RAGAS` không bật) | Không có số đo faithfulness / context precision / context recall; kết luận chất lượng chỉ dựa trên token-F1 và một LLM judge duy nhất | Chạy `RUN_RAGAS=1` cho cả ba trạng thái và bổ sung 4 chỉ số đó vào bảng so sánh mục 10 |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác. <!-- Mục 1 đã điền đủ 4 thành viên, MSSV và đường dẫn repository. -->
- [x] Phân công khớp với module, artifact và kết quả thực tế. <!-- Cột Owner ở mục 3 đã điền; mỗi owner đối chiếu được với báo cáo cá nhân tương ứng. -->
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp. <!-- Đã chạy lại hai lần liên tiếp, kết quả trùng khớp hoàn toàn. -->
- [x] Baseline, corrupted và repaired dùng cùng evaluation set. <!-- Cả ba lần gọi evaluate_pipeline đều trỏ vào data/eval/test_set.json. -->
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được. <!-- Đã kiểm tra từng đường dẫn nêu trong mục 7. -->
- [ ] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng. <!-- 4 file <MSSV>_HoTen.md đã có đủ nội dung; còn chờ từng thành viên tự đọc lại và tick mục 10 trong báo cáo của mình. report/individual_report.md giữ nguyên làm template gốc. -->
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh. <!-- .env nằm trong .gitignore; báo cáo chỉ nêu TÊN biến môi trường, không nêu giá trị. -->
