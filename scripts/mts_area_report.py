import argparse
import csv
import os
import re
from pathlib import Path

from PIL import Image
import numpy as np


FILENAME_RE = re.compile(r"^(img_(?P<n>\d+)_(?P<m>\d+)_(?P<tag>[^_]*)?(?P<eq>_equalized)?(?:_[^_]*)?)_s\.png$")


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

    rows = []
    for s_path in base_dir.glob("*_s.png"):
        match = FILENAME_RE.match(s_path.name)
        if not match:
            # Skip files not following naming convention
            continue
        base = match.group(1)
        n = match.group("n")
        m = match.group("m")
        tag = match.group("tag") or ""
        equalized = bool(match.group("eq"))

        m_path = s_path.with_name(f"{base}_m.png")
        if not m_path.exists():
            # Incomplete pair; skip
            continue

        s_area = compute_foreground_area(s_path)
        m_area = compute_foreground_area(m_path)

        rows.append({
            "base": base,
            "n": int(n),
            "m": int(m),
            "tag": tag,
            "equalized": int(equalized),
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


