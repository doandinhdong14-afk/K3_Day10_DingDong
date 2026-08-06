# Member Role Report — Day 10: Data Pipeline & Data Observability

> Mỗi thành viên trong nhóm tự hoàn thành mẫu này để báo cáo đúng vai trò, phần việc và mức hiểu của mình. Không sao chép nguyên báo cáo chung hoặc báo cáo của thành viên khác. Thay nội dung trong dấu `[ ]` và xóa các dòng hướng dẫn không cần thiết trước khi nộp.

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | [Dương Hải Long]             |
| MSSV               | [2A202601607]                     |
| Khóa/Lớp         | [K3]              |
| Tên nhóm         | [DingDong]     |
| Vai trò chính    | [AI dev]                 |
| Repository         | [Đường dẫn repository] |
| Ngày hoàn thành | [2026-8-6]               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| [Khởi chạy LLM local]      | []           | [Input]          | [Output/artifact] | [Hoàn thành] |
| [Tích hợp LLM local vào pipeline]      | [testset.py]           | [Câu hỏi của người dùng/tài liệu truy vấn]          | [Intent từ câu truy vấn/câu trả lời] | [Một phần] |
| Tạo embedding và nạp vào ChromaDB]      | [phase1.py]           | [chunks]          | [vector database] | [Hoàn thành] |

Chỉ nhận ownership cho phần bạn trực tiếp thực hiện. Liên hệ rõ phần việc của bạn với đầu vào, đầu ra và các thành viên phụ thuộc vào phần đó.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| [Tham gia crawl và làm sạch/bẩn dữ liệu] | [cleaning.py/corruption.py] | [data/raw] |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| [Chạy LLM local] | [testset.py] | [data/eval/ (evaluation test set)] | [(src/evaluation/testset.py) trong run_phase1.py] |


Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

[data/eval/testset.json]

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

[Embedding, truy vấn, xác định intent và sinh câu trả lời]

### Cách triển khai

[Sử dụng LLM, prompt được đưa vào dưới dạng json {"user", "content"}{"assistant", "content"}   ]

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | [corpus sạch (cleaned data) và schema câu hỏi/ground truth để sinh evaluation set.]           |
| Output                         | [Artifact data/eval/testset.json chứa danh sách câu trả lời + ground truth; định dạng JSON với các trường id, answer, ground_truth] |
| Module phụ thuộc             | [src/ingestion/cleaning.py (để lấy dữ liệu đã chuẩn hóa), src/core/config.py (đường dẫn, cấu hình).]                    |
| Module sử dụng output        | [src/evaluation/metrics.py (tính chỉ số), src/pipelines/phase1.py và corruption_flow.py (chạy baseline/corruption/repaired).]                    |
| Điều kiện lỗi cần xử lý | [- Không có dữ liệu sạch để tạo testset → báo lỗi hoặc bỏ qua.
- Ground truth rỗng hoặc thiếu trường → raise exception.
- Định dạng JSON không hợp lệ → validate schema trước khi ghi file.]                   |

### Cách xác minh

```bash
[python testset.py]
```

- **Kết quả mong đợi:** [testset.json) được sinh ra từ corpus sạch, chứa danh sách câu trả lời và ground truth đầy đủ, đúng schema (id, answer, ground_truth]
- **Kết quả thực tế:** [data/eval/testset.json]
- **Artifact/log:** [data/eval/testset.json, data/logs/testset_generation.log.]

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** [Mô hình chạy tốn nhiều thời gian.]
- **Các phương án đã cân nhắc:** [Chạy trên GPU/ Dùng mô hình nhỏ hơn]
- **Phương án đã chọn:** [Chạy trên GPU.]
- **Lý do:** [GPU có khả năng tính toán song song hàng nghìn phép tính cùng lúc, phù hợp để chạy ANN.]
- **Bằng chứng quyết định phù hợp:** [Thời gian giảm đi đagns kể]

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** [Che toàn bộ secret trước khi ghi.]
- **Lệnh hoặc bước tái hiện:** [Lệnh/bước.]
- **Nguyên nhân gốc:** [Root cause, không chỉ mô tả triệu chứng.]
- **Cách xử lý:** [Thay đổi cụ thể.]
- **Cách xác minh sau khi sửa:** [Lệnh và kết quả.]
- **Điều học được:** [Bài học kỹ thuật.]

Nếu chưa xử lý xong:

- **Phạm vi bị ảnh hưởng:** [Module/artifact.]
- **Những gì đã loại trừ:** [Các giả thuyết đã kiểm tra.]
- **Bước tiếp theo:** [Hành động có thể kiểm chứng.]

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
5. Repair được xem là thành công dựa trên artifact và metric nào?

**Câu trả lời:**
1. Crossref API trả về raw JSON, lưu trong data/raw/. Embedding + metadata được nạp vào ChromaDB → tạo vector index để phục vụ retrieval.
2. so sánh câu trả lời agent với ground truth để tính mean_token_f1, judge_accuracy, mean_judge_score.
3. quality = đúng/đủ, freshness = mới/cập nhật.
4. Giữ test set cố định giúp chứng minh rõ ràng: baseline tốt → corrupted giảm → repaired khôi phục.
5. Nếu báo cáo comparison (corruption_report.md) cho thấy repaired ≈ baseline và vượt corrupted rõ rệt thì repair thành công.
[Viết câu trả lời tại đây.]

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.0000 | 0.8000 | 1.0000 | thể hiện tương ddooiss rõ ảnh hưởng của dữ liệu lên truy vấn |
| `mean_token_f1` | 1.0000 | 0.7137 | 1.0000 | Giảm mạnh hơn hit rate vì có câu retrieve đúng nhưng nội dung đã bị làm rỗng hoặc sai ngày |
| `judge_accuracy` | 1.0000 | 0.7000 | 1.0000 | Cả ba chấm bằng LLM judge thật, 20/20 câu, không có lượt nào rơi về heuristic |
| `mean_judge_score` | 5.0000 | 3.9000 | 5.0000 | 6 câu bị corruption đều bị chấm 1–3 điểm, xem phân tích bên dưới |
| Quality checks | PASS 9/9 | FAIL 6/9 | PASS 9/9 | Fail: `paper_id_unique`, `summary_length_minimum`, `age_days_within_freshness_threshold` |
| Freshness status | FRESH (0/24 stale) | STALE (3/23 stale) | FRESH (0/24 stale) | `latest_published` tụt từ 2026-08-01 xuống 2026-07-03 |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:

1. [Data corruption] → [quality/freshness signal thay đổi] → [agent metric thay đổi].
2. [Repair action] → [quality/freshness signal phục hồi] → [agent metric phục hồi hoặc chưa phục hồi].

Corruption nào ảnh hưởng rõ nhất và vì sao?

[Phân tích dựa trên số liệu.]

Kết quả nào khác với kỳ vọng ban đầu?

[Nêu kết quả, giả thuyết và cách đã kiểm tra.]

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. [Điều học được về data pipeline: rất quan trọng]
2. [Điều học được về data quality/observability: vô cùng quan trọng]
3. [Điều học được về ảnh hưởng của data đến RAG agent: dữ liệu sạch thì trả lời tốt]

### Nếu có thêm thời gian

[Nêu một cải thiện cụ thể, lý do và cách đo cải thiện đó.]

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [ ] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [ ] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [ ] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [ ] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [ ] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [ ] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** [Dương Hải Long]
**Ngày xác nhận:** [2026-8-6]
