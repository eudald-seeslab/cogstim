import os
import logging
import numpy as np
from PIL import Image, ImageDraw
from tqdm import tqdm

from cogstim.base_generator import BaseGenerator
from cogstim.mts_helpers.planner import GenerationPlan


class StripePatternGenerator(BaseGenerator):
    """Generates images with rotated stripe patterns."""

    def __init__(self, config):
        super().__init__(config)
        self.min_thickness = config["min_thickness"]
        self.max_thickness = config["max_thickness"]
        self.min_spacing = config["min_spacing"]
        self.min_stripe_num = config["min_stripe_num"]
        self.max_stripe_num = config["max_stripe_num"]
        self.size = config["img_size"]
        self.dir_path = config["output_dir"]
        self.angles = config["angles"]
        self.max_attempts = config["max_attempts"]
        self.train_num = config["train_num"]
        self.test_num = config["test_num"]
        self.tag = config["tag"]
        self.background_colour = config["background_colour"]
        # Calculate circumscribed size for rotation
        self.c_size = int(self.size / 2 * np.sqrt(2)) * 2

    def create_images(self):
        """Generate the complete set of images using unified GenerationPlan."""
        self.setup_directories()

        for phase, num_images in [("train", self.train_num), ("test", self.test_num)]:
            # Build generation plan for this phase
            plan = GenerationPlan(
                mode="lines",
                angles=self.angles,
                min_stripe_num=self.min_stripe_num,
                max_stripe_num=self.max_stripe_num,
                num_repeats=num_images,
            ).build()

            tasks = plan.get_tasks()
            total_images = len(tasks)

            self.log_generation_info(
                f"Generating {total_images} images for {phase} in '{self.dir_path}/{phase}'."
            )

            # Execute each task in the plan
            for task in tqdm(tasks, desc=f"{phase}"):
                angle = task["angle"]
                num_stripes = task["num_stripes"]
                rep = task["rep"]

                try:
                    img = self.create_rotated_stripes(num_stripes, angle)
                    tag_suffix = f"_{self.tag}" if self.tag else ""
                    filename = f"img_{num_stripes}_{rep}{tag_suffix}.png"
                    img.save(os.path.join(self.dir_path, phase, str(angle), filename))
                except Exception as e:
                    logging.error(
                        f"Failed to generate image: angle={angle}, stripes={num_stripes}, rep={rep}"
                    )
                    logging.error(str(e))
                    raise

    def create_rotated_stripes(self, num_stripes, angle):
        """Create an image with the specified number of stripes at the given angle."""
        img = Image.new("RGB", (self.c_size, self.c_size), color=self.background_colour)
        draw = ImageDraw.Draw(img)

        # Generate random stripe thicknesses
        stripe_thickness = np.random.randint(
            self.min_thickness, self.max_thickness, num_stripes
        )

        # Calculate valid range for stripe positions
        min_start_point = (self.c_size - self.size) // 2 * np.cos(angle * np.pi / 180)
        max_start_point = (
                self.c_size - min_start_point - self.min_thickness - self.min_spacing
        )

        # Generate non-overlapping stripe positions
        starting_positions = self._generate_valid_positions(
            num_stripes, min_start_point, max_start_point, stripe_thickness
        )

        # Draw the stripes
        for i in range(num_stripes):
            upper_left = (starting_positions[i], 0)
            lower_right = (
                starting_positions[i] + stripe_thickness[i],
                self.c_size,
            )
            draw.rectangle([upper_left, lower_right], fill="white")

        # Rotate and crop
        rotated_img = img.rotate(angle)
        crop_box = (
            (self.c_size - self.size) // 2,
            (self.c_size - self.size) // 2,
            (self.c_size + self.size) // 2,
            (self.c_size + self.size) // 2,
        )
        return rotated_img.crop(crop_box)

    def _generate_valid_positions(self, num_stripes, min_start, max_start, thicknesses):
        """Generate non-overlapping positions for stripes."""
        attempts = 0
        while attempts < self.max_attempts:
            positions = np.random.randint(min_start, max_start, num_stripes)
            if not self._check_overlaps(positions, thicknesses):
                return positions
            attempts += 1

        raise ValueError(
            f"Failed to generate non-overlapping positions after {self.max_attempts} attempts"
        )

    def _check_overlaps(self, starting_positions, stripe_thickness):
        """Check if any stripes overlap."""
        for i in range(len(starting_positions)):
            for j in range(i + 1, len(starting_positions)):
                if (
                        starting_positions[i]
                        < starting_positions[j] + stripe_thickness[j] + self.min_spacing
                        and starting_positions[i] + stripe_thickness[i] + self.min_spacing
                        > starting_positions[j]
                ):
                    return True
        return False

    def get_subdirectories(self):
        subdirs = []
        for phase in ["train", "test"]:
            for angle in self.angles:
                subdirs.append((phase, str(angle)))
        return subdirs

