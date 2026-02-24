import argparse
import csv
import os
import re
from pathlib import Path

from PIL import Image
import numpy as np


# One image per file: mts_{trial_id:05d}_{r|e}_{a|b}_{n_dots}[_version].png
FILENAME_RE = re.compile(
    r"^mts_(?P<trial_id>\d{5})_(?P<eq_type>r|e)_(?P<role>a|b)_(?P<n_dots>\d+)(?:_[^_]+)?\.png$"
)


def compute_foreground_area(image_path: Path) -> int:
    """Count non-white pixels as foreground area (black dots on white background)."""
    with Image.open(image_path) as im:
        arr = np.asarray(im.convert("RGB"))
    # Non-white pixels
    non_white = np.any(arr != [255, 255, 255], axis=-1)
    return int(np.count_nonzero(non_white))


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute sample/match areas for MTS pairs and write CSV")
    parser.add_argument("--dir", dest="dir", default=os.path.join("images", "match_to_sample", "train"), help="Directory with MTS images (defaults to images/match_to_sample/train)")
    parser.add_argument("--out", dest="out", default="mts_train_areas.csv", help="Output CSV filename (defaults to mts_train_areas.csv in CWD)")
    args = parser.parse_args()

    base_dir = Path(args.dir)
    if not base_dir.exists():
        raise FileNotFoundError(f"Directory not found: {base_dir}")

    # Group parsed files by (trial_id, eq_type); each pair has role "a" (match) and "b" (sample).
    by_pair: dict[tuple[str, str], dict[str, Path]] = {}
    for path in base_dir.glob("mts_*.png"):
        match = FILENAME_RE.match(path.name)
        if not match:
            continue
        trial_id = match.group("trial_id")
        eq_type = match.group("eq_type")
        role = match.group("role")
        n_dots = match.group("n_dots")
        key = (trial_id, eq_type)
        if key not in by_pair:
            by_pair[key] = {}
        by_pair[key][role] = (path, int(n_dots))

    rows = []
    for (trial_id, eq_type), files in sorted(by_pair.items()):
        if "a" not in files or "b" not in files:
            continue
        (m_path, n_match) = files["a"]
        (s_path, n_sample) = files["b"]
        s_area = compute_foreground_area(s_path)
        m_area = compute_foreground_area(m_path)
        base = f"mts_{trial_id}_{eq_type}"
        rows.append({
            "base": base,
            "n": n_sample,
            "m": n_match,
            "tag": trial_id,
            "equalized": 1 if eq_type == "e" else 0,
            "s_area_px": s_area,
            "m_area_px": m_area,
            "s_file": str(s_path),
            "m_file": str(m_path),
        })

    # Write CSV
    fieldnames = ["base", "n", "m", "tag", "equalized", "s_area_px", "m_area_px", "s_file", "m_file"]
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {args.out}")


if __name__ == "__main__":
    main()


