# PROD load test — after_cap2

- URL: `https://computer-vision-project-hl82.onrender.com`
- Thời điểm (UTC): 2026-11-10 16:18
- Ảnh: `data\ood_samples\tree\00000055.jpg` (81 KB)
- 20 request mỗi mức đồng thời, timeout 60s, warm-up 2 request (không tính)

## Cold start

`/health` trả 200 sau **22.5s** (1 lần thử); `/predict` đầu tiên: **10059 ms** client / 9771 ms server

## Warm — theo số request đồng thời

| Đồng thời | OK/N | Error rate | p50 (ms) | p95 (ms) | p99 (ms) | Server p50 (ms) | Throughput (req/s) | Lỗi |
|---|---|---|---|---|---|---|---|---|
| 1 | 20/20 | 0% | 5199 | 6133 | 6440 | 4866 | 0.20 | - |
| 2 | 20/20 | 0% | 7504 | 9340 | 9944 | 7100 | 0.26 | - |
| 4 | 20/20 | 0% | 14544 | 16425 | 16889 | 7252 | 0.27 | - |
| 8 | 20/20 | 0% | 27006 | 31139 | 31778 | 7051 | 0.27 | - |

Client = thời gian người dùng thật chờ (mạng + xếp hàng + xử lý). Server = `latency_ms` do API tự đo quanh phần xử lý ảnh. Client p50 tăng theo số đồng thời trong khi server p50 giữ nguyên nghĩa là request đang **xếp hàng** chứ không phải model chậm đi.
