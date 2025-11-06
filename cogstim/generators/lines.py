#!/usr/bin/env python3

import os
import argparse
import logging
import numpy as np
from tqdm import tqdm
from cogstim.helpers.base_generator import BaseGenerator
from cogstim.helpers.image_utils import ImageCanvas
from cogstim.helpers.planner import GenerationPlan
from cogstim.helpers.constants import IMAGE_DEFAULTS, LINE_DEFAULTS

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class LinesGenerator(BaseGenerator):
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
        self.config = config  # Store for summary check
        
        # Calculate circumscribed size for rotation
        self.c_size = int(self.size / 2 * np.sqrt(2)) * 2

    def generate_images(self):
        """Generate the complete set of images with different angles and stripe counts using unified planner."""
        self.setup_directories()

        for phase, num_images in [("train", self.train_num), ("test", self.test_num)]:
            # Build generation plan
            plan = GenerationPlan(
                task_type="lines",
                num_repeats=num_images,
                angles=self.angles,
                min_stripes=self.min_stripe_num,
                max_stripes=self.max_stripe_num
            ).build()
            
            self.log_generation_info(f"Generating {len(plan)} images for {phase}...")

            # Execute plan
            for task in tqdm(plan.tasks, desc=f"{phase}"):
                angle = task.params['angle']
                num_stripes = task.params['num_stripes']
                rep = task.rep
                
                try:
                    img = self.create_rotated_stripes(num_stripes, angle)
                    tag_suffix = f"_{self.tag}" if self.tag else ""
                    filename = f"img_{num_stripes}_{rep}{tag_suffix}.png"
                    img.save(os.path.join(self.dir_path, phase, str(angle), filename))
                except Exception as e:
                    logging.error(
                        f"Failed to generate image: angle={angle}, stripes={num_stripes}, set={rep}"
                    )
                    logging.error(str(e))
                    raise
            
            # Write summary CSV if enabled
            if self.config.get("summary", False):
                phase_output_dir = os.path.join(self.dir_path, phase)
                plan.write_summary_csv(phase_output_dir)

    def create_rotated_stripes(self, num_stripes, angle):
        """Create an image with the specified number of stripes at the given angle."""
        canvas = ImageCanvas(self.c_size, self.background_colour, mode="RGB")

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
            canvas.draw_rectangle([upper_left, lower_right], fill="white")

        # Rotate and crop
        rotated_img = canvas.img.rotate(angle)
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


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate images with rotated stripe patterns."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="../images/head_rotation_one_stripe",
        help="Directory to save generated images",
    )
    parser.add_argument(
        "--img-sets", type=int, default=50, help="Number of image sets to generate"
    )
    parser.add_argument(
        "--angles",
        type=int,
        nargs="+",
        default=[0, 45, 90, 135],
        help="List of rotation angles",
    )
    parser.add_argument(
        "--min-stripes", type=int, default=2, help="Minimum number of stripes per image"
    )
    parser.add_argument(
        "--max-stripes",
        type=int,
        default=10,
        help="Maximum number of stripes per image",
    )
    parser.add_argument(
        "--img-size", type=int, default=IMAGE_DEFAULTS["init_size"], help="Size of the output images"
    )
    parser.add_argument(
        "--tag", type=str, default="", help="Optional tag to add to image filenames"
    )
    parser.add_argument(
        "--min-thickness", type=int, default=LINE_DEFAULTS["min_thickness"], help="Minimum stripe thickness"
    )
    parser.add_argument(
        "--max-thickness", type=int, default=LINE_DEFAULTS["max_thickness"], help="Maximum stripe thickness"
    )
    parser.add_argument(
        "--min-spacing", type=int, default=LINE_DEFAULTS["min_spacing"], help="Minimum spacing between stripes"
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=10000,  # This is specific to lines, not a general default
        help="Maximum attempts to generate non-overlapping stripes",
    )

    return parser.parse_args()


def main():
    """Main entry point of the script."""
    args = parse_args()

    config = {
        "output_dir": args.output_dir,
        "img_sets": args.img_sets,
        "angles": args.angles,
        "min_stripe_num": args.min_stripes,
        "max_stripe_num": args.max_stripes,
        "img_size": args.img_size,
        "tag": args.tag,
        "min_thickness": args.min_thickness,
        "max_thickness": args.max_thickness,
        "min_spacing": args.min_spacing,
        "max_attempts": args.max_attempts,
        "background_colour": "#000000",
    }

    try:
        generator = LinesGenerator(config)
        generator.generate_images()
        logging.info("Image generation completed successfully!")
    except Exception as e:
        logging.error(f"Error during image generation: {str(e)}")
        raise


if __name__ == "__main__":
    main()
