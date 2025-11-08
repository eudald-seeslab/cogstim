import os
import csv

from cogstim.helpers.image_utils import get_file_extension, save_image


def save_image_pair(s_np, s_points, m_np, m_points, output_dir, base_name, img_format):
    s_np.draw_points(s_points)
    m_np.draw_points(m_points)
    
    ext = get_file_extension(img_format)
    s_path = os.path.join(output_dir, f"{base_name}_s.{ext}")
    m_path = os.path.join(output_dir, f"{base_name}_m.{ext}")
    
    save_image(s_np, s_path, img_format)
    save_image(m_np, m_path, img_format)


def save_pair_with_basename(pair, output_dir, base_name, img_format):
    s_np, s_points, m_np, m_points = pair
    save_image_pair(s_np, s_points, m_np, m_points, output_dir, base_name, img_format)


def build_basename(n1: int, n2: int, rep: int, equalized: bool, version_tag: str | None = None) -> str:
    eq = "_equalized" if equalized else ""
    v_tag = f"_{version_tag}" if version_tag else ""
    return f"img_{n1}_{n2}_{rep}{eq}{v_tag}"


class SummaryWriter:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.rows = []

    def add(self, num1, num2, area1_px, area2_px, equalized):
        ratio = num1 / num2 if num2 != 0 else 0
        abs_diff_px = abs(area1_px - area2_px)
        denom = max(area1_px, area2_px, 1)
        rel_diff = abs_diff_px / denom
        self.rows.append([
            num1,
            num2,
            area1_px,
            area2_px,
            ratio,
            abs_diff_px,
            rel_diff,
            bool(equalized),
        ])

    def write_csv(self, filename: str = "summary.csv"):
        if not self.rows:
            return
        os.makedirs(self.output_dir, exist_ok=True)
        target_path = os.path.join(self.output_dir, filename)
        with open(target_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "num1",
                "num2",
                "area1_px",
                "area2_px",
                "ratio",
                "abs_diff_px",
                "rel_diff",
                "equalized",
            ])
            writer.writerows(self.rows)
        print(f"Summary written to: {target_path}")
