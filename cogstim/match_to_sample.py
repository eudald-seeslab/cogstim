import os
import argparse
from tqdm import tqdm

from cogstim.dots_core import PointLayoutError
from cogstim.config import MTS_EASY_RATIOS, MTS_HARD_RATIOS
from cogstim.mts_helpers.factory import create_numberpoints_image as _create_np_image, generate_random_points
from cogstim.mts_helpers.geometry import equalize_pair as _equalize_geom
from cogstim.mts_helpers.io import save_pair_with_basename, SummaryWriter
from cogstim.mts_helpers.planner import GenerationPlan, resolve_ratios
from cogstim.base_generator import BaseGenerator


# Default general configuration
GENERAL_CONFIG = {
    "dot_colour": "black",
    "background_colour": "white",
    "min_radius": 5,
    "max_radius": 15,
    "attempts_limit": 1000,
    "tolerance": 0.01,
    "ratios": "all",
}
DEFAULT_ATTEMPTS_LIMIT = 5000
DEFAULT_BG_COLOUR = "white"
DEFAULT_DOT_COLOUR = "black"
DEFAULT_TOLERANCE = 0.01        # 1% relative difference by default
DEFAULT_ABS_TOL = 2            # absolute area tolerance in pixels


class ImagePrinter:
    """Executes a GenerationPlan: generates/saves images and reports metrics."""

    def __init__(self, args):
        self.args = args

    def run(self, plan, recorder):
        for item in plan.tasks:
            n1 = item["n1"]
            n2 = item["n2"]
            rep = item["rep"]
            want_equalize = item["equalize"]

            base_root = f"img_{n1}_{n2}_{rep}"

            if want_equalize:
                pair, success = generate_pair(n_first=n1, n_second=n2, args=self.args,
                                              error_label="initial layout for equalization",
                                              equalize=True)
                if pair is None:
                    continue
                s_np, s_points, m_np, m_points = pair
                area1 = s_np.compute_area(s_points, "colour_1")
                area2 = m_np.compute_area(m_points, "colour_1")
                recorder.add(n1, n2, area1, area2, equalized=bool(success))

                # Save images: only save unequal pairs if equalization succeeded
                should_save = True
                if n1 != n2 and not success:
                    should_save = False
                if should_save:
                    tag = "equalized" if success else "rnd"
                    save_pair_with_basename(pair, self.args.output_dir, f"{base_root}_{tag}")
            else:
                pair, _ = generate_pair(n_first=n1, n_second=n2, args=self.args, error_label="random", equalize=False)
                if pair is None:
                    continue
                s_np, s_points, m_np, m_points = pair
                area1 = s_np.compute_area(s_points, "colour_1")
                area2 = m_np.compute_area(m_points, "colour_1")
                recorder.add(n1, n2, area1, area2, equalized=False)
                save_pair_with_basename(pair, self.args.output_dir, f"{base_root}_rnd")


def try_build_random_pair(n_first, n_second,
                          bg_colour, dot_colour,
                          min_radius, max_radius,
                          attempts_limit,
                          error_label):
    """Try to create a pair (n_first, n_second). Return tuple or None and print contextualized error.

    error_label examples: "random", "initial layout for equalization", "equal pair"
    """
    try:
        _, s_np = _create_np_image(bg_colour=bg_colour,
                                                dot_colour=dot_colour,
                                                min_radius=min_radius,
                                                max_radius=max_radius,
                                                attempts_limit=attempts_limit)
        _, m_np = _create_np_image(bg_colour=bg_colour,
                                                dot_colour=dot_colour,
                                                min_radius=min_radius,
                                                max_radius=max_radius,
                                                attempts_limit=attempts_limit)
        s_points = generate_random_points(s_np, n_first)
        m_points = generate_random_points(m_np, n_second)
        return s_np, s_points, m_np, m_points
    except PointLayoutError as e:
        print(f"Error generating {n_first},{n_second} {error_label}: {e}")
        return None


def generate_pair(n_first, n_second, args, error_label, equalize=False):
    """Create a pair with optional equalization. Returns (pair_tuple, success_flag).

    pair_tuple is (s_np, s_points, m_np, m_points) or None if creation failed.
    success_flag is True/False if equalize=True, otherwise None.
    """
    pair = try_build_random_pair(
        n_first=n_first,
        n_second=n_second,
        bg_colour=args.background_colour,
        dot_colour=args.dot_colour,
        min_radius=args.min_radius,
        max_radius=args.max_radius,
        attempts_limit=args.attempts_limit,
        error_label=error_label,
    )
    if pair is None:
        return None, None
    if not equalize:
        return pair, None
    s_np, s_points, m_np, m_points = pair
    success = _equalize_geom(
        s_np,
        s_points,
        m_np,
        m_points,
        rel_tolerance=args.tolerance,
        abs_tolerance=DEFAULT_ABS_TOL,
        attempts_limit=args.attempts_limit,
    )
    return (s_np, s_points, m_np, m_points), success


class MatchToSampleGenerator(BaseGenerator):
    """Generator for match-to-sample dot array pairs."""

    def __init__(self, config):
        super().__init__(config)
        self.train_num = config["train_num"]
        self.test_num = config["test_num"]

        # Determine ratios to use
        self.ratios = resolve_ratios(
            self.config["ratios"],
            MTS_EASY_RATIOS,
            MTS_HARD_RATIOS
        )

        self.setup_directories()

    def create_and_save(self, n1, n2, equalize, tag, phase="train"):
        """Create and save a match-to-sample pair."""
        # Create args object for generate_pair
        class Args:
            def __init__(self, config):
                self.background_colour = config.get("background_colour", DEFAULT_BG_COLOUR)
                self.dot_colour = config.get("dot_colour", DEFAULT_DOT_COLOUR)
                self.min_radius = config.get("min_radius", 5)
                self.max_radius = config.get("max_radius", 15)
                self.attempts_limit = config.get("attempts_limit", DEFAULT_ATTEMPTS_LIMIT)
                self.tolerance = config.get("tolerance", DEFAULT_TOLERANCE)
                self.output_dir = os.path.join(config["output_dir"], phase)

        args = Args(self.config)

        # Generate the pair
        base_root = f"img_{n1}_{n2}_{tag}"

        if equalize:
            pair, success = generate_pair(n_first=n1, n_second=n2, args=args,
                                          error_label="initial layout for equalization",
                                          equalize=True)
            if pair is None:
                return

            # Only save if equalization succeeded or n1 == n2
            should_save = True
            if n1 != n2 and not success:
                should_save = False
            if should_save:
                tag_suffix = "equalized" if success else "rnd"
                save_pair_with_basename(pair, args.output_dir, f"{base_root}_{tag_suffix}")
        else:
            pair, _ = generate_pair(n_first=n1, n_second=n2, args=args,
                                   error_label="random", equalize=False)
            if pair is None:
                return
            save_pair_with_basename(pair, args.output_dir, f"{base_root}_rnd")

    def generate_images(self):
        """Generate all image pairs for train and test using unified GenerationPlan."""
        for phase, num_images in [("train", self.train_num), ("test", self.test_num)]:
            # Build generation plan for this phase
            plan = GenerationPlan(
                mode="mts",
                ratios=self.ratios,
                min_point_num=self.config["min_point_num"],
                max_point_num=self.config["max_point_num"],
                num_repeats=num_images,
            ).build()
            
            tasks = plan.get_tasks()
            total_images = len(tasks)
            
            self.log_generation_info(
                f"Generating {total_images} image pairs for {phase} in '{self.config['output_dir']}/{phase}'."
            )
            
            # Execute each task in the plan
            for task in tqdm(tasks, desc=f"{phase}"):
                n = task["n1"]
                m = task["n2"]
                rep = task["rep"]
                self.create_and_save(n, m, task["equalize"], rep, phase)


def main():
    parser = argparse.ArgumentParser(description="Generate images for a Match-to-Sample task with optional area equalization.")
    parser.add_argument("--min_point_num", type=int, default=1, help="Minimum number of points per image")
    parser.add_argument("--max_point_num", type=int, default=9, help="Maximum number of points per image")
    parser.add_argument("--ratios", type=str, choices=["easy", "hard", "all"], default="all", help="Ratio set to use: easy|hard|all")
    parser.add_argument("--num_repeats", type=int, default=1, help="How many times to repeat generation per combination (to diversify images)")
    parser.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE, help="Relative tolerance for area equalization (e.g., 0.01 for 1%%)")
    parser.add_argument("--output_dir", type=str, default="mts_output", help="Output directory to save generated images")
    parser.add_argument("--min_radius", type=int, default=20, help="Minimum dot radius")
    parser.add_argument("--max_radius", type=int, default=30, help="Maximum dot radius")
    parser.add_argument("--background_colour", type=str, default=DEFAULT_BG_COLOUR, help="Background color (name or hex)")
    parser.add_argument("--dot_colour", type=str, default=DEFAULT_DOT_COLOUR, help="Dot color (name or hex)")
    parser.add_argument("--attempts_limit", type=int, default=DEFAULT_ATTEMPTS_LIMIT, help="Maximum attempts to equalize or generate a non-overlapping layout")
    parser.add_argument("--summary", action="store_true", help="Write a CSV summary with per-pair metrics in the output directory")
    args = parser.parse_args()


    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    # Plan all tasks
    planner = GenerationPlan(args.ratios, args.min_point_num, args.max_point_num, args.num_repeats).build()

    # General info
    total_conditions = len(planner.tasks) 
    print(f"Generating {total_conditions} image pairs.")

    # Execute planned tasks
    recorder = SummaryWriter(args.output_dir)
    printer = ImagePrinter(args)
    printer.run(planner, recorder)

    # Write summary if requested
    if args.summary:
        recorder.write_csv()

    print("Process completed. Images saved to:", args.output_dir)


if __name__ == "__main__":
    main()
