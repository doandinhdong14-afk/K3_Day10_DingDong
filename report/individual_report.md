# Member Role Report — Day 10: Data Pipeline & Data Observability

> Mỗi thành viên trong nhóm tự hoàn thành mẫu này để báo cáo đúng vai trò, phần việc và mức hiểu của mình. Không sao chép nguyên báo cáo chung hoặc báo cáo của thành viên khác. Thay nội dung trong dấu `[ ]` và xóa các dòng hướng dẫn không cần thiết trước khi nộp.

> **Lưu ý về provider LLM:** run đã nộp chạy với `provider=groq`, `model=openai/gpt-oss-20b` (xác minh tại `data/reports/phase1_report.md`, mục 1: `llm_provider | groq`, `llm_model | openai/gpt-oss-20b`). Groq là provider mặc định trong `src/core/config.py` (`LLM_PROVIDER=groq`, `LLM_MODEL=openai/gpt-oss-20b`); project cũng hỗ trợ gemini, openai, anthropic, openrouter, ollama và custom qua biến `LLM_PROVIDER`. **Nếu chạy lại pipeline trên provider khác thì phải cập nhật lại hai trường provider/model ở mọi chỗ báo cáo này nhắc tới chúng**, vì `judge_accuracy` và `mean_judge_score` phụ thuộc trực tiếp vào LLM judge.

## 1. Thông tin cá nhân

<!-- CAN DIEN: Thanh vien tu dien toan bo bang duoi day. Khong ai khac duoc dien ho. -->

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | [Họ và tên]             |
| MSSV               | [MSSV]                     |
| Khóa/Lớp         | [K3 hoặc K4]              |
| Tên nhóm         | [Tên hoặc mã nhóm]     |
| Vai trò chính    | [Vai trò]                 |
| Repository         | [Đường dẫn repository] |
| Ngày hoàn thành | [YYYY-MM-DD]               |

## 2. Vai trò và phạm vi công việc

### Danh mục 7 khối deliverable của project (để chọn phần việc của mình)

Bảng dưới đây liệt kê đúng 7 khối deliverable của project và file/artifact thực tế mà mỗi khối chịu trách nhiệm. Thành viên chọn các khối mình trực tiếp làm rồi chép sang bảng "Phần việc sở hữu" bên dưới.

| # | Khối deliverable           | File nguồn phụ trách                                              | Artifact phải bàn giao                                                                                                             |
| -: | -------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| 1 | Raw ingestion              | `src/ingestion/crossref.py`                                       | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` (24 raw records)                                              |
| 2 | Cleaning & data modeling   | `src/ingestion/cleaning.py`                                       | `data/clean/papers_clean.csv`, `data/clean/papers_clean.json` (24 dòng × 16 cột, có `text_for_embedding`)                     |
| 3 | Evaluation set             | `src/evaluation/testset.py`                                       | `data/eval/test_set.json` (20 câu hỏi / 5 paper / 4 loại câu hỏi)                                                              |
| 4 | Quality & freshness        | `src/observability/quality.py`                                    | `data/quality/baseline_quality.json`, `corrupted_quality.json`, `repaired_quality.json`, 3 file `freshness_report*.json`      |
| 5 | Reporting                  | `src/observability/reporting.py`                                  | `data/reports/phase1_report.md`, `data/reports/corruption_report.md`                                                              |
| 6 | Baseline orchestration     | `src/pipelines/phase1.py`, `src/retrieval/index.py`               | `data/results/baseline_metrics.json`, `baseline_answers.json`, `agent_demo_answers.json`, `data/embeddings/`, `data/chroma/` |
| 7 | Corruption & repair        | `src/ingestion/corruption.py`, `src/pipelines/corruption_flow.py` | `data/results/corruption_log.json`, `corrupted_metrics.json`, `repaired_metrics.json` + bộ CSV/JSON corrupted/repaired         |

Các khối phụ trợ dùng chung (không tính là deliverable riêng): `src/core/config.py` (đường dẫn + tham số `max_results=24`, `top_k=4`, `freshness_threshold_days=180`), `src/retrieval/qa.py`, `src/retrieval/llm.py`, `src/retrieval/agent.py`, `src/evaluation/metrics.py`.

### Phần việc sở hữu

<!-- CAN DIEN: Chi giu lai cac dong ung voi khoi ma ban TRUC TIEP lam. Xoa cac dong con lai. -->

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| [Phần việc]      | [File/hàm]           | [Input]          | [Output/artifact] | [Hoàn thành/Một phần/Chưa hoàn thành] |
| [Phần việc]      | [File/hàm]           | [Input]          | [Output/artifact] | [Hoàn thành/Một phần/Chưa hoàn thành] |

Chỉ nhận ownership cho phần bạn trực tiếp thực hiện. Liên hệ rõ phần việc của bạn với đầu vào, đầu ra và các thành viên phụ thuộc vào phần đó.

Thứ tự phụ thuộc thực tế giữa các khối (khối sau không chạy được nếu khối trước chưa có artifact):

```text
Khối 1 raw ingestion
   -> Khối 2 cleaning (đọc data/raw/crossref_records.json)
   -> Khối 3 test set + Khối 6 index/baseline (đọc data/clean/papers_clean.json)
   -> Khối 4 quality/freshness + Khối 5 reporting (đọc clean frame + metrics)
   -> Khối 7 corruption/repair (bắt buộc phải có baseline_metrics.json, clean_json,
      test_set.json, crossref_records.json — nếu thiếu thì corruption_flow raise RuntimeError)
```

### Việc hỗ trợ ngoài phạm vi chính

<!-- CAN DIEN: Chi ghi viec ban that su lam giup nguoi khac, kem bang chung (commit, artifact, log). -->

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| [Debug/tích hợp/tài liệu] | [Tên hoặc module] | [Kết quả và bằng chứng] |

## 3. Kết quả theo vai trò

<!-- CAN DIEN: Cot 1-3 do thanh vien tu dien theo khoi minh so huu. Cot "Cach xac minh" duoi day la lenh THAT SU cua project, dung nguyen van duoc. -->

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| [Mô tả cụ thể] | [Đường dẫn file] | [Artifact/metrics/report] | [Chọn lệnh trong bảng bên dưới] |
| [Mô tả cụ thể] | [Đường dẫn file] | [Artifact/metrics/report] | [Chọn lệnh trong bảng bên dưới] |

### Lệnh xác minh thật của từng khối

| Khối | Lệnh chạy | Artifact phải mở để đối chiếu | Dấu hiệu đạt |
| ---- | ----------- | -------------------------------- | -------------- |
| Tiền đề cho mọi khối gọi LLM | `python script/check_llm.py` | stdout của script | 3 dòng `[OK  ]` cho *chat bình thường*, *structured output*, *tool calling* (ngoài dòng `[OK  ] credentials` in trước đó), kết thúc bằng `KET LUAN: provider san sang`. Nếu *structured output* lỗi thì judge rơi về heuristic dự phòng và `judge_*` mất ý nghĩa. |
| 1. Raw ingestion | `python script/run_phase1.py` (bước 2/10) | `data/raw/crossref_records.json` | file có 24 record, mỗi record đủ `paper_id/title/summary/authors/published` |
| 2. Cleaning | `python script/run_phase1.py` (bước 3–4/10) | `data/clean/papers_clean.csv` | 24 dòng, 16 cột, cột `text_for_embedding` không rỗng |
| 3. Evaluation set | `python script/run_phase1.py` (bước 6/10); ép tạo lại bằng biến môi trường `REFRESH_TEST_SET=1` | `data/eval/test_set.json` | 20 sample, 4 `question_type`, mỗi sample có đúng 1 `ground_truth_doc_ids` |
| 4. Quality & freshness | `python script/run_phase1.py` (bước 8/10) và `python script/run_corruption_flow.py` (bước 6 và 8/10) | `data/quality/baseline_quality.json`, `corrupted_quality.json`, `repaired_quality.json`, `freshness_report*.json` | baseline 12/12 pass, corrupted 7/12 pass với 5 `failed_check_names`, repaired 12/12 pass |
| 5. Reporting | `python script/run_phase1.py` (bước 9/10), `python script/run_corruption_flow.py` (bước 9/10) | `data/reports/phase1_report.md`, `data/reports/corruption_report.md` | bảng so sánh 3 trạng thái khớp với các file `*_metrics.json` |
| 6. Baseline orchestration | `python script/run_phase1.py` | `data/results/baseline_metrics.json`, khối "TOM TAT ARTIFACT PHASE 1" ở cuối stdout | `retrieval_hit_rate=1.0`, `mean_token_f1=1.0`, `judge_accuracy=1.0`, `mean_judge_score=5`; mọi dòng artifact là `[OK]` |
| 7. Corruption & repair | `python script/run_corruption_flow.py` | `data/results/corruption_log.json`, `corrupted_metrics.json`, `repaired_metrics.json` | log có đúng 7 step, `source_rows=24`, `result_rows=23`, `deterministic=true`; repaired trở lại 1.0/1.0/1.0/5.0 |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

<!-- CAN DIEN: Viet 3-5 cau ve dung mot artifact ma phan viec cua ban sinh ra. Vi du tham khao (KHONG chep nguyen van, phai doi sang artifact cua ban): -->

[Mô tả artifact, metric hoặc kết quả tích hợp mà phần việc của bạn tạo ra. Nêu rõ đường dẫn file, số liệu chính đọc được trong file đó, và ai là người dùng lại output này ở bước sau.]

## 4. Giải thích phần kỹ thuật đã thực hiện

<!-- CAN DIEN: Muc 4 duoi day mo ta dung pipeline that cua project. Thanh vien thu hep lai vao khoi minh so huu, giu nguyen cac so lieu va ten ham vi chung deu doc ra tu source/artifact. -->

### Vấn đề cần giải quyết

Pipeline phải chứng minh được một quan hệ nhân quả: **chất lượng dữ liệu quyết định chất lượng câu trả lời của RAG agent**. Muốn chứng minh được thì mọi bước từ nguồn Crossref đến vector index phải xác định (deterministic), mọi artifact trung gian phải ghi ra đĩa để đối chiếu, và ba trạng thái baseline / corrupted / repaired phải được chấm trên **cùng một** test set. Nếu một bước nào đó tự ý đổi dữ liệu (ví dụ sinh lại test set từ dữ liệu đã hỏng), phép so sánh mất hết ý nghĩa.

### Cách triển khai

Luồng dữ liệu thực tế trong project:

```text
Crossref REST API (query = "agentic retrieval augmented generation large language model",
                   filter = from-pub-date:<hôm nay - 180 ngày>,has-abstract:true)
  -> crossref.fetch_source_records()   : over-fetch max_results*3 = 72 rows rồi lọc còn 24
  -> data/raw/crossref_response.json (payload thô) + data/raw/crossref_records.json (24 record đã parse)
  -> cleaning.build_clean_dataframe()  : frame 16 cột, sort published giảm dần, 2 lượt khử trùng
  -> data/clean/papers_clean.{csv,json} (24 dòng)
  -> index.LocalEmbeddingIndex.build() : MiniLM-L6-v2 embed cột text_for_embedding
                                         -> ChromaDB cosine, collection papers-baseline
  -> testset.build_test_set()          : 5 paper × 4 loại câu hỏi = 20 sample -> data/eval/test_set.json
  -> metrics.evaluate_pipeline()       : qa.answer_question() + LLM judge
                                         -> baseline_metrics.json + baseline_answers.json
  -> quality.run_data_quality_checks() + quality.build_freshness_report()
  -> corruption.corrupt_clean_dataframe() -> index papers-corrupted -> đánh giá lại
  -> corruption_flow bước 7: repair bằng cách BUILD LẠI từ data/raw/crossref_records.json
                             (không vá frame corrupted) -> index papers-repaired -> đánh giá lại
```

Bốn quyết định kỹ thuật đáng chú ý trong luồng này:

1. **Over-fetch rồi lọc.** `fetch_source_records()` xin `max_results * 3 = 72` dòng từ Crossref rồi mới lọc, vì bộ lọc phía client loại khá nhiều record (thiếu abstract, abstract dưới 80 ký tự, không phải chữ Latin). Nếu chỉ xin đúng 24 dòng thì sau khi lọc sẽ không đủ dữ liệu.
2. **`text_for_embedding` là văn bản duy nhất được embed.** Cột này ghép `title + authors + categories + published + summary` thành một đoạn. Đây là lý do một corruption chỉ chạm vào `summary` vẫn làm thay đổi vector của cả document.
3. **`published`/`updated` giữ nguyên kiểu chuỗi.** Cleaning ghi `published.date().isoformat()` chứ không giữ `Timestamp`, vì metadata của ChromaDB chỉ nhận kiểu nguyên thủy (str/int/float/bool). Bước corruption cũng phải tuân theo ràng buộc này — hàm `_shift_year_back()` luôn trả về string.
4. **Router theo từ khóa trong `qa.py` quyết định cách viết câu hỏi.** `_extract_answer()` chọn trường metadata theo cụm từ trong câu hỏi ("who authored" → `authors_joined`, "when was" → `published`, "what categories" → `categories_joined`, còn lại → `first_sentence(summary)`). Vì vậy `testset.py` phải sinh câu hỏi đúng theo các cụm đó, bọc tiêu đề trong dấu nháy đơn để regex `r"'([^']+)'"` của `answer_question()` bắt được, và loại các paper có tiêu đề chứa dấu nháy đơn hoặc chứa chính các cụm routing.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | `data/raw/crossref_records.json` — list các `PaperRecord` (11 trường: `paper_id`, `title`, `summary`, `authors`, `categories`, `primary_category`, `published`, `updated`, `abs_url`, `pdf_url`, `comment`). Tham số cấu hình lấy từ `src/core/config.py`: `max_results=24`, `top_k=4`, `freshness_threshold_days=180`. |
| Output                         | `data/clean/papers_clean.{csv,json}` — 24 dòng × 16 cột: 11 trường gốc (đã gộp authors/categories thành `authors_joined`, `categories_joined`) cộng `age_days`, `author_count`, `title_chars`, `summary_chars`, `text_for_embedding`. Từ đây sinh tiếp `data/embeddings/papers_embeddings.json` (manifest: backend, embedding_model, persist_path, collection_name, documents) và collection ChromaDB. |
| Module phụ thuộc             | `src/core/config.py` (đường dẫn + ngưỡng), `src/core/utils.py` (`normalize_whitespace`, `compact_join`, `first_sentence`, `read_json`/`write_json`/`write_csv`), `src/ingestion/crossref.py` (kiểu `PaperRecord`). |
| Module sử dụng output        | `src/retrieval/index.py` (đọc `text_for_embedding` + metadata), `src/evaluation/testset.py` (sinh câu hỏi + ground truth), `src/observability/quality.py` (12 check + freshness), `src/ingestion/corruption.py` (kiểm tra 11 cột bắt buộc rồi mới làm hỏng), `src/pipelines/corruption_flow.py`. |
| Điều kiện lỗi cần xử lý | Xem bảng chi tiết ngay bên dưới. |

Các điều kiện lỗi **thực sự** đã được xử lý trong code (không phải giả định):

| Điều kiện lỗi | Vị trí xử lý | Cách xử lý |
| --------------- | -------------- | ------------ |
| Crossref trả HTTP 429/500/502/503/504 hoặc `requests.RequestException` | `crossref._get_with_retry()` | Thử tối đa 5 lần, thời gian chờ khởi điểm 1s và nhân đôi sau mỗi lần (1→2→4→8s). Hết 5 lần thì raise `RuntimeError` kèm lỗi cuối cùng. |
| Crossref không có trường `subject` | `crossref._format_categories()` | Fallback sang `container-title` → `type` → `publisher`; nếu vẫn rỗng thì gán `["uncategorized"]`. **Đo thực tế: 0/24 record của run này có trường `subject`**, nghĩa là toàn bộ giá trị `categories_joined` trong dataset đều đến từ nhánh fallback. |
| ChromaDB metadata chỉ nhận kiểu nguyên thủy | `cleaning.build_clean_dataframe()` và `corruption._shift_year_back()` | `published`/`updated` luôn được ghi dưới dạng chuỗi `YYYY-MM-DD`, không giữ `pd.Timestamp`. |
| Abstract rỗng hoặc quá ngắn | `crossref.parse_crossref_payload()` (`MIN_SUMMARY_CHARS = 80`) và `cleaning.build_clean_dataframe()` (kiểm tra lại lần hai) | Bỏ hẳn record. Đây cũng chính là ngưỡng mà check `summary_min_length` dùng lại, nên baseline luôn 0 dòng vi phạm. |
| Bài không phải chữ Latin | `crossref._looks_latin()` | Yêu cầu ≥70% ký tự chữ cái là ASCII trên cả `title` lẫn `summary`, vì MiniLM-L6-v2 chỉ mạnh với tiếng Anh. |
| Ngày tháng hỏng | `crossref._format_date()`, `cleaning._parse_date()`, `corruption._parse_iso_date()` | Thiếu tháng/ngày thì mặc định 1; ngày không hợp lệ thì lùi về `YYYY-01-01`; parse thất bại thì bỏ dòng ở cleaning. |
| Trùng lặp bản ghi | `crossref.parse_crossref_payload()` (set `seen_ids`) + `cleaning` (khử theo `paper_id`, rồi khử theo `title` viết thường) | Hai lượt khử độc lập; nhờ vậy baseline đạt `paper_id_unique` = PASS. |
| Dataframe thiếu cột | `quality.run_data_quality_checks()` (`_missing_column_check`) và `corruption._require_columns()` | Quality báo FAIL kèm tên cột thay vì ném `KeyError`; corruption raise `ValueError` liệt kê cột thiếu. |
| LLM judge gọi thất bại | `metrics._judge_answer()` | Bắt exception rồi rơi về giám khảo heuristic dựa trên `token_f1` (≥0.95 → 5, ≥0.5 → 3, còn lại → 1) và ghi rõ lý do vào trường `reasoning`. |
| Agent demo lỗi (rate limit, tool calling không hỗ trợ) | `phase1._run_agent_demo()` | Chỉ in cảnh báo rồi đi tiếp — lỗi LLM ở bước demo không được phép làm hỏng các artifact đã sinh ở bước 1–9. |
| Thiếu artifact của phase 1 khi chạy phase 2 | `corruption_flow._require_phase1_artifacts()` | Raise `RuntimeError` liệt kê từng file thiếu và yêu cầu chạy `script/run_phase1.py` trước. |

### Cách xác minh

```bash
python script/check_llm.py
python script/run_phase1.py
python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** `check_llm.py` trả về 3 dòng `[OK  ]`; `run_phase1.py` in 10 bước và khối tổng kết artifact toàn `[OK]`; `run_corruption_flow.py` in bảng so sánh 3 trạng thái, trong đó corrupted thấp hơn baseline và repaired quay lại bằng baseline.
- **Kết quả thực tế:** đúng như mong đợi. Baseline `1.0000 / 1.0000 / 1.0000 / 5.0000`; corrupted `0.8000 / 0.6684 / 0.6500 / 3.6000`; repaired `1.0000 / 1.0000 / 1.0000 / 5.0000`. Số dòng `24 → 23 → 24`. Chạy hai lần liên tiếp cho kết quả **giống hệt nhau**, xác nhận pipeline deterministic.
- **Artifact/log:** `data/results/baseline_metrics.json`, `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, `data/results/corruption_log.json`, `data/quality/*.json`, `data/reports/phase1_report.md`, `data/reports/corruption_report.md`. Không file nào trong số này chứa API key; `.env` nằm trong `.gitignore` và không được trích dẫn ở bất kỳ đâu trong báo cáo.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** `corruption.py` phải chọn xem *dòng nào* trong clean frame sẽ bị làm hỏng bởi từng loại corruption. Test set chỉ chấm 5 paper trong tổng số 24 dòng (`testset._select_papers()` lấy `df.iloc[::step]` với `step = len(usable) // 5 = 4`, tức các vị trí 0, 4, 8, 12, 16). Nếu chọn dòng sai, corruption có thể rơi hết vào 19 paper không được chấm — quality check vẫn FAIL nhưng metric của agent không nhúc nhích, và bài lab mất luôn phần chứng minh nhân quả.

- **Các phương án đã cân nhắc:**
  - **Phương án A — chọn ngẫu nhiên có seed:** dùng `random.Random(seed).sample(range(n_rows), k)` cho mỗi loại corruption. Ưu điểm: viết ngắn, "trông giống" lỗi dữ liệu ngoài thực tế hơn, và có seed nên vẫn lặp lại được. Nhược điểm: không kiểm soát được có bao nhiêu paper *được chấm* bị chạm; hai loại corruption có thể cùng rơi vào một paper (không tách được ảnh hưởng), hoặc rơi hết vào paper không được chấm (metric không đổi). Kết quả còn phụ thuộc vào thứ tự dòng do Crossref trả về, nên đổi query là phải dò lại seed.
  - **Phương án B — offset xác định suy ra từ stride của test set:** không dùng RNG. Đặt `TESTSET_STRIDE = 4` (chính là stride của `testset.py`); sau khi bước 1 xóa `DROP_LATEST = 3` dòng đầu, các paper được chấm dồn về "làn" bắt đầu tại `EVAL_LANE_START = (-3) % 4 = 1`. Gán cho mỗi loại corruption một điểm xuất phát khác nhau **trên chính làn đó**: `blank_summary = 1`, `inject_noise = 1 + 4 = 5`, `truncate_title = 1 + 8 = 9`, `stale_dates = 1 + 12 = 13`. Bước nhảy chọn dòng `SELECTION_STRIDE = TESTSET_STRIDE + 1 = 5` lệch pha với làn test set, nên các dòng còn lại của cùng một loại corruption rơi vào paper *không* được chấm.

- **Phương án đã chọn:** Phương án B.

- **Lý do:** B bảo đảm **mỗi loại corruption chạm đúng một paper đang được chấm điểm**, nên có thể quy trách nhiệm cho từng loại một cách riêng biệt thay vì chỉ nói chung chung "dữ liệu hỏng thì metric giảm". Đổi lại là mất tính "tự nhiên" của lỗi ngẫu nhiên và code phức tạp hơn (phải tự viết `_pick_positions()` có xử lý quay vòng modulo và chống lặp vô hạn khi `stride` chia hết `n_rows`). Với mục tiêu của bài lab — *đo* được ảnh hưởng chứ không *mô phỏng* sự cố — khả năng quy trách nhiệm quan trọng hơn tính ngẫu nhiên. B cũng loại bỏ hoàn toàn RNG nên `corruption_log.json` ghi `"deterministic": true` và hai lần chạy liên tiếp cho kết quả giống hệt.

- **Bằng chứng quyết định phù hợp:** đối chiếu `data/results/corruption_log.json` với `data/eval/test_set.json` cho thấy 4 trong 5 paper được chấm bị 4 loại corruption khác nhau chạm vào, mỗi loại đúng một paper:

  | Loại corruption | `paper_id` được chấm bị chạm | Vị trí | Hệ quả đo được trên corrupted |
  | ----------------- | ------------------------------- | -------- | --------------------------------- |
  | `drop_latest_records` | `10.2118/234689-pa` | 0 (bị xóa) | q001–q004 mất hoàn toàn: `retrieval_hit=false`, `token_f1` = 0.000/0.000/0.273/0.095 |
  | `blank_summary` | `10.3390/buildings16132637` | 1 | q008 trả về chuỗi rỗng, `token_f1 = 0.000`, judge score 1 |
  | `inject_noise` | `10.21203/rs.3.rs-10012178/v1` | 5 | q012 trả về `"LOREM IPSUM DOLOR ###### CORRUPTED PAYLOAD @@@@@@."`, `token_f1 = 0.000` |
  | `truncate_title` | `10.22214/ijraset.2026.82233` | 9 | q013–q016 **không** đổi: vẫn `token_f1 = 1.000`, judge 5/5 (phân tích ở mục 8) |
  | `stale_dates` | `10.1093/sleep/zsag091.0346` | 13 | q018 trả `2023-05-01` thay vì `2026-05-01`, `token_f1 = 0.000` |

  Nếu dùng phương án A thì bảng này không thể lập được. Chính bảng này cho phép kết luận ở mục 8 rằng `drop_latest_records` là loại gây hại nhất (4/20 câu hỏi) còn `truncate_title` không gây hại đo được (0/20 câu hỏi).

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** ngay khi import thư viện, Python chết ở tầng loader chứ không vào được code của project. Thông báo có dạng:

  ```text
  ImportError: DLL load failed while importing <module>._lib: 
  ... is not signed and cannot run on a system with Smart App Control enabled.
  ```

  <!-- CAN DIEN: Dan lai DUNG NGUYEN VAN traceback trong terminal cua ban vao khoi tren
       (khoi hien tai la ban rut gon, chua phai nguyen van). Nho che duong dan tuyet doi
       co ten user va moi API key truoc khi dan. -->

  (Đường dẫn tuyệt đối chứa tên người dùng đã được lược bỏ; log gốc không chứa secret nào.)

- **Lệnh hoặc bước tái hiện:**

  ```bash
  # Trên máy Windows 11 bật Smart App Control, sau khi cài dependency
  # bằng phiên bản mới nhất mà resolver tự chọn (pandas 3.x / pyarrow 24–25.x)
  python -c "import pandas"
  python script/run_phase1.py    # chết ngay ở bước 3/10 "Lam sach du lieu"
  ```

- **Nguyên nhân gốc:** không phải lỗi của code project. Windows 11 Smart App Control chặn việc nạp các file nhị phân `.pyd`/`.dll` **không có chữ ký số**. Các wheel dựng sẵn của `pandas` dòng 3.x và `pyarrow` dòng 24–25.x mà resolver chọn về chứa extension đã biên dịch nhưng chưa được ký, nên loader của Windows từ chối nạp trước khi Python kịp chạy bất kỳ dòng lệnh nào. `requirements.txt`/`pyproject.toml` chỉ ghi ràng buộc mở (`pandas>=2.2.2`) nên resolver mặc nhiên lấy bản mới nhất — đây là lỗ hổng về khả năng tái lập môi trường, không phải lỗi logic.

- **Cách xử lý:** ghim ngược về cặp phiên bản có wheel nạp được trên máy này thay vì tắt Smart App Control (tắt tính năng bảo mật toàn hệ thống chỉ để cài một thư viện là đánh đổi tồi):

  ```bash
  pip install --force-reinstall "pandas==2.3.3" "pyarrow==21.0.0"
  ```

- **Cách xác minh sau khi sửa:**

  ```bash
  python -c "import pandas, pyarrow; print(pandas.__version__, pyarrow.__version__)"
  # -> 2.3.3 21.0.0
  python script/run_phase1.py
  python script/run_corruption_flow.py
  ```

  Cả hai pipeline chạy hết 10/10 bước và sinh đủ artifact. Môi trường `.venv` hiện tại của project vẫn đang giữ đúng cặp `pandas 2.3.3` / `pyarrow 21.0.0` này; trong khi đó `uv.lock` **chưa** được cập nhật (còn ghi `pandas 3.0.3` và `pyarrow 24.0.0`), nên nếu ai đó dựng lại môi trường từ lock file thì lỗi sẽ tái diễn — đây là việc tồn đọng cần xử lý.

- **Điều học được:** ràng buộc phiên bản kiểu `>=` không đủ để tái lập môi trường. Lỗi ở tầng loader của hệ điều hành có triệu chứng giống hệt lỗi cài đặt sai (`ImportError`), nên phải đọc kỹ nội dung thông báo trước khi đi sửa code — ở đây thông điệp "not signed" mới là manh mối, không phải chữ "ImportError". Bài học vận hành: khi môi trường chạy được thì phải ghim lại phiên bản đó vào file khóa, nếu không lần dựng lại tiếp theo sẽ hỏng.

<!-- CAN DIEN: Neu blocker cua ban khac (vi du model LLM bi provider khai tu, phat hien qua HTTP 404,
     xu ly bang cach doi model trong .env roi chay lai script/check_llm.py), hay thay toan bo muc 6
     bang blocker cua chinh ban, van giu du 6 gach dau dong: trieu chung / tai hien / nguyen nhan goc /
     cach xu ly / cach xac minh / dieu hoc duoc. Nho che moi API key truoc khi dan log. -->

Nếu chưa xử lý xong:

- **Phạm vi bị ảnh hưởng:** `uv.lock` vẫn ghi cặp phiên bản gây lỗi; ai dựng môi trường bằng `uv sync` sẽ gặp lại đúng lỗi trên.
- **Những gì đã loại trừ:** không phải lỗi thiếu Microsoft Visual C++ Redistributable (đã cài đủ); không phải xung đột `numpy` (thử cài lại `numpy` riêng vẫn lỗi); không phải lỗi của code project (lỗi xảy ra ngay ở `python -c "import pandas"`, chưa chạm tới `src/`).
- **Bước tiếp theo:** ghim `pandas==2.3.3` và `pyarrow==21.0.0` vào `pyproject.toml`, chạy lại `uv lock`, rồi xác minh bằng cách dựng môi trường sạch và chạy `python script/run_phase1.py` một lần từ đầu.

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
5. Repair được xem là thành công dựa trên artifact và metric nào?

**Câu trả lời:**

**1. Từ Crossref đến vector index.** `fetch_source_records()` gọi `GET https://api.crossref.org/works` với `query = "agentic retrieval augmented generation large language model"` và `filter = from-pub-date:<hôm nay - 180 ngày>,has-abstract:true`, xin dư `24 × 3 = 72` dòng. Payload thô được lưu nguyên trạng vào `data/raw/crossref_response.json`. `parse_crossref_payload()` gỡ thẻ XML/HTML trong abstract, chuẩn hóa `date-parts` thành `YYYY-MM-DD`, ghép tên tác giả, suy ra `categories` (fallback venue/type/publisher vì 0/24 record có trường `subject`), loại bài không phải chữ Latin và bài có abstract dưới 80 ký tự, rồi cắt còn 24 record ghi vào `data/raw/crossref_records.json`. `build_clean_dataframe()` biến 24 record đó thành frame 16 cột, tính thêm `age_days`, `title_chars`, `summary_chars`, khử trùng hai lượt (theo `paper_id` rồi theo `title` viết thường), sắp xếp `published` giảm dần, và quan trọng nhất là ghép cột `text_for_embedding` = `title + authors + categories + published + summary`. Cuối cùng `LocalEmbeddingIndex.build()` cho `sentence-transformers/all-MiniLM-L6-v2` mã hóa **cột `text_for_embedding`** rồi `add()` vào ChromaDB (`PersistentClient` tại `data/chroma/`, `space = cosine`), kèm metadata gồm `paper_id`, `title`, `published`, `authors_joined`, `categories_joined`, `summary`, `abs_url`, `pdf_url`. Ba trạng thái dùng ba collection tách biệt: `papers-baseline`, `papers-corrupted`, `papers-repaired`.

**2. Test set và ground-truth document IDs.** `build_test_set()` chọn 5 paper trải đều trên dataset (`df.iloc[::4]`) rồi sinh 4 câu hỏi cho mỗi paper — `authors`, `date`, `categories`, `summary` — tổng cộng **20 sample**. Mỗi sample lưu `ground_truth` (lấy trực tiếp từ frame sạch) và `ground_truth_doc_ids` (đúng một `paper_id`). Khi chấm, `evaluate_pipeline()` gọi `answer_question()` lấy `top_k = 4` document rồi tính hai loại chỉ số khác nhau:
   - **Retrieval:** `retrieval_hit = any(doc_id in ground_truth_doc_ids for doc_id in retrieved_doc_ids)` — chỉ hỏi "document đúng có nằm trong top-4 không", hoàn toàn không quan tâm câu trả lời.
   - **Answer quality:** `token_f1` so trùng tập token giữa câu trả lời và `ground_truth`, còn LLM judge (structured output Pydantic: `score` 1–5, `correct` bool, `reasoning`) chấm về mặt ngữ nghĩa. Nhờ tách đôi như vậy mà có thể phân biệt "lấy nhầm tài liệu" với "lấy đúng tài liệu nhưng nội dung tài liệu đã hỏng" — chính là trường hợp q008 và q012 ở mục 8.

**3. Quality checks khác freshness monitoring.** `run_data_quality_checks()` chạy **12 check trên 5 chiều** — completeness, uniqueness, validity, consistency, freshness — và trả lời câu hỏi "dữ liệu có *đúng* không": có dòng nào rỗng, có `paper_id` trùng, `title_chars` có khớp `len(title)`, `published` có đúng định dạng `YYYY-MM-DD`. Đó là kiểm tra dạng pass/fail theo dòng. `build_freshness_report()` thì trả lời câu hỏi "dữ liệu có *mới* không" và xuất ra các đại lượng liên tục để theo dõi theo thời gian: `latest_published`, `oldest_published`, `stale_rows`, `stale_ratio`, `max/min/mean_age_days`, `is_fresh`, kèm danh sách `stale_paper_ids` để truy vết. Hai thứ giao nhau đúng ở một điểm: check `freshness_within_threshold` (`age_days > 180`) là ảnh chụp nhị phân của cùng tín hiệu mà freshness report mô tả chi tiết. Trên dữ liệu corrupted, check này chỉ nói "FAIL, 4/23 dòng", còn freshness report nói thêm rằng `mean_age_days` nhảy từ **83.33 lên 278.7**, `max_age_days` từ **175 lên 1256**, và chỉ đích danh 4 `paper_id` bị đẩy lùi ngày. Quality check dùng để **chặn** (gate) dữ liệu xấu; freshness report dùng để **quan sát** xu hướng.

**4. Vì sao phải dùng cùng test set cho cả ba trạng thái.** Vì test set và `ground_truth` được sinh **từ dữ liệu sạch**. Nếu sinh lại test set từ frame corrupted thì `ground_truth` của câu hỏi summary sẽ chính là chuỗi rỗng hoặc chuỗi rác, câu hỏi ngày tháng sẽ lấy đúng ngày đã bị đẩy lùi — agent trả về rác và vẫn được chấm 5/5. Metric sẽ "đẹp" trên dữ liệu hỏng, tức là phép đo tự phá chính nó. Trong code, `phase1._load_or_build_test_set()` cố tình đọc lại `data/eval/test_set.json` nếu file đã tồn tại và chỉ tạo mới khi bật `REFRESH_TEST_SET`, còn `corruption_flow` truyền thẳng `settings.paths.eval_testset` cho cả hai lần đánh giá của nó (corrupted ở bước 5, repaired ở bước 8) và không chấm lại baseline mà nạp thẳng `data/results/baseline_metrics.json` do phase 1 sinh ra trên đúng file test set đó. Nhờ đó cả ba trạng thái đều là **20 sample giống hệt**, và chênh lệch `1.0000 → 0.6684 → 1.0000` của `mean_token_f1` chỉ có thể do dữ liệu, không do phép đo.

**5. Repair thành công dựa trên artifact và metric nào.** Repair không phải là vá frame corrupted mà là **dựng lại từ snapshot nguồn đáng tin cậy**: `corruption_flow` bước 7 gọi `load_raw_records(data/raw/crossref_records.json)` rồi `build_clean_dataframe()` lại từ đầu — cùng đúng con đường mà baseline đã đi. Kết luận thành công dựa trên ba nhóm bằng chứng độc lập:
   - **Số dòng:** `data/clean/papers_clean_repaired.csv` có 24 dòng, đúng bằng baseline (corrupted chỉ 23).
   - **Tín hiệu dữ liệu:** `data/quality/repaired_quality.json` báo `passed_checks = 12`, `failed_checks = 0`, `failed_check_names = []`, `total_failed_rows = 0`; `data/quality/freshness_report_repaired.json` báo `is_fresh = true`, `stale_rows = 0`, `stale_ratio = 0.0`, `max_age_days = 175`, `mean_age_days = 83.33` — trùng khít với freshness report của baseline.
   - **Metric của agent:** `data/results/repaired_metrics.json` cho `retrieval_hit_rate = 1.0`, `mean_token_f1 = 1.0`, `judge_accuracy = 1.0`, `mean_judge_score = 5` trên đúng 20 sample cũ.
   Ba nhóm bằng chứng phải cùng phục hồi thì mới kết luận repair thành công. Nếu chỉ metric hồi mà quality vẫn FAIL thì nhiều khả năng lỗi nằm ở phép đo chứ không phải dữ liệu đã lành.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |   1.0000 |    0.8000 |   1.0000 | Giảm đúng 0.2000 = 4/20 câu, và cả 4 câu đó (q001–q004) đều thuộc paper `10.2118/234689-pa` bị `drop_latest_records` xóa. Đây là metric duy nhất chỉ bị **một** loại corruption tác động. |
| `mean_token_f1`      |   1.0000 |    0.6684 |   1.0000 | Giảm 0.3316. Tách theo loại câu hỏi: summary 0.4190, date 0.6000, authors 0.8000, categories 0.8545 — câu summary chịu thiệt nặng nhất vì bị cả blank lẫn noise đánh vào. |
| `judge_accuracy`     |   1.0000 |    0.6500 |   1.0000 | Giảm 0.3500, tức 7/20 câu bị chấm sai: q001–q004 (mất document), q008 (summary rỗng), q012 (summary rác), q018 (ngày sai). |
| `mean_judge_score`   |   5.0000 |    3.6000 |   5.0000 | Giảm 1.4000/5.0. Theo loại câu hỏi: summary 2.60, date 3.40, authors 4.20, categories 4.20. |
| Quality checks         |    12/12 |      7/12 |    12/12 | 5 check FAIL trên corrupted: `paper_id_unique` (2 dòng), `title_min_length` (3), `summary_not_empty` (3), `summary_min_length` (3), `freshness_within_threshold` (4). Tổng `total_failed_rows = 15`. |
| Freshness status       | fresh (0/24 stale) | **NOT fresh** (4/23 stale) | fresh (0/24 stale) | `stale_ratio` 0.0 → 0.1739 → 0.0; `mean_age_days` 83.33 → 278.7 → 83.33; `max_age_days` 175 → 1256 → 175; `oldest_published` 2026-02-12 → 2023-02-26 → 2026-02-12. |

Số dòng dữ liệu: baseline **24** → corrupted **23** (xóa 3, thêm 2 bản trùng) → repaired **24**. Cả ba trạng thái được chấm trên cùng `data/eval/test_set.json` gồm 20 câu hỏi / 5 paper / 4 loại câu hỏi.

### Kết luận từ số liệu

1. **Corruption → tín hiệu quality/freshness → metric agent.**
   `corrupt_clean_dataframe()` chạy 7 bước (xóa 3 dòng mới nhất, xóa trắng 3 summary, chèn 153 ký tự rác vào 3 summary, cắt 3 title còn 8 ký tự, đẩy lùi 4 ngày đi 3 năm, thêm 2 dòng trùng, dựng lại `text_for_embedding` cho cả 23 dòng)
   → `corrupted_quality.json` rớt từ 12/12 xuống **7/12** với 5 check FAIL trên 15 dòng lỗi, và `freshness_report_corrupted.json` chuyển `is_fresh` từ `true` sang **`false`** với `stale_rows = 4/23`, `mean_age_days` tăng gấp 3.3 lần (83.33 → 278.7)
   → `corrupted_metrics.json` cho `retrieval_hit_rate` **1.0000 → 0.8000**, `mean_token_f1` **1.0000 → 0.6684**, `judge_accuracy` **1.0000 → 0.6500**, `mean_judge_score` **5.0000 → 3.6000**.

2. **Repair → tín hiệu quality/freshness phục hồi → metric agent phục hồi.**
   `corruption_flow` bước 7 dựng lại frame từ `data/raw/crossref_records.json` (24 raw record) thay vì vá frame hỏng, rồi build lại collection `papers-repaired`
   → `repaired_quality.json` quay lại **12/12 pass**, `failed_check_names = []`, `total_failed_rows = 0`; `freshness_report_repaired.json` quay lại `is_fresh = true`, `stale_rows = 0`, `mean_age_days = 83.33` — **trùng khít từng con số** với freshness report của baseline
   → `repaired_metrics.json` quay lại **1.0000 / 1.0000 / 1.0000 / 5.0000**, tức phục hồi **hoàn toàn** về mức baseline, không chỉ "cải thiện một phần".

Corruption nào ảnh hưởng rõ nhất và vì sao?

**`drop_latest_records` (xóa 3 dòng mới nhất) là loại gây hại rõ nhất**, và kết luận này đọc thẳng ra được từ `corrupted_answers.json`:

| Loại corruption | Số câu hỏi bị hỏng | Metric bị ảnh hưởng |
| ----------------- | ---------------------: | --------------------- |
| `drop_latest_records` | **4/20** (q001–q004) | cả 4 metric, và là **nguyên nhân duy nhất** làm `retrieval_hit_rate` giảm |
| `blank_summary` | 1/20 (q008) | `token_f1`, `judge_*` |
| `inject_noise` | 1/20 (q012) | `token_f1`, `judge_*` |
| `stale_dates` | 1/20 (q018) | `token_f1`, `judge_*` |
| `truncate_title` | **0/20** | không metric nào |
| `duplicate_rows` | **0/20** | không metric nào (chỉ làm `paper_id_unique` FAIL) |

Lý do `drop_latest_records` nặng nhất: các loại corruption khác chỉ **làm bẩn** nội dung của một document vẫn còn nằm trong index, nên retrieval vẫn tìm đúng `paper_id` và chỉ câu trả lời bị sai. Riêng việc xóa dòng thì **rút hẳn document ra khỏi corpus** — không còn gì để tìm. Với q001–q004, top-4 trả về `10.55041/isjem07213` và `10.21203/rs.3.rs-9882260/v1`, tức agent tự tin trả lời bằng tài liệu của một bài báo hoàn toàn khác: hỏi tác giả bài SafeRAG thì nhận về `"Dr. Sumalatha P, Manoj Kumar"` thay vì `"Qianwen Cao, Chiyu Zhang, Junxiong Ning, Gongru Li"`. Đây là dạng lỗi nguy hiểm nhất trong RAG — hệ thống không hề báo lỗi mà trả về câu trả lời sai một cách trôi chảy. Một chi tiết nữa: chỉ mình `drop_latest_records` chạm vào **cả 4 câu hỏi** của một paper (một paper = 4 câu hỏi trong test set), trong khi các loại còn lại chỉ phá được một loại câu hỏi cụ thể của paper mà nó chạm tới.

Kết quả nào khác với kỳ vọng ban đầu?

**`truncate_title` không gây ra bất kỳ thiệt hại đo được nào** — hoàn toàn trái với dự đoán. Giả thuyết ban đầu là: cắt tiêu đề `10.22214/ijraset.2026.82233` còn 8 ký tự (`"Hybrid G"`) sẽ phá cơ chế tra cứu chính xác của `qa.answer_question()`, vì hàm này bắt tiêu đề trong dấu nháy đơn bằng regex `r"'([^']+)'"` rồi gọi `index.lookup()` — mà `documents_by_title` giờ chỉ còn khóa `"hybrid g"`, không thể khớp tiêu đề đầy đủ trong câu hỏi. Dự đoán là 4 câu q013–q016 sẽ hỏng.

Đã kiểm tra bằng cách mở `data/results/corrupted_answers.json` và lọc riêng q013–q016. Kết quả thực tế: cả 4 câu vẫn `retrieval_hit = true`, `token_f1 = 1.000`, judge `correct = true` với score 5. Nguyên nhân: `lookup()` đúng là thất bại, nhưng `answer_question()` **luôn chạy song song** `index.search(question)` và chỉ ưu tiên kết quả `lookup` khi nó có giá trị. Ở đây tìm kiếm ngữ nghĩa vẫn xếp `10.22214/ijraset.2026.82233` ở hạng 1, vì `text_for_embedding` còn nguyên 4 thành phần khác (authors, categories, published, summary) — tiêu đề chỉ là một phần nhỏ trong vector.

Bài học rút ra là quan hệ giữa data quality và chất lượng agent **không phải một-một**: `truncate_title` làm check `title_min_length` FAIL trên 3 dòng và `duplicate_rows` làm `paper_id_unique` FAIL trên 2 dòng, nhưng cả hai đều không làm suy giảm bất kỳ metric nào. Nói cách khác, **2 trong 5 check FAIL của trạng thái corrupted không có hệ quả đo được ở đầu ra**. Điều này không có nghĩa hai check đó vô dụng — chúng bắt được lỗi thật, và tiêu đề cụt vẫn sẽ hiển thị sai cho người dùng — nhưng nó cảnh báo rằng không nên suy diễn ngược từ "check FAIL" ra "agent chắc chắn tệ đi", cũng như không nên suy từ "metric không đổi" ra "dữ liệu vẫn ổn".

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về data pipeline: snapshot dữ liệu thô là thứ đắt giá nhất trong toàn bộ pipeline.** Bước repair không hề "sửa" gì cả — nó gọi `load_raw_records(data/raw/crossref_records.json)` rồi `build_clean_dataframe()` lại từ đầu, tức đi đúng con đường baseline đã đi. Nhờ có snapshot thô mà việc phục hồi trở thành *tái dựng* thay vì *vá lỗi*: kết quả là 24/24 dòng và 12/12 check quay lại nguyên trạng, không sót lỗi tồn dư. Nếu chỉ lưu frame đã làm sạch thì không thể phục hồi 3 dòng bị xóa, vì thông tin đó đã biến mất khỏi mọi artifact hạ nguồn. Hệ quả thiết kế: mọi biến đổi phá hủy phải luôn đứng *sau* một điểm lưu bất biến.

2. **Về data quality/observability: quality check và freshness monitoring trả lời hai câu hỏi khác nhau và không thay thế được nhau.** 12 check trả lời "dữ liệu có đúng không" bằng pass/fail (corrupted: 7/12, 15 dòng lỗi), còn freshness report trả lời "dữ liệu có mới không" bằng các đại lượng liên tục (`mean_age_days` 83.33 → 278.7, `max_age_days` 175 → 1256, `stale_ratio` 0 → 0.1739, kèm 4 `paper_id` cụ thể). Nếu chỉ nhìn quality check thì chỉ biết "có 4 dòng quá hạn"; phải mở freshness report mới thấy `oldest_published` tụt từ 2026-02-12 về 2023-02-26 — tức là bản chất lỗi là ngày bị đẩy lùi 3 năm, chứ không phải dữ liệu cũ dần theo thời gian. Gate cần pass/fail, còn chẩn đoán cần số liệu liên tục.

3. **Về ảnh hưởng của data đến RAG agent: hỏng dữ liệu không làm agent báo lỗi, nó làm agent tự tin trả lời sai.** Không có một exception nào được ném ra trong suốt lần chạy corrupted — pipeline chạy hết 10/10 bước, sinh đủ artifact, và trả về 20/20 câu trả lời. Chỉ khi đối chiếu với ground truth mới lộ ra q001 trả về tác giả của một bài báo khác, q008 trả về chuỗi rỗng, q012 trả về `"LOREM IPSUM DOLOR ###### CORRUPTED PAYLOAD @@@@@@."`, q018 trả về `2023-05-01` thay vì `2026-05-01`. Điều này giải thích vì sao evaluation phải tách `retrieval_hit_rate` khỏi `token_f1`: q001 sai vì *lấy nhầm tài liệu* (`retrieval_hit = false`), còn q008 và q012 sai vì *tài liệu đúng nhưng nội dung đã hỏng* (`retrieval_hit = true`, `token_f1 = 0.000`). Gộp chung một chỉ số thì mất hẳn khả năng chẩn đoán này.

### Nếu có thêm thời gian

**Cải thiện đề xuất: biến bộ quality check thành một gate chặn thật sự đứng trước bước index, thay vì một báo cáo chạy sau khi mọi thứ đã xong.**

Hiện tại `run_data_quality_checks()` được gọi ở bước 8/10 của `phase1.py` — tức là **sau** khi index đã build (bước 5) và evaluation đã chạy (bước 7). Trên trạng thái corrupted, hệ quả là dữ liệu hỏng vẫn được embed và đưa vào ChromaDB một cách bình thường; chỉ đến cuối mới có một file JSON nói rằng 5 check đã FAIL. Trong môi trường thật thì đó chính là kịch bản index đã bị nhiễm bẩn.

Cách làm: thêm hàm `assert_quality_gate(df, settings)` chạy ngay sau `build_clean_dataframe()` và trước `LocalEmbeddingIndex.build()`. Gate chia mức độ nghiêm trọng — nhóm *blocking* (`paper_id_unique`, `summary_not_empty`, `text_for_embedding_present`, `row_count`) thì raise `RuntimeError` và dừng pipeline; nhóm *warning* (`freshness_within_threshold`, `title_min_length`) thì chỉ in cảnh báo rồi đi tiếp. Phân nhóm này không tùy tiện mà dựa vào bằng chứng ở mục 8: `summary_not_empty` FAIL kéo `token_f1` của q008 xuống 0.000 nên phải chặn, còn `title_min_length` FAIL mà 4 câu q013–q016 vẫn đạt 1.000 nên chỉ cần cảnh báo.

**Cách đo cải thiện** (có tiêu chí đạt/không đạt rõ ràng, chạy lại được):

1. Chạy `python script/run_corruption_flow.py` như hiện tại và ghi lại mốc: pipeline chạy hết 10/10 bước, collection `papers-corrupted` được tạo với 23 document, `corrupted_metrics.json` ghi `judge_accuracy = 0.6500`.
2. Bật gate rồi chạy lại. **Tiêu chí đạt:** pipeline dừng ở bước build index với `RuntimeError` nêu đích danh `summary_not_empty` (3 dòng) và `paper_id_unique` (2 dòng); collection `papers-corrupted` **không** được tạo thêm document nào; không có file `corrupted_metrics.json` mới nào được ghi.
3. Chạy `python script/run_phase1.py` trên dữ liệu sạch để kiểm tra không có báo động giả. **Tiêu chí đạt:** vẫn chạy hết 10/10 bước và `baseline_metrics.json` giữ nguyên `1.0000 / 1.0000 / 1.0000 / 5.0000`.
4. **Chỉ số theo dõi:** số document hỏng lọt vào ChromaDB, hiện tại là 23/23 trên trạng thái corrupted, mục tiêu là 0/23. Đây là con số đếm được trực tiếp từ manifest `data/embeddings/papers_embeddings_corrupted.json`, không cần suy diễn.

## 10. Cam kết của thành viên

<!-- CAN DIEN: CHI thanh vien moi duoc tich cac o duoi day, va chi tich sau khi da tu doc lai
     toan bo bao cao va doi chieu voi artifact thuc te. De trong neu chua tu kiem tra. -->

Đánh dấu sau khi tự kiểm tra:

- [ ] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [ ] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [ ] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [ ] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [ ] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [ ] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

<!-- CAN DIEN: Ho ten va ngay xac nhan phai do chinh thanh vien dien. -->

**Họ và tên:** [Họ và tên]
**Ngày xác nhận:** [YYYY-MM-DD]
