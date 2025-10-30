import argparse
import csv
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Check MTS equalization differences from CSV produced by mts_area_report.py")
    parser.add_argument("csv_path", help="Path to mts_areas CSV (e.g., mts_train_areas.csv)")
    parser.add_argument("--rel_tol", type=float, default=1e-6, help="Relative tolerance (default: 1e-6)")
    parser.add_argument("--abs_tol", type=int, default=2, help="Absolute tolerance in pixels (default: 2)")
    parser.add_argument("--show", type=int, default=20, help="Show up to N worst mismatches (default: 20)")
    parser.add_argument("--remove_over_rel", type=float, default=None, help="If set, mark equalized pairs with rel diff > threshold for removal")
    parser.add_argument("--delete", action="store_true", help="Actually delete files flagged for removal (otherwise dry-run)")
    args = parser.parse_args()

    path = Path(args.csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")

    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                n = int(r["n"])
                m = int(r["m"])
                eq = bool(int(r["equalized"]))
                s_area = int(r["s_area_px"])
                m_area = int(r["m_area_px"])
                base = r.get("base", "")
                s_file = r.get("s_file", "")
                m_file = r.get("m_file", "")
                rows.append((base, n, m, eq, s_area, m_area, s_file, m_file))
            except Exception:
                continue

    total = len(rows)
    eq_rows = [r for r in rows if r[3]]
    neq_rows = [r for r in rows if not r[3]]

    def rel_diff(a: int, b: int) -> float:
        denom = max(a, b, 1)
        return abs(a - b) / denom

    # Equalized stats
    eq_diffs_abs = [abs(r[4] - r[5]) for r in eq_rows]
    eq_diffs_rel = [rel_diff(r[4], r[5]) for r in eq_rows]

    eq_within = [i for i, (ad, rd) in enumerate(zip(eq_diffs_abs, eq_diffs_rel)) if ad <= args.abs_tol or rd <= args.rel_tol]
    eq_mismatch = [i for i, (ad, rd) in enumerate(zip(eq_diffs_abs, eq_diffs_rel)) if not (ad <= args.abs_tol or rd <= args.rel_tol)]

    print(f"Total rows: {total}")
    print(f"Equalized rows: {len(eq_rows)}  |  Non-equalized rows: {len(neq_rows)}")
    if eq_rows:
        print("Equalized summary (abs px | rel):")
        print(f"  mean: {sum(eq_diffs_abs)/len(eq_diffs_abs):.3f} | {sum(eq_diffs_rel)/len(eq_diffs_rel):.6f}")
        print(f"  max : {max(eq_diffs_abs)} | {max(eq_diffs_rel):.6f}")
        print(f"  within tol: {len(eq_within)}/{len(eq_rows)}  ({100.0*len(eq_within)/len(eq_rows):.1f}%)")

    # Show worst mismatches
    if eq_mismatch:
        worst = sorted(eq_mismatch, key=lambda i: (eq_diffs_abs[i], eq_diffs_rel[i]), reverse=True)[: args.show]
        print(f"\nTop {len(worst)} equalized mismatches (abs px, rel, base, n, m, s_area, m_area):")
        for i in worst:
            base, n, m, _, sa, ma, *_ = eq_rows[i]
            print(f"  {eq_diffs_abs[i]}, {eq_diffs_rel[i]:.6f}, {base}, {n}, {m}, {sa}, {ma}")

    # Optional removal of out-of-tolerance equalized pairs based on relative threshold
    if args.remove_over_rel is not None:
        to_remove = [i for i, rd in enumerate(eq_diffs_rel) if rd > args.remove_over_rel]
        print(f"\nFlagged for removal (equalized, rel diff > {args.remove_over_rel}): {len(to_remove)}")
        if to_remove:
            # Show up to N examples
            sample = to_remove[: args.show]
            print("Examples to remove (rel, base):")
            for i in sample:
                print(f"  {eq_diffs_rel[i]:.6f}, {eq_rows[i][0]}")

            if args.delete:
                removed = 0
                for i in to_remove:
                    _, _, _, _, _, _, s_path, m_path = eq_rows[i]
                    s_p = Path(s_path)
                    m_p = Path(m_path)
                    if s_p.exists():
                        try:
                            s_p.unlink()
                            removed += 1
                        except Exception:
                            pass
                    if m_p.exists():
                        try:
                            m_p.unlink()
                            removed += 1
                        except Exception:
                            pass
                print(f"Deleted {removed} files from {len(to_remove)} pairs.")


if __name__ == "__main__":
    main()


