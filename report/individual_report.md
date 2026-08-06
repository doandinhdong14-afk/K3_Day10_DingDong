# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| :--- | :--- |
| Họ và tên | Trần Hoài Nam |
| MSSV | 2153225278 |
| Khóa/Lớp | K3 |
| Tên nhóm | K3_Day10_DingDong |
| Vai trò chính | Core Data Engineer & RAG Pipeline Orchestrator (Xây dựng toàn bộ luồng Ingestion, Cleaning, Evaluation, Observability & Corruption Flow) |
| Repository | [https://github.com/doandinhdong14-afk/K3_Day10_DingDong](https://github.com/doandinhdong14-afk/K3_Day10_DingDong) |
| Ngày hoàn thành | 2026-08-06 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| :--- | :--- | :--- | :--- | :--- |
| **Data Ingestion** | [`src/ingestion/crossref.py`](file:///c:/Users/PC/K3_Day10_DingDong/src/ingestion/crossref.py) (`fetch_source_records`, `parse_crossref_payload`) | REST API endpoint Crossref | Raw JSON artifacts (`crossref_response.json`, `crossref_records.json`) | **Hoàn thành** |
| **Data Cleaning** | [`src/ingestion/cleaning.py`](file:///c:/Users/PC/K3_Day10_DingDong/src/ingestion/cleaning.py) (`build_clean_dataframe`) | List raw `PaperRecord` | CSV & JSON sạch (`papers_clean.csv`, `papers_clean.json`) | **Hoàn thành** |
| **Evaluation Testset** | [`src/evaluation/testset.py`](file:///c:/Users/PC/K3_Day10_DingDong/src/evaluation/testset.py) (`build_test_set`) | Cleaned DataFrame | Testcase JSON (`test_set.json`) với 24 câu hỏi mẫu | **Hoàn thành** |
| **Data Observability** | [`src/observability/quality.py`](file:///c:/Users/PC/K3_Day10_DingDong/src/observability/quality.py) & [`reporting.py`](file:///c:/Users/PC/K3_Day10_DingDong/src/observability/reporting.py) | Clean/Corrupted DataFrame | `quality.json`, `freshness_report.json`, `phase1_report.md` | **Hoàn thành** |
| **Corruption & Repair** | [`src/ingestion/corruption.py`](file:///c:/Users/PC/K3_Day10_DingDong/src/ingestion/corruption.py) & [`src/pipelines/corruption_flow.py`](file:///c:/Users/PC/K3_Day10_DingDong/src/pipelines/corruption_flow.py) | Clean DataFrame & Raw records | `corruption_log.json`, `corruption_report.md` | **Hoàn thành** |
| **Web UI Demo** | [`app.py`](file:///c:/Users/PC/K3_Day10_DingDong/app.py) | Config, ChromaDB Index & Pipeline outputs | Streamlit Interactive Dashboard UI | **Hoàn thành** |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| :--- | :--- | :--- |
| Config & Environment Setup | Toàn bộ hệ thống | Điều chỉnh `pyproject.toml` tương thích Python 3.14.6 trên Windows, thiết lập `.env`. |
| Retrieval Indexing & QA | Module `src/retrieval/` | Tích hợp ChromaDB HNSW Cosine vector store và mô hình `all-MiniLM-L6-v2`. |
| Streamlit Web Interface | Thuyết trình & Demo | Xây dựng giao diện Web Modern Dark Tech UI (`app.py`) hỗ trợ chạy 1-click & trực quan hóa đồ thị Plotly. |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| **Baseline Data Pipeline (Phase 1)** | [`src/pipelines/phase1.py`](file:///c:/Users/PC/K3_Day10_DingDong/src/pipelines/phase1.py) | Tạo 24 bản ghi sạch, Vector index ChromaDB, Baseline metrics và `phase1_report.md` | Chạy `python script/run_phase1.py` ➔ Trả về `Phase 1 Completed Successfully` |
| **Simulate Data Corruption & Auto-repair (Phase 2)** | [`src/pipelines/corruption_flow.py`](file:///c:/Users/PC/K3_Day10_DingDong/src/pipelines/corruption_flow.py) | Tạo dataset rác, kiểm tra độ tụt điểm RAG, tự động repair và xuất `corruption_report.md` | Chạy `python script/run_corruption_flow.py` ➔ Hit rate sụt giảm từ 100% ➔ 75% ➔ Hồi phục 100% |
| **Streamlit Interactive UI** | [`app.py`](file:///c:/Users/PC/K3_Day10_DingDong/app.py) | Web Dashboard 4 trang tương tác trực quan | Chạy `streamlit run app.py` ➔ Hiển thị UI tại `http://localhost:8501` |

**Mô tả Output cụ thể đã tạo ra:**
- Đã tạo ra bộ dữ liệu sạch `papers_clean.csv` (24 bài báo khoa học chuẩn hóa 16 cột), bộ đề testcase 24 câu hỏi `test_set.json`, và bảng báo cáo so sánh đối chiếu chỉ số 3 trạng thái tại [`data/reports/corruption_report.md`](file:///c:/Users/PC/K3_Day10_DingDong/data/reports/corruption_report.md).

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Bài lab yêu cầu xây dựng một Data Pipeline tự động chuyển đổi dữ liệu bài báo khoa học không cấu trúc từ Crossref API thành Vector Embeddings, đo lường các chỉ số chất lượng RAG Agent (`Retrieval Hit Rate`, `Token F1`, `LLM Judge Score`), đồng thời chứng minh tác động tiêu cực của lỗi dữ liệu (Data Corruption) và giải pháp tự phục hồi (Auto-Repair) từ dữ liệu thô ban đầu.

### Cách triển khai
1. **Ingestion & Retry Logic**: Gọi HTTP API `https://api.crossref.org/works` với cơ chế Exponential Backoff (`2s ➔ 4s ➔ 8s`) xử lý nghẽn mạng 429. Dùng Regex `re.sub(r"<[^>]+>", " ", ...)` lọc thẻ JATS XML trong abstract.
2. **Cleaning & Text Formatting**: Lọc bản ghi null/ngắn, ghép `authors_joined`, tính `age_days` đo độ tươi mới, và dựng cột `text_for_embedding` chứa toàn bộ tiêu đề, tóm tắt, tác giả, danh mục.
3. **Data Observability**: Xây dựng hàm `run_data_quality_checks` đếm null/duplicate/summary ngắn và `build_freshness_report` cảnh báo bản ghi > 180 ngày.
4. **Data Corruption**: Cố tình chèn 6 loại lỗi: xóa bản ghi mới nhất, xóa rỗng summary, chèn noise rác, cắt ngắn tiêu đề, lùi ngày xuất bản về 2020 và nhân bản dòng trùng lặp.
5. **Auto-Repair**: Nạp lại dữ liệu từ raw source artifact `crossref_records.json` để rebuild toàn bộ Clean DataFrame và ChromaDB Vector Index.

### Input, output và contract

| Thành phần | Mô tả |
| :--- | :--- |
| **Input** | Rest API Payload Crossref JSON / Raw file `crossref_records.json` |
| **Output** | `papers_clean.csv`, ChromaDB Collection HNSW, `test_set.json`, `corruption_report.md` |
| **Module phụ thuộc** | `requests`, `pandas`, `chromadb`, `sentence-transformers`, `langchain` |
| **Module sử dụng output** | `retrieval.index`, `evaluation.metrics`, `observability.reporting`, `app.py` |
| **Điều kiện lỗi cần xử lý** | Lỗi 429/503 HTTP Rate Limit, thẻ JATS XML trong abstract, bài báo bị thiếu tác giả hoặc thiếu DOI |

### Cách xác minh

```bash
python script/run_phase1.py
python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Pha 1 hoàn thành 100% sạch (`PASSED`). Pha 2 phát hiện dữ liệu lỗi (`FAILED`), sụt giảm Hit Rate, sau đó khôi phục lại 100% (`PASSED`).
- **Kết quả thực tế:**
  - Baseline Hit Rate: `1.0000`, Token F1: `0.4389`, Quality: `PASSED`
  - Corrupted Hit Rate: `0.7500`, Token F1: `0.2744`, Quality: `FAILED`
  - Repaired Hit Rate: `1.0000`, Token F1: `0.4389`, Quality: `PASSED`
- **Artifact/log:**
  - [`data/results/baseline_metrics.json`](file:///c:/Users/PC/K3_Day10_DingDong/data/results/baseline_metrics.json)
  - [`data/results/corrupted_metrics.json`](file:///c:/Users/PC/K3_Day10_DingDong/data/results/corrupted_metrics.json)
  - [`data/results/repaired_metrics.json`](file:///c:/Users/PC/K3_Day10_DingDong/data/results/repaired_metrics.json)
  - [`data/reports/corruption_report.md`](file:///c:/Users/PC/K3_Day10_DingDong/data/reports/corruption_report.md)

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Môi trường máy tính Windows chạy Python 3.14.6 bị thiếu C++ Build Tools khiến việc biên dịch thư viện `scikit-network` (phụ thuộc của `ragas`) bị lỗi cài đặt package.
- **Các phương án đã cân nhắc:**
  1. Yêu cầu cài đặt Visual Studio C++ Build Tools nặng nhiều GB vào máy.
  2. Nâng upper-bound Python trong `pyproject.toml` lên `<3.15`, chuyển `ragas` sang optional dependency và xây dựng hàm Heuristic Token F1 & LLM Judge fallback tự động.
- **Phương án đã chọn:** Phương án 2 (Thay đổi `pyproject.toml` và xây dựng Heuristic Judge fallback trong `src/evaluation/metrics.py`).
- **Lý do:** Giúp môi trường cài đặt cực nhẹ, chạy ổn định 100% trên Windows Python 3.14 mà vẫn đảm bảo tính toán đầy đủ các chỉ số `Retrieval Hit Rate`, `Token F1`, `LLM Judge Accuracy` mà không bị gián đoạn.
- **Bằng chứng quyết định phù hợp:** Kết quả `uv run python script/run_phase1.py` chạy mượt mà không gặp bất kỳ lỗi biên dịch nào.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:**
  `HTTP Error 429: Too Many Requests` và thẻ JATS XML `<jats:p>Summary text...</jats:p>` xuất hiện làm rác nội dung abstract bài báo khi lấy từ API Crossref.
- **Lệnh hoặc bước tái hiện:** Chạy hàm `fetch_source_records()` với số lượng bài báo lớn trong khoảng thời gian ngắn.
- **Nguyên nhân gốc:** Crossref API giới hạn tần suất truy cập (rate limit) đối với unauthenticated client, đồng thời trường abstract lưu dưới dạng XML chứ không phải plain text.
- **Cách xử lý:**
  1. Thêm `headers={"User-Mail": "student@example.com"}` và thuật toán `time.sleep(2.0 * (2 ** attempt))` (Exponential Backoff).
  2. Thêm hàm `_clean_abstract()` sử dụng Regex `re.sub(r"<[^>]+>", " ", raw_abstract)` để xóa toàn bộ thẻ XML.
- **Cách xác minh sau khi sửa:** Tất cả 24 bản ghi raw trong `crossref_records.json` đều là plain text sạch đẹp và không gặp lỗi 429.
- **Điều học được:** Đồ án làm việc với Third-party REST API luôn cần có HTTP Retry Policy và Data Cleaning Parser cho định dạng XML/HTML.

---

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   Dữ liệu JSON thô được tải từ Crossref API ➔ Qua parser loại bỏ thẻ XML ➔ Lưu artifact `crossref_records.json` ➔ Qua `cleaning.py` để làm sạch, khử trùng lặp, tạo cột rich text `text_for_embedding` ➔ Nạp vào mô hình `sentence-transformers/all-MiniLM-L6-v2` chuyển thành vector 384 chiều ➔ Lưu vào ChromaDB Collection định dạng HNSW Cosine Index.

2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   Mỗi testcase chứa câu hỏi `question` và danh sách `ground_truth_doc_ids` (DOI chuẩn). Khi RAG Agent chạy, nó tìm kiếm Top-K bài báo tương đồng nhất (`retrieved_doc_ids`). Nếu đúng DOI chuẩn nằm trong danh sách truy xuất, `retrieval_hit_rate` được tính là `1.0`, ngược lại là `0.0`. Sau đó so sánh văn bản trả lời với `ground_truth` để tính điểm Token F1.

3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   - **Quality checks** (`run_data_quality_checks`): Giám sát tính toàn vẹn của dữ liệu tại thời điểm hiện tại (đếm dòng null, trùng lặp DOI, summary bị quá ngắn/xóa rỗng).
   - **Freshness monitoring** (`build_freshness_report`): Giám sát độ tươi mới theo thời gian (tính số tuổi `age_days = run_date - published_date` và cảnh báo nếu dữ liệu quá hạn > 180 ngày).

4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   Đó là nguyên tắc điều kiện hằng số (Control Variable) trong khoa học dữ liệu. Dùng chung một bộ 24 testcase cố định giúp đảm bảo sự so sánh công bằng tuyệt đối giữa 3 trạng thái. Mọi sự thay đổi về điểm số (`Hit Rate` giảm từ 100% ➔ 75%) đều do chất lượng dữ liệu bị biến đổi chứ không phải do câu hỏi khó/dễ khác nhau.

5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   Repair thành công khi:
   - Status Data Quality trong `repaired_quality.json` chuyển từ `FAILED` trở lại `PASSED`.
   - Artifact `repaired_metrics.json` có `retrieval_hit_rate` phục hồi từ `0.7500` về `1.0000` và `mean_token_f1` phục hồi về `0.4389`.
   - Báo cáo [`data/reports/corruption_report.md`](file:///c:/Users/PC/K3_Day10_DingDong/data/reports/corruption_report.md) ghi nhận sự phục hồi 100%.

---

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| :--- | :---: | :---: | :---: | :--- |
| `retrieval_hit_rate` | **1.0000** | **0.7500** | **1.0000** | Dữ liệu lỗi làm mất bản ghi & sai tiêu đề làm sụt giảm 25% khả năng tìm kiếm; khôi phục 100% sau khi Repair. |
| `mean_token_f1` | **0.4389** | **0.2744** | **0.4389** | Văn bản rác noise làm suy giảm chất lượng câu trả lời; khôi phục hoàn toàn sau khi làm sạch từ Raw. |
| `judge_accuracy` | **0.3750** | **0.2500** | **0.3750** | Đánh giá tính đúng đắn giảm khi gặp dữ liệu nhiễu và phục hồi sau khi sửa. |
| `mean_judge_score` | **2.42** / 5.0 | **1.92** / 5.0 | **2.42** / 5.0 | Điểm số đánh giá tổng quan bị sụt giảm trong pha Corrupted. |
| Quality checks | **`PASSED`** | **`FAILED`** | **`PASSED`** | Hệ thống Observability phát hiện chính xác các lỗi rỗng/trùng lặp do hàm Corruption tạo ra. |
| Freshness status | **`FRESH`** | **`STALE`** | **`FRESH`** | Cảnh báo chính xác khi lùi ngày xuất bản của bài báo về năm 2020. |

### Kết luận từ số liệu

1. **Data corruption** (`blank_summary`, `inject_noise`, `drop_latest_records`) ➔ **Data Quality báo `FAILED` & Freshness báo `STALE`** ➔ **RAG Retrieval Hit Rate sụt giảm từ 100% xuống 75%, Token F1 giảm từ 0.4389 xuống 0.2744**.
2. **Repair action** (Nạp lại dữ liệu sạch từ `crossref_records.json` & Rebuild ChromaDB) ➔ **Data Quality phục hồi về `PASSED` & Freshness phục hồi về `FRESH`** ➔ **RAG Retrieval Hit Rate phục hồi hoàn toàn về 100%, Token F1 phục hồi về 0.4389**.

- **Corruption nào ảnh hưởng rõ nhất và vì sao?**
  Hành vi `drop_latest_records` (xóa bản ghi bài báo) và `blank_summary` (xóa rỗng tóm tắt) ảnh hưởng nghiêm trọng nhất vì làm biến mất thông tin ngữ cảnh hoàn toàn khỏi Vector Store, dẫn đến RAG Agent không thể truy xuất đúng tài liệu nguồn (Hit Rate rớt thẳng xuống 75%).
- **Kết quả nào khác với kỳ vọng ban đầu?**
  Ban đầu dự đoán việc chèn văn bản rác `GARBAGE_NOISE` chỉ làm giảm Token F1, nhưng thực tế nó còn làm méo mó vector embedding làm Cosine Similarity bị lệch, ảnh hưởng nhẹ đến thứ tự xếp hạng Top-K trong Vector Database.

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Data Quality quyết định AI Quality (Garbage In, Garbage Out)**: Mô hình RAG Agent dù hiện đại đến đâu cũng sẽ trả lời sai nếu dữ liệu Vector Database bị thiếu hoặc dính rác.
2. **Tầm quan trọng của Raw Source Artifacts**: Lưu trữ dữ liệu thô ban đầu (`crossref_records.json`) là "chìa khóa" giúp hệ thống có thể tự động khôi phục (Auto-Repair) 100% khi xảy ra sự cố dữ liệu.
3. **Data Observability là bắt buộc**: Cần phải có các bộ kiểm tra tự động (Quality Checks & Freshness Monitoring) chạy liên tục để phát hiện sớm lỗi dữ liệu trước khi người dùng phát hiện ra.

### Nếu có thêm thời gian

Tôi sẽ triển khai cơ chế **Automated Pipeline Circuit Breaker**: Khi `run_data_quality_checks()` phát hiện dữ liệu bị `FAILED`, hệ thống sẽ tự động ngắt (Circuit Break) không cho nạp dữ liệu lỗi vào ChromaDB Production, đồng thời tự động kích hoạt hàm `repair_flow()` ngầm trước khi phục vụ người dùng.

---

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Đoàn Đình Đông  
**Ngày xác nhận:** 2026-08-06  
