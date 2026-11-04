# P5 — Insight, báo cáo, dashboard và đánh giá

P5 chạy trên nhánh `feature/reporting`. Code P1–P4 không bị sửa, merge hoặc
cherry-pick. Các bản source export nằm trong `artifacts/upstream/<commit>/`
(đã được Git ignore); dữ liệu nằm trong `data/` (đã được Git ignore).

## Cài đặt

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-reporting.txt
```

Môi trường do phiên triển khai tạo sẵn là `.venv-reporting`; có thể dùng
`.\.venv-reporting\Scripts\python.exe` thay cho `python` trong các lệnh dưới.
P5 offline không cần API key. Module báo cáo dùng thư viện chuẩn; chỉ phần đọc
Parquet, biểu đồ và dashboard cần pandas/pyarrow/Streamlit.

## Chạy P1–P4 nguyên bản để lấy output

Nếu chưa có output, cần cài dependency của upstream vào môi trường thực thi
(pandas, numpy, scikit-learn, pyarrow, python-dotenv, chromadb,
sentence-transformers, rank-bm25). Lần chạy embedding local đầu tiên cần tải model.

```powershell
python scripts/run_upstream_outputs.py --reviews "C:\Users\JWOS\Documents\STUDY\DBM\P\Reviews.csv" --nrows 20000 --max-rag-reviews 1000 --output-dir data/processed
```

Bỏ `--nrows` để chạy toàn bộ CSV; điều chỉnh `--max-rag-reviews` theo tài nguyên.
Thư mục output phải rỗng để tránh trộn các lần chạy. Mỗi lần chạy nên dùng thư mục
mới và chỉ rõ đường dẫn đó cho lệnh P5. `--skip-rag` dành cho trường hợp không
chạy được P4; P5 sẽ báo thiếu bằng chứng, không tạo dữ liệu truy xuất giả.

Script lần lượt chạy ingestion, preprocessing, issue analysis từ snapshot `rag`,
trend analysis từ snapshot `text-mining`, rồi gọi các API P4 có sẵn để export
`retrieval_results.json`. Adapter `export_p4_outputs.py` chỉ gọi loader, chunker,
embedder, vector store và retriever của P4; không viết lại thuật toán.
Không gọi CLI `run_rag.py` vì CLI upstream thiếu `import os`. Source upstream
vẫn giữ nguyên; cũng không dùng phần sinh insight cũ để thay cho nhiệm vụ P5.

## Đầu vào P5

| Dữ liệu | Tên theo đề bài | Tên hiện có được hỗ trợ |
|---|---|---|
| Review sạch | `clean_reviews.parquet` | `reviews_clean.parquet` hoặc `reviews_clean.csv` |
| Sentiment | `sentiment.parquet` | `sentiment.csv`; thiếu thì dùng nhãn/số sao trong review |
| Phân nhóm | `clusters.parquet` | `issue_assignments.parquet` hoặc `.csv` |
| Vấn đề | `issues.json` | `issues_ranked.json` |
| Xu hướng | `trend.csv` | `issue_monthly_trends.csv` |
| Mẫu xu hướng | `patterns.csv` | `issue_trend_summary.csv` |
| Bằng chứng P4 | `retrieval_results.json` | Adapter export từ API P4 |
| Insight cũ (tùy chọn) | — | `rag_insights.json`, giữ như nội dung chưa đánh giá |

`issues` phải là danh sách object có `issue_id`; schema metric hiện tại của P3
(`metrics.n_reviews`, `metrics.pct_one_star`, `priority_score`, `examples`) được
giữ nguyên. Không suy đoán schema khác. Các bảng liên kết bằng `review_id` và
`issue_id`. ID trùng hoặc có hai file thay thế cùng loại sẽ gây lỗi rõ ràng.
Thiếu artifact tùy chọn được ghi vào warnings, không thay bằng dữ liệu giả.

`retrieval_results.json` là danh sách object gồm `issue_id`, `evidence_reviews`
và `relevant_policies`. Mỗi document chứa `doc_id`, `text`, `metadata` từ P4.
Review metadata cần `review_id`; policy metadata cần `policy_id`, `file_name`,
và có thể có `section_title`. Output này không phải nhãn chuẩn đánh giá retrieval.

## Tạo báo cáo và mở dashboard

```powershell
python scripts/run_reporting.py --input-dir data/processed --output-dir reports/p5
python -m streamlit run app/reporting_dashboard.py --server.address 127.0.0.1
```

Đầu ra:

- `reports/p5/reports.json`: metadata, SHA-256 đầu vào, sentiment summary và báo cáo từng issue.
- `reports/p5/reports.md`: báo cáo có metric, hướng điều tra, đề xuất và bằng chứng.
- `reports/p5/evaluation.json`: kết quả kiểm tra artifact, liên kết ID, nguồn trích dẫn và giới hạn đánh giá.

Dashboard có bộ lọc từ khóa/điểm ưu tiên/bằng chứng, biểu đồ ưu tiên và sentiment,
xu hướng theo tháng, chi tiết từng issue, nguồn trích dẫn, provenance và tải báo cáo.
Dashboard chỉ đọc file; không chạy lại upstream hoặc tự gọi API.

## Sinh insight bằng Gemini (tùy chọn)

```powershell
python -m pip install google-genai
$env:GEMINI_API_KEY = "YOUR_KEY"
$env:GEMINI_MODEL = "YOUR_MODEL"
python scripts/run_reporting.py --input-dir data/processed --output-dir reports/p5 --provider gemini
```

Chỉ mode này gửi metric và bằng chứng đã đối chiếu đến Gemini. Mỗi claim phải dẫn
ID đã có trong bằng chứng; response sai schema hoặc dẫn ID lạ bị loại, giữ báo cáo
offline và ghi trạng thái fallback. Claim LLM luôn được hiển thị như giả thuyết cần
duyệt. Mode offline không khẳng định root cause từ từ khóa và không bịa chính sách.

## Đánh giá và các giới hạn

- Trích dẫn review được đối chiếu ID và đoạn trích với output review sạch.
- Policy được đối chiếu nội dung và nguồn ghi trong output P4; chưa xác thực độc lập.
- Review đại diện P3 và bằng chứng truy xuất P4 có nhãn origin riêng.
- Kiểm tra assignment không liên kết được với review hoặc issue.
- Không gọi tỷ lệ đối chiếu nguồn là độ chính xác, faithfulness hay relevance.
- Chưa có ground truth: Recall@k/MRR, sentiment accuracy và semantic faithfulness
  được ghi `not_evaluated`, không gán điểm giả.
- Code hiện tại của P3 dùng tỷ lệ 1 sao trong nhóm review 1–2 sao làm severity;
  không phải tỷ lệ tiêu cực trên mọi review cùng chủ đề.
- P3 tính growth theo 12 tháng, P2 theo 3 tháng và khác mẫu số. P5 giữ riêng,
  không ghép hai chỉ số thành một kết luận.
- Chạy giới hạn dòng hoặc số review index phải đọc kèm provenance; không suy rộng
  thành kết quả của toàn bộ dataset.

## Kiểm thử

```powershell
python -m unittest discover -s tests -p test_reporting.py -v
python -m unittest discover -s tests -p test_reporting_dashboard.py -v
```

Các test dùng fixture nhỏ chỉ để kiểm tra hợp đồng file, ID trùng, metric thiếu,
trích dẫn bịa, nguồn không đủ, positive evidence, validation LLM và giữ nguyên
đầu vào. Fixture không được dùng làm dữ liệu trình diễn hoặc báo cáo thật.

## Output thật đã chạy trong phiên triển khai

Đầu vào `Reviews.csv` có 568.454 dòng. Lần chạy đầy đủ nằm tại
`data/processed_full/`; lần chạy thử 20.000 dòng nằm tại `data/processed/`.
Lệnh tạo lại báo cáo bàn giao:

```powershell
.\.venv-reporting\Scripts\python.exe scripts/run_reporting.py --input-dir data/processed_full --output-dir reports/p5
.\.venv-reporting\Scripts\python.exe -m streamlit run app/reporting_dashboard.py --server.address 127.0.0.1
```

P1–P3 xử lý toàn bộ CSV; P4 chỉ index 1.000 review đầu, không phải toàn bộ
review sạch. Dashboard và báo cáo ghi rõ phạm vi này. Báo cáo mặc định tạo
offline; chế độ Gemini là tùy chọn và chưa được kiểm thử với API thật.

## Insight do trợ lý tổng hợp từ output hiện tại

`reports/p5/analyst_insights.json` chứa 6 nhận định tổng hợp và phân tích riêng
12 nhóm: quan sát có nguồn, diễn giải, điều chưa biết và hành động đề xuất.
Đây là phân tích đọc nội dung do trợ lý thực hiện, không gọi Gemini và không
phải kết quả thẩm định độc lập. Review P3 bổ sung được ghi rõ, không đánh đồng
với bằng chứng truy xuất P4. Policy 2026 chỉ dùng tham chiếu cho dữ liệu lịch sử.

Tạo lại báo cáo có phần phân tích này:

```powershell
.\.venv-reporting\Scripts\python.exe scripts/run_reporting.py --input-dir data/processed_full --output-dir reports/p5 --analysis-file reports/p5/analyst_insights.json
```

P5 kiểm tra SHA-256 của input và ID nguồn trước khi ghép. Nếu chạy lại upstream
và output đổi, cần đọc và cập nhật phân tích trước; không tự dùng lại nhận định cũ.
Dashboard hiển thị phần tổng hợp ở tab Tổng quan và phân tích riêng ở Điều tra
vấn đề. Nội dung này cũng có trong `reports.json` và `reports.md`.
