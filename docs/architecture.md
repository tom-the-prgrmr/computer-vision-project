# Kiến trúc

Sơ đồ dưới đây phản ánh đúng code thật trong repo tại thời điểm viết (sau
Giai đoạn 9) — không phải bản dự kiến ban đầu. 3 sơ đồ: (1) kiến trúc model
suy luận, (2) luồng request end-to-end từ trình duyệt tới API, (3) luồng
dữ liệu/training.

## 1. Kiến trúc model — 2 lớp độc lập

Model **được train** là YOLOv8 (detect + classify tư thế trong 1 bước, xuất
ONNX). Sau đó mỗi box được crop và đưa qua MediaPipe Pose (**pretrained,
không train**) để lấy 33 keypoint, rồi so với ngưỡng góc khớp thủ công
(`POSE_RULES`, **rule-based, không phải model**) để chấm form. 3 loại khối
này được chấm điểm khác nhau trong rubric (mục 1-4,7 dùng model train được;
mục 6 là "ý tưởng riêng", không có accuracy/F1 của chính nó) — xem
`CLAUDE.md`.

```mermaid
graph TD
    A["Ảnh input<br/>(RGB, HWC)"] --> B["YOLOv8 ONNX<br/>(đã train — src/models/onnx_inference.py)"]
    B -->|"letterbox 640×640<br/>+ per-class NMS"| C["Boxes + pose class + confidence<br/>(run_onnx_detection)"]
    C --> D["Crop từng box"]
    D --> E["MediaPipe Pose<br/>(pretrained, off-the-shelf —<br/>src/pose_scoring/landmark_extraction.py)"]
    E -->|"33 landmark (x,y) px"| F["resolve_joint_angle()<br/>(3 điểm khớp → góc)"]
    F --> G["score_pose()<br/>(rule-based, hand-tuned —<br/>src/pose_scoring/angle_rules.py)"]
    G -->|"so với POSE_RULES[pose_class]<br/>(AngleRange min/max)"| H["form_ok + tips<br/>(gợi ý sửa form)"]
    C --> I["Detection: pose, confidence, box"]
    H --> I
    I --> J["PredictResponse<br/>(app/schemas.py)"]

    style B fill:#2d5a2d,color:#fff
    style E fill:#5a4a2d,color:#fff
    style G fill:#4a2d5a,color:#fff
```

**Chú thích màu:** xanh lá = model tự train (YOLOv8, rubric mục 1-4,7);
vàng = pretrained dùng nguyên (MediaPipe Pose, không tính vào accuracy của
model chính); tím = rule-based thủ công (không phải model, rubric mục 6 —
"ý tưởng riêng", không có metric accuracy/F1 riêng).

## 2. Luồng request end-to-end (thật, đã deploy)

Frontend (`web/index.html`, tĩnh) và backend (`app/`, FastAPI) chạy tách
origin khi deploy thật (Cloudflare Pages + Render — Giai đoạn 9); khi chạy
local qua `uvicorn app.main:app`, backend tự mount luôn `web/` cùng origin
(không cần bước CORS). Model + MediaPipe chỉ load **1 lần** lúc có request
đầu tiên (`PoseDetectionService._ensure_loaded()`, lazy), không load lại
mỗi request.

```mermaid
sequenceDiagram
    participant U as Người dùng (trình duyệt/iPhone Safari)
    participant FE as web/index.html<br/>(Cloudflare Pages, tĩnh)
    participant API as FastAPI app/controller.py<br/>(Render, /predict)
    participant SVC as PoseDetectionService<br/>(app/service.py)
    participant ONNX as onnxruntime.InferenceSession<br/>(models/best.onnx)
    participant MP as MediaPipe Pose

    U->>FE: Bật camera / upload ảnh
    FE->>FE: captureAndPredict()<br/>canvas.toBlob() (JPEG)
    FE->>API: POST /predict (multipart form, BACKEND_URL)
    API->>SVC: predict_image(image_bytes)
    SVC->>SVC: _ensure_loaded() (lazy, 1 lần/process)
    SVC->>ONNX: _detect(image) → run_onnx_detection()
    ONNX-->>SVC: boxes + pose class + confidence
    loop mỗi box detect được
        SVC->>SVC: crop box
        SVC->>MP: _extract_landmarks(crop)
        MP-->>SVC: 33 landmarks (hoặc None nếu crop rỗng)
        SVC->>SVC: score_pose(pose_class, landmarks)
    end
    SVC-->>API: PredictResponse (detections + latency_ms)
    API-->>FE: JSON (CORS: Access-Control-Allow-Origin theo ALLOWED_ORIGINS)
    FE->>FE: drawDetectionsOnto() (box+tip đè lên canvas)<br/>renderResults() (card kết quả)
    FE-->>U: Hiện box/tip + card trên màn hình
```

`/predict_video` (`app/controller.py`) đã wire route nhưng
`PoseDetectionService.predict_video()` vẫn raise `NotImplementedError` —
optional (T7.7), không làm vì ngoài phạm vi buffer thời gian, web demo xử
lý video bằng cách gọi lặp lại `/predict` mỗi frame phía client (xem
`CAPTURE_INTERVAL_MS` trong `web/index.html`), không phải 1 endpoint video
streaming thật.

## 3. Luồng dữ liệu & training

**v1 là pipeline duy nhất đã chạy hết vòng đời thật** (download → train →
ablation → eval → export → deploy). **v2 vẫn là code stub**
(`bootstrap_bboxes()` raise `NotImplementedError`) — không triển khai vì
Giai đoạn 5 (feedback loop) đo được OOD accuracy 94.4% trên baseline v1,
không tìm ra pattern lỗi cần dataset lớn hơn để sửa, nên quyết định không
cần v2 (đúng tinh thần buffer PLAN.md: chỉ làm v2 nếu dư thời gian).

```mermaid
graph TD
    subgraph v1["v1 — ĐÃ CHẠY THẬT (5 lớp, Roboflow)"]
        A1["scripts/download_data.sh<br/>(ROBOFLOW_API_KEY)"] --> A2["data/raw/yoga_v1/<br/>(YOLO format, có sẵn bbox)"]
    end
    subgraph v2["v2 — CODE STUB, CHƯA CHẠY (15-20 lớp, Yoga-82)"]
        B1["Yoga-82<br/>(chỉ có classification label)"] -.-> B2["bootstrap_bboxes()<br/>src/data/bootstrap_bbox.py<br/>(NotImplementedError — chưa cần)"]
        B2 -.-> B3["data/processed/yoga_v2/<br/>(pseudo-label, weak supervision)"]
    end
    A2 --> C["notebooks/02_train_detector.ipynb<br/>train() — src/models/train.py<br/>seed=42, epochs=50"]
    C --> D["Baseline (aug on) vs Ablation (aug off)<br/>Giai đoạn 3 — 2 run, cùng seed/epochs"]
    D --> E["notebooks/03_evaluation_error_analysis.ipynb<br/>mAP, confusion matrix, EigenCAM"]
    E --> F["notebooks/05_feedback_loop_ood.ipynb<br/>OOD test 18 ảnh ngoài dataset<br/>→ 94.4% — đủ robust, không retrain"]
    F --> G["notebooks/04_export_onnx.ipynb<br/>export_onnx() — src/models/export.py"]
    G --> H["models/best.onnx<br/>(Git LFS, dùng ở app/ + deploy)"]

    style B2 fill:#5a2d2d,color:#fff
    style B3 fill:#5a2d2d,color:#fff
```

## Deploy topology thật (Giai đoạn 9)

```mermaid
graph LR
    Phone["iPhone Safari<br/>(HTTPS công khai)"] --> CF["Cloudflare Pages<br/>computer-vision-project.pthieu290998.workers.dev<br/>(static — chỉ serve web/)"]
    CF -->|"fetch BACKEND_URL + /predict<br/>(CORS: ALLOWED_ORIGINS)"| Render["Render Web Service<br/>computer-vision-project-hl82.onrender.com<br/>(Docker, free — cold start ~15p không dùng)"]
    Render --> ONNXR["onnxruntime + MediaPipe<br/>(CPU, models/best.onnx qua Git LFS)"]
```

Phương án thay thế (đã build + review, chưa dùng): VPS riêng + Caddy
(`docker-compose.yml`, `Caddyfile`) — gộp frontend+backend 1 process, không
cold start, dùng nếu Render free không đủ ổn định (xem
`docs/specs/g9-deploy-public.md`).
