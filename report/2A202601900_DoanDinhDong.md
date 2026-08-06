# Member Role Report — Day 10: Data Pipeline & Data Observability

> Báo cáo vai trò cá nhân của **Đoàn Đình Đông (2A202601900)** — nhóm trưởng nhóm DingDong. Nội dung dưới đây chỉ mô tả phần việc do cá nhân tôi trực tiếp thực hiện, không sao chép báo cáo nhóm hay báo cáo của thành viên khác.

> **Lưu ý về provider LLM:** run đã nộp chạy với `provider=groq`, `model=openai/gpt-oss-20b` (xác minh tại `data/reports/phase1_report.md`, mục 1: `llm_provider | groq`, `llm_model | openai/gpt-oss-20b`). Groq là provider mặc định trong `src/core/config.py` (`LLM_PROVIDER=groq`, `LLM_MODEL=openai/gpt-oss-20b`); project cũng hỗ trợ gemini, openai, anthropic, openrouter, ollama và custom qua biến `LLM_PROVIDER`. **Nếu chạy lại pipeline trên provider khác thì phải cập nhật lại hai trường provider/model ở mọi chỗ báo cáo này nhắc tới chúng**, vì `judge_accuracy` và `mean_judge_score` phụ thuộc trực tiếp vào LLM judge.

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Đoàn Đình Đông |
| MSSV               | 2A202601900 |
| Khóa/Lớp         | K3 |
| Tên nhóm         | DingDong (4 thành viên) |
| Vai trò chính    | Nhóm trưởng — Reporting, Baseline orchestration, Corruption & repair owner |
| Repository         | https://github.com/doandinhdong14-afk/K3_Day10_DingDong |
| Ngày hoàn thành | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

### Danh mục 7 khối deliverable của project (để chọn phần việc của mình)

Bảng dưới đây liệt kê đúng 7 khối deliverable của project và file/artifact thực tế mà mỗi khối chịu trách nhiệm. Các khối được **in đậm** là khối tôi trực tiếp làm.

| # | Khối deliverable           | File nguồn phụ trách                                              | Artifact phải bàn giao                                                                                                             |
| -: | -------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| 1 | Raw ingestion              | `src/ingestion/crossref.py`                                       | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` (24 raw records)                                              |
| 2 | Cleaning & data modeling   | `src/ingestion/cleaning.py`                                       | `data/clean/papers_clean.csv`, `data/clean/papers_clean.json` (24 dòng × 16 cột, có `text_for_embedding`)                     |
| 3 | Evaluation set             | `src/evaluation/testset.py`                                       | `data/eval/test_set.json` (20 câu hỏi / 5 paper / 4 loại câu hỏi)                                                              |
| 4 | Quality & freshness        | `src/observability/quality.py`                                    | `data/quality/baseline_quality.json`, `corrupted_quality.json`, `repaired_quality.json`, 3 file `freshness_report*.json`      |
| **5** | **Reporting**              | **`src/observability/reporting.py`**                              | **`data/reports/phase1_report.md`, `data/reports/corruption_report.md`, `data/reports/answer_diff.md`**                         |
| **6** | **Baseline orchestration** | **`src/pipelines/phase1.py`, `src/retrieval/index.py`**           | **`data/results/baseline_metrics.json`, `baseline_answers.json`, `agent_demo_answers.json`, `data/embeddings/`, `data/chroma/`** |
| **7** | **Corruption & repair**    | **`src/ingestion/corruption.py`, `src/pipelines/corruption_flow.py`** | **`data/results/corruption_log.json`, `corrupted_metrics.json`, `repaired_metrics.json` + bộ CSV/JSON corrupted/repaired**     |

Các khối phụ trợ dùng chung (không tính là deliverable riêng): `src/core/config.py` (đường dẫn + tham số `max_results=24`, `top_k=4`, `freshness_threshold_days=180`), `src/retrieval/qa.py`, `src/retrieval/llm.py`, `src/retrieval/agent.py`, `src/evaluation/metrics.py`.

Nhóm chia theo cấu hình 4 người khuyến nghị trong [`README.md`](README.md) mục 5, có một điều chỉnh: `reporting.py` (khối 5) được tách khỏi Observability owner và chuyển sang tôi, vì cả ba file report đều phải đọc output của hai flow do tôi điều phối. Observability owner vì vậy giữ nguyên `quality.py` (khối 4).

| Họ và tên | MSSV | Vai trò | Khối sở hữu | Báo cáo cá nhân |
| ----------- | ------ | --------- | ------------- | ----------------- |
| Trần Hoài Nam | 2A202601751 | Source owner | Khối 1 — `crossref.py` | [`2A202601751_TranHoaiNam.md`](2A202601751_TranHoaiNam.md) |
| Dương Hải Long | 2A202601607 | Data model & evaluation-set owner | Khối 2, 3 — `cleaning.py`, `testset.py` | [`2A202601607_DuongHaiLong.md`](2A202601607_DuongHaiLong.md) |
| Đặng Quang Minh | 2A202601459 | Observability owner | Khối 4 — `quality.py` | [`2A202601459_DangQuangMinh.md`](2A202601459_DangQuangMinh.md) |
| **Đoàn Đình Đông (leader)** | **2A202601900** | **Reporting, orchestration & corruption owner** | **Khối 5, 6, 7 + điều phối tích hợp** | báo cáo này |

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | ------------ |
| Khối 5 — Reporting | `src/observability/reporting.py`: `generate_phase1_report()`, `generate_corruption_report()`, `generate_answer_diff_report()` | `*_metrics.json`, `*_quality.json`, `freshness_report*.json`, `*_answers.json` | `data/reports/phase1_report.md` (3904 B), `corruption_report.md` (2951 B), `answer_diff.md` (5936 B) | Hoàn thành |
| Khối 6 — Baseline orchestration | `src/pipelines/phase1.py` (10 bước), `src/retrieval/index.py` (`LocalEmbeddingIndex`) | 24 raw record từ khối 1, clean frame từ khối 2, test set từ khối 3 | `data/results/baseline_metrics.json`, `baseline_answers.json` (20 câu), `agent_demo_answers.json` (2 câu), `data/embeddings/papers_embeddings.json` (24 doc), collection `papers-baseline` | Hoàn thành |
| Khối 7 — Corruption & repair | `src/ingestion/corruption.py` (`corrupt_clean_dataframe()`, `_pick_positions()`, `_shift_year_back()`), `src/pipelines/corruption_flow.py` (10 bước) | `data/clean/papers_clean.json` (corrupt), `data/raw/crossref_records.json` (repair), `data/eval/test_set.json`, `baseline_metrics.json` | `corruption_log.json` (7 step, 24→23 dòng), `corrupted_metrics.json`, `repaired_metrics.json`, `papers_clean_corrupted.*`, `papers_clean_repaired.*`, collection `papers-corrupted` / `papers-repaired` | Hoàn thành |
| Điều phối tích hợp (vai trò leader) | Chốt contract dùng chung, trình tự chạy, review đầu ra của khối 1–4 trước khi đưa vào flow | Deliverable của 3 thành viên còn lại | Trình tự phụ thuộc bên dưới; kiểm tra `_require_phase1_artifacts()` chặn được flow khi thiếu artifact | Hoàn thành |
| `app/dashboard.py` — Streamlit dashboard (**ngoài yêu cầu bắt buộc**) | `app/dashboard.py` (729 dòng) | Toàn bộ artifact trong `data/` + collection ChromaDB đã build | Dashboard chỉ **đọc** artifact, không chạy lại pipeline, nên mọi con số trên màn hình luôn khớp file | Hoàn thành (phụ trợ) |

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

Vì hai khối cuối của chuỗi này (6 và 7) đều là của tôi, việc quan trọng nhất trong vai trò leader không phải là viết thêm code mà là **giữ cho contract giữa khối 1–4 không đổi giữa các lần chạy**. Cụ thể, `corruption_flow._require_phase1_artifacts()` là chốt chặn tôi đặt ra để flow phase 2 dừng ngay với `RuntimeError` liệt kê từng file thiếu, thay vì chạy tiếp trên artifact cũ và cho ra một bảng so sánh sai.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| ------------ | -------------------------------- | ---------- |
| Debug môi trường: chẩn đoán `ImportError` ở tầng loader do Smart App Control chặn wheel không ký, tìm ra cặp phiên bản chạy được | Cả nhóm — không ai chạy được `python -c "import pandas"` trước khi sửa | `.venv` hiện giữ `pandas 2.3.3` / `pyarrow 21.0.0`; cả hai pipeline chạy hết 10/10 bước. Chi tiết ở mục 6 |
| Phát hiện Crossref **không bao giờ** trả trường `subject`, báo lại cho owner `crossref.py` để thêm nhánh fallback | Trần Hoài Nam — `src/ingestion/crossref.py` (`_format_categories()`) | Đo trực tiếp trên `data/raw/crossref_response.json`: **0/72 item** có `subject`. Sau khi có fallback venue → type → publisher: `data/clean/papers_clean.csv` có 0/24 dòng `categories_joined` rỗng, 0/24 dòng rơi về `uncategorized`. 5 câu hỏi loại `categories` (`q003`, `q007`, `q011`, `q015`, `q019`) đều đạt `token_f1 = 1.0` ở baseline |
| Chốt ràng buộc metadata ChromaDB (chỉ nhận str/int/float/bool) khi build index, báo lại cho owner `cleaning.py` | Dương Hải Long — `src/ingestion/cleaning.py` | `published`/`updated` được giữ nguyên kiểu chuỗi `YYYY-MM-DD` thay vì `pd.Timestamp`. Tôi tuân theo đúng ràng buộc này trong `corruption._shift_year_back()` (luôn trả về string), nhờ đó frame corrupted vẫn index được và pha 2 không sụp |
| Đối chiếu output của `quality.py` với metrics trước khi viết report | Đặng Quang Minh — `src/observability/quality.py` | Xác nhận 12 check chạy được trên cả 3 frame có số dòng khác nhau (24 / 23 / 24) và `_missing_column_check` báo FAIL kèm tên cột thay vì ném `KeyError`. Bằng chứng: `corrupted_quality.json` đọc được trên frame 23 dòng, `total_failed_rows = 15` |
| Viết thêm `generate_answer_diff_report()` để nhóm có bằng chứng ở mức output, không chỉ ở mức metric | Toàn nhóm — dùng cho mục 10 của `group_report.md` | `data/reports/answer_diff.md`: 7/20 câu đổi output khi dữ liệu hỏng, 7/7 quay về đúng sau repair |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------------- | ----------------------------- | ------------------- | --------------- |
| Dựng orchestration 10 bước cho pha 1: nạp settings → raw → clean → index → test set → evaluate → quality → report → agent demo | `src/pipelines/phase1.py`, `src/retrieval/index.py` | `baseline_metrics.json` = `1.0000 / 1.0000 / 1.0000 / 5.0000` trên 20 sample; `papers_embeddings.json` manifest 24 document; collection `papers-baseline` | `python script/run_phase1.py` — khối "TOM TAT ARTIFACT PHASE 1" ở cuối stdout phải toàn `[OK]` |
| Cho phép chạy lại pipeline mà không phá mốc so sánh: `_load_or_build_test_set()` đọc lại test set cũ, chỉ tạo mới khi bật `REFRESH_TEST_SET` | `src/pipelines/phase1.py` | `data/eval/test_set.json` giữ nguyên 8509 B / 20 sample qua mọi lần chạy | Chạy `run_phase1.py` hai lần, kiểm tra `test_set.json` không đổi kích thước và `q001`–`q020` không đổi `ground_truth` |
| Thiết kế 6 loại corruption **không dùng RNG**, canh offset lệch pha với stride của test set | `src/ingestion/corruption.py` (`corrupt_clean_dataframe`, `_pick_positions`) | `corruption_log.json`: 7 step, `source_rows = 24`, `result_rows = 23`, `total_affected_rows = 18`, `deterministic: true`, `selection_stride = 5`, offsets `{blank:1, noise:5, truncate:9, stale:13, duplicate:0}` | `python script/run_corruption_flow.py` rồi mở `data/results/corruption_log.json` |
| Dựng flow repair theo hướng **tái tạo từ raw snapshot**, không vá frame hỏng | `src/pipelines/corruption_flow.py` bước 7 (`load_raw_records` + `build_clean_dataframe`) | `papers_clean_repaired.csv` = 103.200 B, trùng khít từng byte với `papers_clean.csv`; `repaired_metrics.json` = `1.0000 / 1.0000 / 1.0000 / 5.0000` | So MD5 hai file clean; đối chiếu `repaired_metrics.json` với `baseline_metrics.json` |
| Chặn phase 2 chạy trên artifact thiếu | `corruption_flow._require_phase1_artifacts()` | `RuntimeError` liệt kê từng file thiếu và yêu cầu chạy `run_phase1.py` trước | Đổi tên `data/results/baseline_metrics.json` rồi chạy `run_corruption_flow.py` — flow dừng ở bước 2/10 |
| Sinh 3 báo cáo Markdown tự động từ artifact, không gõ tay số liệu | `src/observability/reporting.py`: `generate_phase1_report()`, `generate_corruption_report()`, `generate_answer_diff_report()` | `phase1_report.md`, `corruption_report.md`, `answer_diff.md` | `python script/run_phase1.py` (bước 9/10) và `python script/run_corruption_flow.py` (bước 9/10); đối chiếu bảng trong report với các file `*_metrics.json` |
| Dựng dashboard chỉ-đọc để trình bày kết quả (ngoài yêu cầu) | `app/dashboard.py` | Dashboard nạp artifact trong `data/` và collection đã build sẵn, không chạy lại pipeline | `streamlit run app/dashboard.py` rồi so số trên màn hình với `data/results/*.json` |

### Lệnh xác minh thật của từng khối

| Khối | Lệnh chạy | Artifact phải mở để đối chiếu | Dấu hiệu đạt |
| ---- | ----------- | -------------------------------- | -------------- |
| Tiền đề cho mọi khối gọi LLM | `python script/check_llm.py` | stdout của script | 3 dòng `[OK  ]` cho *chat bình thường*, *structured output*, *tool calling* (ngoài dòng `[OK  ] credentials` in trước đó), kết thúc bằng `KET LUAN: provider san sang`. Nếu *structured output* lỗi thì judge rơi về heuristic dự phòng và `judge_*` mất ý nghĩa. |
| 1. Raw ingestion | `python script/run_phase1.py` (bước 2/10) | `data/raw/crossref_records.json` | file có 24 record, mỗi record đủ `paper_id/title/summary/authors/published` |
| 2. Cleaning | `python script/run_phase1.py` (bước 3–4/10) | `data/clean/papers_clean.csv` | 24 dòng, 16 cột, cột `text_for_embedding` không rỗng |
| 3. Evaluation set | `python script/run_phase1.py` (bước 6/10); ép tạo lại bằng biến môi trường `REFRESH_TEST_SET=1` | `data/eval/test_set.json` | 20 sample, 4 `question_type`, mỗi sample có đúng 1 `ground_truth_doc_ids` |
| 4. Quality & freshness | `python script/run_phase1.py` (bước 8/10) và `python script/run_corruption_flow.py` (bước 6 và 8/10) | `data/quality/baseline_quality.json`, `corrupted_quality.json`, `repaired_quality.json`, `freshness_report*.json` | baseline 12/12 pass, corrupted 7/12 pass với 5 `failed_check_names`, repaired 12/12 pass |
| **5. Reporting (của tôi)** | `python script/run_phase1.py` (bước 9/10), `python script/run_corruption_flow.py` (bước 9/10) | `data/reports/phase1_report.md`, `data/reports/corruption_report.md`, `data/reports/answer_diff.md` | bảng so sánh 3 trạng thái khớp với các file `*_metrics.json` |
| **6. Baseline orchestration (của tôi)** | `python script/run_phase1.py` | `data/results/baseline_metrics.json`, khối "TOM TAT ARTIFACT PHASE 1" ở cuối stdout | `retrieval_hit_rate=1.0`, `mean_token_f1=1.0`, `judge_accuracy=1.0`, `mean_judge_score=5`; mọi dòng artifact là `[OK]` |
| **7. Corruption & repair (của tôi)** | `python script/run_corruption_flow.py` | `data/results/corruption_log.json`, `corrupted_metrics.json`, `repaired_metrics.json` | log có đúng 7 step, `source_rows=24`, `result_rows=23`, `deterministic=true`; repaired trở lại 1.0/1.0/1.0/5.0 |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

**`data/reports/answer_diff.md` (5936 bytes)** là artifact tôi bổ sung ngoài bộ report gốc, sinh bởi hàm `generate_answer_diff_report()` mà tôi viết thêm vào `src/observability/reporting.py` và gọi ở bước 9/10 của `corruption_flow.py`. Hàm này đọc song song ba file `baseline_answers.json`, `corrupted_answers.json`, `repaired_answers.json`, đánh index theo `id` câu hỏi rồi đặt cạnh nhau **câu trả lời thật** mà agent trả về ở ba trạng thái. Kết quả đọc được trong file: 20 câu hỏi trên cùng một evaluation set, **7/20 câu đổi output** khi dữ liệu bị hỏng (`q001`–`q004`, `q008`, `q012`, `q018`) và **7/7 câu quay về đúng** câu trả lời baseline sau khi repair. Lý do tôi bỏ công viết thêm: bốn metric tổng hợp chỉ nói "chất lượng giảm 0.3316", còn file này cho thấy cụ thể agent đã trả lời sai *cái gì* — ví dụ `q001` hỏi tác giả bài SafeRAG thì baseline trả `Qianwen Cao, Chiyu Zhang, Junxiong Ning, Gongru Li` còn corrupted trả `Dr. Sumalatha P, Manoj Kumar` của một bài báo hoàn toàn khác. Output này được nhóm dùng lại làm bằng chứng ở mục 7 và mục 10 của `group_report.md`, vì nó là bằng chứng ở mức output, độc lập với mọi chỉ số tổng hợp.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Pipeline phải chứng minh được một quan hệ nhân quả: **chất lượng dữ liệu quyết định chất lượng câu trả lời của RAG agent**. Muốn chứng minh được thì mọi bước từ nguồn Crossref đến vector index phải xác định (deterministic), mọi artifact trung gian phải ghi ra đĩa để đối chiếu, và ba trạng thái baseline / corrupted / repaired phải được chấm trên **cùng một** test set. Nếu một bước nào đó tự ý đổi dữ liệu (ví dụ sinh lại test set từ dữ liệu đã hỏng), phép so sánh mất hết ý nghĩa.

Đây chính là phần khó của khối 6 và khối 7 mà tôi phụ trách: mỗi khối phía trước chỉ cần đúng ở đầu ra của mình, còn hai flow orchestration phải giữ cho **cả ba lần đo nằm trên cùng một thước**.

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

Bốn quyết định kỹ thuật đáng chú ý trong luồng này (hai điểm đầu thuộc khối 1–2 của thành viên khác, tôi ghi lại vì chúng ràng buộc trực tiếp code của tôi ở khối 6–7):

1. **Over-fetch rồi lọc.** `fetch_source_records()` xin `max_results * 3 = 72` dòng từ Crossref rồi mới lọc, vì bộ lọc phía client loại khá nhiều record (thiếu abstract, abstract dưới 80 ký tự, không phải chữ Latin). Nếu chỉ xin đúng 24 dòng thì sau khi lọc sẽ không đủ dữ liệu.
2. **`text_for_embedding` là văn bản duy nhất được embed.** Cột này ghép `title + authors + categories + published + summary` thành một đoạn. Đây là lý do một corruption chỉ chạm vào `summary` vẫn làm thay đổi vector của cả document — và cũng là lý do bước `rebuild_embedding_text` trong `corruption.py` là **bắt buộc**: nếu bỏ nó, dữ liệu hỏng chỉ nằm trong CSV còn vector vẫn sạch, toàn bộ phép đo của pha 2 sẽ vô nghĩa.
3. **`published`/`updated` giữ nguyên kiểu chuỗi.** Cleaning ghi `published.date().isoformat()` chứ không giữ `Timestamp`, vì metadata của ChromaDB chỉ nhận kiểu nguyên thủy (str/int/float/bool). Bước corruption cũng phải tuân theo ràng buộc này — hàm `_shift_year_back()` của tôi luôn trả về string.
4. **Router theo từ khóa trong `qa.py` quyết định cách viết câu hỏi.** `_extract_answer()` chọn trường metadata theo cụm từ trong câu hỏi ("who authored" → `authors_joined`, "when was" → `published`, "what categories" → `categories_joined`, còn lại → `first_sentence(summary)`). Vì vậy `testset.py` phải sinh câu hỏi đúng theo các cụm đó, bọc tiêu đề trong dấu nháy đơn để regex `r"'([^']+)'"` của `answer_question()` bắt được, và loại các paper có tiêu đề chứa dấu nháy đơn hoặc chứa chính các cụm routing.

### Input, output và contract

Bảng dưới đây thu hẹp vào đúng ba khối tôi sở hữu.

| Thành phần | Mô tả |
| ------------ | ------- |
| Input | **Khối 6:** `data/clean/papers_clean.json` (24 dòng × 16 cột) từ khối 2 và `data/eval/test_set.json` (20 sample) từ khối 3. **Khối 7:** thêm `data/results/baseline_metrics.json` và `data/raw/crossref_records.json` (24 `PaperRecord`, 11 trường). **Khối 5:** các file `*_metrics.json`, `*_quality.json`, `freshness_report*.json`, `*_answers.json`. Tham số lấy từ `src/core/config.py`: `max_results=24`, `top_k=4`, `freshness_threshold_days=180` |
| Output | **Khối 6:** `baseline_metrics.json`, `baseline_answers.json` (20 câu đầy đủ), `agent_demo_answers.json` (2 câu), `data/embeddings/papers_embeddings.json` (manifest: backend, embedding_model, persist_path, collection_name, documents — 24 doc), collection `papers-baseline` trong `data/chroma/`. **Khối 7:** `corruption_log.json` (7 step), `papers_clean_corrupted.{csv,json}` (23 dòng), `papers_clean_repaired.{csv,json}` (24 dòng), `corrupted_metrics.json`, `repaired_metrics.json`, manifest `_corrupted` (23 doc) và `_repaired` (24 doc), collection `papers-corrupted` / `papers-repaired`. **Khối 5:** ba file Markdown trong `data/reports/` |
| Module phụ thuộc | `src/core/config.py` (đường dẫn + ngưỡng), `src/core/utils.py` (`read_json`/`write_json`/`write_csv`/`write_text`, `normalize_whitespace`, `now_utc`), `src/ingestion/cleaning.py` (`build_clean_dataframe` — dùng lại nguyên vẹn ở bước repair), `src/ingestion/crossref.py` (`load_raw_records`), `src/evaluation/metrics.py` (`evaluate_pipeline`), `src/observability/quality.py` (12 check + freshness), `src/retrieval/qa.py` và `src/retrieval/agent.py` |
| Module sử dụng output | `src/observability/reporting.py` đọc lại toàn bộ metrics/quality/answers của tôi; `app/dashboard.py` đọc mọi artifact trong `data/`; và bản thân `corruption_flow.py` đọc `baseline_metrics.json` do `phase1.py` sinh ra — nghĩa là khối 6 là input trực tiếp của khối 7 |
| Điều kiện lỗi cần xử lý | Xem bảng chi tiết ngay bên dưới |

Các điều kiện lỗi **thực sự** đã được xử lý trong code (không phải giả định). Bốn dòng cuối nằm trong code của tôi:

| Điều kiện lỗi | Vị trí xử lý | Cách xử lý |
| --------------- | -------------- | ------------ |
| Crossref trả HTTP 429/500/502/503/504 hoặc `requests.RequestException` | `crossref._get_with_retry()` | Thử tối đa 5 lần, thời gian chờ khởi điểm 1s và nhân đôi sau mỗi lần (1→2→4→8s). Hết 5 lần thì raise `RuntimeError` kèm lỗi cuối cùng. |
| Crossref không có trường `subject` | `crossref._format_categories()` | Fallback sang `container-title` → `type` → `publisher`; nếu vẫn rỗng thì gán `["uncategorized"]`. **Đo thực tế: 0/72 item của run này có trường `subject`**, nghĩa là toàn bộ giá trị `categories_joined` trong dataset đều đến từ nhánh fallback. |
| ChromaDB metadata chỉ nhận kiểu nguyên thủy | `cleaning.build_clean_dataframe()` và `corruption._shift_year_back()` | `published`/`updated` luôn được ghi dưới dạng chuỗi `YYYY-MM-DD`, không giữ `pd.Timestamp`. |
| Abstract rỗng hoặc quá ngắn | `crossref.parse_crossref_payload()` (`MIN_SUMMARY_CHARS = 80`) và `cleaning.build_clean_dataframe()` (kiểm tra lại lần hai) | Bỏ hẳn record. Đây cũng chính là ngưỡng mà check `summary_min_length` dùng lại, nên baseline luôn 0 dòng vi phạm. |
| Bài không phải chữ Latin | `crossref._looks_latin()` | Yêu cầu ≥70% ký tự chữ cái là ASCII trên cả `title` lẫn `summary`, vì MiniLM-L6-v2 chỉ mạnh với tiếng Anh. |
| Ngày tháng hỏng | `crossref._format_date()`, `cleaning._parse_date()`, `corruption._parse_iso_date()` | Thiếu tháng/ngày thì mặc định 1; ngày không hợp lệ thì lùi về `YYYY-01-01`; parse thất bại thì bỏ dòng ở cleaning. |
| Trùng lặp bản ghi | `crossref.parse_crossref_payload()` (set `seen_ids`) + `cleaning` (khử theo `paper_id`, rồi khử theo `title` viết thường) | Hai lượt khử độc lập; nhờ vậy baseline đạt `paper_id_unique` = PASS. |
| Dataframe thiếu cột | `quality.run_data_quality_checks()` (`_missing_column_check`) và **`corruption._require_columns()`** | Quality báo FAIL kèm tên cột thay vì ném `KeyError`; corruption raise `ValueError` liệt kê cột thiếu. |
| **Frame nguồn quá ít dòng để corrupt** | **`corruption.corrupt_clean_dataframe()`, hằng số `MIN_SOURCE_ROWS = 8`** | Từ chối chạy nếu frame nhỏ hơn 8 dòng, vì 6 loại corruption trên frame quá nhỏ sẽ chồng lên nhau và không còn tách được ảnh hưởng. Giá trị này được ghi lại vào `corruption_log.json` (`"min_source_rows": 8`) để audit. |
| LLM judge gọi thất bại | `metrics._judge_answer()` | Bắt exception rồi rơi về giám khảo heuristic dựa trên `token_f1` (≥0.95 → 5, ≥0.5 → 3, còn lại → 1) và ghi rõ lý do vào trường `reasoning`. |
| **Agent demo lỗi (rate limit, tool calling không hỗ trợ)** | **`phase1._run_agent_demo()`** | Chỉ in cảnh báo rồi đi tiếp — lỗi LLM ở bước demo không được phép làm hỏng các artifact đã sinh ở bước 1–9. |
| **Thiếu artifact của phase 1 khi chạy phase 2** | **`corruption_flow._require_phase1_artifacts()`** | Raise `RuntimeError` liệt kê từng file thiếu và yêu cầu chạy `script/run_phase1.py` trước. |

### Cách xác minh

```bash
python script/check_llm.py
python script/run_phase1.py
python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** `check_llm.py` trả về 3 dòng `[OK  ]`; `run_phase1.py` in 10 bước và khối tổng kết artifact toàn `[OK]`; `run_corruption_flow.py` in bảng so sánh 3 trạng thái, trong đó corrupted thấp hơn baseline và repaired quay lại bằng baseline.
- **Kết quả thực tế:** đúng như mong đợi. Baseline `1.0000 / 1.0000 / 1.0000 / 5.0000`; corrupted `0.8000 / 0.6684 / 0.6500 / 3.6000`; repaired `1.0000 / 1.0000 / 1.0000 / 5.0000`. Số dòng `24 → 23 → 24`. Chạy hai lần liên tiếp cho kết quả **giống hệt nhau**, xác nhận pipeline deterministic.
- **Artifact/log:** `data/results/baseline_metrics.json`, `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, `data/results/corruption_log.json`, `data/quality/*.json`, `data/reports/phase1_report.md`, `data/reports/corruption_report.md`, `data/reports/answer_diff.md`. Không file nào trong số này chứa API key; `.env` nằm trong `.gitignore` và không được trích dẫn ở bất kỳ đâu trong báo cáo.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** `corruption.py` phải chọn xem *dòng nào* trong clean frame sẽ bị làm hỏng bởi từng loại corruption. Test set chỉ chấm 5 paper trong tổng số 24 dòng (`testset._select_papers()` lấy `df.iloc[::step]` với `step = len(usable) // 5 = 4`, tức các vị trí 0, 4, 8, 12, 16). Nếu chọn dòng sai, corruption có thể rơi hết vào 19 paper không được chấm — quality check vẫn FAIL nhưng metric của agent không nhúc nhích, và bài lab mất luôn phần chứng minh nhân quả.

- **Các phương án đã cân nhắc:**
  - **Phương án A — chọn ngẫu nhiên có seed:** dùng `random.Random(seed).sample(range(n_rows), k)` cho mỗi loại corruption. Ưu điểm: viết ngắn, "trông giống" lỗi dữ liệu ngoài thực tế hơn, và có seed nên vẫn lặp lại được. Nhược điểm: không kiểm soát được có bao nhiêu paper *được chấm* bị chạm; hai loại corruption có thể cùng rơi vào một paper (không tách được ảnh hưởng), hoặc rơi hết vào paper không được chấm (metric không đổi). Kết quả còn phụ thuộc vào thứ tự dòng do Crossref trả về, nên đổi query là phải dò lại seed.
  - **Phương án B — offset xác định suy ra từ stride của test set:** không dùng RNG. Đặt `TESTSET_STRIDE = 4` (chính là stride của `testset.py`); sau khi bước 1 xóa `DROP_LATEST = 3` dòng đầu, các paper được chấm dồn về "làn" bắt đầu tại `EVAL_LANE_START = (-3) % 4 = 1`. Gán cho mỗi loại corruption một điểm xuất phát khác nhau **trên chính làn đó**: `blank_summary = 1`, `inject_noise = 1 + 4 = 5`, `truncate_title = 1 + 8 = 9`, `stale_dates = 1 + 12 = 13`. Bước nhảy chọn dòng `SELECTION_STRIDE = TESTSET_STRIDE + 1 = 5` lệch pha với làn test set, nên các dòng còn lại của cùng một loại corruption rơi vào paper *không* được chấm.

- **Phương án đã chọn:** Phương án B. Các con số này đọc lại được nguyên vẹn trong `data/results/corruption_log.json`, mục `parameters`: `"selection_stride": 5`, `"offsets": {"blank_summary": 1, "inject_noise": 5, "truncate_title": 9, "stale_dates": 13, "duplicate_rows": 0}`, `"deterministic": true`.

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

  > Khối trên là **bản rút gọn** của thông báo gốc, không phải nguyên văn: đường dẫn tuyệt đối có chứa tên người dùng đã được lược bỏ, và log gốc trên terminal đã bị ghi đè sau khi cài lại dependency. Manh mối định danh lỗi — cụm `is not signed and cannot run on a system with Smart App Control enabled` — được giữ nguyên văn. Log gốc không chứa secret nào.

- **Lệnh hoặc bước tái hiện:**

  ```bash
  # Trên máy Windows 11 bật Smart App Control, sau khi cài dependency
  # bằng phiên bản mới nhất mà resolver tự chọn (pandas 3.x / pyarrow 24-25.x)
  python -c "import pandas"
  python script/run_phase1.py    # chết ngay ở bước 3/10 "Lam sach du lieu"
  ```

- **Nguyên nhân gốc:** không phải lỗi của code project. Windows 11 Smart App Control chặn việc nạp các file nhị phân `.pyd`/`.dll` **không có chữ ký số**. Các wheel dựng sẵn của `pandas` dòng 3.x và `pyarrow` dòng 24–25.x mà resolver chọn về chứa extension đã biên dịch nhưng chưa được ký, nên loader của Windows từ chối nạp trước khi Python kịp chạy bất kỳ dòng lệnh nào. `pyproject.toml` chỉ ghi ràng buộc mở (`pandas>=2.2.2`, không ghim `pyarrow`) nên resolver mặc nhiên lấy bản mới nhất — đây là lỗ hổng về khả năng tái lập môi trường, không phải lỗi logic.

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

- **Điều học được:** ràng buộc phiên bản kiểu `>=` không đủ để tái lập môi trường. Lỗi ở tầng loader của hệ điều hành có triệu chứng giống hệt lỗi cài đặt sai (`ImportError`), nên phải đọc kỹ nội dung thông báo trước khi đi sửa code — ở đây thông điệp "not signed" mới là manh mối, không phải chữ "ImportError". Bài học vận hành: khi môi trường chạy được thì phải ghim lại phiên bản đó vào file khóa, nếu không lần dựng lại tiếp theo sẽ hỏng. Với vai trò leader, tôi coi đây là lỗi của mình vì đã để cả nhóm bắt đầu code trước khi chốt được một môi trường dựng lại được.

Phần chưa xử lý xong:

- **Phạm vi bị ảnh hưởng:** `uv.lock` vẫn ghi cặp phiên bản gây lỗi (`pandas 3.0.3`, `pyarrow 24.0.0`); ai dựng môi trường bằng `uv sync` sẽ gặp lại đúng lỗi trên. Bài nộp chạy được là nhờ `.venv` đã cài tay, không nhờ lock file.
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

**1. Từ Crossref đến vector index.** `fetch_source_records()` gọi `GET https://api.crossref.org/works` với `query = "agentic retrieval augmented generation large language model"` và `filter = from-pub-date:<hôm nay - 180 ngày>,has-abstract:true`, xin dư `24 × 3 = 72` dòng. Payload thô được lưu nguyên trạng vào `data/raw/crossref_response.json`. `parse_crossref_payload()` gỡ thẻ XML/HTML trong abstract, chuẩn hóa `date-parts` thành `YYYY-MM-DD`, ghép tên tác giả, suy ra `categories` (fallback venue/type/publisher vì 0/72 item có trường `subject`), loại bài không phải chữ Latin và bài có abstract dưới 80 ký tự, rồi cắt còn 24 record ghi vào `data/raw/crossref_records.json`. `build_clean_dataframe()` biến 24 record đó thành frame 16 cột, tính thêm `age_days`, `title_chars`, `summary_chars`, khử trùng hai lượt (theo `paper_id` rồi theo `title` viết thường), sắp xếp `published` giảm dần, và quan trọng nhất là ghép cột `text_for_embedding` = `title + authors + categories + published + summary`. Cuối cùng `LocalEmbeddingIndex.build()` cho `sentence-transformers/all-MiniLM-L6-v2` mã hóa **cột `text_for_embedding`** rồi `add()` vào ChromaDB (`PersistentClient` tại `data/chroma/`, `space = cosine`), kèm metadata gồm `paper_id`, `title`, `published`, `authors_joined`, `categories_joined`, `summary`, `abs_url`, `pdf_url`. Ba trạng thái dùng ba collection tách biệt: `papers-baseline`, `papers-corrupted`, `papers-repaired` — đây là ràng buộc tôi phải giữ trong cả hai flow, vì nếu ghi đè lên cùng một collection thì trạng thái trước bị mất và không so sánh lại được.

**2. Test set và ground-truth document IDs.** `build_test_set()` chọn 5 paper trải đều trên dataset (`df.iloc[::4]`) rồi sinh 4 câu hỏi cho mỗi paper — `authors`, `date`, `categories`, `summary` — tổng cộng **20 sample** (`q001`–`q004` cho `10.2118/234689-pa`, `q005`–`q008` cho `10.3390/buildings16132637`, `q009`–`q012` cho `10.21203/rs.3.rs-10012178/v1`, `q013`–`q016` cho `10.22214/ijraset.2026.82233`, `q017`–`q020` cho `10.1093/sleep/zsag091.0346`). Mỗi sample lưu `ground_truth` (lấy trực tiếp từ frame sạch) và `ground_truth_doc_ids` (đúng một `paper_id`). Khi chấm, `evaluate_pipeline()` gọi `answer_question()` lấy `top_k = 4` document rồi tính hai loại chỉ số khác nhau:
   - **Retrieval:** `retrieval_hit = any(doc_id in ground_truth_doc_ids for doc_id in retrieved_doc_ids)` — chỉ hỏi "document đúng có nằm trong top-4 không", hoàn toàn không quan tâm câu trả lời.
   - **Answer quality:** `token_f1` so trùng tập token giữa câu trả lời và `ground_truth`, còn LLM judge (structured output Pydantic: `score` 1–5, `correct` bool, `reasoning`) chấm về mặt ngữ nghĩa. Nhờ tách đôi như vậy mà có thể phân biệt "lấy nhầm tài liệu" với "lấy đúng tài liệu nhưng nội dung tài liệu đã hỏng" — chính là trường hợp q008 và q012 ở mục 8.

**3. Quality checks khác freshness monitoring.** `run_data_quality_checks()` chạy **12 check trên 5 chiều** — completeness, uniqueness, validity, consistency, freshness — và trả lời câu hỏi "dữ liệu có *đúng* không": có dòng nào rỗng, có `paper_id` trùng, `title_chars` có khớp `len(title)`, `published` có đúng định dạng `YYYY-MM-DD`. Đó là kiểm tra dạng pass/fail theo dòng. `build_freshness_report()` thì trả lời câu hỏi "dữ liệu có *mới* không" và xuất ra các đại lượng liên tục để theo dõi theo thời gian: `latest_published`, `oldest_published`, `stale_rows`, `stale_ratio`, `max/min/mean_age_days`, `is_fresh`, kèm danh sách `stale_paper_ids` để truy vết. Hai thứ giao nhau đúng ở một điểm: check `freshness_within_threshold` (`age_days > 180`) là ảnh chụp nhị phân của cùng tín hiệu mà freshness report mô tả chi tiết. Trên dữ liệu corrupted, check này chỉ nói "FAIL, 4/23 dòng", còn freshness report nói thêm rằng `mean_age_days` nhảy từ **83.33 lên 278.7**, `max_age_days` từ **175 lên 1256**, và chỉ đích danh 4 `paper_id` bị đẩy lùi ngày. Quality check dùng để **chặn** (gate) dữ liệu xấu; freshness report dùng để **quan sát** xu hướng.

**4. Vì sao phải dùng cùng test set cho cả ba trạng thái.** Vì test set và `ground_truth` được sinh **từ dữ liệu sạch**. Nếu sinh lại test set từ frame corrupted thì `ground_truth` của câu hỏi summary sẽ chính là chuỗi rỗng hoặc chuỗi rác, câu hỏi ngày tháng sẽ lấy đúng ngày đã bị đẩy lùi — agent trả về rác và vẫn được chấm 5/5. Metric sẽ "đẹp" trên dữ liệu hỏng, tức là phép đo tự phá chính nó. Đây là ràng buộc tôi phải thi hành trong chính code của mình: `phase1._load_or_build_test_set()` cố tình đọc lại `data/eval/test_set.json` nếu file đã tồn tại và chỉ tạo mới khi bật `REFRESH_TEST_SET`, còn `corruption_flow` truyền thẳng `settings.paths.eval_testset` cho cả hai lần đánh giá của nó (corrupted ở bước 5, repaired ở bước 8) và **không chấm lại baseline** mà nạp thẳng `data/results/baseline_metrics.json` do phase 1 sinh ra trên đúng file test set đó. Nhờ đó cả ba trạng thái đều là **20 sample giống hệt**, và chênh lệch `1.0000 → 0.6684 → 1.0000` của `mean_token_f1` chỉ có thể do dữ liệu, không do phép đo.

**5. Repair thành công dựa trên artifact và metric nào.** Repair không phải là vá frame corrupted mà là **dựng lại từ snapshot nguồn đáng tin cậy**: `corruption_flow` bước 7 gọi `load_raw_records(data/raw/crossref_records.json)` rồi `build_clean_dataframe()` lại từ đầu — cùng đúng con đường mà baseline đã đi. Kết luận thành công dựa trên ba nhóm bằng chứng độc lập:
   - **Số dòng:** `data/clean/papers_clean_repaired.csv` có 24 dòng (103.200 bytes, trùng khít từng byte với `papers_clean.csv`), đúng bằng baseline; corrupted chỉ 23.
   - **Tín hiệu dữ liệu:** `data/quality/repaired_quality.json` báo `passed_checks = 12`, `failed_checks = 0`, `total_failed_rows = 0`; `data/quality/freshness_report_repaired.json` báo `is_fresh = true`, `stale_rows = 0`, `stale_ratio = 0.0`, `max_age_days = 175`, `mean_age_days = 83.33` — trùng khít với freshness report của baseline.
   - **Metric của agent:** `data/results/repaired_metrics.json` cho `retrieval_hit_rate = 1.0`, `mean_token_f1 = 1.0`, `judge_accuracy = 1.0`, `mean_judge_score = 5` trên đúng 20 sample cũ; và `answer_diff.md` xác nhận 7/7 câu từng đổi output đã quay về đúng câu trả lời baseline.
   Ba nhóm bằng chứng phải cùng phục hồi thì mới kết luận repair thành công. Nếu chỉ metric hồi mà quality vẫn FAIL thì nhiều khả năng lỗi nằm ở phép đo chứ không phải dữ liệu đã lành.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |   1.0000 |    0.8000 |   1.0000 | Giảm đúng 0.2000 = 4/20 câu, và cả 4 câu đó (q001–q004) đều thuộc paper `10.2118/234689-pa` bị `drop_latest_records` xóa. Đây là metric duy nhất chỉ bị **một** loại corruption tác động. |
| `mean_token_f1`      |   1.0000 |    0.6684 |   1.0000 | Giảm 0.3316. Tách theo loại câu hỏi: summary 0.4190, date 0.6000, authors 0.8000, categories 0.8545 — câu summary chịu thiệt nặng nhất vì bị cả blank lẫn noise đánh vào. |
| `judge_accuracy`     |   1.0000 |    0.6500 |   1.0000 | Giảm 0.3500, tức 7/20 câu bị chấm sai: q001–q004 (mất document), q008 (summary rỗng), q012 (summary rác), q018 (ngày sai). |
| `mean_judge_score`   |   5.0000 |    3.6000 |   5.0000 | Giảm 1.4000/5.0. Theo loại câu hỏi: summary 2.60, date 3.40, authors 4.20, categories 4.20. Đáng chú ý: 13 câu giữ 5/5, 7 câu còn lại đều bị chấm **1/5** — không có câu nào rơi vào mức điểm trung gian. |
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
   → `repaired_quality.json` quay lại **12/12 pass**, `total_failed_rows = 0`; `freshness_report_repaired.json` quay lại `is_fresh = true`, `stale_rows = 0`, `mean_age_days = 83.33` — **trùng khít từng con số** với freshness report của baseline
   → `repaired_metrics.json` quay lại **1.0000 / 1.0000 / 1.0000 / 5.0000**, tức phục hồi **hoàn toàn** về mức baseline, không chỉ "cải thiện một phần". Kiểm tra sâu hơn ở mức từng câu: cả 20/20 câu trong `repaired_answers.json` trùng khớp với `baseline_answers.json` trên `answer`, `retrieval_hit` và `token_f1`.

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

Bài học rút ra là quan hệ giữa data quality và chất lượng agent **không phải một-một**: `truncate_title` làm check `title_min_length` FAIL trên 3 dòng và `duplicate_rows` làm `paper_id_unique` FAIL trên 2 dòng, nhưng cả hai đều không làm suy giảm bất kỳ metric nào. Nói cách khác, **2 trong 5 check FAIL của trạng thái corrupted không có hệ quả đo được ở đầu ra**. Chiều ngược lại cũng đúng và còn đáng lo hơn: `inject_noise` **không bị check nào trong 12 check bắt được** (vì corruption cập nhật luôn `summary_chars` nên check consistency vẫn PASS, và summary vẫn dài hơn 80 ký tự) nhưng lại làm q012 trả về nguyên chuỗi rác. Kết luận: không nên suy diễn ngược từ "check FAIL" ra "agent chắc chắn tệ đi", cũng như không nên suy từ "12/12 check PASS" ra "dữ liệu chắc chắn ổn".

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về data pipeline: snapshot dữ liệu thô là thứ đắt giá nhất trong toàn bộ pipeline.** Bước repair mà tôi viết không hề "sửa" gì cả — nó gọi `load_raw_records(data/raw/crossref_records.json)` rồi `build_clean_dataframe()` lại từ đầu, tức đi đúng con đường baseline đã đi. Nhờ có snapshot thô mà việc phục hồi trở thành *tái dựng* thay vì *vá lỗi*: kết quả là 24/24 dòng và 12/12 check quay lại nguyên trạng, không sót lỗi tồn dư, và file clean repaired trùng khít từng byte với file clean baseline. Nếu chỉ lưu frame đã làm sạch thì không thể phục hồi 3 dòng bị xóa, vì thông tin đó đã biến mất khỏi mọi artifact hạ nguồn. Hệ quả thiết kế: mọi biến đổi phá hủy phải luôn đứng *sau* một điểm lưu bất biến.

2. **Về data quality/observability: quality check và freshness monitoring trả lời hai câu hỏi khác nhau và không thay thế được nhau.** 12 check trả lời "dữ liệu có đúng không" bằng pass/fail (corrupted: 7/12, 15 dòng lỗi), còn freshness report trả lời "dữ liệu có mới không" bằng các đại lượng liên tục (`mean_age_days` 83.33 → 278.7, `max_age_days` 175 → 1256, `stale_ratio` 0 → 0.1739, kèm 4 `paper_id` cụ thể). Nếu chỉ nhìn quality check thì chỉ biết "có 4 dòng quá hạn"; phải mở freshness report mới thấy `oldest_published` tụt từ 2026-02-12 về 2023-02-26 — tức là bản chất lỗi là ngày bị đẩy lùi 3 năm, chứ không phải dữ liệu cũ dần theo thời gian. Gate cần pass/fail, còn chẩn đoán cần số liệu liên tục.

3. **Về ảnh hưởng của data đến RAG agent: hỏng dữ liệu không làm agent báo lỗi, nó làm agent tự tin trả lời sai.** Không có một exception nào được ném ra trong suốt lần chạy corrupted — flow chạy hết 10/10 bước, sinh đủ artifact, và trả về 20/20 câu trả lời. Chỉ khi đối chiếu với ground truth mới lộ ra q001 trả về tác giả của một bài báo khác, q008 trả về chuỗi rỗng, q012 trả về `"LOREM IPSUM DOLOR ###### CORRUPTED PAYLOAD @@@@@@."`, q018 trả về `2023-05-01` thay vì `2026-05-01`. Điều này giải thích vì sao evaluation phải tách `retrieval_hit_rate` khỏi `token_f1`: q001 sai vì *lấy nhầm tài liệu* (`retrieval_hit = false`), còn q008 và q012 sai vì *tài liệu đúng nhưng nội dung đã hỏng* (`retrieval_hit = true`, `token_f1 = 0.000`). Gộp chung một chỉ số thì mất hẳn khả năng chẩn đoán này — và cũng chính vì vậy tôi viết thêm `answer_diff.md`, để nhìn được cái sai ở mức output chứ không chỉ ở mức trung bình.

### Nếu có thêm thời gian

**Cải thiện đề xuất: biến bộ quality check thành một gate chặn thật sự đứng trước bước index, thay vì một báo cáo chạy sau khi mọi thứ đã xong.** Đây là thay đổi nằm trong khối 6 và 7 mà tôi sở hữu, nên tôi có thể tự thực hiện trọn vẹn.

Hiện tại `run_data_quality_checks()` được gọi ở bước 8/10 của `phase1.py` — tức là **sau** khi index đã build (bước 5) và evaluation đã chạy (bước 7). Trên trạng thái corrupted, hệ quả là dữ liệu hỏng vẫn được embed và đưa vào ChromaDB một cách bình thường; chỉ đến cuối mới có một file JSON nói rằng 5 check đã FAIL. Trong môi trường thật thì đó chính là kịch bản index đã bị nhiễm bẩn.

Cách làm: thêm hàm `assert_quality_gate(df, settings)` chạy ngay sau `build_clean_dataframe()` và trước `LocalEmbeddingIndex.build()`. Gate chia mức độ nghiêm trọng — nhóm *blocking* (`paper_id_unique`, `summary_not_empty`, `text_for_embedding_present`, `row_count`) thì raise `RuntimeError` và dừng pipeline; nhóm *warning* (`freshness_within_threshold`, `title_min_length`) thì chỉ in cảnh báo rồi đi tiếp. Phân nhóm này không tùy tiện mà dựa vào bằng chứng ở mục 8: `summary_not_empty` FAIL kéo `token_f1` của q008 xuống 0.000 nên phải chặn, còn `title_min_length` FAIL mà 4 câu q013–q016 vẫn đạt 1.000 nên chỉ cần cảnh báo.

**Cách đo cải thiện** (có tiêu chí đạt/không đạt rõ ràng, chạy lại được):

1. Chạy `python script/run_corruption_flow.py` như hiện tại và ghi lại mốc: flow chạy hết 10/10 bước, collection `papers-corrupted` được tạo với 23 document, `corrupted_metrics.json` ghi `judge_accuracy = 0.6500`.
2. Bật gate rồi chạy lại. **Tiêu chí đạt:** flow dừng ở bước build index với `RuntimeError` nêu đích danh `summary_not_empty` (3 dòng) và `paper_id_unique` (2 dòng); collection `papers-corrupted` **không** được tạo thêm document nào; không có file `corrupted_metrics.json` mới nào được ghi.
3. Chạy `python script/run_phase1.py` trên dữ liệu sạch để kiểm tra không có báo động giả. **Tiêu chí đạt:** vẫn chạy hết 10/10 bước và `baseline_metrics.json` giữ nguyên `1.0000 / 1.0000 / 1.0000 / 5.0000`.
4. **Chỉ số theo dõi:** số document hỏng lọt vào ChromaDB, hiện tại là 23/23 trên trạng thái corrupted, mục tiêu là 0/23. Đây là con số đếm được trực tiếp từ manifest `data/embeddings/papers_embeddings_corrupted.json`, không cần suy diễn.

Một việc tồn đọng nữa mà tôi phải làm với tư cách leader: ghim `pandas==2.3.3` / `pyarrow==21.0.0` vào `pyproject.toml` rồi chạy lại `uv lock`, để `uv sync` dựng ra được đúng môi trường đã dùng cho bài nộp (chi tiết ở mục 6).

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Đoàn Đình Đông
**Ngày xác nhận:** 2026-08-06
