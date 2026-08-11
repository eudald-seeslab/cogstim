import csv
import os
from tqdm import tqdm

from cogstim.helpers.dots_core import DotsCore, PointLayoutError
from cogstim.helpers.constants import MTS_EASY_RATIOS, MTS_HARD_RATIOS, MTS_DEFAULTS, IMAGE_DEFAULTS
from cogstim.helpers.mts_geometry import equalize_pair as _equalize_geom
from cogstim.helpers.planner import GenerationPlan, resolve_ratios
from cogstim.helpers.base_generator import BaseGenerator
from cogstim.helpers.image_utils import resolve_stimulus_colour


# TODO: This should be moved elsewhere
GENERAL_CONFIG = {
    **MTS_DEFAULTS,
    "ratios": "all",
    "init_size": IMAGE_DEFAULTS["init_size"],
}


MTS_TRIAL_ID_PADDING = 5


def build_basename(trial_id: int, role: str, n_dots: int, equalized: bool, version_tag: str | None = None) -> str:
    """
    Build a basename for a single MTS image (sample or match).
    Each file is self-described: trial id, random/equalized, role (a=match, b=sample), dot count.
    Pairs are linked by trial_id; sorting by filename orders by trial then role (a before b).
    Format: mts_{trial_id:05d}_{r|e}_{a|b}_{n_dots}[_version].png

    Args:
        trial_id: Zero-based trial index (pairs share this id).
        role: "a" (match) or "b" (sample).
        n_dots: Number of dots in this image.
        equalized: Whether this pair used area equalization ("e"); otherwise "r" (random).
        version_tag: Optional version tag to append.

    Returns:
        Basename string like "mts_00000_r_a_5" or "mts_00000_e_b_3_v1".
    """
    eq_char = "e" if equalized else "r"
    v_tag = f"_{version_tag}" if version_tag else ""
    return f"mts_{trial_id:0{MTS_TRIAL_ID_PADDING}d}_{eq_char}_{role}_{n_dots}{v_tag}"


def save_image_pair(generator, s_np, s_points, m_np, m_points, trial_id, n1, n2, equalized, *subdirs, version_tag=None):
    """
    Save a pair of images (sample and match) using a generator's save method.
    Sample is role "b", match is role "a" so filenames sort with match then sample per trial.
    """
    s_np.draw_points(s_points)
    m_np.draw_points(m_points)

    s_basename = build_basename(trial_id, "b", n1, equalized, version_tag)
    m_basename = build_basename(trial_id, "a", n2, equalized, version_tag)

    generator.save_image(s_np, s_basename, *subdirs)
    generator.save_image(m_np, m_basename, *subdirs)




class MatchToSampleGenerator(BaseGenerator):
    """Generator for match-to-sample dot array pairs."""

    # Each planned task writes a sample and a match image.
    images_per_task = 2


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
        dot_colour = resolve_stimulus_colour(
            self.config.get("dot_colour"),
            self.config["background_colour"],
            MTS_DEFAULTS["dot_colour"],
        )
        
        # Create sample image
        s_np = DotsCore(
            init_size=init_size,
            colour_1=dot_colour,
            bg_colour=self.config["background_colour"],
            min_point_radius=self.config["min_point_radius"],
            max_point_radius=self.config["max_point_radius"],
            attempts_limit=self.config["attempts_limit"]
        )
        s_points = s_np.design_n_points(n1, "colour_1")
        
        # Create match image
        m_np = DotsCore(
            init_size=init_size,
            colour_1=dot_colour,
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
    
    def save_image_pair(self, pair, trial_id, n1, n2, equalized, phase="train"):
        """Save a pair of images with trial-scoped basenames."""
        s_np, s_points, m_np, m_points = pair
        save_image_pair(
            self, s_np, s_points, m_np, m_points,
            trial_id, n1, n2, equalized, phase,
            version_tag=self.config.get("version_tag"),
        )

    def create_and_save(self, trial_id, n1, n2, equalize, phase="train"):
        """Create and save a pair of images, retrying unlucky layouts.

        Equalizing a pair can fail for a particular random draw: growing the
        smaller set's radii may push a dot off the canvas or into a neighbour.
        That is a property of the layout, not of the requested dot counts, so a
        fresh layout usually succeeds. Previously a single failure silently
        dropped the pair.

        Returns:
            bool: True if the pair was written to disk.
        """
        for _ in range(self.config["attempts_limit"]):
            try:
                pair = self.create_image_pair(n1, n2, equalize)
            except PointLayoutError:
                # Could not even place the dots; a new draw may do better.
                continue
            if pair is not None:
                self.save_image_pair(pair, trial_id, n1, n2, equalize, phase)
                return True
        return False

    def get_subdirectories(self):
        return [("train",), ("test",)]

    def write_failed_pairs(self, failures):
        """Record pairs that could not be generated, for inspection and retry.

        The file is written with the same columns that ``--tasks-csv`` reads, so
        the missing pairs can be regenerated directly with:

            cogstim match-to-sample --tasks-csv <output_dir>/failed_pairs.csv

        Args:
            failures: list of (phase, trial_id, n1, n2, equalized) tuples.

        Returns:
            str: path to the file written.
        """
        path = os.path.join(self.output_dir, "failed_pairs.csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["sample", "match", "equalized", "phase", "trial_id"])
            for phase, trial_id, n1, n2, equalized in failures:
                writer.writerow([n1, n2, str(bool(equalized)).upper(), phase, trial_id])
        return path
    
    def build_plan(self, phase, num_sets):
        """Eight tasks per (n1, n2) pair, balanced 50/50 match against non-match.

        Each task writes two images, a sample and a match, so images_per_task
        is 2 for this generator.
        """
        tasks_csv = self.config.get("tasks_csv")
        tasks_copies = self.config.get("tasks_copies", 1)

        plan = GenerationPlan(
            task_type="mts",
            min_point_num=self.config["min_point_num"],
            max_point_num=self.config["max_point_num"],
            num_repeats=num_sets,
            ratios=self.ratios
        )
        if tasks_csv:
            copies = max(1, num_sets) * tasks_copies
            plan.build_from_mts_csv(tasks_csv, num_copies=copies)
        else:
            plan.build()
        return plan

    def generate_images(self):
        """Generate all image pairs for train and test using unified planner or CSV."""
        total_pairs = 0
        failures = []

        for phase, num_images in self.iter_phases():
            if num_images <= 0:
                continue
            plan = self.build_plan(phase, num_images)

            self.log_generation_info(f"Generating {len(plan)} image pairs for {phase}...")

            for trial_id, task in enumerate(tqdm(plan.tasks, desc=f"{phase}")):
                n = task.params.get("n1")
                m = task.params.get("n2")
                equalize = task.params.get("equalize", False)
                if self.create_and_save(trial_id, n, m, equalize, phase):
                    total_pairs += 1
                else:
                    failures.append((phase, trial_id, n, m, equalize))

            self.write_summary_if_enabled(plan, phase)

        if failures:
            path = self.write_failed_pairs(failures)
            self._logger.warning(
                f"{len(failures)} of {total_pairs + len(failures)} pairs could not be "
                f"generated and are missing from the output. Their parameters were "
                f"written to '{path}'; regenerate them with "
                f"--tasks-csv '{path}'."
            )

        self.failed_pairs = failures
        return total_pairs
