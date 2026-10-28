"""Detect train->valid/test leakage in the Roboflow v1 dataset and re-split it
by duplicate group (Giai đoạn 12 — docs/specs/g12-sua-ro-ri-va-do-prod.md).

Roboflow's README says "No image augmentation", but many valid/test images
are horizontally flipped copies of train images (same source name
`0000xxxx_jpg`, same class), and some are cropped/shifted copies uploaded
under a different source name. Two images belong to the same group if:
  (a) same source name (part before `_jpg.rf.`) AND same class set, or
  (b) dHash of one is within DHASH_THRESHOLD bits of the other's dHash or of
      its horizontal mirror (near-identical / flipped copies), or
  (c) among each image's ORB_CANDIDATES nearest neighbours -- by dHash of
      the whole image AND by dHash of the labelled-box crop (catches zoomed/
      re-framed copies whose whole-image hash moved a lot) -- ORB
      keypoint matching + RANSAC finds >= ORB_MIN_INLIERS geometrically
      consistent matches (same photo cropped/shifted -- dHash alone can't
      separate these from different people in the same pose on a white
      background).
Groups are closed transitively (union-find), then each whole group is
assigned to exactly one split.

The split is saved as a manifest CSV that IS committed to git
(data/splits/...), because data/processed/ is gitignored and Colab
re-downloads the raw dataset: Colab applies the manifest instead of
recomputing hashes/ORB (which can shift slightly across library versions).

CLI:
    python -m src.data.dedup_split data/raw/yoga_v1            # report + apply manifest (build it if missing)
    python -m src.data.dedup_split data/raw/yoga_v1 --rebuild  # recompute the split, overwrite manifest
"""

import argparse
import csv
import random
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

SPLITS = ("train", "valid", "test")
# 16x16 dHash (256 bits). Calibrated on yoga_v1: all 371 known duplicate
# pairs (same source name + class) are 0-1 bits apart; random pairs are
# >= 26 bits. An 8x8 hash at threshold 10 looked fine per pair (0.15% false
# matches) but over ~513k pairs union-find chained hundreds of different
# people on white backgrounds into one 106-image group.
DHASH_SIZE = 16
DHASH_THRESHOLD = 12
# Known duplicate pairs score >= ~430 inliers; unrelated pairs mostly < 10.
# Leakage counts are stable for thresholds 20-40 (max group 10 images);
# 25 also catches same-photoshoot near-duplicates (same person/background).
ORB_CANDIDATES = 10
ORB_MIN_INLIERS = 25
MANIFEST_PATH = Path("data/splits/yoga_v1_clean_manifest.csv")
OUT_DIR = Path("data/processed/yoga_v1_clean")
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


@dataclass
class ImageEntry:
    split: str
    path: Path
    source: str  # Roboflow source name, e.g. "00000006"
    classes: tuple[int, ...]  # sorted unique class ids from the label file
    dhash: int
    dhash_mirror: int
    crop_dhash: int  # dHash of the largest labelled box (whole image if no box)
    crop_dhash_mirror: int

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def main_class(self) -> int:
        """Class used for stratification (-1 = no box)."""
        return self.classes[0] if self.classes else -1


def _dhash(image: Image.Image, size: int = DHASH_SIZE) -> int:
    gray = image.convert("L").resize((size + 1, size), Image.LANCZOS)
    px = gray.tobytes()
    bits = 0
    for row in range(size):
        for col in range(size):
            left = px[row * (size + 1) + col]
            right = px[row * (size + 1) + col + 1]
            bits = (bits << 1) | (left > right)
    return bits


def _source_name(file_name: str) -> str:
    return file_name.split("_jpg.rf.")[0].split(".rf.")[0]


def _largest_box_crop(image: Image.Image, label_path: Path) -> Image.Image:
    boxes = []
    if label_path.exists():
        for line in label_path.read_text().splitlines():
            parts = line.split()
            if len(parts) == 5:
                _, x, y, w, h = map(float, parts)
                boxes.append((w * h, x, y, w, h))
    if not boxes:
        return image
    _, x, y, w, h = max(boxes)
    W, H = image.size
    left, top = max(0, (x - w / 2) * W), max(0, (y - h / 2) * H)
    right, bottom = min(W, (x + w / 2) * W), min(H, (y + h / 2) * H)
    if right - left < 2 or bottom - top < 2:
        return image
    return image.crop((left, top, right, bottom))


def _read_classes(label_path: Path) -> tuple[int, ...]:
    if not label_path.exists():
        return ()
    ids = {int(line.split()[0]) for line in label_path.read_text().splitlines() if line.strip()}
    return tuple(sorted(ids))


def load_entries(dataset_dir: Path) -> list[ImageEntry]:
    entries = []
    for split in SPLITS:
        image_dir = dataset_dir / split / "images"
        for path in sorted(image_dir.iterdir()):
            if path.suffix.lower() not in IMAGE_EXTS:
                continue
            label_path = dataset_dir / split / "labels" / f"{path.stem}.txt"
            with Image.open(path) as image:
                crop = _largest_box_crop(image, label_path)
                entries.append(
                    ImageEntry(
                        split=split,
                        path=path,
                        source=_source_name(path.name),
                        classes=_read_classes(label_path),
                        dhash=_dhash(image),
                        dhash_mirror=_dhash(ImageOps.mirror(image)),
                        crop_dhash=_dhash(crop),
                        crop_dhash_mirror=_dhash(ImageOps.mirror(crop)),
                    )
                )
    return entries


def _dhash_distance(a: ImageEntry, b: ImageEntry) -> int:
    return min((a.dhash ^ b.dhash).bit_count(), (a.dhash_mirror ^ b.dhash).bit_count())


def _crop_dhash_distance(a: ImageEntry, b: ImageEntry) -> int:
    return min((a.crop_dhash ^ b.crop_dhash).bit_count(), (a.crop_dhash_mirror ^ b.crop_dhash).bit_count())


def _orb_features(gray: np.ndarray, orb: cv2.ORB) -> tuple[list, np.ndarray | None]:
    return orb.detectAndCompute(gray, None)


def _ransac_inliers(feat_a: tuple, feat_b: tuple, matcher: cv2.BFMatcher) -> int:
    (kp_a, des_a), (kp_b, des_b) = feat_a, feat_b
    if des_a is None or des_b is None or len(kp_a) < 10 or len(kp_b) < 10:
        return 0
    good = [
        pair[0]
        for pair in matcher.knnMatch(des_a, des_b, k=2)
        if len(pair) == 2 and pair[0].distance < 0.75 * pair[1].distance
    ]
    if len(good) < 8:
        return 0
    pts_a = np.float32([kp_a[m.queryIdx].pt for m in good])
    pts_b = np.float32([kp_b[m.trainIdx].pt for m in good])
    _, mask = cv2.estimateAffinePartial2D(pts_a, pts_b, method=cv2.RANSAC, ransacReprojThreshold=8)
    return int(mask.sum()) if mask is not None else 0


def find_duplicate_groups(entries: list[ImageEntry]) -> list[int]:
    """Return group id per entry (same index as `entries`). ORB step takes
    ~1 min for ~1000 images on CPU."""
    parent = list(range(len(entries)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        parent[find(i)] = find(j)

    by_source: dict[tuple[str, tuple[int, ...]], int] = {}
    for i, entry in enumerate(entries):
        key = (entry.source, entry.classes)
        if key in by_source:
            union(i, by_source[key])
        else:
            by_source[key] = i

    n = len(entries)
    candidates: set[tuple[int, int]] = set()
    for i in range(n):
        distances = sorted((_dhash_distance(entries[i], entries[j]), j) for j in range(n) if j != i)
        for distance, j in distances:
            if distance <= DHASH_THRESHOLD:
                union(i, j)
        crop_nearest = sorted((_crop_dhash_distance(entries[i], entries[j]), j) for j in range(n) if j != i)
        for _, j in distances[:ORB_CANDIDATES] + crop_nearest[:ORB_CANDIDATES]:
            candidates.add((min(i, j), max(i, j)))

    orb = cv2.ORB_create(1000)
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
    features, features_mirror = [], []
    for entry in entries:
        gray = cv2.imread(str(entry.path), cv2.IMREAD_GRAYSCALE)
        features.append(_orb_features(gray, orb))
        features_mirror.append(_orb_features(cv2.flip(gray, 1), orb))
    for i, j in sorted(candidates):
        if find(i) == find(j):
            continue
        inliers = max(
            _ransac_inliers(features[i], features[j], matcher),
            _ransac_inliers(features_mirror[i], features[j], matcher),
        )
        if inliers >= ORB_MIN_INLIERS:
            union(i, j)

    roots = [find(i) for i in range(len(entries))]
    renumber = {root: n for n, root in enumerate(dict.fromkeys(roots))}
    return [renumber[root] for root in roots]


def leakage_report(splits: list[str], groups: list[int]) -> dict[str, tuple[int, int]]:
    """For valid/test: (images sharing a group with train, total images)."""
    train_groups = {g for s, g in zip(splits, groups) if s == "train"}
    report = {}
    for split in ("valid", "test"):
        members = [g for s, g in zip(splits, groups) if s == split]
        report[split] = (sum(g in train_groups for g in members), len(members))
    return report


def group_split(
    entries: list[ImageEntry],
    groups: list[int],
    ratios: tuple[float, float, float] = (0.70, 0.15, 0.15),
    seed: int = 42,
) -> list[str]:
    """Assign every group wholly to one split, stratified by class.

    Within each class, groups are shuffled (seeded) then each goes to the
    split furthest below its target image count -- greedy fill by images,
    not by groups, since groups have different sizes.
    """
    members: dict[int, list[int]] = defaultdict(list)
    for i, g in enumerate(groups):
        members[g].append(i)

    groups_by_class: dict[int, list[int]] = defaultdict(list)
    for g, idxs in members.items():
        main = Counter(entries[i].main_class for i in idxs).most_common(1)[0][0]
        groups_by_class[main].append(g)

    rng = random.Random(seed)
    assignment: dict[int, str] = {}
    for cls in sorted(groups_by_class):
        cls_groups = sorted(groups_by_class[cls])
        rng.shuffle(cls_groups)
        total = sum(len(members[g]) for g in cls_groups)
        filled = dict.fromkeys(SPLITS, 0)
        for g in cls_groups:
            target = min(SPLITS, key=lambda s: filled[s] / (ratios[SPLITS.index(s)] * total))
            assignment[g] = target
            filled[target] += len(members[g])
    return [assignment[g] for g in groups]


def write_manifest(entries: list[ImageEntry], groups: list[int], new_splits: list[str], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["old_split", "file", "group", "main_class", "new_split"])
        for entry, group, new_split in zip(entries, groups, new_splits):
            writer.writerow([entry.split, entry.name, group, entry.main_class, new_split])


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _class_header(dataset_dir: Path) -> str:
    """`nc:` + `names:` block copied verbatim from the original data.yaml."""
    original_yaml = (dataset_dir / "data.yaml").read_text(encoding="utf-8")
    names_block = original_yaml[original_yaml.index("names:") : original_yaml.index("nc:")]
    nc_line = next(line for line in original_yaml.splitlines() if line.startswith("nc:"))
    return f"{nc_line}\n{names_block}"


def clean_original_files(manifest: list[dict[str, str]], split: str = "test") -> list[str]:
    """Files of an ORIGINAL Roboflow split sharing no group with the original
    train split -- the only fair test set for a model trained on the original
    split (T12.3). Do NOT evaluate such a model on the new test split: it may
    contain images the model trained on."""
    train_groups = {row["group"] for row in manifest if row["old_split"] == "train"}
    return [row["file"] for row in manifest if row["old_split"] == split and row["group"] not in train_groups]


def write_subset_yaml(dataset_dir: Path, split: str, files: list[str], out_dir: Path) -> Path:
    """data.yaml whose val AND test both point at a txt list of the given
    files inside dataset_dir/<split>/images (labels are found by
    Ultralytics' images->labels path convention). Used to evaluate the old
    model on clean_original_files() only."""
    out_dir.mkdir(parents=True, exist_ok=True)
    list_path = out_dir / f"{split}.txt"
    list_path.write_text(
        "".join(f"{(dataset_dir / split / 'images' / f).resolve().as_posix()}\n" for f in files),
        encoding="utf-8",
    )
    list_ref = list_path.resolve().as_posix()
    yaml_path = out_dir / "data.yaml"
    yaml_path.write_text(
        f"train: {list_ref}\nval: {list_ref}\ntest: {list_ref}\n{_class_header(dataset_dir)}",
        encoding="utf-8",
    )
    return yaml_path


def apply_manifest(dataset_dir: Path, manifest: list[dict[str, str]], out_dir: Path = OUT_DIR) -> None:
    """Copy images + labels from dataset_dir into out_dir/<new_split>/ and
    write a data.yaml keeping the original class names (with their
    "yoga-pose " prefix, so app CLASS_NAMES stay valid)."""
    if out_dir.exists():
        shutil.rmtree(out_dir)
    for row in manifest:
        src_img = dataset_dir / row["old_split"] / "images" / row["file"]
        src_lbl = dataset_dir / row["old_split"] / "labels" / f"{Path(row['file']).stem}.txt"
        for src, kind in ((src_img, "images"), (src_lbl, "labels")):
            if not src.exists():
                if kind == "images":
                    raise FileNotFoundError(f"manifest lists {src} but it is missing -- wrong dataset version?")
                continue
            dst = out_dir / row["new_split"] / kind / src.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    (out_dir / "data.yaml").write_text(
        f"path: {out_dir.resolve().as_posix()}\n"
        "train: train/images\nval: valid/images\ntest: test/images\n"
        f"{_class_header(dataset_dir)}",
        encoding="utf-8",
    )


def summarize(manifest: list[dict[str, str]]) -> None:
    groups_per_split: dict[str, set[str]] = defaultdict(set)
    classes_per_split: dict[str, Counter] = defaultdict(Counter)
    for row in manifest:
        groups_per_split[row["new_split"]].add(row["group"])
        classes_per_split[row["new_split"]][row["main_class"]] += 1
    for split in SPLITS:
        n_images = sum(classes_per_split[split].values())
        dist = dict(sorted(classes_per_split[split].items()))
        print(f"  {split:5}: {n_images:4} images, {len(groups_per_split[split]):4} groups, class dist {dist}")
    crossing = [g for g in set().union(*groups_per_split.values()) if sum(g in groups_per_split[s] for s in SPLITS) > 1]
    print(f"  groups crossing splits: {len(crossing)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("dataset_dir", type=Path)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    parser.add_argument("--rebuild", action="store_true", help="recompute groups/split and overwrite the manifest")
    args = parser.parse_args()

    if args.rebuild or not args.manifest.exists():
        entries = load_entries(args.dataset_dir)
        groups = find_duplicate_groups(entries)
        splits = [e.split for e in entries]
        print(f"{len(entries)} images -> {len(set(groups))} duplicate groups")
        print("Leakage in ORIGINAL split (images sharing a group with train):")
        for split, (leaked, total) in leakage_report(splits, groups).items():
            print(f"  {split:5}: {leaked}/{total} leaked, {total - leaked} clean")
        new_splits = group_split(entries, groups)
        write_manifest(entries, groups, new_splits, args.manifest)
        print(f"Manifest written: {args.manifest}")

    manifest = read_manifest(args.manifest)
    print("NEW split:")
    summarize(manifest)
    apply_manifest(args.dataset_dir, manifest, args.out)
    print(f"Dataset written: {args.out}/data.yaml")


if __name__ == "__main__":
    main()
