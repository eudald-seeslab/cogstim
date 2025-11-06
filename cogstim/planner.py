"""
Unified planning mechanism for stimulus generation across all task types.

This module provides a common interface for planning image generation tasks,
replacing the previously duplicated logic in different generators.
"""

from typing import List, Tuple, Dict, Any, Optional


class GenerationTask:
    """Represents a single generation task with all parameters needed."""
    
    def __init__(self, task_type: str, rep: int = 0, **params):
        """
        Initialize a generation task with flexible parameters.
        
        Args:
            task_type: Type of task ('ans', 'mts', 'one_colour', 'shapes', 'lines')
            rep: Repetition/iteration number
            **params: Task-specific parameters:
                - For ans/mts: n1, n2, equalize
                - For one_colour: n
                - For shapes: shape, color, surface
                - For lines: angle, num_stripes
        """
        self.task_type = task_type
        self.rep = rep
        self.params = params
        
        # For backward compatibility with dot tasks
        self.n1 = params.get('n1')
        self.n2 = params.get('n2')
        self.equalize = params.get('equalize', False)
    
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
        
        Generates 4 variants:
        - (n, m) non-equalized
        - (m, n) non-equalized (order swap)
        - (n, m) equalized
        - (m, n) equalized (order swap)
        
        Args:
            n: First point count
            m: Second point count
            rep: Repetition number
        """
        # Non-equalized orders
        self.tasks.append(GenerationTask("ans", rep, n1=n, n2=m, equalize=False))
        self.tasks.append(GenerationTask("ans", rep, n1=m, n2=n, equalize=False))
        # Equalized orders
        self.tasks.append(GenerationTask("ans", rep, n1=n, n2=m, equalize=True))
        self.tasks.append(GenerationTask("ans", rep, n1=m, n2=n, equalize=True))
    
    def expand_mts_tasks(self, n: int, m: int, rep: int) -> None:
        """
        Expand match-to-sample tasks for a given (n, m) pair.
        
        Generates 6 variants:
        - (n, m) non-equalized
        - (m, n) non-equalized (order swap)
        - (n, m) equalized
        - (m, n) equalized (order swap)
        - (n, n) equalized (equal pair)
        - (m, m) non-equalized (equal pair)
        
        Args:
            n: First point count
            m: Second point count
            rep: Repetition number
        """
        # Random orders
        self.tasks.append(GenerationTask("mts", rep, n1=n, n2=m, equalize=False))
        self.tasks.append(GenerationTask("mts", rep, n1=m, n2=n, equalize=False))
        # Equalized orders
        self.tasks.append(GenerationTask("mts", rep, n1=n, n2=m, equalize=True))
        self.tasks.append(GenerationTask("mts", rep, n1=m, n2=n, equalize=True))
        # Equal pairs
        self.tasks.append(GenerationTask("mts", rep, n1=n, n2=n, equalize=True))
        self.tasks.append(GenerationTask("mts", rep, n1=m, n2=m, equalize=False))
    
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
    
    def get_tasks_as_dicts(self) -> List[Dict[str, Any]]:
        """Get tasks as list of dictionaries (for backward compatibility)."""
        return [task.to_dict() for task in self.tasks]
    
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


def resolve_ratios(mode: str, easy_ratios: List[float], hard_ratios: List[float]) -> List[float]:
    """
    Resolve ratio mode string to actual ratio list.
    
    Args:
        mode: One of 'easy', 'hard', or 'all'
        easy_ratios: List of easy ratios
        hard_ratios: List of hard ratios
    
    Returns:
        Combined or filtered list of ratios
    
    Raises:
        ValueError: If mode is invalid
    """
    if mode == "easy":
        return list(easy_ratios)
    elif mode == "hard":
        return list(hard_ratios)
    elif mode == "all":
        return list(easy_ratios) + list(hard_ratios)
    else:
        raise ValueError(f"Invalid ratio mode: {mode}")

