import os
from tqdm import tqdm
import logging

from cogstim.helpers.dots_core import DotsCore, PointLayoutError
from cogstim.helpers.constants import COLOUR_MAP, ANS_EASY_RATIOS, ANS_HARD_RATIOS, DOT_DEFAULTS, IMAGE_DEFAULTS
from cogstim.helpers.base_generator import BaseGenerator
from cogstim.helpers.image_utils import resolve_stimulus_colour
from cogstim.helpers.planner import GenerationPlan, resolve_ratios, small_numerosity_warning

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
        self.dot_colours = self._resolve_dot_colours()
        
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

    def _resolve_dot_colours(self):
        """Hex codes of the dot colours, visible against the background.

        Returns:
            tuple: (colour_1, colour_2); colour_2 is None in one-colour mode.
        """
        background = self.config["background_colour"]
        colour_1 = resolve_stimulus_colour(
            self.config.get("colour_1"), background, DOT_DEFAULTS["dot_colour"]
        )
        colour_2 = None
        if not self.config["ONE_COLOUR"]:
            colour_2 = resolve_stimulus_colour(
                self.config.get("colour_2"), background, "blue"
            )
        return colour_1, colour_2

    def create_image(self, n1, n2, surface):
        """Place and draw n1 dots of colour 1 and n2 of colour 2.

        Args:
            n1: Dots of colour 1.
            n2: Dots of colour 2; 0 in one-colour mode.
            surface: One of SURFACE_CONDITIONS. 'random' leaves the drawn radii
                as they are, 'equal' matches the total surface of the two
                colours, and 'inverse' makes the colour with fewer dots cover
                more surface, by the factor the other has more dots.
        """
        colour_1, colour_2 = self.dot_colours

        number_points = DotsCore(
            init_size=IMAGE_DEFAULTS["init_size"],
            colour_1=colour_1,
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

        if not self.config["ONE_COLOUR"]:
            if surface == "equal":
                point_array = number_points.equalize_areas(point_array)
            elif surface == "inverse":
                point_array = number_points.set_area_ratio(point_array, n2 / n1)
            elif surface != "random":
                raise ValueError(f"Unknown surface condition '{surface}'")
        return number_points.draw_points(point_array)

    def create_and_save(self, n1, n2, surface, phase, tag=""):
        condition = "" if surface == "random" else f"_{surface}"
        v_tag = f"_{self.config['version_tag']}" if self.config['version_tag'] else ""
        layout = self.config.get("layout", "mixed")
        sep = "_separated" if layout == "separated" else ""
        
        filename = f"img_{n1}_{n2}_{tag}{condition}{sep}{v_tag}"

        attempts = 0
        while attempts < self.config["attempts_limit"]:
            try:
                self.create_and_save_once(filename, n1, n2, surface, phase)
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

    def create_and_save_once(self, filename, n1, n2, surface, phase):
        img = self.create_image(n1, n2, surface)
        colour = self.config["colour_1"] if n1 > n2 else self.config["colour_2"]
        
        image_name = self.save_image(img, filename, phase, colour)
        colour_1, colour_2 = self.dot_colours
        if colour_2 is not None:
            self.record_property_pair((image_name, colour_1), (image_name, colour_2))

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

    def build_plan(self, phase, num_sets):
        """Both colour orders of each (n1, n2) pair, once per surface condition.

        With --tasks-csv the pairs come from the file instead of from the ratio
        sweep, and each set is one copy of that distribution.
        """
        task_type = "one_colour" if self.config["ONE_COLOUR"] else "ans"
        tasks_csv = self.config.get("tasks_csv")
        tasks_copies = self.config.get("tasks_copies", 1)

        plan = GenerationPlan(
            task_type=task_type,
            min_point_num=self.config["min_point_num"],
            max_point_num=self.config["max_point_num"],
            num_repeats=num_sets,
            ratios=self.ratios,
            surface_conditions=self.config.get("surface_conditions"),
        )
        if tasks_csv:
            copies = max(1, num_sets) * tasks_copies
            plan.build_from_ans_csv(tasks_csv, num_copies=copies)
        else:
            plan.build()

        message = small_numerosity_warning(plan)
        if message:
            self._logger.warning(message)
        return plan

    def generate_images(self):
        """Generate images using unified planning mechanism or CSV."""
        tasks_csv = self.config.get("tasks_csv")

        for phase, num_images in self.iter_phases():
            if tasks_csv and num_images <= 0:
                continue
            plan = self.build_plan(phase, num_images)

            self.log_generation_info(
                f"Generating {len(plan)} images for {phase} in '{self.output_dir}/{phase}'."
            )
            
            for task in tqdm(plan.tasks, desc=f"{phase}"):
                if task.task_type == "one_colour":
                    n1 = task.params.get('n')
                    n2 = 0
                    surface = "random"
                else:
                    n1 = task.params.get('n1')
                    n2 = task.params.get('n2', 0)
                    surface = task.params.get('surface', "random")
                
                rep = task.rep
                
                self.create_and_save(n1, n2, surface=surface, phase=phase, tag=rep)
            
            self.write_summary_if_enabled(plan, phase)
