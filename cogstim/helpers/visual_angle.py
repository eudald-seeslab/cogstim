#!/usr/bin/env python3
"""Sizes in degrees of visual angle, given how the stimuli will be viewed.

Psychophysics reports sizes as the angle they subtend at the eye, which is
what the retina sees; Gebuis & Reynvoet (2011), for instance, give their dot
diameters as 0.11 to 0.79 degrees at 57 cm. A pixel is only an angle once the
viewing distance and the display's pixel density are known, so CogStim keeps
pixels as its unit and converts at the edges: options given in degrees are
turned into pixels before anything is drawn, and exports can report degrees
alongside pixels.

A length of theta degrees centred on the line of sight spans
2 * distance * tan(theta / 2) on the screen. Areas are converted with the size
of one degree squared, which is exact only for small angles; at the sizes a
stimulus has, the difference from the exact solid angle is well below the
rasterisation error of the dots.
"""

import math
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ViewingGeometry:
    """How far the viewer sits and how fine the display is.

    Attributes:
        distance_cm: Distance from the eye to the screen, in centimetres.
        pixels_per_cm: Pixel density of the display: its width in pixels
            divided by its width in centimetres.
    """

    distance_cm: float
    pixels_per_cm: float

    def __post_init__(self):
        if self.distance_cm <= 0 or self.pixels_per_cm <= 0:
            raise ValueError("Viewing distance and pixel density must be positive")

    @classmethod
    def from_config(cls, config) -> Optional["ViewingGeometry"]:
        """The geometry a configuration describes, or None when it gives none.

        Raises:
            ValueError: if only one of the two values is present.
        """
        distance = config.get("viewing_distance_cm")
        density = config.get("pixels_per_cm")
        if distance is None and density is None:
            return None
        if distance is None or density is None:
            raise ValueError(
                "Degrees of visual angle need both --viewing-distance-cm and "
                "--pixels-per-cm"
            )
        return cls(distance, density)

    def length_px(self, degrees: float) -> float:
        """Pixels spanned by a length that subtends ``degrees`` at the eye."""
        return 2 * self.distance_cm * math.tan(math.radians(degrees) / 2) * self.pixels_per_cm

    def length_deg(self, pixels: float) -> float:
        """Degrees subtended at the eye by a length of ``pixels``."""
        return math.degrees(2 * math.atan(pixels / (2 * self.distance_cm * self.pixels_per_cm)))

    def radius_px(self, degrees: float) -> float:
        """Pixels of a radius given in degrees, i.e. half a diameter of twice that."""
        return self.length_px(2 * degrees) / 2

    @property
    def px_per_deg(self) -> float:
        """Pixels spanned by one degree at the centre of gaze."""
        return self.length_px(1.0)

    def area_deg2(self, pixels_squared: float) -> float:
        """Square degrees covered by an area in square pixels (small-angle)."""
        return pixels_squared / self.px_per_deg ** 2
