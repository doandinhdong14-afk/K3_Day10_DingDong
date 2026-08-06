# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Đặng Quang Minh |
| MSSV | 2A202601459 |
| Khóa/Lớp | K3 |
| Tên nhóm | DingDong |
| Vai trò chính | Pipeline owner — toàn bộ 8 module `TODO(student)`  |
| Repository | https://github.com/doandinhdong14-afk/K3_Day10_DingDong/tree/Minh |
| Ngày hoàn thành | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Raw ingestion | `src/ingestion/crossref.py`: `parse_crossref_payload`, `fetch_source_records`, `load_raw_records`, `effective_source_filter` | Crossref REST API | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Hoàn thành |
| Cleaning & data modeling | `src/ingestion/cleaning.py`: `build_clean_dataframe`, `build_text_for_embedding`, `compute_age_days`, `load_clean_dataframe` | `list[PaperRecord]` | `data/clean/papers_clean.csv`, `papers_clean.json` (16 cột) | Hoàn thành |
| Evaluation set | `src/evaluation/testset.py`: `build_test_set` | Cleaned dataframe | `data/eval/test_set.json` (20 câu hỏi) | Hoàn thành |
| Data quality & freshness | `src/observability/quality.py`: `run_data_quality_checks`, `build_freshness_report` | Dataframe bất kỳ (baseline/corrupted/repaired) | `data/quality/*_quality.json`, `data/quality/gx/*_gx_validation.json`, `freshness_report*.json` | Hoàn thành |
| Reporting | `src/observability/reporting.py`: `generate_phase1_report`, `generate_corruption_report`, `describe_judge_mode` | Metrics + quality + freshness dicts | `data/reports/phase1_report.md`, `corruption_report.md` | Hoàn thành |
| Corruption | `src/ingestion/corruption.py`: `corrupt_clean_dataframe` | Cleaned dataframe | `data/clean/papers_clean_corrupted.*`, `data/results/corruption_log.json` | Hoàn thành |
| Baseline orchestration | `src/pipelines/phase1.py`: `main` | Settings + tất cả module trên | Toàn bộ artifact Pha 1 | Hoàn thành |
| Corruption & repair orchestration | `src/pipelines/corruption_flow.py`: `main` | Baseline artifacts + raw records | Corrupted/repaired metrics, comparison report | Hoàn thành |

Phần **không** thuộc phạm vi của tôi (starter đã cung cấp sẵn, tôi chỉ đọc và sử dụng đúng contract, không sửa):
`src/core/config.py`, `src/core/utils.py`, `src/retrieval/*` (embeddings, index, llm, agent, qa).

Hai thay đổi nằm ngoài phần `TODO(student)` mà tôi có thực hiện, xin nêu rõ (cả hai đều giữ nguyên chữ ký của `_judge_answer` và `evaluate_pipeline`, và giữ nguyên hành vi mặc định):

1. `src/evaluation/metrics.py` — tách nhánh heuristic sẵn có thành `_heuristic_verdict()`, thêm **retry có backoff cho lỗi rate limit** trong `_judge_answer()` (tôn trọng `retryDelay` mà provider trả về), và thêm công tắc `JUDGE_MODE=heuristic` để ép cả ba lượt evaluate dùng chung heuristic khi không có đủ quota LLM.
2. `src/pipelines/phase1.py` — agent demo có retry tương tự và lưu kết quả theo từng câu, để một câu bị rate limit không xoá mất các câu đã trả lời được.

Lý do và bằng chứng ở mục 8.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Gỡ blocker cài đặt trên macOS Intel | Toàn nhóm — bước `pip install -e .` | Thêm `constraints.txt` ghim `cryptography<49`, `torch==2.2.2`, `numpy<2`, `transformers<5`; môi trường cài được và cả hai pipeline chạy end-to-end |
| Kiểm chứng tính so sánh được của metrics | Khối evaluation | Thêm `describe_judge_mode()` để report ghi rõ mỗi lần evaluate dùng LLM judge hay heuristic fallback |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Gọi Crossref có retry/backoff, parse JATS abstract, lưu raw response + raw records | `crossref.py`, `data/raw/` | 24 raw records có đủ DOI/title/abstract/ngày | `python script/run_phase1.py`, đọc `data/raw/crossref_records.json` |
| Chuẩn hóa và loại bỏ record không dùng được, sinh `text_for_embedding` và `age_days` | `cleaning.py`, `data/clean/` | 24 clean row × 16 cột | Đọc `data/clean/papers_clean.csv` |
| Sinh evaluation set 4 loại câu hỏi, có ground-truth doc ID | `testset.py`, `data/eval/test_set.json` | 20 câu / 5 paper | Đọc `data/eval/test_set.json` |
| Bộ 9 data quality check chạy bằng Great Expectations | `quality.py`, `data/quality/` | Baseline PASS 9/9; corrupted FAIL 6/9 | Đọc `data/quality/baseline_quality.json`, `corrupted_quality.json` |
| 6 kịch bản corruption deterministic kèm log truy vết | `corruption.py`, `data/results/corruption_log.json` | 24 → 23 row, log ghi rõ `paper_id` bị tác động | Đọc `data/results/corruption_log.json` |
| Chạy agent demo có retry, lưu kết quả theo từng câu | `phase1.py`, `data/results/agent_demo_answers.json` | 3/3 câu được agent trả lời bằng tool trên corpus local | Đọc `data/results/agent_demo_answers.json` |
| Ghép hai flow end-to-end và sinh comparison report | `phase1.py`, `corruption_flow.py`, `data/reports/` | `phase1_report.md`, `corruption_report.md` | Chạy hai script trong mục 4 |

Một output cụ thể mà phần việc của tôi tạo ra và dùng để xác minh kết luận:

`data/results/corrupted_answers.json` cho phép truy ngược từng câu hỏi về đúng loại corruption đã gây ra lỗi. Ví dụ `q01-*` mất retrieval hit vì paper mới nhất bị `drop_latest_records`; `q02-summary` vẫn retrieve đúng document nhưng trả về chuỗi rỗng vì `blank_summary`; `q04-date` retrieve đúng nhưng trả sai ngày vì `stale_publication_date`. Đây là bằng chứng ở mức từng record, không chỉ ở mức metric tổng.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Xây toàn bộ vòng đời dữ liệu cho một hệ thống RAG và chứng minh bằng số liệu rằng chất lượng dữ liệu quyết định chất lượng câu trả lời: từ ingestion Crossref → cleaning → embedding/index → evaluation → quality/freshness → corruption → repair → so sánh ba trạng thái.

### Cách triển khai

**Ingestion.** `fetch_source_records` gọi `https://api.crossref.org/works` với `query.bibliographic`, `filter` và `rows = max_results × 3` (over-fetch vì một phần item sẽ bị loại ở bước parse). Retry tối đa 5 lần với exponential backoff cho các status 429/500/502/503/504, có tôn trọng header `Retry-After`. `parse_crossref_payload` bóc tag JATS trong `abstract`, ghép `given + family` thành tên tác giả, đọc `date-parts` thành ISO date, fallback `subject` → `container-title` → `type` cho categories, và loại mọi record thiếu DOI/title/abstract/ngày xuất bản.

**Cleaning.** `build_clean_dataframe` chuẩn hóa whitespace, chỉ giữ dạng chuỗi đã join cho `authors`/`categories` để CSV và JSON round-trip không mất kiểu, tính `age_days = run_date − published`, lọc bỏ record có title/summary quá ngắn hoặc `age_days < 0`, dedupe theo `paper_id` rồi theo `title`, sort theo `published` giảm dần. `text_for_embedding` là một khối văn bản gồm Title / Authors / Categories / Published / Summary — cùng một hàm `build_text_for_embedding` được dùng lại ở bước corruption để corrupted dataset vẫn đúng schema.

**Evaluation set.** `build_test_set` chọn 5 paper trải đều từ mới đến cũ (deterministic theo vị trí, không random) và sinh 4 câu hỏi mỗi paper. Cách đặt câu hỏi bám đúng router trong `retrieval/qa.py::_extract_answer` ("who authored" → authors, "when was" → published, "what categories" → categories, còn lại → câu đầu của summary). Tôi loại các title có dấu nháy đơn vì `answer_question` dùng regex `'([^']+)'` để lookup title chính xác.

**Data quality.** Một danh sách spec duy nhất (`_check_specs`) được dịch sang hai engine: Great Expectations 1.x (ephemeral context → pandas data source → validation definition) và một fallback thuần pandas cho cùng 9 check, trả về đúng một schema kết quả. Vì API của Great Expectations thay đổi nhanh giữa các phiên bản, fallback đảm bảo pipeline không vỡ; trường `engine` trong artifact ghi rõ engine nào đã chạy.

**Corruption.** 6 kịch bản deterministic chọn theo vị trí dòng nên chạy lại luôn ra kết quả giống nhau: xóa 3 paper mới nhất, làm rỗng 3 summary, chèn noise vào 3 summary, cắt 2 title còn 12 ký tự, lùi 3 published date về 4 năm trước, nhân đôi 2 row. Sau đó các cột dẫn xuất (`title_chars`, `summary_chars`, `text_for_embedding`) được tính lại.

**Repair.** Repair đọc lại `data/raw/crossref_records.json` và chạy lại đúng `build_clean_dataframe` — tức là dựng lại từ nguồn, không vá trên dataset đã hỏng.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | Crossref REST API; các đường dẫn artifact lấy từ `src/core/config.py`, không hard-code |
| Output | Cleaned dataframe 16 cột; test set JSON; quality/freshness JSON; corrupted/repaired dataset; hai markdown report |
| Module phụ thuộc | `core.config`, `core.utils`, `retrieval.index`, `retrieval.qa`, `evaluation.metrics` |
| Module sử dụng output | `retrieval.index` cần `paper_id`, `title`, `text_for_embedding`, `published`, `authors_joined`, `categories_joined`, `summary`, `abs_url`, `pdf_url` |
| Điều kiện lỗi cần xử lý | Crossref 429/503; abstract chứa JATS markup; record thiếu trường; `published` không parse được hoặc ở tương lai; corrupted dataset có summary rỗng và `paper_id` trùng; LLM judge hết quota |

### Cách xác minh

```bash
python -m pip install -e . -c constraints.txt
python script/run_phase1.py
python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** baseline chạy sạch với quality PASS và freshness FRESH; corruption làm giảm retrieval/answer metrics đồng thời làm quality FAIL và freshness STALE; repair đưa cả metrics lẫn quality signal về lại mức baseline.
- **Kết quả thực tế:** đúng như mong đợi, số liệu ở mục 8.
- **Artifact/log:** `data/reports/phase1_report.md`, `data/reports/corruption_report.md`, `data/results/*.json`, `data/quality/*.json`. Không có file nào chứa secret; `.env` nằm trong `.gitignore`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lần fetch đầu tiên, corpus lấy về hoàn toàn lệch chủ đề (ung bướu, nha khoa, nội tiết) và toàn bộ 24 record có cùng một `published` — freshness không còn phương sai để đo. Ngoài ra một số record có `published` năm 2027–2028.
- **Các phương án đã cân nhắc:** (1) giữ `sort=published&order=desc` rồi lọc chủ đề ở phía client; (2) chuyển sang `sort=relevance` và chặn record tương lai ngay từ filter; (3) clamp `age_days` về 0 cho ngày tương lai.
- **Phương án đã chọn:** phương án (2) — dùng `sort=relevance`, thêm `until-pub-date:<hôm nay>` vào filter, và để `compute_age_days` trả về giá trị âm thật thay vì clamp, sau đó cleaning loại các record đó.
- **Lý do:** `sort=published` ghi đè xếp hạng relevance của Crossref nên trả về bài mới nhất bất kể chủ đề — sai ngay từ tầng nguồn, lọc ở client chỉ che triệu chứng. Clamp `age_days` thì che mất một anomaly thật (metadata forthcoming) đúng vào chỗ mà bài lab muốn quan sát.
- **Bằng chứng quyết định phù hợp:** sau thay đổi, corpus đúng chủ đề RAG/LLM/agentic, `published` trải từ 2026-02-12 đến 2026-08-01, `age_days` từ 5 đến 175 ngày, `median_age_days = 66` — đủ phương sai để freshness threshold 180 ngày có ý nghĩa, và `stale_rows = 0` ở baseline.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:**

  ```text
  ERROR: Failed building wheel for cryptography
  💥 maturin failed
    Caused by: Cargo build finished with "exit status: 101"
  ...
  [transformers] Disabling PyTorch because PyTorch >= 2.4 is required but found 2.2.2
  A module that was compiled using NumPy 1.x cannot be run in NumPy 2.4.6
  ```

- **Lệnh hoặc bước tái hiện:** `python -m pip install -e .` trên macOS 12.7.6, Python 3.11, kiến trúc x86_64 (Mac Intel).
- **Nguyên nhân gốc:** ba ràng buộc chồng nhau, đều đến từ việc máy là Mac Intel. `cryptography` từ bản 49 trở đi chỉ phát hành wheel macOS cho `arm64`, nên pip buộc phải build từ source và cần Rust + OpenSSL. `torch` chỉ có wheel macOS x86_64 đến 2.2.2, mà `transformers` 5.x yêu cầu `torch >= 2.4` nên tự tắt backend PyTorch. Bản `torch` 2.2.2 lại được compile với NumPy 1.x nên vỡ ABI khi chạy cùng NumPy 2.x.
- **Cách xử lý:** thêm `constraints.txt` ghim `cryptography<49`, `torch==2.2.2`, `numpy<2`, `transformers<5` và cài bằng `python -m pip install -e . -c constraints.txt`.
- **Cách xác minh sau khi sửa:** import thành công `numpy 1.26.4`, `torch 2.2.2`, `transformers 4.57.6`, `sentence-transformers 5.6.1`, `chromadb 1.5.9`, `great_expectations 1.19.1`; sau đó cả hai pipeline chạy hết end-to-end và sinh đầy đủ artifact.
- **Điều học được:** một lỗi build ở tầng dependency thường không phải lỗi của một package đơn lẻ mà là hệ quả của ma trận wheel theo nền tảng. Đọc đúng tên wheel trên PyPI (`macosx_11_0_arm64` so với `macosx_10_9_universal2`) cho ra nguyên nhân nhanh hơn nhiều so với đọc log của Rust.

## 7. Hiểu biết về luồng end-to-end

1. **Từ Crossref đến vector index.** `fetch_source_records` gọi API, lưu nguyên response vào `data/raw/crossref_response.json` để truy vết, rồi parse thành `PaperRecord` và lưu `crossref_records.json`. `build_clean_dataframe` chuẩn hóa và sinh cột `text_for_embedding`. `LocalEmbeddingIndex.build` encode cột đó bằng `all-MiniLM-L6-v2`, ghi vào ChromaDB collection `papers-baseline` với cosine space, và xuất manifest ra `data/embeddings/`.

2. **Evaluation set và ground-truth doc IDs.** Mỗi sample mang theo `ground_truth_doc_ids` là `paper_id` của paper được dùng để sinh câu hỏi. `retrieval_hit_rate` kiểm tra retriever có trả về `paper_id` đó trong top-k hay không — đo riêng tầng retrieval. `mean_token_f1` và `judge_*` đo nội dung câu trả lời. Tách hai tầng như vậy cho phép phân biệt "retrieve sai document" với "retrieve đúng nhưng document đã hỏng nội dung".

3. **Quality checks khác freshness ở đâu.** Quality checks trả lời "dataset có đúng schema và ràng buộc không" — not null, unique, độ dài tối thiểu, định dạng ngày. Freshness monitoring trả lời "dataset có còn mới không" — `latest_published`, `max_age_days`, số dòng vượt ngưỡng 180 ngày. Một dataset có thể pass toàn bộ ràng buộc schema mà vẫn cũ; và ngược lại. Trong bài này `age_days` xuất hiện ở cả hai nơi, nhưng vai trò khác nhau: quality dùng nó như một ràng buộc pass/fail, freshness dùng nó để mô tả phân phối tuổi của dữ liệu.

4. **Vì sao phải dùng cùng test set.** Nếu mỗi trạng thái sinh test set riêng thì test set của corrupted sẽ được sinh từ chính dữ liệu đã hỏng, ground truth cũng hỏng theo, và metric sẽ đo "agent có nhất quán với dữ liệu hỏng không" chứ không phải "chất lượng câu trả lời giảm bao nhiêu". Giữ nguyên `data/eval/test_set.json` cho cả ba trạng thái khiến mọi thay đổi trong metric chỉ có thể đến từ thay đổi của corpus.

5. **Repair thành công dựa trên gì.** Ba bằng chứng phải cùng phục hồi: (a) `data/quality/repaired_quality.json` quay lại PASS 9/9; (b) `freshness_report_repaired.json` quay lại `FRESH` với `latest_published` bằng baseline; (c) `repaired_metrics.json` có `retrieval_hit_rate` và `mean_token_f1` trở lại mức baseline. Chỉ metric phục hồi mà quality vẫn FAIL thì chưa gọi là repair.

## 8. Phân tích kết quả

### Metrics chính

> Số liệu dưới đây được đọc trực tiếp từ `data/results/*.json` và `data/quality/*.json` của lượt chạy cuối cùng.

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.0000 | 0.8000 | 1.0000 | 4/20 câu mất hit, đúng bằng 4 câu hỏi của paper mới nhất bị `drop_latest_records` |
| `mean_token_f1` | 1.0000 | 0.7137 | 1.0000 | Giảm mạnh hơn hit rate vì có câu retrieve đúng nhưng nội dung đã bị làm rỗng hoặc sai ngày |
| `judge_accuracy` | 1.0000 | 0.7000 | 1.0000 | Cả ba chấm bằng LLM judge thật, 20/20 câu, không có lượt nào rơi về heuristic |
| `mean_judge_score` | 5.0000 | 3.9000 | 5.0000 | 6 câu bị corruption đều bị chấm 1–3 điểm, xem phân tích bên dưới |
| Quality checks | PASS 9/9 | FAIL 6/9 | PASS 9/9 | Fail: `paper_id_unique`, `summary_length_minimum`, `age_days_within_freshness_threshold` |
| Freshness status | FRESH (0/24 stale) | STALE (3/23 stale) | FRESH (0/24 stale) | `latest_published` tụt từ 2026-08-01 xuống 2026-07-03 |

**Ghi chú về LLM judge.** Ba trạng thái cần tổng cộng 60 lượt chấm, trong khi free tier của Gemini chỉ cấp 20 request/ngày cho mỗi model của mỗi project. Ban đầu lượt evaluate baseline dùng hết quota, các lượt sau nhận `429 RESOURCE_EXHAUSTED` và rơi ngay về heuristic judge. Tệ hơn, ở một lượt chạy lại thì quota được nhả lại đúng giữa chừng, khiến `describe_judge_mode()` báo `baseline = mixed: 6 LLM / 14 heuristic`, `corrupted = mixed: 12 LLM / 8 heuristic`, `repaired = heuristic (20/20)` — ba trạng thái được chấm bằng ba thước đo khác nhau nên cột `judge_*` khi đó vô nghĩa để so sánh.

Tôi xử lý bằng hai thay đổi. Thứ nhất, thêm retry có backoff cho lỗi rate limit trong `_judge_answer()`: 429 là lỗi tạm thời, rơi thẳng về heuristic ngay lần đầu chính là nguyên nhân gây ra tình trạng judge bị trộn. Thứ hai, chuyển sang một API key thuộc project khác và dùng model `gemini-3.5-flash-lite` (model cũ `gemini-2.5-flash` trả về `404 no longer available to new users` với key mới), để có đủ quota cho cả 60 lượt chấm cộng agent demo.

Kết quả của lượt chạy cuối: `corruption_report.md` xác nhận `baseline = corrupted = repaired = LLM judge (20/20)`, và kiểm tra trực tiếp trên ba file `*_answers.json` cho thấy **0/60 câu** rơi về heuristic. Cột `judge_*` trong bảng trên vì vậy là bằng chứng độc lập với `token_f1`, không phải bản rời rạc hóa của nó.

Cơ chế phòng vệ vẫn được giữ nguyên: nếu lần chạy sau lại hết quota, comparison report sẽ tự in cảnh báo khi ba trạng thái không cùng judge, nên sai lệch kiểu này không thể lọt qua im lặng. Khi không có đủ quota, `JUDGE_MODE=heuristic` cho phép ép cả ba dùng chung heuristic một cách tất định — vẫn so sánh được, chỉ là yếu hơn.

**Agent demo.** `data/results/agent_demo_answers.json` chứa 3/3 câu trả lời thật của agent (`create_agent` với hai tool `semantic_search_papers` và `lookup_paper`). Agent trả lời đúng tác giả và đúng ngày xuất bản của paper được hỏi, dựa trên corpus đã index chứ không phải kiến thức sẵn có của model.

### Kết luận từ số liệu

1. `drop_latest_records` xóa 3 paper mới nhất → `freshness_report_corrupted.json` chuyển sang `STALE` với `latest_published` lùi từ `2026-08-01` về `2026-07-03`, đồng thời `stale_publication_date` đẩy `max_age_days` lên `1526` khiến check `age_days_within_freshness_threshold` fail 3/23 dòng → `retrieval_hit_rate` giảm từ `1.0000` xuống `0.8000`, vì cả 4 câu hỏi thuộc paper bị xóa đều không còn document đúng để retrieve.

2. Repair dựng lại dataset từ `data/raw/crossref_records.json` bằng đúng hàm `build_clean_dataframe` → `repaired_quality.json` trở lại PASS 9/9 và `freshness_report_repaired.json` trở lại `FRESH` với `latest_published` bằng baseline → `retrieval_hit_rate` và `mean_token_f1` trở lại `1.0000`, tức là phục hồi hoàn toàn.

**Corruption nào ảnh hưởng rõ nhất và vì sao?**

`drop_latest_records` ảnh hưởng nặng nhất lên metric vì nó là loại lỗi duy nhất phá tầng retrieval: document đúng biến mất khỏi index nên không có cách nào trả lời đúng, kéo theo cả 4 câu hỏi của paper đó mất điểm ở mọi metric cùng lúc. Các corruption khác chỉ phá nội dung: với `blank_summary`, `q02-summary` vẫn retrieve đúng document (`retrieval_hit = true`) nhưng trả về chuỗi rỗng nên `token_f1 = 0`; với `stale_publication_date`, `q04-date` retrieve đúng nhưng trả `2022-06-02` thay vì ngày thật. Đây cũng là lý do `mean_token_f1` giảm sâu hơn `retrieval_hit_rate`.

Về phía observability thì ngược lại: loại gây ồn nhiều nhất cho quality suite là `duplicate_rows` và `blank_summary`. Duplicate làm `paper_id_unique` fail 4/23 dòng, còn blank summary làm `summary_length_minimum` fail 5/23 dòng — 5 chứ không phải 3, vì 2 dòng bị nhân đôi lại chính là các dòng đã bị làm rỗng summary.

**Kết quả nào khác với kỳ vọng ban đầu?**

Tôi kỳ vọng `mean_token_f1` ở baseline sẽ nhỏ hơn 1.0. Thực tế nó đúng bằng `1.0000`. Giả thuyết của tôi là do `retrieval/qa.py::_extract_answer` trả về nguyên văn giá trị metadata (`authors_joined`, `published`, `categories_joined`, hoặc câu đầu của `summary`), trong khi `build_test_set` sinh ground truth từ đúng những trường đó — nên khi retrieve đúng document thì hai chuỗi trùng khớp hoàn toàn. Tôi kiểm tra bằng cách mở `data/results/baseline_answers.json` và đối chiếu `answer` với `ground_truth` của từng sample, xác nhận chúng khớp từng token. Hệ quả cần lưu ý: ở corpus sạch, `mean_token_f1` gần như đo lại chính `retrieval_hit_rate`; nó chỉ thực sự tách biệt khi nội dung document bị hỏng, và đúng lúc đó nó cho tín hiệu mà hit rate không thấy được (`q02-summary` và `q04-date` ở trên).

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Data pipeline:** giữ lại raw artifact không phải là thủ tục hình thức. Toàn bộ bước repair trong bài này chỉ khả thi vì `data/raw/crossref_records.json` còn nguyên — repair là chạy lại cleaning từ nguồn, không phải vá dataset đã hỏng. Nếu chỉ lưu cleaned data thì lỗi dữ liệu sẽ không thể đảo ngược.

2. **Data quality/observability:** quality checks và freshness bắt được lỗi ở tầng dataset trước khi nó kịp biến thành câu trả lời sai. Trong lượt chạy corrupted, quality suite fail ngay 3 check và freshness chuyển STALE — tín hiệu này xuất hiện ở bước kiểm tra dataset, tức là trước khi bất kỳ câu hỏi nào được chạy qua agent.

3. **Ảnh hưởng của data lên RAG agent:** cần tách metric theo tầng. `retrieval_hit_rate` chỉ bắt được lỗi làm mất document; `mean_token_f1` mới bắt được lỗi làm hỏng nội dung của document vẫn đang được retrieve đúng. Nếu chỉ đo một trong hai thì `blank_summary` và `stale_publication_date` sẽ hoàn toàn vô hình.

### Nếu có thêm thời gian

Tôi sẽ làm test set khó hơn. Hiện `mean_token_f1` ở baseline đúng bằng `1.0000` vì `_extract_answer` trả về nguyên văn trường metadata mà chính test set dùng làm ground truth, nên ở corpus sạch nó gần như trùng với `retrieval_hit_rate`. Cải thiện cụ thể: thêm loại câu hỏi cần tổng hợp từ nhiều paper (ví dụ "những paper nào cùng đề cập tới hallucination?") với `ground_truth_doc_ids` gồm nhiều ID, khiến `retrieval_hit_rate` phải tính theo recall trên tập nhiều document thay vì chỉ cần trúng một. Cách đo: nếu `mean_token_f1` ở baseline tụt xuống dưới 1.0 trong khi `retrieval_hit_rate` vẫn cao, nghĩa là hai chỉ số đã thực sự đo hai thứ khác nhau và test set đã đủ khó để phân biệt chất lượng sinh câu trả lời với chất lượng retrieval.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Đặng Quang Minh
**Ngày xác nhận:** 2026-08-06
