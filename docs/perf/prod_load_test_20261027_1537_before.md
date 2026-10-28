# PROD load test — before

- URL: `https://computer-vision-project-hl82.onrender.com`
- Thời điểm (UTC): 2026-10-27 15:43
- Ảnh: `data\ood_samples\tree\00000055.jpg` (81 KB)
- 20 request mỗi mức đồng thời, timeout 60s, warm-up 2 request (không tính)

## Warm — theo số request đồng thời

| Đồng thời | OK/N | Error rate | p50 (ms) | p95 (ms) | p99 (ms) | Server p50 (ms) | Throughput (req/s) | Lỗi |
|---|---|---|---|---|---|---|---|---|
| 1 | 20/20 | 0% | 5154 | 6294 | 6310 | 4862 | 0.19 | - |
| 2 | 20/20 | 0% | 9653 | 10910 | 11060 | 4802 | 0.20 | - |
| 4 | 18/20 | 10% | 11111 | 42142 | 42411 | 4658 | 0.21 | HTTP 502 |
| 8 | 15/20 | 25% | 21726 | 49084 | 51519 | 4902 | 0.18 | HTTP 502, TimeoutError |

Client = thời gian người dùng thật chờ (mạng + xếp hàng + xử lý). Server = `latency_ms` do API tự đo quanh phần xử lý ảnh. Client p50 tăng theo số đồng thời trong khi server p50 giữ nguyên nghĩa là request đang **xếp hàng** chứ không phải model chậm đi.
