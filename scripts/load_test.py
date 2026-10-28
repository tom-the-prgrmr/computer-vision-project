"""Stress test the DEPLOYED /predict endpoint (T12.9 —
docs/specs/g12-sua-ro-ri-va-do-prod.md).

Measures what a real user of the public deployment experiences, not the
Colab training box: cold start (service asleep -> first answer), then for
each concurrency level the client-side p50/p95/p99 latency, throughput and
error rate, plus the server-reported `latency_ms` (pure model time) so
queueing/network time can be told apart from inference time.

Standard library only (urllib + concurrent.futures) — nothing to install.

Usage:
    python scripts/load_test.py --url https://computer-vision-project-hl82.onrender.com
    python scripts/load_test.py --url http://localhost:8000 --levels 1,2 --requests 5 --no-cold
"""

import argparse
import csv
import json
import statistics
import time
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

# Portrait 740x1159 photo from outside the training set — close to what a
# phone upload looks like (the 640x640 Roboflow images would understate
# decode/resize cost).
DEFAULT_IMAGE = Path("data/ood_samples/tree/00000055.jpg")


@dataclass
class Sample:
    level: int
    started_at_s: float  # offset from the start of this level's run
    client_ms: float
    status: int  # HTTP status, 0 = network error / timeout
    server_ms: float | None
    error: str


def _multipart(image_path: Path) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    content_type = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="{image_path.name}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode() + image_path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    return body, f"multipart/form-data; boundary={boundary}"


def predict_once(url: str, body: bytes, content_type: str, timeout: float) -> tuple[float, int, float | None, str]:
    request = urllib.request.Request(f"{url}/predict", data=body, headers={"Content-Type": content_type})
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read()
            status = response.status
    except urllib.error.HTTPError as exc:
        return (time.perf_counter() - start) * 1000, exc.code, None, f"HTTP {exc.code}"
    except Exception as exc:  # timeout, connection reset, DNS...
        return (time.perf_counter() - start) * 1000, 0, None, type(exc).__name__
    client_ms = (time.perf_counter() - start) * 1000
    try:
        server_ms = float(json.loads(payload)["latency_ms"])
    except (ValueError, KeyError, TypeError):
        return client_ms, status, None, "bad JSON"
    return client_ms, status, server_ms, ""


def measure_cold_start(url: str, body: bytes, content_type: str, timeout: float, max_wait_s: float) -> dict:
    """Poll /health until it answers 200, then time the first /predict.
    Only meaningful if the service has been idle long enough to sleep
    (Render free tier: ~15 min without traffic)."""
    start = time.perf_counter()
    attempts = 0
    while time.perf_counter() - start < max_wait_s:
        attempts += 1
        try:
            with urllib.request.urlopen(f"{url}/health", timeout=timeout) as response:
                if response.status == 200:
                    break
        except Exception:
            time.sleep(2)
    else:
        return {"health_ready_s": None, "health_attempts": attempts, "first_predict_ms": None}
    health_ready_s = time.perf_counter() - start
    first_ms, status, server_ms, error = predict_once(url, body, content_type, timeout)
    return {
        "health_ready_s": health_ready_s,
        "health_attempts": attempts,
        "first_predict_ms": first_ms if status == 200 else None,
        "first_predict_server_ms": server_ms,
        "first_predict_error": error,
    }


def run_level(url: str, body: bytes, content_type: str, level: int, n_requests: int, timeout: float) -> tuple[list[Sample], float]:
    level_start = time.perf_counter()

    def one(_: int) -> Sample:
        started = time.perf_counter() - level_start
        client_ms, status, server_ms, error = predict_once(url, body, content_type, timeout)
        return Sample(level, started, client_ms, status, server_ms, error)

    with ThreadPoolExecutor(max_workers=level) as pool:
        samples = list(pool.map(one, range(n_requests)))
    return samples, time.perf_counter() - level_start


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return float("nan")
    if len(values) == 1:
        return values[0]
    return statistics.quantiles(values, n=100, method="inclusive")[int(p) - 1]


def summarize(samples: list[Sample], wall_s: float) -> dict:
    ok = [s for s in samples if s.status == 200 and not s.error]
    client = [s.client_ms for s in ok]
    server = [s.server_ms for s in ok if s.server_ms is not None]
    return {
        "level": samples[0].level,
        "n": len(samples),
        "ok": len(ok),
        "error_rate": 1 - len(ok) / len(samples),
        "p50_ms": _percentile(client, 50),
        "p95_ms": _percentile(client, 95),
        "p99_ms": _percentile(client, 99),
        "server_p50_ms": _percentile(server, 50),
        "throughput_rps": len(ok) / wall_s if wall_s > 0 else 0.0,
        "wall_s": wall_s,
        "errors": sorted({s.error for s in samples if s.error}),
    }


def write_report(out_md: Path, args: argparse.Namespace, cold: dict | None, rows: list[dict], label: str) -> None:
    lines = [
        f"# PROD load test — {label}",
        "",
        f"- URL: `{args.url}`",
        f"- Thời điểm (UTC): {datetime.now(timezone.utc):%Y-%m-%d %H:%M}",
        f"- Ảnh: `{args.image}` ({args.image.stat().st_size // 1024} KB)",
        f"- {args.requests} request mỗi mức đồng thời, timeout {args.timeout:.0f}s, warm-up {args.warmup} request (không tính)",
        "",
    ]
    if cold is not None:
        lines += ["## Cold start", ""]
        if cold["health_ready_s"] is None:
            lines.append(f"`/health` không trả 200 sau {args.cold_max_wait:.0f}s ({cold['health_attempts']} lần thử).")
        else:
            lines.append(
                f"`/health` trả 200 sau **{cold['health_ready_s']:.1f}s** ({cold['health_attempts']} lần thử); "
                f"`/predict` đầu tiên: **{cold['first_predict_ms'] or float('nan'):.0f} ms** client / "
                f"{cold['first_predict_server_ms'] or float('nan'):.0f} ms server"
                + (f" (lỗi: {cold['first_predict_error']})" if cold.get("first_predict_error") else "")
            )
        lines.append("")
    lines += [
        "## Warm — theo số request đồng thời",
        "",
        "| Đồng thời | OK/N | Error rate | p50 (ms) | p95 (ms) | p99 (ms) | Server p50 (ms) | Throughput (req/s) | Lỗi |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['level']} | {r['ok']}/{r['n']} | {r['error_rate']:.0%} | {r['p50_ms']:.0f} | {r['p95_ms']:.0f} | "
            f"{r['p99_ms']:.0f} | {r['server_p50_ms']:.0f} | {r['throughput_rps']:.2f} | {', '.join(r['errors']) or '-'} |"
        )
    lines += [
        "",
        "Client = thời gian người dùng thật chờ (mạng + xếp hàng + xử lý). Server = `latency_ms` "
        "do API tự đo quanh phần xử lý ảnh. Client p50 tăng theo số đồng thời trong khi server p50 "
        "giữ nguyên nghĩa là request đang **xếp hàng** chứ không phải model chậm đi.",
        "",
    ]
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Stress test the deployed /predict endpoint.")
    parser.add_argument("--url", required=True, help="base URL, no trailing slash")
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    parser.add_argument("--levels", default="1,2,4,8", help="comma-separated concurrency levels")
    parser.add_argument("--requests", type=int, default=20, help="requests per concurrency level")
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--no-cold", action="store_true", help="skip the cold-start measurement")
    parser.add_argument("--cold-max-wait", type=float, default=180.0)
    parser.add_argument("--label", default="before", help="tag for output files, e.g. before / after")
    parser.add_argument("--out-dir", type=Path, default=Path("docs/perf"))
    args = parser.parse_args()
    args.url = args.url.rstrip("/")

    body, content_type = _multipart(args.image)
    cold = None
    if not args.no_cold:
        print("Cold start: polling /health ...")
        cold = measure_cold_start(args.url, body, content_type, args.timeout, args.cold_max_wait)
        print(f"  {cold}")

    for _ in range(args.warmup):
        predict_once(args.url, body, content_type, args.timeout)

    stamp = f"{datetime.now(timezone.utc):%Y%m%d_%H%M}"
    all_samples, rows = [], []
    for level in (int(x) for x in args.levels.split(",")):
        samples, wall_s = run_level(args.url, body, content_type, level, args.requests, args.timeout)
        row = summarize(samples, wall_s)
        rows.append(row)
        all_samples += samples
        print(
            f"  concurrency={level}: ok {row['ok']}/{row['n']}, p50 {row['p50_ms']:.0f} ms, p95 {row['p95_ms']:.0f} ms, "
            f"server p50 {row['server_p50_ms']:.0f} ms, {row['throughput_rps']:.2f} req/s, errors {row['errors'] or '-'}"
        )

    csv_path = args.out_dir / f"prod_load_test_{stamp}_{args.label}.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["level", "started_at_s", "client_ms", "status", "server_ms", "error"])
        for s in all_samples:
            writer.writerow([s.level, f"{s.started_at_s:.3f}", f"{s.client_ms:.1f}", s.status, s.server_ms, s.error])
    md_path = args.out_dir / f"prod_load_test_{stamp}_{args.label}.md"
    write_report(md_path, args, cold, rows, args.label)
    print(f"Report: {md_path}\nRaw: {csv_path}")


if __name__ == "__main__":
    main()
