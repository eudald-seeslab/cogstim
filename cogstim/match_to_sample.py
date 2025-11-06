import os
import argparse
from tqdm import tqdm

from cogstim.dots_core import NumberPoints, PointLayoutError
from cogstim.config import MTS_EASY_RATIOS, MTS_HARD_RATIOS
from cogstim.mts_helpers.geometry import equalize_pair as _equalize_geom
from cogstim.mts_helpers.io import save_image_pair, save_pair_with_basename, SummaryWriter, build_basename
from cogstim.planner import GenerationPlan, resolve_ratios
from cogstim.base_generator import BaseGenerator
from cogstim.defaults import MTS_DEFAULTS


# Default general configuration
GENERAL_CONFIG = {
    **MTS_DEFAULTS,
    "ratios": "all",
}


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
                          init_size, min_point_radius, 
                          max_point_radius, attempts_limit,
                          error_label):
    """Try to create a pair (n_first, n_second). Return tuple or None and print contextualized error.

    error_label examples: "random", "initial layout for equalization", "equal pair"
    """
    try:
        s_np = NumberPoints(init_size=init_size,
                           colour_1=dot_colour,
                           bg_colour=bg_colour,
                           min_point_radius=min_point_radius,
                           max_point_radius=max_point_radius,
                           attempts_limit=attempts_limit)
        m_np = NumberPoints(init_size=init_size,
                           colour_1=dot_colour,
                           bg_colour=bg_colour,
                           min_point_radius=min_point_radius,
                           max_point_radius=max_point_radius,
                           attempts_limit=attempts_limit)
        s_points = s_np.design_n_points(n_first, "colour_1")
        m_points = m_np.design_n_points(n_second, "colour_1")
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
        init_size=args.init_size,
        min_point_radius=args.min_point_radius,
        max_point_radius=args.max_point_radius,
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
        abs_tolerance=args.abs_tolerance,
        attempts_limit=args.attempts_limit,
    )
    return (s_np, s_points, m_np, m_points), success


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
        # TODO: remove this once we have a default init_size
        init_size = self.config.get("init_size", 512)  # Default to 512 if not specified
        
        # Create sample image
        s_np = NumberPoints(
            init_size=init_size,
            colour_1=self.config["dot_colour"],
            bg_colour=self.config["background_colour"],
            min_point_radius=self.config["min_point_radius"],
            max_point_radius=self.config["max_point_radius"],
            attempts_limit=self.config["attempts_limit"]
        )
        s_points = s_np.design_n_points(n1, "colour_1")
        
        # Create match image
        m_np = NumberPoints(
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


def main():
    parser = argparse.ArgumentParser(description="Generate images for a Match-to-Sample task with optional area equalization.")
    parser.add_argument("--min_point_num", type=int, default=1, help="Minimum number of points per image")
    parser.add_argument("--max_point_num", type=int, default=9, help="Maximum number of points per image")
    parser.add_argument("--ratios", type=str, choices=["easy", "hard", "all"], default="all", help="Ratio set to use: easy|hard|all")
    parser.add_argument("--num_repeats", type=int, default=1, help="How many times to repeat generation per combination (to diversify images)")
    parser.add_argument("--tolerance", type=float, default=MTS_DEFAULTS["tolerance"], help="Relative tolerance for area equalization (e.g., 0.01 for 1%%)")
    parser.add_argument("--abs_tolerance", type=int, default=MTS_DEFAULTS["abs_tolerance"], help="Absolute area tolerance in pixels")
    parser.add_argument("--output_dir", type=str, default="mts_output", help="Output directory to save generated images")
    parser.add_argument("--min_point_radius", type=int, default=20, help="Minimum dot radius")
    parser.add_argument("--max_point_radius", type=int, default=30, help="Maximum dot radius")
    parser.add_argument("--background_colour", type=str, default=MTS_DEFAULTS["background_colour"], help="Background color (name or hex)")
    parser.add_argument("--dot_colour", type=str, default=MTS_DEFAULTS["dot_colour"], help="Dot color (name or hex)")
    parser.add_argument("--attempts_limit", type=int, default=MTS_DEFAULTS["attempts_limit"], help="Maximum attempts to equalize or generate a non-overlapping layout")
    parser.add_argument("--summary", action="store_true", help="Write a CSV summary with per-pair metrics in the output directory")
    parser.add_argument("--init_size", type=int, default=512, help="Image size in pixels")
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
