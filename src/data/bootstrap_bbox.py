"""Bootstrap bounding-box labels for the v2 (15-20 class) yoga pose dataset.

Yoga-82 only has whole-image classification labels (one pose per image, no
bounding box). We don't want to hand-annotate hundreds of images, so instead:

1. Run a pretrained person detector (YOLOv8n, COCO weights, class "person")
   on every Yoga-82 image.
2. Keep the highest-confidence "person" box per image (Yoga-82 images are
   single-subject, so this is a safe heuristic — sanity check a sample).
3. Re-label that box with the image's existing Yoga-82 pose class instead of
   "person" -> gives a detection-ready dataset (bbox + pose class) with zero
   manual annotation.
4. Export to YOLO format (data.yaml + labels/*.txt) alongside the v1 Roboflow
   set so both can be trained/compared.

This is a weak-supervision step, not a trained model — call it out as such in
docs/problem_statement.md and the video, don't present it as ground truth.

TODO:
- [ ] point RAW_DIR at the downloaded Yoga-82 image folder (per-class subdirs)
- [ ] pick the ~15-20 classes with enough images (see notebooks/01_data_exploration.ipynb)
- [ ] run detection, filter out images with no person detected above CONF_THRESHOLD
- [ ] spot-check ~30 random boxes visually before trusting the pseudo-labels
- [ ] write YOLO-format labels + data.yaml to data/processed/yoga_v2/
"""

from pathlib import Path

RAW_DIR = Path("data/raw/yoga82")
OUT_DIR = Path("data/processed/yoga_v2")
PERSON_DETECTOR_WEIGHTS = "yolov8n.pt"  # pretrained COCO checkpoint
CONF_THRESHOLD = 0.5


def bootstrap_bboxes(raw_dir: Path = RAW_DIR, out_dir: Path = OUT_DIR) -> None:
    """Generate pseudo bounding-box labels for every image under raw_dir.

    raw_dir is expected to have one subfolder per pose class, e.g.:
        raw_dir/tree/img001.jpg
        raw_dir/warrior2/img002.jpg
    """
    raise NotImplementedError(
        "Fill in once Yoga-82 subset is downloaded — see TODO list in the module docstring."
    )


if __name__ == "__main__":
    bootstrap_bboxes()
