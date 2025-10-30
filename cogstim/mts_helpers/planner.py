from typing import List, Tuple
from enum import Enum

from cogstim.config import MTS_EASY_RATIOS, MTS_HARD_RATIOS

class TaskExpansionMode(Enum):
    """Modes for expanding tasks from position pairs."""
    ANS_TWO_COLOUR = "ans_two_colour"  # 4 tasks: (n,m), (m,n) × equalized/non-equalized
    ANS_ONE_COLOUR = "ans_one_colour"  # 1 task: (n, 0) non-equalized
    MTS = "mts"  # 6 tasks: 4 ANS-style + 2 equal pairs (n,n) and (m,m)


class PositionComputationMode(Enum):
    """Modes for computing valid position pairs."""
    ANS = "ans"  # range(min, max), b = round(b), b <= max_p
    MTS = "mts"  # range(min, max+1), b.is_integer(), b in [min, max], b != a


class GenerationPlan:
    """
    Unified planning mechanism for generating image combinations.
    
    Supports both ANS (two-colour and one-colour) and MTS generation modes.
    """
    def __init__(
        self,
        ratios: list | str,
        min_point_num: int,
        max_point_num: int,
        num_repeats: int,
        task_mode: TaskExpansionMode = TaskExpansionMode.MTS,
        position_mode: PositionComputationMode = PositionComputationMode.MTS,
        one_colour: bool = False,
        ratio_resolver=None
    ):
        """
        Initialize a generation plan.
        
        Args:
            ratios: List of ratios or mode string ("easy", "hard", "all")
            min_point_num: Minimum number of points
            max_point_num: Maximum number of points
            num_repeats: Number of repetitions per combination
            task_mode: How to expand tasks from position pairs
            position_mode: How to compute valid position pairs
            one_colour: If True, generate one-colour tasks (single counts)
            ratio_resolver: Function to resolve ratio strings to lists
        """
        if isinstance(ratios, (list, tuple)):
            self.ratios = list(ratios)
        elif ratio_resolver:
            self.ratios = ratio_resolver(ratios)
        else:
            # Default: resolve as MTS ratios for backward compatibility
            self.ratios = resolve_mts_ratios(ratios, easy_ratios=MTS_EASY_RATIOS, hard_ratios=MTS_HARD_RATIOS)
        
        self.min_point_num = min_point_num
        self.max_point_num = max_point_num
        self.num_repeats = num_repeats
        self.task_mode = task_mode
        self.position_mode = position_mode
        self.one_colour = one_colour
        self.tasks = []

    def expand_tasks(self, n: int, m: int, rep: int) -> None:
        """Expand a position pair into tasks based on the task_mode."""
        if self.task_mode == TaskExpansionMode.ANS_ONE_COLOUR:
            # One-colour mode: single task with n1=n, n2=0, no equalization
            self.tasks.append({"n1": n, "n2": 0, "rep": rep, "equalize": False})
        
        elif self.task_mode == TaskExpansionMode.ANS_TWO_COLOUR:
            # Two-colour ANS: 4 tasks (both orders × equalized/non-equalized)
            self.tasks.append({"n1": n, "n2": m, "rep": rep, "equalize": False})
            self.tasks.append({"n1": m, "n2": n, "rep": rep, "equalize": False})
            self.tasks.append({"n1": n, "n2": m, "rep": rep, "equalize": True})
            self.tasks.append({"n1": m, "n2": n, "rep": rep, "equalize": True})
        
        elif self.task_mode == TaskExpansionMode.MTS:
            # MTS: 6 tasks (4 ANS-style + 2 equal pairs)
            # Random orders
            self.tasks.append({"n1": n, "n2": m, "rep": rep, "equalize": False})
            self.tasks.append({"n1": m, "n2": n, "rep": rep, "equalize": False})
            # Equalized orders
            self.tasks.append({"n1": n, "n2": m, "rep": rep, "equalize": True})
            self.tasks.append({"n1": m, "n2": n, "rep": rep, "equalize": True})
            # Equal pairs
            self.tasks.append({"n1": n, "n2": n, "rep": rep, "equalize": True})
            self.tasks.append({"n1": m, "n2": m, "rep": rep, "equalize": False})

    def build(self) -> "GenerationPlan":
        """Build the plan by computing positions and expanding tasks."""
        positions = self.compute_positions()
        for rep in range(self.num_repeats):
            for (n, m) in positions:
                self.expand_tasks(n, m, rep)
        return self

    def compute_positions(self) -> List[Tuple[int, int]]:
        """Compute valid position pairs based on position_mode."""
        if self.one_colour:
            # One-colour mode: return single counts as (a, 0) pairs
            return [(a, 0) for a in range(self.min_point_num, self.max_point_num + 1)]
        
        positions = []
        
        if self.position_mode == PositionComputationMode.ANS:
            # ANS-style: range(min, max) excludes max, uses round() check
            for a in range(self.min_point_num, self.max_point_num):
                for ratio in self.ratios:
                    b = a / ratio
                    # Keep if b rounds to an integer and is within range
                    if b == round(b) and b <= self.max_point_num:
                        positions.append((a, int(b)))
        
        else:  # PositionComputationMode.MTS
            # MTS-style: range(min, max+1) includes max, uses is_integer() check
            for a in range(self.min_point_num, self.max_point_num + 1):
                for ratio in self.ratios:
                    b = a / ratio
                    if b.is_integer():
                        b = int(b)
                        if b >= self.min_point_num and b <= self.max_point_num and b != a:
                            positions.append((a, b))
            
            # MTS also deduplicates by sorting pairs
            positions = sorted({tuple(sorted(pair)) for pair in positions})
        
        return positions


def resolve_mts_ratios(mode: str, easy_ratios: list, hard_ratios: list) -> list:
    """Resolve MTS ratio mode string to list of ratios."""
    if mode == "easy":
        return list(easy_ratios)
    elif mode == "hard":
        return list(hard_ratios)
    elif mode == "all":
        return list(easy_ratios) + list(hard_ratios)
    else:
        raise ValueError(f"Invalid ratio mode: {mode}")


def resolve_ans_ratios(mode: str, easy_ratios: list, hard_ratios: list) -> list:
    """Resolve ANS ratio mode string to list of ratios."""
    if mode == "easy":
        return list(easy_ratios)
    elif mode == "hard":
        return list(hard_ratios)
    elif mode == "all":
        return list(easy_ratios) + list(hard_ratios)
    else:
        raise ValueError(f"Invalid ratio mode: {mode}")
