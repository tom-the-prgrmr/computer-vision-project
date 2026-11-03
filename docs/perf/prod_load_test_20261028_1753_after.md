# PROD load test — after

- URL: `https://computer-vision-project-hl82.onrender.com`
- Thời điểm (UTC): 2026-10-28 17:57
- Ảnh: `data\ood_samples\tree\00000055.jpg` (81 KB)
- 20 request mỗi mức đồng thời, timeout 60s, warm-up 2 request (không tính)

## Cold start

`/health` trả 200 sau **0.3s** (1 lần thử); `/predict` đầu tiên: **7776 ms** client / 7505 ms server

## Warm — theo số request đồng thời

| Đồng thời | OK/N | Error rate | p50 (ms) | p95 (ms) | p99 (ms) | Server p50 (ms) | Throughput (req/s) | Lỗi |
|---|---|---|---|---|---|---|---|---|
| 1 | 19/20 | 5% | 5292 | 6569 | 7858 | 4947 | 0.18 | HTTP 502 |
| 2 | 20/20 | 0% | 6908 | 8511 | 8895 | 6504 | 0.28 | - |
| 4 | 20/20 | 0% | 10198 | 13340 | 16494 | 9650 | 0.37 | - |
| 8 | 0/20 | 100% | nan | nan | nan | nan | 0.00 | HTTP 502 |

Client = thời gian người dùng thật chờ (mạng + xếp hàng + xử lý). Server = `latency_ms` do API tự đo quanh phần xử lý ảnh. Client p50 tăng theo số đồng thời trong khi server p50 giữ nguyên nghĩa là request đang **xếp hàng** chứ không phải model chậm đi.
