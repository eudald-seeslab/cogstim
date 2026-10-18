# Recipes

Quick copy-paste commands for common research goals. Each recipe includes context and expected output structure.

## Recipe 1: Binary Shapes with Fixed Positions

**Goal:** Generate circle vs star discrimination with no positional variation (jitter disabled).

```bash
cogstim shapes --train-num 50 --test-num 20 --no-jitter --seed 1234
```

**Expected output:** 70 sets = **14 000 images**, at 200 images per set.
```
images/shapes/
  ├── train/
  │   ├── circle/  (5000 images)
  │   └── star/    (5000 images)
  └── test/
      ├── circle/  (2000 images)
      └── star/    (2000 images)
```

> **Warning:** `--no-jitter` fixes the position, and rotation is off by default,
> so shape size is the only thing that varies. Surface areas are swept in steps
> of 100, but the radius they imply is rounded to whole pixels, so neighbouring
> steps render identically: only about **24 of those 5000 circles are distinct**,
> each repeated roughly 200 times. CogStim warns you when this happens.
>
> Use `--no-jitter` only when you genuinely want repeated identical stimuli. For
> varied fixed-position stimuli, add `--random-rotation`, or widen
> `--min-surface`/`--max-surface`. Leaving jitter on (the default) gives 4994
> distinct images out of 5000.

---

## Recipe 2: ANS Easy Ratios – Small Pilot Set

**Goal:** Generate a small approximate number system dataset with easy discrimination ratios. Half the images have equal total surface for the two colours (controlling for cumulative area); half use random dot sizes.

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

**Note:** Each image set produces ~75 images covering different ratios and quantities. Filenames include `_equal` for images whose two colours cover the same surface.

**Tip**: You can specify custom ratios for precise control. For example, `--ratios 1/2,3/4` generates only 1:2 and 3:4 ratios.

---

## Recipe 3: Single-Colour Quantities (1–10) with Constant Surface

**Goal:** Generate single-colour dot arrays numbered 1–10 where total surface area is held constant across quantities.

```bash
cogstim one-colour \
  --train-num 50 --test-num 20 \
  --min-dot-num 1 --max-dot-num 10 \
  --dot-colour-1 yellow \
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

**Goal:** Generate sample/match dot array pairs for enumeration tasks. Half with equal total surface; half with random dot sizes. Uses sample/match naming convention.

```bash
cogstim match-to-sample \
  --ratios easy \
  --train-num 50 --test-num 20 \
  --min-dot-num 1 --max-dot-num 10 \
  --dot-colour-1 yellow \
  --seed 1234
```

**Expected output:**
```
images/match_to_sample/
  ├── train/
  │   ├── mts_00000_e_a_3.png
  │   ├── mts_00000_e_b_2.png
  │   ├── mts_00001_r_a_5.png
  │   ├── mts_00001_r_b_4.png
  │   └── ... (many pairs)
  └── test/
      └── ... (similar structure)
```

**Note:** Each file is named `mts_{trial_id:05d}_{r|e|i}_{a|b}_{n_dots}[_version].png`; `a` = match, `b` = sample; `r` = random, `e` = equal surface, `i` = inverse surface.

---

## Recipe 5: Lines at Specific Angles (0°/45°/90°/135°)

**Goal:** Generate rotated stripe patterns for orientation discrimination experiments.

```bash
cogstim lines \
  --train-num 50 --test-num 20 \
  --angles 0 45 90 135 \
  --min-stripe-num 3 --max-stripe-num 5 \
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
  --shape-colours red green \
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

## Recipe 9: A Set in Which No Visual Cue Predicts Number

**Goal:** Generate ANS arrays in which neither the total surface nor the area the dots extend over tells a participant which colour has more dots, following Gebuis and Reynvoet (2011), and export the visual properties to check it.

```bash
cogstim ans \
  --min-dot-num 4 --max-dot-num 10 \
  --ratios 1/2,2/3,3/4,4/5 \
  --min-dot-radius-px 8 --max-dot-radius-px 12 \
  --surface random equal inverse \
  --hull random equal inverse \
  --visual-properties \
  --train-num 5 --seed 1234
```

**Expected output:**
```
images/ans/
  ├── train/
  │   ├── yellow/  (one image per pair, colour order, surface and hull condition)
  │   └── blue/
  ├── visual_properties.csv
  └── visual_property_pairs.csv
```

**Note:** Each dot-count pair appears once per combination of the three surface and the three hull conditions, so over the set the colour with more dots covers more surface, the same surface or less surface in a third of the images each, and likewise for the area it extends over. The small dots leave room for the inverse conditions; with the default 20–30 px dots the plan is refused for the wider ratios. To confirm that no cue predicts number, regress `numerical_distance` on each `_diff` column of `visual_property_pairs.csv`, as Gebuis and Reynvoet did for their own stimuli.

---

## Recipe 10: Presenting the Images in PsychoPy or jsPsych

**Goal:** Use a generated set in an experiment. CogStim writes files, not experiments; the presentation software loads them. With `--visual-properties`, `visual_property_pairs.csv` lists every image with its dot counts, which is a ready trial list.

```bash
cogstim ans --ratios easy --min-dot-num 4 --max-dot-num 10 --train-num 2 \
  --visual-properties --seed 1234 --output-dir stimuli
```

**PsychoPy** (Python): one trial per row, with the correct answer taken from the counts.

```python
import csv
from psychopy import visual, event

win = visual.Window(fullscr=True, units="pix")
with open("stimuli/visual_property_pairs.csv", newline="") as f:
    trials = list(csv.DictReader(f))

for trial in trials:
    stim = visual.ImageStim(win, image="stimuli/" + trial["image_1"])
    stim.draw()
    win.flip()
    key = event.waitKeys(keyList=["f", "j"])[0]   # f: more yellow, j: more blue
    correct = (int(trial["n_1"]) > int(trial["n_2"])) == (key == "f")
```

**jsPsych** (JavaScript): the same list as `timeline_variables`, exported once to JSON.

```javascript
const trials = [ // from visual_property_pairs.csv, e.g. with Python's csv and json modules
  {stimulus: "stimuli/train/yellow/img_5_4_0.png", n1: 5, n2: 4},
];
const procedure = {
  timeline: [{
    type: jsPsychImageKeyboardResponse,
    stimulus: jsPsych.timelineVariable("stimulus"),
    choices: ["f", "j"],
    data: {n1: jsPsych.timelineVariable("n1"), n2: jsPsych.timelineVariable("n2")},
  }],
  timeline_variables: trials,
  randomize_order: true,
};
```

**Note:** The image paths in the CSV are relative to the output directory. `cogstim_config.yaml` in the same directory records every option used, so the stimuli can be regenerated with `cogstim run stimuli/cogstim_config.yaml`.

---

## Tips for All Recipes

1. **Always use `--seed`** for reproducibility in experiments (e.g., `--seed 1234`).
2. **Start with `--demo`** to preview output structure before large runs.
3. **Adjust `--attempts-limit`** if dot placement fails (increase for dense or large dots).
4. **Check margins** when changing `--img-size` – shapes/dots may clip if sizes are too large for the canvas.
