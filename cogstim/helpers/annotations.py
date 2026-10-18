#!/usr/bin/env python3
"""Export where every stimulus feature is, and render stimuli as vectors.

Reviewer @srvanderplas rejected the paper's computer-vision and eye-tracking
claims in JOSS review openjournals/joss-reviews#10532 because the package wrote
images and nothing else:

    "This suggests that the authors have not examined whether their software is
    suitable for a wider range of use cases beyond the ones motivating the
    development of this package, but still would like to claim a broader
    application range for the software."

Both outputs here come from the same Scene recorded while drawing, so an
annotation and an SVG can never disagree with the raster they describe.
"""

import csv
import json
import os
from typing import List, Tuple

from cogstim.helpers.geometry import ELLIPSE, LINE, POLYGON, RECTANGLE

ANNOTATION_FIELDS = [
    "image",
    "element_index",
    "label",
    "kind",
    "centre_x",
    "centre_y",
    "bbox_x_min",
    "bbox_y_min",
    "bbox_x_max",
    "bbox_y_max",
    "bbox_width",
    "bbox_height",
    "radius",
    "colour",
    "vertices",
]


def element_records(image_name: str, scene) -> List[dict]:
    """Describe every visible element of one image.

    Args:
        image_name: Filename the elements belong to, relative to the output root.
        scene: The Scene recorded while the image was drawn.

    Returns:
        list: One dict per element, keyed by ANNOTATION_FIELDS.
    """
    records = []
    for index, element in enumerate(scene.visible_elements()):
        x_min, y_min, x_max, y_max = element.bbox
        centre_x, centre_y = element.centre
        records.append({
            "image": image_name,
            "element_index": index,
            "label": element.label,
            "kind": element.kind,
            "centre_x": round(centre_x, 3),
            "centre_y": round(centre_y, 3),
            "bbox_x_min": round(x_min, 3),
            "bbox_y_min": round(y_min, 3),
            "bbox_x_max": round(x_max, 3),
            "bbox_y_max": round(y_max, 3),
            "bbox_width": round(element.bbox_width, 3),
            "bbox_height": round(element.bbox_height, 3),
            "radius": round(element.radius, 3),
            "colour": element.fill,
            "vertices": " ".join(
                f"{round(x, 3)},{round(y, 3)}" for x, y in element.points
            ),
        })
    return records


def write_annotations_csv(path: str, records: List[dict]) -> None:
    """Write annotation records as CSV, the format most CV tooling ingests."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=ANNOTATION_FIELDS)
        writer.writeheader()
        writer.writerows(records)


def write_annotations_json(path: str, records: List[dict], canvas_size=None) -> None:
    """Write annotation records as JSON, grouped by image.

    Args:
        path: File to write.
        records: Records from element_records().
        canvas_size: Optional (width, height) recorded once for the whole set.
    """
    grouped: dict = {}
    for record in records:
        grouped.setdefault(record["image"], []).append(
            {k: v for k, v in record.items() if k != "image"}
        )

    payload = {"images": [
        {"image": name, "elements": elements} for name, elements in grouped.items()
    ]}
    if canvas_size:
        payload["canvas"] = {"width": canvas_size[0], "height": canvas_size[1]}

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def scene_to_svg(scene) -> str:
    """Render a Scene as an SVG document.

    The paper claims SVG output, but --img-format never accepted it. Vector
    output needs the shapes themselves rather than pixels, which is exactly what
    the Scene holds.

    Args:
        scene: The Scene recorded while drawing.

    Returns:
        str: A complete SVG document.
    """
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{scene.width}" '
        f'height="{scene.height}" viewBox="0 0 {scene.width} {scene.height}">',
        f'  <rect width="{scene.width}" height="{scene.height}" '
        f'fill="{scene.background}"/>',
    ]

    for element in scene.visible_elements():
        parts.append("  " + _element_to_svg(element))

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def _format_number(value: float) -> str:
    """Trim trailing zeros so the markup stays readable."""
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _element_to_svg(element) -> str:
    """Render one element as an SVG tag."""
    label = f' data-label="{element.label}"' if element.label else ""

    if element.kind == ELLIPSE:
        cx, cy = element.centre
        rx = element.bbox_width / 2
        ry = element.bbox_height / 2
        return (
            f'<ellipse cx="{_format_number(cx)}" cy="{_format_number(cy)}" '
            f'rx="{_format_number(rx)}" ry="{_format_number(ry)}" '
            f'fill="{element.fill}"{label}/>'
        )

    if element.kind == RECTANGLE:
        x_min, y_min, x_max, y_max = element.bbox
        return (
            f'<rect x="{_format_number(x_min)}" y="{_format_number(y_min)}" '
            f'width="{_format_number(x_max - x_min)}" '
            f'height="{_format_number(y_max - y_min)}" '
            f'fill="{element.fill}"{label}/>'
        )

    if element.kind == LINE:
        (x0, y0), (x1, y1) = element.points
        return (
            f'<line x1="{_format_number(x0)}" y1="{_format_number(y0)}" '
            f'x2="{_format_number(x1)}" y2="{_format_number(y1)}" '
            f'stroke="{element.fill}" stroke-width="{_format_number(element.width)}"'
            f'{label}/>'
        )

    points = " ".join(
        f"{_format_number(x)},{_format_number(y)}" for x, y in element.points
    )
    return f'<polygon points="{points}" fill="{element.fill}"{label}/>'
