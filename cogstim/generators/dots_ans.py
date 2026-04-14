import os
from tqdm import tqdm
import logging

from cogstim.helpers.dots_core import DotsCore, PointLayoutError
from cogstim.helpers.constants import COLOUR_MAP, ANS_EASY_RATIOS, ANS_HARD_RATIOS, DOT_DEFAULTS, IMAGE_DEFAULTS
from cogstim.helpers.base_generator import BaseGenerator
from cogstim.helpers.planner import GenerationPlan, resolve_ratios

logging.basicConfig(level=logging.INFO)


# TODO: This should be moved elsewhere
GENERAL_CONFIG = {
    "colour_1": "yellow",
    "colour_2": "blue",
    "attempts_limit": DOT_DEFAULTS["attempts_limit"],
    "background_colour": "black",
    "min_point_radius": DOT_DEFAULTS["min_point_radius"],
    "max_point_radius": DOT_DEFAULTS["max_point_radius"],
    "layout": DOT_DEFAULTS["layout"],
    "gap": DOT_DEFAULTS["gap"],
}


class TerminalPointLayoutError(ValueError):
    pass


class DotsANSGenerator(BaseGenerator):
    def __init__(self, config):
        super().__init__(config)
        
        self.ratios = resolve_ratios(
            self.config["ratios"], 
            ANS_EASY_RATIOS, 
            ANS_HARD_RATIOS
        )
        
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

    def _compute_separated_regions(self, init_size, boundary, gap):
        """Return (left_region, right_region) rectangles for separated layout."""
        half = init_size / 2
        left = (boundary, half - gap / 2, boundary, init_size - boundary)
        right = (half + gap / 2, init_size - boundary, boundary, init_size - boundary)
        return left, right

    def create_image(self, n1, n2, equalized):
        colour_2 = None if self.config["ONE_COLOUR"] else COLOUR_MAP[self.config["colour_2"]]

        number_points = DotsCore(
            init_size=IMAGE_DEFAULTS["init_size"],
            colour_1=COLOUR_MAP[self.config["colour_1"]],
            colour_2=colour_2,
            bg_colour=self.config["background_colour"],
            mode=IMAGE_DEFAULTS["mode"],
            min_point_radius=self.config["min_point_radius"],
            max_point_radius=self.config["max_point_radius"],
            attempts_limit=self.config["attempts_limit"]
        )

        layout = self.config.get("layout", "mixed")
        if layout == "separated" and not self.config["ONE_COLOUR"]:
            gap = self.config.get("gap", DOT_DEFAULTS["gap"])
            left_region, right_region = self._compute_separated_regions(
                IMAGE_DEFAULTS["init_size"], number_points.boundary_width, gap
            )
            point_array = number_points.design_n_points(n1, "colour_1", region=left_region)
            point_array = number_points.design_n_points(
                n2, "colour_2", point_array=point_array, region=right_region
            )
        else:
            point_array = number_points.design_n_points(n1, "colour_1")
            point_array = number_points.design_n_points(n2, "colour_2", point_array=point_array)

        if equalized and not self.config["ONE_COLOUR"]:
            point_array = number_points.equalize_areas(point_array)
        return number_points.draw_points(point_array)

    def create_and_save(self, n1, n2, equalized, phase, tag=""):
        eq = "_equalized" if equalized else ""
        v_tag = f"_{self.config['version_tag']}" if self.config['version_tag'] else ""
        layout = self.config.get("layout", "mixed")
        sep = "_separated" if layout == "separated" else ""
        
        filename = f"img_{n1}_{n2}_{tag}{eq}{sep}{v_tag}"

        attempts = 0
        while attempts < self.config["attempts_limit"]:
            try:
                self.create_and_save_once(filename, n1, n2, equalized, phase)
                break
            except PointLayoutError as e:
                logging.debug(f"Failed to create image {filename} because '{e}' Retrying.")
                attempts += 1

                if attempts == self.config["attempts_limit"]:
                    raise TerminalPointLayoutError(
                        f"""Failed to create image {filename} after {attempts} attempts. 
                        Your points are probably too big, or there are too many. 
                        Stopping."""
                    )

    def create_and_save_once(self, filename, n1, n2, equalized, phase):
        img = self.create_image(n1, n2, equalized)
        colour = self.config["colour_1"] if n1 > n2 else self.config["colour_2"]
        
        self.save_image(img, filename, phase, colour)

    def get_positions(self):
        """Get valid (n1, n2) position pairs based on configured ratios."""
        task_type = "one_colour" if self.config["ONE_COLOUR"] else "ans"
        plan = GenerationPlan(
            task_type=task_type,
            min_point_num=self.config["min_point_num"],
            max_point_num=self.config["max_point_num"],
            num_repeats=1,  # Just for computing positions
            ratios=self.ratios
        )
        return plan.compute_positions()

    def generate_images(self):
        """Generate images using unified planning mechanism or CSV."""
        task_type = "one_colour" if self.config["ONE_COLOUR"] else "ans"
        tasks_csv = self.config.get("tasks_csv")
        tasks_copies = self.config.get("tasks_copies", 1)

        for phase, num_images in self.iter_phases():
            if tasks_csv and num_images <= 0:
                continue
            plan = GenerationPlan(
                task_type=task_type,
                min_point_num=self.config["min_point_num"],
                max_point_num=self.config["max_point_num"],
                num_repeats=num_images,
                ratios=self.ratios
            )
            if tasks_csv:
                copies = max(1, num_images) * tasks_copies
                plan.build_from_ans_csv(tasks_csv, num_copies=copies)
            else:
                plan.build()
            
            self.log_generation_info(
                f"Generating {len(plan)} images for {phase} in '{self.output_dir}/{phase}'."
            )
            
            for task in tqdm(plan.tasks, desc=f"{phase}"):
                if task.task_type == "one_colour":
                    n1 = task.params.get('n')
                    n2 = 0
                    equalized = False
                else:
                    n1 = task.params.get('n1')
                    n2 = task.params.get('n2', 0)
                    equalized = task.params.get('equalize', False)
                
                rep = task.rep
                
                self.create_and_save(n1, n2, equalized=equalized, phase=phase, tag=rep)
            
            self.write_summary_if_enabled(plan, phase)
