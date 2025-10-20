from typing import List, Tuple

from cogstim.config import MTS_EASY_RATIOS, MTS_HARD_RATIOS


class GenerationPlan:
    def __init__(self, ratios: list | str, min_point_num: int, max_point_num: int, num_repeats: int):
        if isinstance(ratios, (list, tuple)):
            self.ratios = list(ratios)
        else:
            self.ratios = resolve_mts_ratios(ratios, easy_ratios=MTS_EASY_RATIOS, hard_ratios=MTS_HARD_RATIOS)
        self.min_point_num = min_point_num
        self.max_point_num = max_point_num
        self.num_repeats = num_repeats
        self.tasks = []


    def expand_tasks(self, n: int, m: int, rep: int) -> None:
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
        positions = self.compute_positions()
        for rep in range(self.num_repeats):
            for (n, m) in positions:
                self.expand_tasks(n, m, rep)
        return self

    def compute_positions(self) -> List[Tuple[int, int]]:
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


def resolve_mts_ratios(mode: str, easy_ratios: list, hard_ratios: list) -> list:
    if mode == "easy":
        return list(easy_ratios)
    elif mode == "hard":
        return list(hard_ratios)
    elif mode == "all":
        return list(easy_ratios) + list(hard_ratios)
    else:
        raise ValueError(f"Invalid ratio mode: {mode}")
