import os
from PIL import Image
from cogstim.dots_core import NumberPoints, PointLayoutError
from tqdm import tqdm
import logging

from cogstim.helpers import COLOUR_MAP, SIZES
from cogstim.config import ANS_EASY_RATIOS, ANS_HARD_RATIOS
from cogstim.base_generator import BaseGenerator

logging.basicConfig(level=logging.INFO)


GENERAL_CONFIG = {
    "colour_1": "yellow",
    "colour_2": "blue",
    "attempts_limit": 2000,
    "background_colour": "black",
    "min_point_radius": SIZES["min_point_radius"],
    "max_point_radius": SIZES["max_point_radius"],
}


## Ratios moved to cogstim.config for reuse


class TerminalPointLayoutError(ValueError):
    pass


class PointsGenerator(BaseGenerator):
    def __init__(self, config):
        super().__init__(config)
        self.train_num = config["train_num"]
        self.test_num = config["test_num"]
        ratios = self.config["ratios"]
        match ratios:
            case "easy":
                self.ratios = ANS_EASY_RATIOS
            case "hard":
                self.ratios = ANS_HARD_RATIOS
            case "all":
                self.ratios = ANS_EASY_RATIOS + ANS_HARD_RATIOS
            case _:
                raise ValueError(f"Invalid ratio mode: {ratios}")
        self.setup_directories()

    def get_subdirectories(self):
        subdirs = []
        classes = [self.config["colour_1"]]
        if not self.config["ONE_COLOUR"]:
            classes.append(self.config["colour_2"])
        
        for phase in ["train", "test"]:
            for class_name in classes:
                subdirs.append((phase, class_name))
        
        return subdirs

    def create_image(self, n1, n2, equalized):
        img = Image.new(
            "RGB",
            (SIZES["init_size"], SIZES["init_size"]),
            color=self.config["background_colour"],
        )
        # Map configured colours to drawer colours. In one-colour mode, only pass colour_1.
        colour_2 = None if self.config["ONE_COLOUR"] else COLOUR_MAP[self.config["colour_2"]]

        number_points = NumberPoints(
            img,
            SIZES["init_size"],
            colour_1=COLOUR_MAP[self.config["colour_1"]],
            colour_2=colour_2,
            min_point_radius=self.config["min_point_radius"],
            max_point_radius=self.config["max_point_radius"],
            attempts_limit=self.config["attempts_limit"],
        )
        point_array = number_points.design_n_points(n1, "colour_1")
        point_array = number_points.design_n_points(
            n2, "colour_2", point_array=point_array
        )
        if equalized and not self.config["ONE_COLOUR"]:
            point_array = number_points.equalize_areas(point_array)
        return number_points.draw_points(point_array)

    def create_and_save(self, n1, n2, equalized, phase, tag=""):
        eq = "_equalized" if equalized else ""
        v_tag = f"_{self.config['version_tag']}" if self.config.get("version_tag") else ""
        name = f"img_{n1}_{n2}_{tag}{eq}{v_tag}.png"

        attempts = 0
        while attempts < self.config["attempts_limit"]:
            try:
                self.create_and_save_once(name, n1, n2, equalized, phase)
                break
            except PointLayoutError as e:
                logging.debug(f"Failed to create image {name} because '{e}' Retrying.")
                attempts += 1

                if attempts == self.config["attempts_limit"]:
                    raise TerminalPointLayoutError(
                        f"""Failed to create image {name} after {attempts} attempts. 
                        Your points are probably too big, or there are too many. 
                        Stopping."""
                    )

    def create_and_save_once(self, name, n1, n2, equalized, phase):
        img = self.create_image(n1, n2, equalized)
        colour = self.config["colour_1"] if n1 > n2 else self.config["colour_2"]
        img.save(
            os.path.join(
                self.config["output_dir"],
                phase,
                colour,
                name,
            )
        )

    def get_positions(self):
        min_p = self.config["min_point_num"]
        max_p = self.config["max_point_num"]

        if self.config["ONE_COLOUR"]:
            # For one-colour mode, we only need a single count per image
            return [(a, 0) for a in range(min_p, max_p + 1)]

        positions = []
        # Note that we don't need the last value of 'a', since 'b' will always be greater.
        for a in range(min_p, max_p):
            # Given 'a', we need to find 'b' in the tuple (a, b) such that b/a is in the ratios list.
            for ratio in self.ratios:
                b = a / ratio

                # We keep this tuple if b is an integer and within the allowed range.
                if b == round(b) and b <= max_p:
                    positions.append((a, int(b)))

        return positions

    def generate_images(self):
        positions = self.get_positions()
        multiplier = 1 if self.config["ONE_COLOUR"] else 4
        
        for phase, num_images in [("train", self.train_num), ("test", self.test_num)]:
            total_images = num_images * len(positions) * multiplier
            self.log_generation_info(
                f"Generating {total_images} images for {phase}: {num_images} sets x {len(positions)} combinations x {multiplier} variants in '{self.output_dir}/{phase}'."
            )
            for i in tqdm(range(num_images), desc=f"{phase}"):
                for pair in positions:
                    if self.config["ONE_COLOUR"]:
                        self.create_and_save(pair[0], 0, equalized=False, phase=phase, tag=i)
                    else:
                        self.create_and_save(pair[0], pair[1], equalized=False, phase=phase, tag=i)
                        self.create_and_save(pair[1], pair[0], equalized=False, phase=phase, tag=i)
                        self.create_and_save(pair[0], pair[1], equalized=True, phase=phase, tag=i)
                        self.create_and_save(pair[1], pair[0], equalized=True, phase=phase, tag=i)
