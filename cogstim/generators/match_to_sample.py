import os
from tqdm import tqdm

from cogstim.helpers.dots_core import DotsCore
from cogstim.helpers.constants import MTS_EASY_RATIOS, MTS_HARD_RATIOS, MTS_DEFAULTS, IMAGE_DEFAULTS
from cogstim.helpers.mts_geometry import equalize_pair as _equalize_geom
from cogstim.helpers.mts_io import save_image_pair, build_basename
from cogstim.helpers.planner import GenerationPlan, resolve_ratios
from cogstim.helpers.base_generator import BaseGenerator


# Default general configuration
GENERAL_CONFIG = {
    **MTS_DEFAULTS,
    "ratios": "all",
    "init_size": IMAGE_DEFAULTS["init_size"],
}


class MatchToSampleGenerator(BaseGenerator):
    """Generator for match-to-sample dot array pairs."""
    
    def __init__(self, config):
        super().__init__(config)
        self.train_num = config["train_num"]
        self.test_num = config["test_num"]
        
        # Determine ratios to use - support both string and list
        ratios_config = self.config["ratios"]
        if isinstance(ratios_config, str):
            self.ratios = resolve_ratios(ratios_config, MTS_EASY_RATIOS, MTS_HARD_RATIOS)
        else:
            self.ratios = ratios_config
        
        self.setup_directories()
    
    def create_image_pair(self, n1, n2, equalize=False):
        """Create a pair of images (sample and match)."""
        init_size = self.config["init_size"]
        
        # Create sample image
        s_np = DotsCore(
            init_size=init_size,
            colour_1=self.config["dot_colour"],
            bg_colour=self.config["background_colour"],
            min_point_radius=self.config["min_point_radius"],
            max_point_radius=self.config["max_point_radius"],
            attempts_limit=self.config["attempts_limit"]
        )
        s_points = s_np.design_n_points(n1, "colour_1")
        
        # Create match image
        m_np = DotsCore(
            init_size=init_size,
            colour_1=self.config["dot_colour"],
            bg_colour=self.config["background_colour"],
            min_point_radius=self.config["min_point_radius"],
            max_point_radius=self.config["max_point_radius"],
            attempts_limit=self.config["attempts_limit"]
        )
        m_points = m_np.design_n_points(n2, "colour_1")
        
        # Equalize areas if requested
        if equalize:
            success, s_points, m_points = _equalize_geom(
                s_np, s_points, m_np, m_points,
                rel_tolerance=self.config["tolerance"],
                abs_tolerance=self.config["abs_tolerance"],
                attempts_limit=self.config["attempts_limit"]
            )
            if not success:
                return None
        
        return (s_np, s_points, m_np, m_points)
    
    def save_image_pair(self, pair, base_name, phase="train"):
        """Save a pair of images."""
        s_np, s_points, m_np, m_points = pair
        output_dir = os.path.join(self.config["output_dir"], phase)
        save_image_pair(s_np, s_points, m_np, m_points, output_dir, base_name)
    
    def create_and_save(self, n1, n2, equalize, tag, phase="train"):
        """Create and save a pair of images."""
        base_name = build_basename(n1, n2, tag, equalize, self.config.get("version_tag"))
        
        pair = self.create_image_pair(n1, n2, equalize)
        if pair is not None:
            self.save_image_pair(pair, base_name, phase)
    
    def get_subdirectories(self):
        return [("train",), ("test",)]
    
    def generate_images(self):
        """Generate all image pairs for train and test using unified planner."""
        for phase, num_images in [("train", self.train_num), ("test", self.test_num)]:
            plan = GenerationPlan(
                task_type="mts",
                min_point_num=self.config["min_point_num"],
                max_point_num=self.config["max_point_num"],
                num_repeats=num_images,
                ratios=self.ratios
            ).build()
            
            self.log_generation_info(f"Generating {len(plan)} image pairs for {phase}...")
            
            for task in tqdm(plan.tasks, desc=f"{phase}"):
                n = task.n1
                m = task.n2
                rep = task.rep
                self.create_and_save(n, m, task.equalize, rep, phase)
            
            # Write summary CSV if enabled
            if self.config.get("summary", False):
                phase_output_dir = os.path.join(self.config["output_dir"], phase)
                plan.write_summary_csv(phase_output_dir)
