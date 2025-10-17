#!/usr/bin/env python3

import os
import random
from typing import List, Tuple

from PIL import Image, ImageDraw

from cogstim.helpers import COLOUR_MAP


class FixationGenerator:
    """Generate fixation target images (A, B, C, AB, AC, BC, ABC).

    Shapes (following Thaler et al., 2013 figure conventions):
      - A: small central dot
      - B: filled disk
      - C: cross (orthogonal bars)
      - AB: disk (with optional dot; when single-colour, same as B)
      - AC: cross (with optional dot; when single-colour, same as C)
      - BC: disk with cross-shaped cut-out (background coloured cross)
      - ABC: disk with cross-shaped cut-out and a central cut-out dot

    All stimuli are rendered on a solid background. The symbol itself uses
    a single colour (as requested), while BC/ABC achieve contrast by
    overdrawing the background colour for the cut-outs.
    """

    def __init__(self, config: dict):
        self.output_dir: str = config["output_dir"]
        self.img_sets: int = config["img_sets"]
        self.types: List[str] = config["types"]
        self.size: int = config["img_size"]
        self.dot_radius: int = config["dot_radius_px"]
        self.disk_radius: int = config["disk_radius_px"]
        self.cross_thickness: int = config["cross_thickness_px"]
        self.cross_arm: int = config.get("cross_arm_px", self.size // 2)
        self.jitter_px: int = config.get("jitter_px", 0)
        self.background_colour: str = config["background_colour"]
        # Map user colour name to hex code where applicable
        symbol_colour_name = config["symbol_colour"]
        self.symbol_colour: str = COLOUR_MAP.get(symbol_colour_name, symbol_colour_name)
        self.tag: str = config.get("tag", "")

    # ----------------------------- public API ----------------------------- #

    def create_images(self) -> None:
        self._create_directories()
        for t in self.types:
            img = self._draw_symbol(t)
            tag_suffix = f"_{self.tag}" if self.tag else ""
            filename = f"fix_{t}{tag_suffix}.png"
            img.save(os.path.join(self.output_dir, filename))

    # ---------------------------- drawing utils --------------------------- #

    def _center_with_jitter(self) -> Tuple[int, int]:
        half = self.size // 2
        if self.jitter_px <= 0:
            return (half, half)
        jx = random.randint(-self.jitter_px, self.jitter_px)
        jy = random.randint(-self.jitter_px, self.jitter_px)
        return (half + jx, half + jy)

    def _blank_image(self) -> Image.Image:
        return Image.new("RGB", (self.size, self.size), color=self.background_colour)

    def _draw_symbol(self, s_type: str) -> Image.Image:
        img = self._blank_image()
        draw = ImageDraw.Draw(img)
        cx, cy = self._center_with_jitter()

        # Helper lambdas
        def draw_dot(colour: str):
            r = self.dot_radius
            draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=colour)

        def draw_disk(colour: str):
            r = self.disk_radius
            draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=colour)

        def draw_cross(colour: str):
            t = self.cross_thickness
            a = self.cross_arm
            # Horizontal bar centered at (cx, cy) with half-length a
            draw.rectangle([(cx - a, cy - t // 2), (cx + a, cy + t // 2)], fill=colour)
            # Vertical bar centered at (cx, cy) with half-length a
            draw.rectangle([(cx - t // 2, cy - a), (cx + t // 2, cy + a)], fill=colour)

        # Compose according to type
        s_type = s_type.upper()
        fore = self.symbol_colour
        back = self.background_colour

        if s_type == "A":
            draw_dot(fore)
        elif s_type == "B":
            draw_disk(fore)
        elif s_type == "C":
            draw_cross(fore)
        elif s_type == "AB":
            draw_disk(fore)
            draw_dot(back)
        elif s_type == "AC":
            draw_cross(fore)
            draw_dot(back)
        elif s_type == "BC":
            draw_disk(fore)
            draw_cross(back)
        elif s_type == "ABC":
            draw_disk(fore)
            draw_cross(back)
            draw_dot(fore)
        else:
            raise ValueError(f"Unknown fixation type: {s_type}")

        return img

    # ----------------------------- filesystem ---------------------------- #

    def _create_directories(self) -> None:
        os.makedirs(self.output_dir, exist_ok=True)
