import os
from tqdm import tqdm
import logging

from cogstim.helpers.dots_core import DotsCore, PointLayoutError
from cogstim.helpers.constants import COLOUR_MAP, ANS_EASY_RATIOS, ANS_HARD_RATIOS, DOT_DEFAULTS, IMAGE_DEFAULTS
from cogstim.helpers.base_generator import BaseGenerator
from cogstim.helpers.planner import GenerationPlan, resolve_ratios

logging.basicConfig(level=logging.INFO)


GENERAL_CONFIG = {
    "colour_1": "yellow",
    "colour_2": "blue",
    "attempts_limit": DOT_DEFAULTS["attempts_limit"],
    "background_colour": "black",
    "min_point_radius": DOT_DEFAULTS["min_point_radius"],
    "max_point_radius": DOT_DEFAULTS["max_point_radius"],
}


class TerminalPointLayoutError(ValueError):
    pass


class DotsANSGenerator(BaseGenerator):
    def __init__(self, config):
        super().__init__(config)
        self.train_num = config["train_num"]
        self.test_num = config["test_num"]
        
        # Resolve ratios using unified planner
        ratios_mode = self.config["ratios"]
        if isinstance(ratios_mode, str):
            self.ratios = resolve_ratios(ratios_mode, ANS_EASY_RATIOS, ANS_HARD_RATIOS)
        else:
            # Support direct ratio lists
            self.ratios = ratios_mode
        
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
        # Map configured colours to drawer colours. In one-colour mode, only pass colour_1.
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
        
        point_array = number_points.design_n_points(n1, "colour_1")
        point_array = number_points.design_n_points(n2, "colour_2", point_array=point_array)
        
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
        """Get positions using unified planner (kept for backward compatibility)."""
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
        """Generate images using unified planning mechanism."""
        task_type = "one_colour" if self.config["ONE_COLOUR"] else "ans"
        
        for phase, num_images in [("train", self.train_num), ("test", self.test_num)]:
            # Build generation plan
            plan = GenerationPlan(
                task_type=task_type,
                min_point_num=self.config["min_point_num"],
                max_point_num=self.config["max_point_num"],
                num_repeats=num_images,
                ratios=self.ratios
            ).build()
            
            self.log_generation_info(
                f"Generating {len(plan)} images for {phase} in '{self.output_dir}/{phase}'."
            )
            
            # Execute plan
            for task in tqdm(plan.tasks, desc=f"{phase}"):
                # Handle different task types
                if task.task_type == "one_colour":
                    n1 = task.params.get('n')
                    n2 = 0
                    equalized = False
                else:  # ans (two-colour)
                    n1 = task.n1
                    n2 = task.n2 if task.n2 is not None else 0
                    equalized = task.equalize
                
                rep = task.rep
                
                # Create and save image
                self.create_and_save(n1, n2, equalized=equalized, phase=phase, tag=rep)
            
            # Write summary CSV if enabled
            if self.config.get("summary", False):
                phase_output_dir = os.path.join(self.output_dir, phase)
                plan.write_summary_csv(phase_output_dir)
