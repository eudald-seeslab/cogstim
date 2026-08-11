"""Generator for visual mask images (dense overlapping dot patterns)."""

from random import randint, choice

from tqdm import tqdm

from cogstim.helpers.image_utils import ImageCanvas
from cogstim.helpers.constants import MASK_DEFAULTS, IMAGE_DEFAULTS, DOT_DEFAULTS, COLOUR_MAP
from cogstim.helpers.base_generator import BaseGenerator


class MaskGenerator(BaseGenerator):
    """Generate dense dot-pattern masks where dots may overlap.

    Each mask is a rectangular canvas filled with many circles of varying
    radii.  Unlike normal dot arrays, overlap is intentional — the goal is
    to produce a visually noisy pattern that hides any underlying stimulus.

    Supports two layouts:
      * ``"full"``  — dots cover the entire canvas (for MTS or ANS mixed).
      * ``"separated"`` — dots are restricted to two halves separated by a
        vertical gap, mirroring the ANS separated layout.

    When ``dot_colour_2`` is set, each dot is randomly assigned one of the
    two colours — matching the two-colour appearance of ANS stimuli.
    """

    def __init__(self, config):
        super().__init__(config)
        self.num_masks = config.get("num_masks", MASK_DEFAULTS["num_masks"])
        self.num_dots = config.get("num_dots", MASK_DEFAULTS["num_dots"])
        self.min_dot_radius = config.get("min_dot_radius", MASK_DEFAULTS["min_dot_radius"])
        self.max_dot_radius = config.get("max_dot_radius", MASK_DEFAULTS["max_dot_radius"])
        self.img_size = config.get("init_size", IMAGE_DEFAULTS["init_size"])
        self.layout = config.get("layout", "full")
        self.gap = config.get("gap", DOT_DEFAULTS["gap"])
        self.dot_colour = self._resolve_colour(
            config.get("dot_colour", MASK_DEFAULTS["dot_colour"])
        )
        raw_colour_2 = config.get("dot_colour_2")
        self.dot_colour_2 = self._resolve_colour(raw_colour_2) if raw_colour_2 else None
        self.bg_colour = self._resolve_colour(
            config.get("background_colour", MASK_DEFAULTS["background_colour"])
        )
        self.setup_directories()

    @staticmethod
    def _resolve_colour(name):
        return COLOUR_MAP.get(name, name)

    def _fill_region(self, canvas, n_dots, x_min, x_max, y_min, y_max, colour=None):
        """Draw *n_dots* random circles constrained to a rectangular region.

        When *colour* is None each dot picks randomly between the two
        configured colours (or uses the single colour if only one is set).
        """
        for _ in range(n_dots):
            r = randint(self.min_dot_radius, self.max_dot_radius)
            x = randint(int(x_min) + r, int(x_max) - r)
            y = randint(int(y_min) + r, int(y_max) - r)
            fill = colour if colour is not None else (
                choice((self.dot_colour, self.dot_colour_2))
                if self.dot_colour_2 else self.dot_colour
            )
            canvas.draw_ellipse((x - r, y - r, x + r, y + r), fill=fill)

    def _create_mask_image(self):
        """Build one mask image according to the configured layout.

        In ``separated`` mode with two colours, colour_1 fills the left
        half and colour_2 fills the right half — mirroring the ANS
        separated stimulus layout.
        """
        canvas = ImageCanvas(self.img_size, self.bg_colour)

        if self.layout == "separated":
            half = self.img_size / 2
            dots_per_half = self.num_dots // 2
            left_colour = self.dot_colour if self.dot_colour_2 else None
            right_colour = self.dot_colour_2 if self.dot_colour_2 else None
            self._fill_region(canvas, dots_per_half,
                              0, half - self.gap / 2, 0, self.img_size,
                              colour=left_colour)
            self._fill_region(canvas, self.num_dots - dots_per_half,
                              half + self.gap / 2, self.img_size, 0, self.img_size,
                              colour=right_colour)
        else:
            self._fill_region(canvas, self.num_dots,
                              0, self.img_size, 0, self.img_size)

        return canvas

    def get_subdirectories(self):
        return []

    def generate_images(self):
        """Generate *num_masks* mask images and save them."""
        version_tag = self.config.get("version_tag", "")
        v_tag = f"_{version_tag}" if version_tag else ""
        sep = "_separated" if self.layout == "separated" else ""

        self.log_generation_info(f"Generating {self.num_masks} mask images ({self.layout})...")

        for i in tqdm(range(self.num_masks), desc="masks"):
            canvas = self._create_mask_image()
            basename = f"mask_{i:04d}{sep}{v_tag}"
            self.save_image(canvas, basename)

        return self.num_masks
