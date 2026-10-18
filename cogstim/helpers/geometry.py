#!/usr/bin/env python3
"""A record of what was drawn in an image, independent of how it was rendered.

Reviewer @srvanderplas rejected the paper's computer-vision claim in JOSS review
openjournals/joss-reviews#10532 because the package produced no such record:

    "the package does not output the basic information which would support e.g.
    training a computer vision algorithm -- some sort of CSV or JSON file that
    documents exactly where the stimuli are found in the image, the size/bounding
    box of the stimuli, and so on. Similar information would be needed for eye
    tracking and other psychometric studies."

Every generator draws through ImageCanvas, so recording each primitive there
yields this description for all of them without changing any drawing logic. The
same record is what makes vector output possible: an SVG is these elements
written out instead of rasterised.
"""

import math
from dataclasses import dataclass, field
from typing import Sequence, Tuple

# Rendered element kinds.
ELLIPSE = "ellipse"
RECTANGLE = "rectangle"
POLYGON = "polygon"
LINE = "line"


@dataclass(frozen=True)
class DrawnElement:
    """One primitive drawn onto a canvas.

    Coordinates are in pixels from the top-left of the finished image, so they
    describe where a feature really is rather than where it was drawn before any
    later transform.

    Attributes:
        kind: One of ELLIPSE, RECTANGLE, POLYGON, LINE.
        points: Vertices as ((x, y), ...). Ellipses and rectangles keep the two
            opposite bounding-box corners; rotating either turns it into a
            polygon, which is why every kind is stored as points.
        fill: Fill colour as a hex code.
        label: What the element is in the stimulus, e.g. "dot" or "stripe".
        width: Stroke width, for lines.
    """

    kind: str
    points: Tuple[Tuple[float, float], ...]
    fill: str
    label: str = ""
    width: float = 0.0

    @property
    def bbox(self) -> Tuple[float, float, float, float]:
        """Axis-aligned bounding box as (x_min, y_min, x_max, y_max)."""
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        return (min(xs), min(ys), max(xs), max(ys))

    @property
    def centre(self) -> Tuple[float, float]:
        """Centre of the bounding box."""
        x0, y0, x1, y1 = self.bbox
        return ((x0 + x1) / 2, (y0 + y1) / 2)

    @property
    def bbox_width(self) -> float:
        x0, _, x1, _ = self.bbox
        return x1 - x0

    @property
    def bbox_height(self) -> float:
        _, y0, _, y1 = self.bbox
        return y1 - y0

    @property
    def radius(self) -> float:
        """Half the mean bounding-box side; the dot radius for circles."""
        return (self.bbox_width + self.bbox_height) / 4

    def transformed(self, rotation_deg: float, centre, offset) -> "DrawnElement":
        """Return this element rotated about a centre and then translated.

        The lines generator draws stripes upright on an oversized canvas, then
        rotates and crops. Applying the same transform here keeps the recorded
        coordinates pointing at where the stripes ended up.

        Args:
            rotation_deg: Rotation in degrees, matching PIL's anticlockwise sense.
            centre: (x, y) the rotation is about.
            offset: (dx, dy) subtracted after rotation, i.e. the crop origin.

        Returns:
            DrawnElement: A new element in final-image coordinates.
        """
        points = self.points
        if self.kind in (ELLIPSE, RECTANGLE) and rotation_deg % 360:
            # A rotated box is no longer axis-aligned, so expand it to corners
            # before rotating or the record would be wrong.
            (x0, y0), (x1, y1) = points
            points = ((x0, y0), (x1, y0), (x1, y1), (x0, y1))

        angle = math.radians(rotation_deg)
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        cx, cy = centre
        dx, dy = offset

        moved = []
        for x, y in points:
            tx, ty = x - cx, y - cy
            # PIL rotates anticlockwise with y pointing down.
            rx = tx * cos_a + ty * sin_a
            ry = -tx * sin_a + ty * cos_a
            moved.append((rx + cx - dx, ry + cy - dy))

        kind = self.kind
        if kind == RECTANGLE and rotation_deg % 360:
            kind = POLYGON

        return DrawnElement(
            kind=kind,
            points=tuple(moved),
            fill=self.fill,
            label=self.label,
            width=self.width,
        )


@dataclass
class Scene:
    """Everything drawn in one image, plus the canvas it was drawn on.

    Attributes:
        width: Image width in pixels.
        height: Image height in pixels.
        background: Background colour as a hex code.
        elements: The primitives drawn, in drawing order.
    """

    width: int
    height: int
    background: str
    elements: list = field(default_factory=list)

    def add(self, element: DrawnElement) -> None:
        self.elements.append(element)

    def transformed(self, rotation_deg: float, centre, offset, width, height) -> "Scene":
        """Return a copy with every element moved into a transformed image."""
        return Scene(
            width=width,
            height=height,
            background=self.background,
            elements=[
                element.transformed(rotation_deg, centre, offset)
                for element in self.elements
            ],
        )

    def visible_elements(self):
        """Elements whose bounding box overlaps the canvas at all.

        Rotating an oversized canvas and cropping leaves some elements entirely
        outside the final image; they are recorded but should not be reported as
        features of it.
        """
        visible = []
        for element in self.elements:
            x0, y0, x1, y1 = element.bbox
            if x1 >= 0 and y1 >= 0 and x0 <= self.width and y0 <= self.height:
                visible.append(element)
        return visible
