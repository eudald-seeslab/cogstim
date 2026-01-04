from typing import List, Tuple, Dict, Literal, Any

from cogstim.config import MTS_EASY_RATIOS, MTS_HARD_RATIOS


def resolve_ratios(mode: str, easy_ratios: list, hard_ratios: list) -> list:
    """Resolve ratio mode string to a list of ratios.
    
    Args:
        mode: One of "easy", "hard", or "all"
        easy_ratios: List of easy ratios
        hard_ratios: List of hard ratios
        
    Returns:
        List of ratio values
        
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


class GenerationPlan:
    """Unified planning mechanism for generating image combinations.
    
    Supports multiple generation modes:
    - "mts": Match-to-sample dot arrays (includes equal pairs)
    - "ans": ANS two-colour dot arrays (4 variants per position)
    - "one_colour": Single-colour dot arrays
    - "shapes": Shape recognition with surfaces and shape/color combinations
    - "lines": Line patterns with angles and stripe counts
    """
    
    def __init__(
        self, 
        mode: Literal["mts", "ans", "one_colour", "shapes", "lines"],
        num_repeats: int,
        # ANS/MTS-specific params
        ratios: list | str = None,
        min_point_num: int = None,
        max_point_num: int = None,
        easy_ratios: list = None,
        hard_ratios: list = None,
        # Shapes-specific params
        min_surface: int = None,
        max_surface: int = None,
        surface_step: int = 100,
        shapes: list = None,
        colours: list = None,
        task_type: str = None,
        # Lines-specific params
        angles: list = None,
        min_stripe_num: int = None,
        max_stripe_num: int = None,
    ):
        """Initialize generation plan.
        
        Args:
            mode: Generation mode - "mts", "ans", "one_colour", "shapes", or "lines"
            num_repeats: Number of repetitions per combination
            
            # ANS/MTS params:
            ratios: Either a list of ratios or a string mode ("easy", "hard", "all")
            min_point_num: Minimum number of points
            max_point_num: Maximum number of points
            easy_ratios: Easy ratios to use if ratios is a string
            hard_ratios: Hard ratios to use if ratios is a string
            
            # Shapes params:
            min_surface: Minimum surface area
            max_surface: Maximum surface area
            surface_step: Step size for surface iterations
            shapes: List of shape names
            colours: List of colour names
            task_type: Shape task type ("two_shapes", "two_colors", "custom")
            
            # Lines params:
            angles: List of rotation angles
            min_stripe_num: Minimum number of stripes
            max_stripe_num: Maximum number of stripes
        """
        self.mode = mode
        self.num_repeats = num_repeats
        self.tasks = []
        
        # ANS/MTS initialization
        if mode in ["mts", "ans", "one_colour"]:
            self.min_point_num = min_point_num
            self.max_point_num = max_point_num
            
            # For one_colour mode, ratios are not needed
            if mode == "one_colour":
                self.ratios = []
            else:
                # For ans and mts modes, ratios are required
                if easy_ratios is None:
                    easy_ratios = MTS_EASY_RATIOS
                if hard_ratios is None:
                    hard_ratios = MTS_HARD_RATIOS
                    
                if isinstance(ratios, (list, tuple)):
                    self.ratios = list(ratios)
                else:
                    self.ratios = resolve_ratios(ratios, easy_ratios=easy_ratios, hard_ratios=hard_ratios)
        
        # Shapes initialization
        elif mode == "shapes":
            self.min_surface = min_surface
            self.max_surface = max_surface
            self.surface_step = surface_step
            self.shapes = shapes or []
            self.colours = colours or []
            self.task_type = task_type
        
        # Lines initialization
        elif mode == "lines":
            self.angles = angles or []
            self.min_stripe_num = min_stripe_num
            self.max_stripe_num = max_stripe_num

    def expand_tasks_mts(self, n: int, m: int, rep: int) -> None:
        """Expand tasks for match-to-sample mode (includes equal pairs)."""
        self.tasks.append({"n1": n, "n2": m, "rep": rep, "equalize": False})
        self.tasks.append({"n1": m, "n2": n, "rep": rep, "equalize": False})
        self.tasks.append({"n1": n, "n2": m, "rep": rep, "equalize": True})
        self.tasks.append({"n1": m, "n2": n, "rep": rep, "equalize": True})
        self.tasks.append({"n1": n, "n2": n, "rep": rep, "equalize": True})
        self.tasks.append({"n1": m, "n2": m, "rep": rep, "equalize": False})

    def expand_tasks_ans(self, n: int, m: int, rep: int) -> None:
        """Expand tasks for ANS mode (no equal pairs, 4 variants per position)."""
        self.tasks.append({"n1": n, "n2": m, "rep": rep, "equalize": False})
        self.tasks.append({"n1": m, "n2": n, "rep": rep, "equalize": False})
        self.tasks.append({"n1": n, "n2": m, "rep": rep, "equalize": True})
        self.tasks.append({"n1": m, "n2": n, "rep": rep, "equalize": True})

    def expand_tasks_one_colour(self, n: int, rep: int) -> None:
        """Expand tasks for one-colour mode (single count, no equalization)."""
        self.tasks.append({"n1": n, "n2": 0, "rep": rep, "equalize": False})

    def expand_tasks_shapes(self, surface: int, shape: str, colour: str, rep: int) -> None:
        """Expand tasks for shapes mode."""
        self.tasks.append({
            "surface": surface,
            "shape": shape,
            "colour": colour,
            "rep": rep
        })

    def expand_tasks_lines(self, angle: int, num_stripes: int, rep: int) -> None:
        """Expand tasks for lines mode."""
        self.tasks.append({
            "angle": angle,
            "num_stripes": num_stripes,
            "rep": rep
        })

    def build(self) -> "GenerationPlan":
        """Build the task list based on the configured mode."""
        if self.mode == "one_colour":
            for rep in range(self.num_repeats):
                for a in range(self.min_point_num, self.max_point_num + 1):
                    self.expand_tasks_one_colour(a, rep)
        
        elif self.mode in ["ans", "mts"]:
            positions = self.compute_positions()
            for rep in range(self.num_repeats):
                for (n, m) in positions:
                    if self.mode == "ans":
                        self.expand_tasks_ans(n, m, rep)
                    else:  # mts
                        self.expand_tasks_mts(n, m, rep)
        
        elif self.mode == "shapes":
            combos = self._get_shape_colour_combinations()
            
            for rep in range(self.num_repeats):
                for surface in range(self.min_surface, self.max_surface, self.surface_step):
                    for shape, colour in combos:
                        self.expand_tasks_shapes(surface, shape, colour, rep)
        
        elif self.mode == "lines":
            for rep in range(self.num_repeats):
                for angle in self.angles:
                    for num_stripes in range(self.min_stripe_num, self.max_stripe_num + 1):
                        self.expand_tasks_lines(angle, num_stripes, rep)
        
        return self

    def _get_shape_colour_combinations(self) -> List[Tuple[str, str]]:
        """Get shape-colour combinations based on task type."""
        combos = []
        
        if self.task_type == "two_shapes":
            for shape in self.shapes:
                combos.append((shape, "yellow"))
        
        elif self.task_type == "two_colors":
            for colour in self.colours:
                combos.append(("circle", colour))
        
        else:  # custom
            for shape in self.shapes:
                for colour in self.colours:
                    combos.append((shape, colour))
        
        return combos

    def compute_positions(self) -> List[Tuple[int, int]]:
        """Compute valid (n, m) pairs based on ratios and point range."""
        positions = []
        for a in range(self.min_point_num, self.max_point_num + 1):
            for ratio in self.ratios:
                b = a / ratio
                if b.is_integer():
                    b = int(b)
                    if b >= self.min_point_num and b <= self.max_point_num and b != a:
                        positions.append((a, b))
        positions = sorted({tuple(sorted(pair)) for pair in positions})
        return positions
    
    def get_tasks(self) -> List[Dict[str, Any]]:
        """Return the list of generation tasks."""
        return self.tasks
