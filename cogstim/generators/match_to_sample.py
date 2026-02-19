import os
from tqdm import tqdm

from cogstim.helpers.dots_core import DotsCore
from cogstim.helpers.constants import MTS_EASY_RATIOS, MTS_HARD_RATIOS, MTS_DEFAULTS, IMAGE_DEFAULTS
from cogstim.helpers.mts_geometry import equalize_pair as _equalize_geom
from cogstim.helpers.planner import GenerationPlan, resolve_ratios
from cogstim.helpers.base_generator import BaseGenerator


# TODO: This should be moved elsewhere
GENERAL_CONFIG = {
    **MTS_DEFAULTS,
    "ratios": "all",
    "init_size": IMAGE_DEFAULTS["init_size"],
}


def save_image_pair(generator, s_np, s_points, m_np, m_points, base_name, *subdirs):
    """
    Save a pair of images (sample and match) using a generator's save method.
    
    Args:
        generator: BaseGenerator instance with save_image method
        s_np: DotsCore instance for sample image
        s_points: Point array for sample image
        m_np: DotsCore instance for match image
        m_points: Point array for match image
        base_name: Base filename without extension
        *subdirs: Subdirectories under output_dir to save to
    """
    s_np.draw_points(s_points)
    m_np.draw_points(m_points)
    
    s_filename = f"{base_name}_s"
    m_filename = f"{base_name}_m"
    
    generator.save_image(s_np, s_filename, *subdirs)
    generator.save_image(m_np, m_filename, *subdirs)


def build_basename(n1: int, n2: int, rep: int, equalized: bool, version_tag: str | None = None) -> str:
    """
    Build a standard basename for image pairs.
    
    Args:
        n1: Number of dots in first array
        n2: Number of dots in second array
        rep: Repetition/iteration number
        equalized: Whether areas are equalized
        version_tag: Optional version tag to append
    
    Returns:
        Basename string like "img_5_3_0_equalized_v1"
    """
    eq = "_equalized" if equalized else ""
    v_tag = f"_{version_tag}" if version_tag else ""
    return f"img_{n1}_{n2}_{rep}{eq}{v_tag}"


class MatchToSampleGenerator(BaseGenerator):
    """Generator for match-to-sample dot array pairs."""
    
    def __init__(self, config):
        super().__init__(config)
        
        self.ratios = resolve_ratios(
            self.config["ratios"],
            MTS_EASY_RATIOS,
            MTS_HARD_RATIOS
        )
        
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
        save_image_pair(self, s_np, s_points, m_np, m_points, base_name, phase)
    
    def create_and_save(self, n1, n2, equalize, tag, phase="train"):
        """Create and save a pair of images."""
        base_name = build_basename(n1, n2, tag, equalize, self.config.get("version_tag"))
        
        pair = self.create_image_pair(n1, n2, equalize)
        if pair is not None:
            self.save_image_pair(pair, base_name, phase)
    
    def get_subdirectories(self):
        return [("train",), ("test",)]
    
    def generate_images(self):
        """Generate all image pairs for train and test using unified planner or CSV."""
        tasks_csv = self.config.get("tasks_csv")
        tasks_copies = self.config.get("tasks_copies", 1)
        total_pairs = 0

        for phase, num_images in self.iter_phases():
            if num_images <= 0:
                continue
            plan = GenerationPlan(
                task_type="mts",
                min_point_num=self.config["min_point_num"],
                max_point_num=self.config["max_point_num"],
                num_repeats=num_images,
                ratios=self.ratios
            )
            if tasks_csv:
                copies = max(1, num_images) * tasks_copies
                plan.build_from_mts_csv(tasks_csv, num_copies=copies)
            else:
                plan.build()

            self.log_generation_info(f"Generating {len(plan)} image pairs for {phase}...")
            total_pairs += len(plan)

            for task in tqdm(plan.tasks, desc=f"{phase}"):
                n = task.params.get("n1")
                m = task.params.get("n2")
                equalize = task.params.get("equalize", False)
                rep = task.rep
                self.create_and_save(n, m, equalize, rep, phase)

            self.write_summary_if_enabled(plan, phase)

        return total_pairs
