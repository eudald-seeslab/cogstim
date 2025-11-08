#!/usr/bin/env python3
"""
Summary writer for image generation statistics.

This module provides a CSV writer for recording statistics about
generated image pairs and other generation metadata.
"""

import os
import csv


class SummaryWriter:
    """
    Writer for image pair summary statistics.
    
    Records information about image pairs and writes to CSV.
    """
    
    def __init__(self, output_dir: str):
        """
        Initialize summary writer.
        
        Args:
            output_dir: Directory to write summary.csv to
        """
        self.output_dir = output_dir
        self.rows = []

    def add(self, num1, num2, area1_px, area2_px, equalized):
        """
        Add a row of statistics for an image pair.
        
        Args:
            num1: Number of dots in first array
            num2: Number of dots in second array
            area1_px: Total area of first array in pixels
            area2_px: Total area of second array in pixels
            equalized: Whether areas were equalized
        """
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
        """
        Write accumulated statistics to CSV file.
        
        Args:
            filename: Name of CSV file (default: summary.csv)
        """
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

