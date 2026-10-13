"""
Unified planning mechanism for stimulus generation across all task types.

This module provides a common interface for planning image generation tasks,
replacing the previously duplicated logic in different generators.
"""

import csv
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from cogstim.helpers.constants import (
    SMALL_NUMEROSITY,
    SURFACE_CONDITIONS,
    DEFAULT_SURFACE_CONDITIONS,
)


class GenerationTask:
    """Represents a single generation task with all parameters needed."""
    
    def __init__(self, task_type: str, rep: int = 0, **params):
        """
        Initialize a generation task with flexible parameters.
        
        Args:
            task_type: Type of task ('ans', 'mts', 'one_colour', 'shapes', 'lines')
            rep: Repetition/iteration number
            **params: Task-specific parameters:
                - For ans/mts: n1, n2, surface
                - For one_colour: n
                - For shapes: shape, color, surface
                - For lines: angle, num_stripes
        """
        self.task_type = task_type
        self.rep = rep
        self.params = params
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary format."""
        result = {
            "task_type": self.task_type,
            "rep": self.rep,
        }
        result.update(self.params)
        return result
    
    def __repr__(self):
        params_str = ", ".join(f"{k}={v}" for k, v in self.params.items())
        return f"Task({self.task_type}, rep={self.rep}, {params_str})"


class GenerationPlan:
    """
    Unified plan for generating stimuli across all task types.
    
    Provides a consistent interface for computing which images to generate
    based on task type, ratios, point ranges, and repetitions.
    
    Supports: ans, mts, one_colour, shapes, lines
    """
    
    def __init__(self, 
                 task_type: str,
                 min_point_num: int = 0, 
                 max_point_num: int = 0, 
                 num_repeats: int = 1,
                 ratios: Optional[List[float]] = None,
                 surface_conditions: Optional[List[str]] = None,
                 # Shapes-specific params
                 shapes: Optional[List[str]] = None,
                 colors: Optional[List[str]] = None,
                 min_surface: Optional[int] = None,
                 max_surface: Optional[int] = None,
                 surface_step: Optional[int] = None,
                 # Lines-specific params
                 angles: Optional[List[int]] = None,
                 min_stripes: Optional[int] = None,
                 max_stripes: Optional[int] = None):
        """
        Initialize a generation plan.
        
        Args:
            task_type: Type of task ('ans', 'mts', 'one_colour', 'shapes', 'lines')
            min_point_num: Minimum number of points (for ans/mts/one_colour)
            max_point_num: Maximum number of points (for ans/mts/one_colour)
            num_repeats: Number of repetitions per combination
            ratios: List of ratios for ANS/MTS tasks
            surface_conditions: Surface conditions each ANS/MTS pair is generated
                in, from SURFACE_CONDITIONS (default: random and equal)
            shapes: List of shape names (for shapes tasks)
            colors: List of color names (for shapes tasks)
            min_surface: Minimum surface area (for shapes tasks)
            max_surface: Maximum surface area (for shapes tasks)
            surface_step: Step between surface values (for shapes tasks)
            angles: List of rotation angles (for lines tasks)
            min_stripes: Minimum number of stripes (for lines tasks)
            max_stripes: Maximum number of stripes (for lines tasks)
        """
        self.task_type = task_type
        self.min_point_num = min_point_num
        self.max_point_num = max_point_num
        self.num_repeats = num_repeats
        self.ratios = ratios if ratios is not None else []
        self.surface_conditions = (
            list(surface_conditions) if surface_conditions is not None
            else list(DEFAULT_SURFACE_CONDITIONS)
        )
        # Shapes params
        self.shapes = shapes or []
        self.colors = colors or []
        self.min_surface = min_surface
        self.max_surface = max_surface
        self.surface_step = surface_step
        # Lines params
        self.angles = angles or []
        self.min_stripes = min_stripes
        self.max_stripes = max_stripes
        self.tasks: List[GenerationTask] = []
    
    def compute_positions(self) -> List[Tuple[int, int]]:
        """
        Compute valid (n1, n2) position pairs based on ratios.
        
        For ANS and MTS tasks, finds all valid pairs where n2/n1 matches a ratio.
        Returns sorted unique pairs.
        
        Returns:
            List of (n, m) tuples where n <= m
        """
        if self.task_type == "one_colour":
            # For one-colour, we just need single counts
            return [(a, 0) for a in range(self.min_point_num, self.max_point_num + 1)]
        
        positions = []
        for a in range(self.min_point_num, self.max_point_num + 1):
            for ratio in self.ratios:
                b = a / ratio
                if b.is_integer():
                    b = int(b)
                    if b >= self.min_point_num and b <= self.max_point_num and b != a:
                        positions.append((a, b))
        
        # Return sorted unique pairs (smallest first)
        return sorted({tuple(sorted(pair)) for pair in positions})
    
    def expand_ans_tasks(self, n: int, m: int, rep: int) -> None:
        """
        Expand ANS two-colour tasks for a given (n, m) pair.

        Both colour orders, (n, m) and (m, n), once per surface condition:
        four tasks with the default random and equal conditions.

        Args:
            n: First point count
            m: Second point count
            rep: Repetition number
        """
        for surface in self.surface_conditions:
            self.tasks.append(GenerationTask("ans", rep, n1=n, n2=m, surface=surface))
            self.tasks.append(GenerationTask("ans", rep, n1=m, n2=n, surface=surface))
    
    def expand_mts_tasks(self, n: int, m: int, rep: int) -> None:
        """
        Expand match-to-sample tasks for a given (n, m) pair.

        Per surface condition, four tasks balanced 50/50 match against
        non-match: (n, m) and (m, n), then (n, n) and (m, m). That is eight
        tasks with the default random and equal conditions.

        Args:
            n: First point count
            m: Second point count
            rep: Repetition number
        """
        for surface in self.surface_conditions:
            self.tasks.append(GenerationTask("mts", rep, n1=n, n2=m, surface=surface))
            self.tasks.append(GenerationTask("mts", rep, n1=m, n2=n, surface=surface))
            self.tasks.append(GenerationTask("mts", rep, n1=n, n2=n, surface=surface))
            self.tasks.append(GenerationTask("mts", rep, n1=m, n2=m, surface=surface))
    
    def expand_one_colour_tasks(self, n: int, rep: int) -> None:
        """
        Expand one-colour tasks for a given n.
        
        Args:
            n: Point count
            rep: Repetition number
        """
        self.tasks.append(GenerationTask("one_colour", rep, n=n))
    
    def expand_shapes_tasks(self, task_subtype: str, rep: int) -> None:
        """
        Expand shapes tasks for all surfaces and shape/color combinations.
        
        Args:
            task_subtype: 'two_shapes', 'two_colors', or 'custom'
            rep: Repetition number
        """
        for surface in range(self.min_surface, self.max_surface, self.surface_step):
            if task_subtype == "two_shapes":
                # Each shape in one color
                for shape in self.shapes:
                    self.tasks.append(GenerationTask("shapes", rep, 
                                                    shape=shape, color=self.colors[0], 
                                                    surface=surface, task_subtype=task_subtype))
            elif task_subtype == "two_colors":
                # One shape in each color
                for color in self.colors:
                    self.tasks.append(GenerationTask("shapes", rep,
                                                    shape=self.shapes[0], color=color,
                                                    surface=surface, task_subtype=task_subtype))
            else:  # custom
                # Each shape-color combination
                for shape in self.shapes:
                    for color in self.colors:
                        self.tasks.append(GenerationTask("shapes", rep,
                                                        shape=shape, color=color,
                                                        surface=surface, task_subtype=task_subtype))
    
    def expand_lines_tasks(self, rep: int) -> None:
        """
        Expand lines tasks for all angles and stripe counts.
        
        Args:
            rep: Repetition number
        """
        for angle in self.angles:
            for num_stripes in range(self.min_stripes, self.max_stripes + 1):
                self.tasks.append(GenerationTask("lines", rep,
                                                angle=angle, num_stripes=num_stripes))
    
    def build(self, task_subtype: Optional[str] = None) -> "GenerationPlan":
        """
        Build the complete task list based on task type and parameters.
        
        Args:
            task_subtype: For shapes tasks, one of: 'two_shapes', 'two_colors', 'custom'
        
        Returns:
            self (for method chaining)
        """
        if self.task_type in ["ans", "mts", "one_colour"]:
            # Point-based tasks use positions from ratios
            positions = self.compute_positions()
            
            for rep in range(self.num_repeats):
                if self.task_type == "one_colour":
                    for (n, _) in positions:
                        self.expand_one_colour_tasks(n, rep)
                elif self.task_type == "ans":
                    for (n, m) in positions:
                        self.expand_ans_tasks(n, m, rep)
                elif self.task_type == "mts":
                    for (n, m) in positions:
                        self.expand_mts_tasks(n, m, rep)
        
        elif self.task_type == "shapes":
            # Shapes tasks iterate over surfaces and shapes/colors
            for rep in range(self.num_repeats):
                self.expand_shapes_tasks(task_subtype or "custom", rep)
        
        elif self.task_type == "lines":
            # Lines tasks iterate over angles and stripe counts
            for rep in range(self.num_repeats):
                self.expand_lines_tasks(rep)
        
        else:
            raise ValueError(f"Unknown task_type: {self.task_type}")
        
        return self

    def build_from_mts_csv(
        self, csv_path: str | Path, num_copies: int = 1
    ) -> "GenerationPlan":
        """
        Build MTS task list from a CSV file.

        CSV must have columns: sample, match, surface.
        Each row defines one (n1, n2, surface) task.
        num_copies repeats the entire distribution that many times (rep 0..num_copies-1).

        Args:
            csv_path: Path to CSV file
            num_copies: Number of copies of the statement distribution (default 1)

        Returns:
            self (for method chaining)
        """
        if self.task_type != "mts":
            raise ValueError("build_from_mts_csv only applies to task_type='mts'")
        tasks_spec = load_mts_tasks_from_csv(csv_path)
        self.tasks = []
        task_id = 0
        for copy_idx in range(num_copies):
            for n1, n2, surface in tasks_spec:
                # Use a unique rep per emitted task so repeated CSV rows do not
                # overwrite each other when filenames include n1/n2/surface/rep.
                self.tasks.append(
                    GenerationTask(
                        "mts",
                        task_id,
                        n1=n1,
                        n2=n2,
                        surface=surface,
                        copy_idx=copy_idx,
                    )
                )
                task_id += 1
        return self

    def build_from_ans_csv(
        self, csv_path: str | Path, num_copies: int = 1
    ) -> "GenerationPlan":
        """
        Build ANS task list from a CSV file.

        CSV must have columns: n1, n2, surface.
        Each row defines one (n1, n2, surface) task.
        num_copies repeats the entire distribution that many times.

        Args:
            csv_path: Path to CSV file
            num_copies: Number of copies of the task distribution (default 1)

        Returns:
            self (for method chaining)
        """
        if self.task_type not in ("ans", "one_colour"):
            raise ValueError("build_from_ans_csv only applies to task_type 'ans' or 'one_colour'")
        tasks_spec = load_ans_tasks_from_csv(csv_path)
        self.tasks = []
        task_id = 0
        for copy_idx in range(num_copies):
            for n1, n2, surface in tasks_spec:
                task_type = self.task_type
                if task_type == "one_colour":
                    self.tasks.append(
                        GenerationTask(
                            "one_colour",
                            task_id,
                            n=n1,
                            copy_idx=copy_idx,
                        )
                    )
                else:
                    self.tasks.append(
                        GenerationTask(
                            "ans",
                            task_id,
                            n1=n1,
                            n2=n2,
                            surface=surface,
                            copy_idx=copy_idx,
                        )
                    )
                task_id += 1
        return self
    
    def small_numerosity_pairs(self) -> List[Tuple[int, int]]:
        """Dot-count pairs that compare fewer than SMALL_NUMEROSITY dots with a different count.

        Returns:
            list: Sorted (smaller, larger) pairs, each listed once.
        """
        pairs = set()
        for task in self.tasks:
            n1, n2 = task.params.get("n1"), task.params.get("n2")
            if n1 is None or n2 is None or n1 == n2:
                continue
            if min(n1, n2) < SMALL_NUMEROSITY:
                pairs.add((min(n1, n2), max(n1, n2)))
        return sorted(pairs)

    def __len__(self):
        """Return the number of tasks in the plan."""
        return len(self.tasks)
    
    def __iter__(self):
        """Iterate over tasks."""
        return iter(self.tasks)
    
    def write_summary_csv(self, output_dir: str, filename: str = "summary.csv"):
        """
        Write the generation plan as a CSV summary.
        
        This creates a summary of what will be/was generated without needing
        to recompute metrics during generation.
        
        Args:
            output_dir: Directory where the CSV will be written
            filename: Name of the CSV file
        """
        import os
        import csv
        
        if not self.tasks:
            return
        
        os.makedirs(output_dir, exist_ok=True)
        target_path = os.path.join(output_dir, filename)
        
        with open(target_path, mode="w", newline="", encoding="utf-8") as f:
            # Get all unique keys from task params
            if self.tasks:
                all_keys = set()
                for task in self.tasks:
                    all_keys.update(task.params.keys())
                
                # Create header: task_type, rep, then sorted param keys
                header = ["task_type", "rep"] + sorted(all_keys)
                writer = csv.DictWriter(f, fieldnames=header)
                writer.writeheader()
                
                # Write each task
                for task in self.tasks:
                    row = {
                        "task_type": task.task_type,
                        "rep": task.rep
                    }
                    row.update(task.params)
                    writer.writerow(row)
        
        print(f"Summary written to: {target_path}")


def _load_tasks_csv(csv_path, first_column: str, second_column: str) -> List[Tuple[int, int, str]]:
    """Read a task CSV with two count columns and an optional surface column.

    The surface column takes a value from SURFACE_CONDITIONS, in any case. A
    missing column or an empty cell means random. The column replaced the
    earlier boolean ``equalized`` column, which is refused rather than guessed
    at: its TRUE is now ``equal`` and its FALSE is ``random``.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Tasks CSV not found: {path}")

    tasks = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames and "equalized" in reader.fieldnames:
            raise ValueError(
                f"{path}: the 'equalized' column was replaced by 'surface', with "
                f"values {', '.join(SURFACE_CONDITIONS)}. Write 'equal' where it "
                "said TRUE and 'random' where it said FALSE."
            )
        for line, row in enumerate(reader, start=2):
            surface = str(row.get("surface") or "random").strip().lower()
            if surface not in SURFACE_CONDITIONS:
                raise ValueError(
                    f"{path}, line {line}: surface must be one of "
                    f"{', '.join(SURFACE_CONDITIONS)}, not '{row['surface']}'"
                )
            tasks.append((int(row[first_column]), int(row[second_column]), surface))
    return tasks


def load_mts_tasks_from_csv(csv_path: str | Path) -> List[Tuple[int, int, str]]:
    """
    Load match-to-sample task specifications from a CSV file.

    Expected columns: sample, match, surface
    - sample: number of dots in sample image
    - match: number of dots in match image
    - surface: random, equal or inverse (case-insensitive; random when absent)

    Returns:
        List of (n1, n2, surface) tuples.
    """
    return _load_tasks_csv(csv_path, "sample", "match")


def load_ans_tasks_from_csv(csv_path: str | Path) -> List[Tuple[int, int, str]]:
    """
    Load ANS task specifications from a CSV file.

    Expected columns: n1, n2, surface
    - n1: number of dots for colour_1
    - n2: number of dots for colour_2 (ignored for one_colour tasks)
    - surface: random, equal or inverse (case-insensitive; random when absent)

    Returns:
        List of (n1, n2, surface) tuples.
    """
    return _load_tasks_csv(csv_path, "n1", "n2")


def small_numerosity_warning(plan: "GenerationPlan") -> Optional[str]:
    """Explain why the plan's smallest arrays confound visual cues with number.

    Gebuis & Reynvoet (2011) found that with arrays of 1-4 dots the area
    extended alone explained 28% of the variance in numerical distance, against
    5% once every array had at least 4 dots. Below that, the hull and the
    contour of an array cannot be matched to a larger array's without making
    the dots themselves bigger, which is a confound of its own. The only
    remedies are to avoid such pairs or to check the cues after the fact.

    Args:
        plan: The GenerationPlan about to be generated.

    Returns:
        str or None: The warning to log, or None when every compared array has
        at least SMALL_NUMEROSITY dots.
    """
    pairs = plan.small_numerosity_pairs()
    if not pairs:
        return None
    examples = ", ".join(f"{a} vs {b}" for a, b in pairs[:3])
    if len(pairs) > 3:
        examples += ", ..."
    return (
        f"{len(pairs)} dot-count pairs compare fewer than {SMALL_NUMEROSITY} dots "
        f"with a larger array ({examples}). Below that count, the area an array "
        "covers and its total contour cannot be matched to a larger array's "
        "without making its dots bigger, so these cues stay confounded with "
        f"number (Gebuis & Reynvoet, 2011). Use --min-dot-num {SMALL_NUMEROSITY} "
        "to avoid such pairs, or keep them and check the cues post hoc with "
        "--visual-properties."
    )


def resolve_ratios(ratios, easy_ratios: List[float], hard_ratios: List[float]) -> List[float]:
    """
    Resolve ratios from either a string mode or a direct list.
    
    Args:
        ratios: Either a string mode ('easy', 'hard', 'all') or a list of ratios
        easy_ratios: List of easy ratios (used if ratios is a string)
        hard_ratios: List of hard ratios (used if ratios is a string)
    
    Returns:
        List of ratios
    
    Raises:
        ValueError: If string mode is invalid
    
    """
    if isinstance(ratios, str):
        if ratios == "easy":
            return list(easy_ratios)
        elif ratios == "hard":
            return list(hard_ratios)
        elif ratios == "all":
            return list(easy_ratios) + list(hard_ratios)
        else:
            raise ValueError(f"Invalid ratio mode: {ratios}")
    else:
        return list(ratios)
