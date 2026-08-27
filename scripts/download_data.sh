#!/usr/bin/env bash
# Download the v1 dataset (5 pose classes, bbox-annotated, YOLO format) from
# Roboflow Universe: https://universe.roboflow.com/object-detection-dt-wzpc6/yolo-yoga-dataset
#
# Requires: pip install roboflow, and a Roboflow API key
# (https://app.roboflow.com/settings/api -> set ROBOFLOW_API_KEY env var)

set -euo pipefail

if [ -z "${ROBOFLOW_API_KEY:-}" ]; then
  echo "Set ROBOFLOW_API_KEY first (see comment at top of this script)." >&2
  exit 1
fi

python - <<'PY'
import os
from roboflow import Roboflow

rf = Roboflow(api_key=os.environ["ROBOFLOW_API_KEY"])
project = rf.workspace("object-detection-dt-wzpc6").project("yolo-yoga-dataset")
dataset = project.version(1).download("yolov8", location="data/raw/yoga_v1")
print("Downloaded to", dataset.location)
PY
