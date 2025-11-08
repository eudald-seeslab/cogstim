# Recipes

Quick copy-paste commands for common research goals. Each recipe includes context and expected output structure.

## Recipe 1: Binary Shapes with Fixed Positions

**Goal:** Generate circle vs star discrimination with no positional variation (jitter disabled).

```bash
cogstim shapes --train-num 50 --test-num 20 --no-jitter --seed 1234
```

**Expected output:**
```
images/shapes/
  ├── train/
  │   ├── circle/  (50 image sets × ~100 variations each)
  │   └── star/    (50 image sets × ~100 variations each)
  └── test/
      ├── circle/  (20 image sets × ~100 variations each)
      └── star/    (20 image sets × ~100 variations each)
```

---

## Recipe 2: ANS Easy Ratios – Small Pilot Set

**Goal:** Generate a small approximate number system dataset with easy discrimination ratios. Half the images have equalized total surface (controlling for cumulative area); half use random dot sizes.

```bash
cogstim ans --ratios easy --train-num 20 --test-num 10 --seed 1234
```

**Expected output:**
```
images/ans/
  ├── train/
  │   ├── yellow/  (images where yellow dots dominate)
  │   └── blue/    (images where blue dots dominate)
  └── test/
      ├── yellow/
      └── blue/
```

**Note:** Each image set produces ~75 images covering different ratios and quantities. Filenames include `_equalized` for surface-controlled images.

**Tip**: You can specify custom ratios for precise control. For example, `--ratios 1/2,3/4` generates only 1:2 and 3:4 ratios.

---

## Recipe 3: Single-Colour Quantities (1–10) with Constant Surface

**Goal:** Generate single-colour dot arrays numbered 1–10 where total surface area is held constant across quantities.

```bash
cogstim one-colour \
  --train-num 50 --test-num 20 \
  --min-point-num 1 --max-point-num 10 \
  --dot-colour yellow \
  --seed 1234
```

**Expected output:**
```
images/one-colour/
  ├── train/
  │   └── yellow/  (50 sets × 10 quantities = 500+ images)
  └── test/
      └── yellow/  (20 sets × 10 quantities = 200+ images)
```

**Note:** Filenames encode the quantity: `img_n_k_[...].png` where `n` is the number of dots.

---

## Recipe 4: Match-to-Sample Pairs with Controlled Surface

**Goal:** Generate sample/match dot array pairs for enumeration tasks. Half equalized for surface area; half with random dot sizes. Uses sample/match naming convention.

```bash
cogstim match-to-sample \
  --ratios easy \
  --train-num 50 --test-num 20 \
  --min-point-num 1 --max-point-num 10 \
  --dot-colour yellow \
  --seed 1234
```

**Expected output:**
```
images/match_to_sample/
  ├── train/
  │   ├── img_2_3_0_equalized_s.png
  │   ├── img_2_3_0_equalized_m.png
  │   ├── img_2_3_0_s.png
  │   ├── img_2_3_0_m.png
  │   └── ... (many pairs)
  └── test/
      └── ... (similar structure)
```

**Note:** Files are named `*_s.png` (sample) and `*_m.png` (match). The pattern is `img_{n}_{m}_{k}[_equalized]_{s|m}.png` where `n` = sample dots, `m` = match dots, `k` = trial index.

---

## Recipe 5: Lines at Specific Angles (0°/45°/90°/135°)

**Goal:** Generate rotated stripe patterns for orientation discrimination experiments.

```bash
cogstim lines \
  --train-num 50 --test-num 20 \
  --angles 0 45 90 135 \
  --min-stripes 3 --max-stripes 5 \
  --seed 1234
```

**Expected output:**
```
images/lines/
  ├── train/
  │   ├── 0/    (vertical stripes)
  │   ├── 45/   (diagonal stripes)
  │   ├── 90/   (horizontal stripes)
  │   └── 135/  (opposite diagonal)
  └── test/
      ├── 0/
      ├── 45/
      ├── 90/
      └── 135/
```

---

## Recipe 6: Custom – Red Triangles vs Green Squares

**Goal:** Generate a custom two-class dataset with specific shape-colour pairings.

```bash
cogstim custom \
  --shapes triangle square \
  --colours red green \
  --train-num 50 --test-num 20 \
  --seed 1234
```

**Expected output:**
```
images/custom/
  ├── train/
  │   ├── triangle_red/
  │   ├── triangle_green/
  │   ├── square_red/
  │   └── square_green/
  └── test/
      ├── triangle_red/
      ├── triangle_green/
      ├── square_red/
      └── square_green/
```

**Note:** This produces 4 classes (all combinations of 2 shapes × 2 colours).

---

## Recipe 7: Fixation ABC with Recommended Parameters

**Goal:** Generate the recommended ABC fixation target (Thaler et al., 2013) with optimal parameters for fixation stability.

```bash
cogstim fixation \
  --types ABC \
  --background-colour black \
  --symbol-colour white \
  --img-size 512 \
  --dot-radius-px 6 \
  --disk-radius-px 128 \
  --cross-thickness-px 24 \
  --cross-arm-px 128
```

**Expected output:**
```
images/fixation/
  └── fix_ABC.png
```

**Note:** Thaler et al. (2013) recommend the ABC type (disk + cross + dot with cut-outs) for best fixational stability. This produces a single fixation image.

---

## Recipe 8: Quick Demo – Preview Any Task

**Goal:** Generate a tiny preview dataset (8 training image sets) to verify output before committing to a large generation run.

```bash
cogstim shapes --demo
```

**Expected output:**
```
images/shapes/
  └── train/
      ├── circle/  (8 image sets)
      └── star/    (8 image sets)
```

**Note:** `--demo` works with any task and is useful for quick iteration and verification.

---

## Tips for All Recipes

1. **Always use `--seed`** for reproducibility in experiments (e.g., `--seed 1234`).
2. **Start with `--demo`** to preview output structure before large runs.
3. **Adjust `--attempts-limit`** if dot placement fails (increase for dense or large dots).
4. **Check margins** when changing `--img-size` – shapes/dots may clip if sizes are too large for the canvas.
