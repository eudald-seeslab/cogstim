import os
from PIL import Image
from cogstim.dots_core import NumberPoints, PointLayoutError
from tqdm import tqdm
import logging

from cogstim.helpers import COLOUR_MAP, SIZES
from cogstim.mts_helpers.planner import GenerationPlan
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

    def generate_images(self):
        """Generate train and test images using the unified GenerationPlan."""
        for phase, num_repeats in [("train", self.train_num), ("test", self.test_num)]:
            # Determine mode based on configuration
            mode = "one_colour" if self.config["ONE_COLOUR"] else "ans"
            
            # Build generation plan for this phase
            plan = GenerationPlan(
                mode=mode,
                ratios=self.config["ratios"],
                min_point_num=self.config["min_point_num"],
                max_point_num=self.config["max_point_num"],
                num_repeats=num_repeats,
                easy_ratios=ANS_EASY_RATIOS,
                hard_ratios=ANS_HARD_RATIOS,
            ).build()
            
            tasks = plan.get_tasks()
            total_images = len(tasks)
            
            self.log_generation_info(
                f"Generating {total_images} images for {phase} in '{self.output_dir}/{phase}'."
            )
            
            # Execute each task in the plan
            for task in tqdm(tasks, desc=f"{phase}"):
                self.create_and_save(
                    n1=task["n1"],
                    n2=task["n2"],
                    equalized=task["equalize"],
                    phase=phase,
                    tag=task["rep"],
                )

