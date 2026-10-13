import csv
import os
from tqdm import tqdm

from cogstim.helpers.dots_core import DotsCore, PointLayoutError, HullLayoutError
from cogstim.helpers import hull_control
from cogstim.helpers.constants import MTS_EASY_RATIOS, MTS_HARD_RATIOS, MTS_DEFAULTS, IMAGE_DEFAULTS
from cogstim.helpers.mts_geometry import equalize_pair as _equalize_geom, set_pair_area_ratio, expand_pair_hulls_to_ratio
from cogstim.helpers.hull_control import UnreachableConditionError
from cogstim.helpers.planner import (
    GenerationPlan,
    resolve_ratios,
    small_numerosity_warning,
    unreachable_hull_message,
)
from cogstim.helpers.base_generator import BaseGenerator
from cogstim.helpers.image_utils import resolve_stimulus_colour


# TODO: This should be moved elsewhere
GENERAL_CONFIG = {
    **MTS_DEFAULTS,
    "ratios": "all",
    "init_size": IMAGE_DEFAULTS["init_size"],
}


MTS_TRIAL_ID_PADDING = 5

# Layouts tried for a hull condition before giving the pair up as unmet.
HULL_ATTEMPTS = 200

# One letter per condition, for the filename.
CONDITION_LETTERS = {"random": "r", "equal": "e", "inverse": "i"}


def build_basename(trial_id: int, role: str, n_dots: int, surface: str, version_tag: str | None = None, hull: str = "random") -> str:
    """
    Build a basename for a single MTS image (sample or match).
    Each file is self-described: trial id, conditions, role (a=match, b=sample), dot count.
    Pairs are linked by trial_id; sorting by filename orders by trial then role (a before b).
    Format: mts_{trial_id:05d}_{r|e|i}[r|e|i]_{a|b}_{n_dots}[_version].png, the first
    letter being the surface condition and the second, present only when it is not
    random, the hull condition.

    Args:
        trial_id: Zero-based trial index (pairs share this id).
        role: "a" (match) or "b" (sample).
        n_dots: Number of dots in this image.
        surface: Surface condition of the pair: "random" (r), "equal" (e) or "inverse" (i).
        version_tag: Optional version tag to append.
        hull: Hull condition of the pair, same vocabulary; omitted when random.

    Returns:
        Basename string like "mts_00000_r_a_5", "mts_00000_e_b_3_v1" or "mts_00000_ri_a_5".
    """
    v_tag = f"_{version_tag}" if version_tag else ""
    letters = CONDITION_LETTERS[surface]
    if hull != "random":
        letters += CONDITION_LETTERS[hull]
    return f"mts_{trial_id:0{MTS_TRIAL_ID_PADDING}d}_{letters}_{role}_{n_dots}{v_tag}"


def save_image_pair(generator, s_np, s_points, m_np, m_points, trial_id, n1, n2, surface, *subdirs, version_tag=None, hull="random"):
    """
    Save a pair of images (sample and match) using a generator's save method.
    Sample is role "b", match is role "a" so filenames sort with match then sample per trial.
    """
    s_np.draw_points(s_points)
    m_np.draw_points(m_points)

    s_basename = build_basename(trial_id, "b", n1, surface, version_tag, hull=hull)
    m_basename = build_basename(trial_id, "a", n2, surface, version_tag, hull=hull)

    s_name = generator.save_image(s_np, s_basename, *subdirs)
    m_name = generator.save_image(m_np, m_basename, *subdirs)
    generator.record_property_pair((s_name, s_np.colour_1), (m_name, m_np.colour_1))




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
    
    def create_image_pair(self, n1, n2, surface="random", hull="random"):
        """Create a pair of images (sample and match).

        Args:
            n1: Dots in the sample.
            n2: Dots in the match.
            surface: One of SURFACE_CONDITIONS. 'equal' matches the total
                surface of the two images within the configured tolerances;
                'inverse' gives the image with fewer dots more surface, by the
                factor the other has more dots.
            hull: One of HULL_CONDITIONS, applied after the surface condition
                by moving the dots of each image about their centroid.

        Returns:
            (s_np, s_points, m_np, m_points), or None when the condition could
            not be met for this layout.
        """
        init_size = self.config["init_size"]
        dot_colour = resolve_stimulus_colour(
            self.config.get("dot_colour"),
            self.config["background_colour"],
            MTS_DEFAULTS["dot_colour"],
        )
        
        def canvas():
            return DotsCore(
                init_size=init_size,
                colour_1=dot_colour,
                bg_colour=self.config["background_colour"],
                min_point_radius=self.config["min_point_radius"],
                max_point_radius=self.config["max_point_radius"],
                attempts_limit=self.config["attempts_limit"]
            )

        s_np, m_np = canvas(), canvas()

        if hull in ("equal", "inverse"):
            # The image that must extend less, the one with more dots, is placed
            # in a circle sized so that the other can spread past it.
            small_is_sample = hull_control.smaller_hull_side(n1, n2) == 1
            n_small, n_large = (n1, n2) if small_is_sample else (n2, n1)
            # hull(large) / hull(small): the image with fewer dots extends
            # further by the factor the other has more dots.
            ratio = n_small / n_large if hull == "inverse" else 1.0
            full_field = s_np.hull_fields()["colour_1"]
            radius = hull_control.reduced_field_radius(
                n_large, ratio, s_np.min_point_radius, s_np.max_point_radius, full_field.radius,
            )
            small_np = s_np if small_is_sample else m_np
            small_points = small_np.design_n_points(
                n_small, "colour_1", field=(full_field.centre, radius)
            )
            large_points = (m_np if small_is_sample else s_np).design_n_points(n_large, "colour_1")
            s_points, m_points = (
                (small_points, large_points) if small_is_sample else (large_points, small_points)
            )
        elif hull == "random":
            s_points = s_np.design_n_points(n1, "colour_1")
            m_points = m_np.design_n_points(n2, "colour_1")
        else:
            raise ValueError(f"Unknown hull condition '{hull}'")
        
        if surface == "equal":
            success, s_points, m_points = _equalize_geom(
                s_np, s_points, m_np, m_points,
                rel_tolerance=self.config["tolerance"],
                abs_tolerance=self.config["abs_tolerance"],
                attempts_limit=self.config["attempts_limit"]
            )
            if not success:
                return None
        elif surface == "inverse":
            success, s_points, m_points = set_pair_area_ratio(
                s_np, s_points, m_np, m_points, n2 / n1
            )
            if not success:
                return None
        elif surface != "random":
            raise ValueError(f"Unknown surface condition '{surface}'")

        if hull != "random":
            ratio = 1.0 if hull == "equal" else n2 / n1
            success, s_points, m_points = expand_pair_hulls_to_ratio(
                s_np, s_points, m_np, m_points, ratio
            )
            if not success:
                raise HullLayoutError("This layout cannot reach the hull ratio by spreading")
        
        return (s_np, s_points, m_np, m_points)
    
    def save_image_pair(self, pair, trial_id, n1, n2, surface, phase="train", hull="random"):
        """Save a pair of images with trial-scoped basenames."""
        s_np, s_points, m_np, m_points = pair
        save_image_pair(
            self, s_np, s_points, m_np, m_points,
            trial_id, n1, n2, surface, phase,
            version_tag=self.config.get("version_tag"),
            hull=hull,
        )

    def create_and_save(self, trial_id, n1, n2, surface, phase="train", hull="random"):
        """Create and save a pair of images, retrying unlucky layouts.

        Equalizing a pair can fail for a particular random draw: growing the
        smaller set's radii may push a dot off the canvas or into a neighbour.
        That is a property of the layout, not of the requested dot counts, so a
        fresh layout usually succeeds. Previously a single failure silently
        dropped the pair.

        Returns:
            bool: True if the pair was written to disk.
        """
        hull_failures = 0
        for _ in range(self.config["attempts_limit"]):
            try:
                pair = self.create_image_pair(n1, n2, surface, hull)
            except HullLayoutError:
                # Borderline hull conditions get a bounded number of draws.
                hull_failures += 1
                if hull_failures == HULL_ATTEMPTS:
                    return False
                continue
            except PointLayoutError:
                # Could not even place the dots; a new draw may do better.
                continue
            if pair is not None:
                self.save_image_pair(pair, trial_id, n1, n2, surface, phase, hull)
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
            failures: list of (phase, trial_id, n1, n2, surface, hull) tuples.

        Returns:
            str: path to the file written.
        """
        path = os.path.join(self.output_dir, "failed_pairs.csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["sample", "match", "surface", "hull", "phase", "trial_id"])
            for phase, trial_id, n1, n2, surface, hull in failures:
                writer.writerow([n1, n2, surface, hull, phase, trial_id])
        return path
    
    def build_plan(self, phase, num_sets):
        """Four tasks per (n1, n2) pair and condition combination, balanced 50/50 match against non-match.

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
            ratios=self.ratios,
            surface_conditions=self.config.get("surface_conditions"),
            hull_conditions=self.config.get("hull_conditions"),
        )
        if tasks_csv:
            copies = max(1, num_sets) * tasks_copies
            plan.build_from_mts_csv(tasks_csv, num_copies=copies)
        else:
            plan.build()

        field_radius = self.config["init_size"] / 2 - DotsCore.boundary_width - DotsCore.point_sep
        message = unreachable_hull_message(
            plan, self.config["min_point_radius"], self.config["max_point_radius"],
            field_radius, DotsCore.point_sep,
        )
        if message:
            raise UnreachableConditionError(message)

        message = small_numerosity_warning(plan)
        if message:
            self._logger.warning(message)
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
                surface = task.params.get("surface", "random")
                hull = task.params.get("hull", "random")
                if self.create_and_save(trial_id, n, m, surface, phase, hull):
                    total_pairs += 1
                else:
                    failures.append((phase, trial_id, n, m, surface, hull))

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
