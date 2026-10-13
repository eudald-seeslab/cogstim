#!/usr/bin/env python3
"""Visual properties of dot arrays, so number and visual cues can be told apart.

Changing the numerosity of a dot array changes its visual properties too: more
dots cover more surface, spread over a larger area and have a longer total
contour. Gebuis & Reynvoet (2011, Behavior Research Methods, 43, 981-986) show
that no generation scheme removes this covariation for every cue at once, and
argue that a stimulus generator should therefore report the visual properties
of every array and every pair, so that an analysis can show afterwards whether
number or a visual cue explains the results.

This module computes the five properties they report, from the Scene recorded
while drawing: total surface, item size, total circumference, area extended
(the convex hull) and density. Pairs are reported with the numerical distance
and the difference in each property, signed so that a positive difference means
the cue is congruent with number.
"""

import csv
import os
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np

from cogstim.helpers.geometry import ELLIPSE

# Points sampled on each dot's outline when computing the convex hull. The hull
# of discs is bounded by arcs; a 90-gon inscribed in a circle covers all but
# 0.08% of its area, far below the rasterisation error of the dots themselves.
HULL_SAMPLES = 90

PROPERTY_NAMES = [
    "total_surface_px",
    "mean_diameter_px",
    "total_circumference_px",
    "convex_hull_px",
    "density",
]

PROPERTY_FIELDS = ["image", "colour", "n_dots", *PROPERTY_NAMES]

PAIR_FIELDS = [
    "image_1", "colour_1", "n_1",
    "image_2", "colour_2", "n_2",
    "numerical_distance", "numerical_ratio", "weber_fraction",
    *[f"{name}_{suffix}" for name in PROPERTY_NAMES for suffix in ("diff", "ratio")],
]


def convex_hull_area(points) -> float:
    """Area of the convex hull of (x, y) points, by Andrew's monotone chain.

    Args:
        points: Sequence of (x, y) pairs.

    Returns:
        float: Hull area, 0 when the points do not span a polygon.
    """
    unique = np.unique(np.asarray(points, dtype=float), axis=0)
    if len(unique) < 3:
        return 0.0
    # np.unique sorts rows lexicographically, which is the order the chain needs.
    sorted_points = [tuple(p) for p in unique]

    def turns_left(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]) > 0

    lower: list = []
    for p in sorted_points:
        while len(lower) >= 2 and not turns_left(lower[-2], lower[-1], p):
            lower.pop()
        lower.append(p)
    upper: list = []
    for p in reversed(sorted_points):
        while len(upper) >= 2 and not turns_left(upper[-2], upper[-1], p):
            upper.pop()
        upper.append(p)
    hull = np.array(lower[:-1] + upper[:-1])

    xs, ys = hull[:, 0], hull[:, 1]
    return float(0.5 * abs(np.dot(xs, np.roll(ys, -1)) - np.dot(ys, np.roll(xs, -1))))


def disc_hull_area(discs: Sequence[Tuple[float, float, float]]) -> float:
    """Area extended by a set of discs: the convex hull of their outlines.

    Gebuis & Reynvoet take the hull rather than the field the dots were placed
    in, because randomly placed dots cluster and cover less than the field.

    Args:
        discs: (centre_x, centre_y, radius) per dot.

    Returns:
        float: Hull area in square pixels.
    """
    angles = np.linspace(0, 2 * np.pi, HULL_SAMPLES, endpoint=False)
    xs = np.concatenate([cx + r * np.cos(angles) for cx, cy, r in discs])
    ys = np.concatenate([cy + r * np.sin(angles) for cx, cy, r in discs])
    return convex_hull_area(np.column_stack([xs, ys]))


def group_properties(discs: Sequence[Tuple[float, float, float]]) -> Dict[str, float]:
    """The five visual properties of one dot array.

    Args:
        discs: (centre_x, centre_y, radius) per dot; at least one.

    Returns:
        dict: n_dots and the values named in PROPERTY_NAMES. Density follows
        Gebuis & Reynvoet: area extended divided by total surface, so a larger
        value means a sparser array.
    """
    radii = np.array([r for _, _, r in discs], dtype=float)
    surface = float(np.sum(np.pi * radii ** 2))
    hull = disc_hull_area(discs)
    return {
        "n_dots": len(radii),
        "total_surface_px": surface,
        "mean_diameter_px": float(np.mean(2 * radii)),
        "total_circumference_px": float(np.sum(2 * np.pi * radii)),
        "convex_hull_px": hull,
        "density": hull / surface,
    }


def image_property_records(image_name: str, scene) -> List[dict]:
    """Describe every dot array in one image, one record per dot colour.

    Args:
        image_name: Filename the arrays belong to, relative to the output root.
        scene: The Scene recorded while the image was drawn.

    Returns:
        list: One dict per colour, keyed by PROPERTY_FIELDS.
    """
    discs_by_colour: Dict[str, list] = {}
    for element in scene.visible_elements():
        if element.kind != ELLIPSE or element.label != "dot":
            continue
        cx, cy = element.centre
        discs_by_colour.setdefault(element.fill, []).append((cx, cy, element.radius))

    return [
        {"image": image_name, "colour": colour, **group_properties(discs)}
        for colour, discs in discs_by_colour.items()
    ]


def pair_property_records(records: Iterable[dict], pairs) -> List[dict]:
    """Compare the two arrays of each pair, numerically and visually.

    Differences and ratios are taken as the more numerous array against the
    less numerous one, so a positive difference means the cue grows with
    number. When both arrays hold the same count, side 1 is taken first.

    Args:
        records: Records from image_property_records().
        pairs: ((image, colour), (image, colour)) per pair, in the order the
            paradigm names them (colour 1 then colour 2; sample then match).

    Returns:
        list: One dict per pair, keyed by PAIR_FIELDS. A pair one of whose
        sides drew no dots has nothing to compare and yields no record.
    """
    by_key = {(record["image"], record["colour"]): record for record in records}

    rows = []
    for side_1, side_2 in pairs:
        if side_1 not in by_key or side_2 not in by_key:
            continue
        first, second = by_key[side_1], by_key[side_2]
        more, fewer = (
            (first, second) if first["n_dots"] >= second["n_dots"] else (second, first)
        )
        row = {
            "image_1": first["image"], "colour_1": first["colour"], "n_1": first["n_dots"],
            "image_2": second["image"], "colour_2": second["colour"], "n_2": second["n_dots"],
            "numerical_distance": more["n_dots"] - fewer["n_dots"],
            "numerical_ratio": fewer["n_dots"] / more["n_dots"],
            "weber_fraction": (more["n_dots"] - fewer["n_dots"]) / more["n_dots"],
        }
        for name in PROPERTY_NAMES:
            row[f"{name}_diff"] = more[name] - fewer[name]
            row[f"{name}_ratio"] = more[name] / fewer[name]
        rows.append(row)
    return rows


def write_properties_csv(path: str, records: List[dict], fields: List[str]) -> None:
    """Write property or pair records as CSV, floats rounded to 3 decimals."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow({
                key: round(value, 3) if isinstance(value, float) else value
                for key, value in record.items()
            })
