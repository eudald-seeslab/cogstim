# User Guide

This guide provides detailed documentation for each CogStim task, including relevant options, examples, and usage patterns.

## Sets and images

`--train-num` and `--test-num` count **sets, not images**.

A set is one sweep of every condition the paradigm defines. For `shapes`, that
means every shape at every surface area in the configured range; for `ans`, every
valid (n1, n2) dot-count pair in both colour orders and every surface condition. So a
single set is many images, and asking for 10 training sets produces far more than
10 files.

This is deliberate: what an experimenter controls is the number of replications
per condition, and the conditions themselves follow from the paradigm. But it
does mean the file count is not something you can read off the command line.

**Use `--dry-run` to see exactly what you will get before generating anything:**

```bash
cogstim shapes --train-num 10 --test-num 5 --dry-run
```

```
Dry run: no images written.
  train: 10 sets x 200 images = 2000 images
  test: 5 sets x 200 images = 1000 images
  total: 3000 images in 'images/shapes'
```

Images per set for the default options of each task:

| Task | Images per set | What varies within a set |
|---|---|---|
| `shapes` | 200 | 100 surface areas × 2 shapes |
| `colours` | 200 | 100 surface areas × 2 colours |
| `custom` | 100 per shape-colour pair | 100 surface areas × every shape × every colour |
| `ans` | 112 | 28 dot-count pairs × 2 colour orders × 2 surface conditions |
| `match-to-sample` | 192 | 12 dot-count pairs × 8 variants × 2 images per pair |
| `one-colour` | 10 | one image per dot count |
| `lines` | 36 | 4 angles × 9 stripe counts |
| `fixation` | n/a | no train/test split; one image per requested type |
| `mask` | n/a | no train/test split; `--mask-num` images |

These figures change with the options you pass — a wider `--min-surface`/
`--max-surface` range or more `--angles` increases them. `--dry-run` always
reports the figure for the arguments you actually gave.

## Annotations and vector output

Every task can describe what it drew, and can write vector images instead of
pixels. Both come from the same record of the drawing, so they always agree with
the raster.

### Where each stimulus feature is

`--metadata` exports the position, size and colour of every element:

```bash
cogstim ans --train-num 10 --metadata csv
```

This writes `annotations.csv` in the output directory, one row per drawn
element:

| Column | Meaning |
|---|---|
| `image` | File the element belongs to, relative to the output directory |
| `element_index` | Position in drawing order within that image |
| `label` | What the element is: `dot`, `stripe`, `circle`, `fixation_disk`, … |
| `kind` | Primitive drawn: `ellipse`, `rectangle`, `polygon`, `line` |
| `centre_x`, `centre_y` | Centre of the bounding box, in pixels |
| `bbox_x_min` … `bbox_y_max` | Bounding box corners, in pixels |
| `bbox_width`, `bbox_height` | Bounding box size |
| `radius` | Half the mean bounding-box side; the dot radius for circles |
| `colour` | Fill colour as a hex code |
| `vertices` | Every vertex, for rotated or polygonal elements |

Use `--metadata json` for the same data grouped per image, or `--metadata both`.

This is what makes the output usable for training object detectors, and for
scoring eye-tracking data against known feature positions. Coordinates describe
the finished image: for `lines`, which draws upright and then rotates, the
recorded vertices are the rotated ones.

### Visual properties of dot arrays

Changing how many dots an array holds changes how it looks: more dots cover
more surface, spread over a larger area and have a longer total contour. Gebuis
and Reynvoet (2011) showed that no way of generating arrays removes this for
every cue at once, and argued that a generator should instead report the visual
properties of every array, so that an analysis can check afterwards whether
number or a visual cue explains a result.

`--visual-properties` does this for `ans`, `one-colour` and `match-to-sample`:

```bash
cogstim ans --train-num 10 --visual-properties
```

It writes `visual_properties.csv`, one row per dot array (an `ans` image holds
two, one per colour):

| Column | Meaning |
|---|---|
| `image` | File the array belongs to, relative to the output directory |
| `colour` | Dot colour as a hex code |
| `n_dots` | Number of dots |
| `total_surface_px` | Summed dot area, in square pixels |
| `mean_diameter_px` | Mean dot diameter, the item size |
| `total_circumference_px` | Summed dot perimeter |
| `convex_hull_px` | Area extended: the convex hull around the dots' outlines |
| `density` | Convex hull divided by total surface, as Gebuis and Reynvoet define it; larger means sparser |

For `ans` and `match-to-sample` it also writes `visual_property_pairs.csv`, one
row per pair: the two colours of an `ans` image, or the sample and match of a
`match-to-sample` trial. Each row gives `numerical_distance`, `numerical_ratio`
and `weber_fraction` (the difference over the larger count), then the `_diff`
and `_ratio` of every property above, taken as the more numerous array against
the less numerous one. A positive difference therefore means the cue grows with
number, which is what a participant could exploit. Regressing
`numerical_distance` on each `_diff` column is the check Gebuis and Reynvoet
ran on their own stimuli.

The convex hull is computed from 90 points on each dot's outline, which
understates the exact hull of the discs by less than 0.1%.

Arrays with fewer than 4 dots cannot have their hull or contour matched to a
larger array's at all; see the
[note on small numerosities](#note-on-small-numerosities).

### Vector images

```bash
cogstim shapes --train-num 10 --img-format svg
```

SVG is rendered from the recorded shapes rather than traced from pixels, so it
scales without loss. Pixel-based options such as `--min-dot-radius-px` still
describe the drawing; they set the coordinates written into the SVG.

## Sizes in degrees of visual angle

This is in beta: the conversions have been tested in code but not yet against a real
display and viewing set-up, so check what one degree comes to on your screen before
relying on them.

Psychophysics reports sizes as the angle they subtend at the eye; Gebuis and Reynvoet
(2011), for instance, give their dot diameters as 0.11 to 0.79 degrees at 57 cm. A pixel
is only an angle once the viewing distance and the display's pixel density are known, so
give both and sizes can be stated in degrees:

```bash
cogstim ans --viewing-distance-cm 57 --pixels-per-cm 38 \
  --img-size-deg 12 --min-dot-radius-deg 0.2 --max-dot-radius-deg 0.4
```

`--pixels-per-cm` is the screen's width in pixels divided by its width in centimetres.
A length of θ degrees spans 2 × distance × tan(θ/2) on the screen; a radius given in
degrees is half a diameter of twice that angle. The degree options override their pixel
counterparts and are turned into whole pixels before anything is drawn, so pixels remain
the unit inside the package and in every export; the run summary states what one degree
came to. With the geometry given, `--visual-properties` also writes `mean_diameter_deg`,
`total_surface_deg2`, `total_circumference_deg` and `convex_hull_deg2`, the areas using
the size of one degree squared, which is exact for small angles.

Degrees are accepted for the image size on every task and for the dot radii of `ans`,
`one-colour` and `match-to-sample`. The shape, stripe and fixation sizes are pixel-only
for now and would follow the same pattern.

## Table of Contents

- [Shapes – Shape Discrimination](#shapes--shape-discrimination)
- [Colours – Colour Discrimination](#colours--colour-discrimination)
- [ANS – Approximate Number System](#ans--approximate-number-system)
- [One-Colour – Single-Colour Dot Arrays](#one-colour--single-colour-dot-arrays)
- [Match-to-Sample – Dot Array Pairs](#match-to-sample--dot-array-pairs)
- [Lines – Rotated Stripe Patterns](#lines--rotated-stripe-patterns)
- [Fixation – Fixation Targets](#fixation--fixation-targets)
- [Custom – Custom Shape/Colour Combinations](#custom--custom-shapecolour-combinations)

---

## Shapes – Shape Discrimination

Generate images of different shapes in the same colour for shape recognition tasks. Use this when you need stimuli that vary only in shape (e.g., circle vs star discrimination).

### Minimal Command

```bash
cogstim shapes --train-num 10 --test-num 5
```

**What it produces:** 15 sets (10 training, 5 test) = **3000 images**, at 200 images per set (100 surface areas x 2 shapes). Circles and stars in yellow, organised into `train/circle/`, `train/star/`, `test/circle/`, and `test/star/` subdirectories.

### Relevant Options

- `--shapes` – Two shapes for discrimination (default: `circle star`)
- `--shape-colours` – Single colour for both shapes (default: `yellow`)
- `--min-surface` / `--max-surface` – Shape surface area range in pixels² (defaults: 10000–20000)
- `--no-jitter` – Disable positional jitter for fixed-position shapes
- `--seed` – Random seed for reproducibility
- `--output-dir` – Custom output directory (default: `images/shapes`)

### Advanced Tweak: Random Rotation

Add random rotation variety to shapes using `--random-rotation`:

```bash
cogstim shapes --train-num 10 --test-num 5 --random-rotation
```

This will rotate each shape by a random angle between 0° and 360°. You can control the rotation range:

```bash
cogstim shapes \
  --train-num 10 --test-num 5 \
  --random-rotation \
  --min-rotation 0 \
  --max-rotation 180
```

**Note**: Circles are obviously not affected by rotation. Rotation is useful for making the task more challenging or for training rotation-invariant models.

### Fuller Example

```bash
cogstim shapes \
  --train-num 60 --test-num 20 \
  --shapes triangle square \
  --shape-colours red \
  --seed 1234
```

This generates 80 sets of red triangles and squares with reproducible randomness.

### Shapes Options Reference

| Flag | Meaning | Default | When to use |
|------|---------|---------|-------------|
| `--shapes` | Two shapes for discrimination | `circle star` | To choose different shape pairs |
| `--shape-colours` | Single colour for shapes | `yellow` | To change shape colour |
| `--min-surface` | Minimum shape area (px²) | `10000` | To adjust shape sizes |
| `--max-surface` | Maximum shape area (px²) | `20000` | To adjust shape sizes |
| `--no-jitter` | Disable positional jitter | Off (jitter enabled) | For fixed-position shapes |
| `--seed` | Random seed | None (random) | For reproducible generation |
| `--train-num` | Number of training sets | `10` | To generate training data |
| `--test-num` | Number of test sets | `0` | To generate test data |

---

## Colours – Colour Discrimination

Generate images of the same shape in different colours for colour recognition tasks. Use this for paradigms where only colour varies (e.g., yellow vs blue circles). Based on standard colour discrimination paradigms.

### Minimal Command

```bash
cogstim colours --train-num 10 --test-num 5
```

**What it produces:** 15 sets (10 training, 5 test) = **3000 images**, at 200 images per set (100 surface areas x 2 colours). Circles in yellow and blue, organised by colour class.

### Relevant Options

- `--shape` – Shape to use for both classes (default: `circle`)
- `--shape-colours` – Two colours for discrimination (default: `yellow blue`)
  - **Note**: For more than two colours, use the [Custom task](#custom--custom-shapecolour-combinations)
- `--min-surface` / `--max-surface` – Shape surface area range in pixels² (defaults: 10000–20000)
- `--no-jitter` – Disable positional jitter for fixed-position stimuli
- `--seed` – Random seed for reproducibility

### Advanced Tweak: Fixed Position Stimuli

Use `--no-jitter` to disable positional variation, useful when position should not be a cue:

```bash
cogstim colours --train-num 10 --test-num 5 --no-jitter
```

### Fuller Example

```bash
cogstim colours \
  --train-num 60 --test-num 20 \
  --shape star \
  --shape-colours red green \
  --no-jitter \
  --seed 1234
```

This generates red and green stars in fixed positions with reproducible randomness.

### Colours Options Reference

| Flag | Meaning | Default | When to use |
|------|---------|---------|-------------|
| `--shape` | Shape for both colour classes | `circle` | To change the base shape |
| `--shape-colours` | Two colours for discrimination | `yellow blue` | To use different colour pairs |
| `--min-surface` | Minimum shape area (px²) | `10000` | To adjust shape sizes |
| `--max-surface` | Maximum shape area (px²) | `20000` | To adjust shape sizes |
| `--no-jitter` | Disable positional jitter | Off (jitter enabled) | For fixed-position stimuli |
| `--seed` | Random seed | None (random) | For reproducible generation |
| `--train-num` | Number of training sets | `10` | To generate training data |
| `--test-num` | Number of test sets | `0` | To generate test data |

---

## ANS – Approximate Number System

Generate two-colour dot arrays for approximate number system tasks. Use this for paradigms investigating numerical cognition where participants discriminate quantities by dominant colour. Based on Halberda et al. (2008).

**Relation to Panamath.** This task implements the stimulus side of the two-colour dot
comparison used by Panamath (Halberda et al., 2008): intermixed yellow and blue dots at
controlled numerical ratios, with total dot surface optionally matched or inverted between the
colours so that cumulative area cannot substitute for numerosity. If you have seen this
paradigm referred to as a Panamath task, this is the subcommand you want.

What it is not: CogStim generates stimuli, it does not administer the test, collect
responses or estimate a Weber fraction, and it is not affiliated with or validated
against the Panamath software. Use it to produce the image set, then present it with
your own experiment software.

### Minimal Command

```bash
cogstim ans --train-num 10 --test-num 5
```

**What it produces:** 15 sets = **1680 images**, at 112 images per set (28 dot-count pairs x 2 colour orders x {random, equal} surface). Yellow and blue dots, organised by dominant colour. Half have equal total dot surface for the two colours; half have random dot sizes.

### Relevant Options

- `--ratios` – Ratio set: `easy`, `hard`, `all`, or custom comma-separated ratios (default: `all`)
  - **easy**: 1:5, 1:4, 1:3, 2:5, 1:2, 3:5, 2:3, 3:4
  - **hard**: 4:5, 5:6, 6:7, 7:8, 8:9, 9:10, 10:11, 11:12
  - **all**: Both easy and hard ratios combined
  - **Custom**: Comma-separated fractions, e.g., `--ratios 1/2,2/3,3/4` (see Advanced Tweak below)
- `--min-dot-num` / `--max-dot-num` – Range of dots per colour (defaults: 1–10)
- `--surface` – Surface conditions to generate: `random`, `equal`, `inverse` (default: `random equal`); see [Surface conditions](#surface-conditions)
- `--hull` – Hull conditions to generate, combined with every surface condition (default: `random`); see [Hull conditions](#hull-conditions)
- `--dot-colour-1` / `--dot-colour-2` – Dot colours (defaults: `yellow`, `blue`)
- `--min-dot-radius-px` / `--max-dot-radius-px` – Dot radius range in pixels (defaults: 20–30)
- `--attempts-limit` – Maximum placement attempts before giving up (default: 10000)
- `--seed` – Random seed for reproducibility

### Surface conditions

Every dot-count pair is generated once per surface condition, which says how the total
dot surface of the two colours relates to their counts:

| Condition | Filename suffix | What it does |
|---|---|---|
| `random` | none | Every radius is drawn independently, so the colour with more dots usually covers more surface |
| `equal` | `_equal` | The two colours cover the same total surface, so surface says nothing about number |
| `inverse` | `_inverse` | The colour with fewer dots covers more surface, by the factor the other has more dots: with 4 vs 8 dots, the 4 cover twice the surface of the 8 |

The default, `--surface random equal`, gives half the images of each. Gebuis and Reynvoet
(2011) note that such a set never contradicts number: a participant answering from
surface alone is right in the random images and at chance in the equal ones. Adding
`inverse` (`--surface random equal inverse`) makes surface useless over the set as a
whole. The `equal` condition grows the colour with less surface; `inverse` rescales both
colours, the fewer up and the more down by the same factor, so dot sizes leave the
configured radius range. Which cues each condition leaves congruent with number can be
read off the [visual properties export](#visual-properties-of-dot-arrays).

To choose a different proportion, or a condition per image, specify the stimuli directly
with `--tasks-csv` — see below.

Each image is generated from an independent random layout, including the different
surface conditions of the same dot counts. This is deliberate: reusing a spatial
configuration across conditions would let participants learn the arrangement rather than
judge numerosity, which is what per-trial randomization exists to prevent.

### Hull conditions

The area an array extends over, its convex hull, grows with the number of dots when
they are placed at random: more dots are more likely to reach the edges of the field.
In CogStim's output the array with more dots has the larger hull in about seven pairs
out of ten, whatever the surface condition, so "which patch is bigger" answers the task
without counting. Gebuis and Reynvoet (2011) vary the field each array is placed in;
CogStim sets the hull itself.

`--hull` takes the same three values as `--surface`, and every dot-count pair is
generated once per combination of the two:

| Condition | Filename suffix | What it does |
|---|---|---|
| `random` | none | Dots stay where they were placed |
| `equal` | `_hull_equal` | Both arrays extend over the same area |
| `inverse` | `_hull_inverse` | The array with fewer dots extends over more area, by the factor the other has more dots |

The default is `random`, so nothing changes unless you ask. To meet a condition, the
array that must extend less, the one with more dots, is placed inside a smaller circle to
begin with, sized so that the other array can spread past it by the required factor; then
the dots of each array are moved away from the array's centroid until its hull reaches the
target. Pulling an already placed array together would stop at the first two dots that
touch, which with ordinary dot sizes is almost at once, so the smaller field does that
work instead. Radii are never touched, so a surface condition applied to the same image
still holds exactly, and the two factors combine freely: `--surface equal --hull inverse`
gives images whose colours cover the same surface while the colour with fewer dots spreads
over more area. Dots stay inside the field they were placed in, the canvas circle or the
colour's half in the separated layout, so no layout appears that random placement could
not have produced.

Not every pair can meet a hull condition: a single dot extends over nothing but itself,
and n dots cannot be placed inside a circle below a certain size. CogStim checks this when
it plans, including under `--dry-run`, and refuses the run naming the pairs that cannot be
met; raise `--min-dot-num`, narrow `--ratios`, shrink the dots or enlarge the image. With
the default dot radius of 20–30 px on a 512 px canvas, `inverse` is possible for ratios of
about 2:3 and closer; smaller dots, for instance `--min-dot-radius-px 8 --max-dot-radius-px
12`, allow it down to 1:2 from 4 dots up, and are what the separated layout needs, since
its halves are small. This is the limit described in the
[note on small numerosities](#note-on-small-numerosities).

In the full layout the two colours share one field, so a hull difference means that one
colour is clustered inside the other's spread. The hull conditions are meant for arrays that occupy separate fields,
as in Gebuis and Reynvoet's experiments: `--layout separated`, and `match-to-sample`, whose
filenames carry a second letter for the hull condition when it is not random
(`mts_00000_ri_a_5.png` is random surface, inverse hull).

### Note on small numerosities

The defaults (`--min-dot-num 1`, `--ratios all`) include pairs such as 1 vs 5
and 2 vs 10. Gebuis and Reynvoet (2011) showed that below 4 dots the area an
array covers (its convex hull) and its total contour cannot be matched to those
of a larger array: a single dot's hull is the dot itself, and enlarging it until
it covers what five dots cover makes dot size covary with number instead. In
their data the hull alone explained 28% of the variance in numerical distance
with arrays of 1 to 4 dots, against 5% once every array had at least 4.

CogStim warns when a plan contains such pairs. Use `--min-dot-num 4` to avoid
them, or keep them, for instance to cover the subitizing range, and check the
cues post hoc with [`--visual-properties`](#visual-properties-of-dot-arrays).
The same applies to `match-to-sample` pairs whose counts differ.

### Choosing exactly which stimuli to generate

`--tasks-csv` replaces the ratio sweep with an explicit list, one row per image. This is
how you control which stimuli get which surface condition, and in what proportion.

```csv
n1,n2,surface
3,2,equal
3,2,random
3,2,inverse
5,4,random
```

```bash
cogstim ans --tasks-csv tasks.csv --train-num 1
```

Produces four images, one per row:

```
train/yellow/img_3_2_0_equal.png
train/yellow/img_3_2_1.png
train/yellow/img_3_2_2_inverse.png
train/yellow/img_5_4_3.png
```

| Column | Meaning |
|---|---|
| `n1` | Dots of the first colour |
| `n2` | Dots of the second colour |
| `surface` | `random`, `equal` or `inverse`: the [surface condition](#surface-conditions) of the image; random when the column is absent |
| `hull` | `random`, `equal` or `inverse`: the [hull condition](#hull-conditions) of the image; random when the column is absent |

`--tasks-copies N` repeats the whole distribution N times. When `--tasks-csv` is set,
`--ratios`, `--min-dot-num` and `--max-dot-num` are ignored, since the file already says
exactly what to generate.

Match-to-sample takes the same approach with columns `sample,match,surface,hull`.

### Advanced Tweak: Controlling Difficulty with Ratios

The `--ratios` flag controls which numerical ratios are used for discrimination. Ratios closer to 1:1 are harder to discriminate:

- **Easy ratios** (use `--ratios easy`): Include 1:2, 2:3, 3:4, etc. These are more discriminable and suitable for initial training or populations with numerical difficulties.
- **Hard ratios** (use `--ratios hard`): Include 4:5, 5:6, 6:7, etc. These are near-equal ratios requiring fine discrimination.
- **All ratios** (use `--ratios all`, the default): Includes the full range from easy to hard, providing a comprehensive numerical discrimination dataset.
- **Custom ratios**: Specify your own comma-separated fraction ratios for precise control over difficulty levels.

Example with easy ratios only:

```bash
cogstim ans --ratios easy --train-num 10 --test-num 5
```

Example with custom specific ratios:

```bash
cogstim ans --ratios 1/2,2/3,3/4,4/5 --train-num 10 --test-num 5
```

This generates images with only the ratios 1:2, 2:3, 3:4, and 4:5.

**Note**: The specific preset ratios were chosen based on Halberda et al. (2008) to span a range of discrimination difficulties.

### Fuller Example

```bash
cogstim ans \
  --ratios easy \
  --train-num 100 --test-num 40 \
  --min-dot-num 5 --max-dot-num 15 \
  --seed 1234
```

This generates a large dataset with only easy ratios and 5–15 dots per colour.

### ANS Options Reference

| Flag | Meaning | Default | When to use |
|------|---------|---------|-------------|
| `--ratios` | Ratio difficulty set | `all` | Use `easy` for simpler tasks, `hard` for difficult discrimination |
| `--surface` | Surface conditions | `random equal` | Add `inverse` so that surface contradicts number in some images |
| `--hull` | Hull conditions | `random` | `equal` or `inverse` to control the area each colour extends over |
| `--min-dot-num` | Min dots per colour | `1` | To set quantity range |
| `--max-dot-num` | Max dots per colour | `10` | To set quantity range |
| `--dot-colour-1` | First dot colour | `yellow` | To customize colours |
| `--dot-colour-2` | Second dot colour | `blue` | To customize colours |
| `--min-dot-radius-px` | Min dot radius (px) | `20` | To adjust dot sizes |
| `--max-dot-radius-px` | Max dot radius (px) | `30` | To adjust dot sizes |
| `--attempts-limit` | Max placement attempts | `10000` | Increase if dots fail to place |
| `--seed` | Random seed | None | For reproducibility |

---

## One-Colour – Single-Colour Dot Arrays

Generate single-colour dot arrays where the class is the quantity of dots. Use this for number discrimination tasks without colour cues. Total surface area is held constant across quantities when possible.

### Minimal Command

```bash
cogstim one-colour --train-num 10 --test-num 5
```

**What it produces:** 15 sets = **150 images**, at 10 images per set (one per dot count). Yellow dots, organised by quantity (1, 2, 3, ... up to `max-point-num`).

### Relevant Options

- `--min-dot-num` / `--max-dot-num` – Range of dot quantities (defaults: 1–10)
- `--dot-colour-1` – Dot colour (default: `yellow`)
- `--min-dot-radius-px` / `--max-dot-radius-px` – Dot radius range in pixels (defaults: 20–30)
- `--attempts-limit` – Maximum placement attempts (default: 10000)
- `--seed` – Random seed for reproducibility

### Advanced Tweak: Limited Quantity Range with Constant Surface

Use a small quantity range (e.g., 1–5) with surface equalization to ensure stimuli vary only in numerosity:

```bash
cogstim one-colour \
  --min-dot-num 1 --max-dot-num 5 \
  --train-num 50 --test-num 20
```

### Fuller Example

```bash
cogstim one-colour \
  --train-num 50 --test-num 20 \
  --min-dot-num 1 --max-dot-num 5 \
  --dot-colour-1 red \
  --seed 1234
```

This generates red dot arrays numbered 1–5 with constant total surface area.

### One-Colour Options Reference

| Flag | Meaning | Default | When to use |
|------|---------|---------|-------------|
| `--min-dot-num` | Min number of dots | `1` | To set quantity range |
| `--max-dot-num` | Max number of dots | `10` | To set quantity range |
| `--dot-colour-1` | Dot colour | `yellow` | To customize colour |
| `--min-dot-radius-px` | Min dot radius (px) | `20` | To adjust dot sizes |
| `--max-dot-radius-px` | Max dot radius (px) | `30` | To adjust dot sizes |
| `--attempts-limit` | Max placement attempts | `10000` | Increase if dots fail to place |
| `--seed` | Random seed | None | For reproducibility |

---

## Match-to-Sample – Dot Array Pairs

Generate sample/match image pairs for match-to-sample tasks. Each trial produces two images: a sample (role `b`) and a match (role `a`). By default, half the trials have equal total dot surface between sample and match and half have random dot sizes; `--surface` adds the inverse condition, in which the image with fewer dots covers more surface. Based on Sella et al. (2013).

### Minimal Command

```bash
cogstim match-to-sample --train-num 10 --test-num 5
```

**What it produces:** 15 sets = 1440 image pairs = **2880 images**, at 192 images per set (12 dot-count pairs x 8 variants x 2 images per pair). Written flat into `images/match_to_sample/train/` and `images/match_to_sample/test/`. Each pair consists of `mts_{trial_id}_{r|e|i}_b_{n_dots}.png` (sample) and `mts_{trial_id}_{r|e|i}_a_{n_dots}.png` (match).

### Relevant Options

- `--ratios` – Ratio set: `easy`, `hard`, or `all` (default: `all`)
- `--min-dot-num` / `--max-dot-num` – Range of dot quantities (defaults: 1–10)
- `--surface` – Surface conditions to generate: `random`, `equal`, `inverse` (default: `random equal`); see [Surface conditions](#surface-conditions)
- `--hull` – Hull conditions to generate, combined with every surface condition (default: `random`); see [Hull conditions](#hull-conditions)
- `--dot-colour-1` – Dot colour (default: `black`)
- `--min-dot-radius-px` / `--max-dot-radius-px` – Dot radius range (defaults: 5–15)
- `--tolerance` – Relative tolerance for area equalization (default: 0.01, i.e., 1%)
- `--abs-tolerance` – Absolute area tolerance in pixels (default: 2)
- `--attempts-limit` – Maximum placement attempts (default: 5000)
- `--seed` – Random seed for reproducibility

Pairs whose counts differ and include fewer than 4 dots are warned about, for
the reason given in the [note on small numerosities](#note-on-small-numerosities).

### File Naming

Filenames are self-described and sort by trial then role: `mts_{trial_id:05d}_{r|e|i}_{a|b}_{n_dots}[_version].png`, where:
- `trial_id` = zero-padded trial index (pairs share this id)
- `r` = random dot sizes, `e` = equal surface, `i` = inverse surface (see [Surface conditions](#surface-conditions))
- a second letter, present only when the hull condition is not random, gives it in the same code (see [Hull conditions](#hull-conditions))
- `a` = match image, `b` = sample image (alphabetical order: match then sample)
- `n_dots` = number of dots in that image
- Optional `_version` tag may follow.

### Advanced Tweak: Tighter Equalization Tolerance

Adjust `--tolerance` to control how closely matched the surface areas are:

```bash
cogstim match-to-sample \
  --tolerance 0.005 \
  --train-num 10 --test-num 5
```

This uses a 0.5% relative tolerance instead of the default 1%.

### Fuller Example

```bash
cogstim match-to-sample \
  --ratios easy \
  --train-num 50 --test-num 20 \
  --min-dot-num 1 --max-dot-num 10 \
  --dot-colour-1 yellow \
  --seed 1234
```

This generates yellow dot array pairs with easy ratios and controlled surface equalization.

### Match-to-Sample Options Reference

| Flag | Meaning | Default | When to use |
|------|---------|---------|-------------|
| `--ratios` | Ratio difficulty set | `all` | Use `easy` for simpler discrimination |
| `--surface` | Surface conditions | `random equal` | Add `inverse` so that surface contradicts number in some trials |
| `--hull` | Hull conditions | `random` | `equal` or `inverse` to control the area each image's dots extend over |
| `--min-dot-num` | Min number of dots | `1` | To set quantity range |
| `--max-dot-num` | Max number of dots | `10` | To set quantity range |
| `--dot-colour-1` | Dot colour | `black` | To customize colour |
| `--min-dot-radius-px` | Min dot radius (px) | `5` | To adjust dot sizes |
| `--max-dot-radius-px` | Max dot radius (px) | `15` | To adjust dot sizes |
| `--tolerance` | Relative area tolerance | `0.01` (1%) | Tighten for stricter equalization |
| `--abs-tolerance` | Absolute area tolerance (px) | `2` | For fine-grained control |
| `--attempts-limit` | Max placement attempts | `5000` | Increase if placement fails |
| `--seed` | Random seed | None | For reproducibility |

---

## Lines – Rotated Stripe Patterns

Generate images with rotated stripe patterns at different angles for orientation discrimination tasks. Based on Srinivasan (2021) studies of visual orientation processing in honeybees.

### Minimal Command

```bash
cogstim lines --train-num 10 --test-num 5
```

**What it produces:** 15 sets = **540 images**, at 36 images per set (4 angles x 9 stripe counts). Stripe patterns at angles 0°, 45°, 90°, and 135°, organised by angle class.

### Relevant Options

- `--angles` – Rotation angles for stripes (default: `0 45 90 135`)
- `--min-stripe-num` / `--max-stripe-num` – Number of stripes per image (defaults: 2–10)
- `--min-line-thickness-px` / `--max-line-thickness-px` – Stripe thickness in pixels (defaults: 10–30)
- `--min-line-spacing-px` – Minimum spacing between stripes in pixels (default: 5)
- `--seed` – Random seed for reproducibility

### Advanced Tweak: Specific Angles

Generate only vertical (90°) and horizontal (0°) stripes:

```bash
cogstim lines \
  --angles 0 90 \
  --train-num 10 --test-num 5
```

### Fuller Example

```bash
cogstim lines \
  --train-num 50 --test-num 20 \
  --angles 0 45 90 135 \
  --min-stripe-num 3 --max-stripe-num 5 \
  --seed 1234
```

This generates stripe patterns at four angles with 3–5 stripes per image.

### Lines Options Reference

| Flag | Meaning | Default | When to use |
|------|---------|---------|-------------|
| `--angles` | Rotation angles (degrees) | `0 45 90 135` | To specify custom angles |
| `--min-stripe-num` | Min stripes per image | `2` | To control stripe density |
| `--max-stripe-num` | Max stripes per image | `10` | To control stripe density |
| `--min-line-thickness-px` | Min stripe thickness (px) | `10` | To adjust stripe width |
| `--max-line-thickness-px` | Max stripe thickness (px) | `30` | To adjust stripe width |
| `--min-line-spacing-px` | Min spacing between stripes (px) | `5` | To control stripe separation |
| `--seed` | Random seed | None | For reproducibility |

---

## Fixation – Fixation Targets

Generate fixation target images for eye-tracking or attention experiments. Supports seven types (A, B, C, AB, AC, BC, ABC) based on Thaler et al. (2013), who recommend using the ABC type for optimal fixation stability.

### Minimal Command

```bash
cogstim fixation --all-types
```

**What it produces:** Seven fixation images (one per type) in `images/fixation/` named `fix_A.png`, `fix_B.png`, etc.

### Relevant Options

- `--all-types` – Generate all seven types
- `--types` – Specific types to generate (e.g., `--types ABC A B`)
- `--symbol-colour` – Fixation symbol colour (default: `white`)
- `--background-colour` – Background colour (default: `white`)
- `--img-size` – Image size in pixels (default: 512)
- `--dot-radius-px` – Central dot radius (default: 6)
- `--disk-radius-px` – Filled disk radius (default: 48)
- `--cross-thickness-px` – Cross bar thickness (default: 12)
- `--cross-arm-px` – Half-length of cross arms (default: 128)
- `--jitter-px` – Positional jitter (default: 0)

### Type Legend

- **A:** Filled disk only
- **B:** Cross only
- **C:** Central dot only
- **AB, AC, BC, ABC:** Combinations (composite types use cut-outs as per Thaler et al.)

### Advanced Tweak: Custom Dimensions

Adjust cross and disk sizes for different display contexts:

```bash
cogstim fixation \
  --all-types \
  --dot-radius-px 8 \
  --disk-radius-px 128 \
  --cross-thickness-px 24 \
  --cross-arm-px 128
```

### Fuller Example

```bash
cogstim fixation \
  --all-types \
  --background-colour black \
  --symbol-colour white \
  --img-size 512 \
  --dot-radius-px 6 \
  --disk-radius-px 128 \
  --cross-thickness-px 24 \
  --cross-arm-px 128
```

This generates all seven fixation types with recommended parameters on a black background.

### Fixation Options Reference

| Flag | Meaning | Default | When to use |
|------|---------|---------|-------------|
| `--all-types` | Generate all seven types | Off | To generate all types at once |
| `--types` | Specific types to generate | All | To select a subset |
| `--symbol-colour` | Fixation symbol colour | `white` | To change symbol colour |
| `--background-colour` | Background colour | `white` | For contrast adjustment |
| `--dot-radius-px` | Central dot radius (px) | `6` | To adjust dot size |
| `--disk-radius-px` | Filled disk radius (px) | `48` | To adjust disk size |
| `--cross-thickness-px` | Cross bar thickness (px) | `12` | To adjust cross thickness |
| `--cross-arm-px` | Cross arm half-length (px) | `128` | To adjust cross size |
| `--jitter-px` | Positional jitter (px) | `0` | To add position variation |

---

## Custom – Custom Shape/Colour Combinations

Generate arbitrary combinations of shapes and colours. Use this for exploratory tasks or when you need multiple shapes and colours in the same dataset.

### Minimal Command

```bash
cogstim custom --shapes circle star --shape-colours red green --train-num 10 --test-num 5
```

**What it produces:** 15 sets = **6000 images**, at 400 images per set (100 surface areas x 2 shapes x 2 colours). All combinations of the specified shapes and colours (red circles, red stars, green circles, green stars), organised by shape-colour class.

### Relevant Options

- `--shapes` – List of shapes (required; choices: `circle`, `star`, `triangle`, `square`)
- `--shape-colours` – List of colours (required; choices: `yellow`, `blue`, `red`, `green`, `black`, `white`, `gray`)
- `--min-surface` / `--max-surface` – Shape surface area range (defaults: 10000–20000)
- `--no-jitter` – Disable positional jitter
- `--seed` – Random seed for reproducibility

### Advanced Tweak: Multi-Class Datasets

Generate datasets with more than two classes for multi-class classification:

```bash
cogstim custom \
  --shapes triangle square circle \
  --shape-colours red green blue \
  --train-num 50 --test-num 20
```

This produces 9 classes (3 shapes × 3 colours).

### Fuller Example

```bash
cogstim custom \
  --shapes triangle square \
  --shape-colours red green \
  --train-num 50 --test-num 20 \
  --no-jitter \
  --seed 1234
```

This generates red and green triangles and squares in fixed positions.

### Custom Options Reference

| Flag | Meaning | Default | When to use |
|------|---------|---------|-------------|
| `--shapes` | List of shapes | Required | To specify shape set |
| `--shape-colours` | List of colours | Required | To specify colour set |
| `--min-surface` | Min shape area (px²) | `10000` | To adjust shape sizes |
| `--max-surface` | Max shape area (px²) | `20000` | To adjust shape sizes |
| `--no-jitter` | Disable positional jitter | Off | For fixed positions |
| `--seed` | Random seed | None | For reproducibility |

---

## Common Options (All Tasks)

These options are available across all tasks:

- `--output-dir PATH` – Custom output directory (default varies by task)
- `--img-size SIZE` – Image size in pixels (default: 512)
- `--img-size-deg`, `--viewing-distance-cm`, `--pixels-per-cm` – Sizes in degrees of visual angle; see [above](#sizes-in-degrees-of-visual-angle)
- `--background-colour COLOUR` – Background colour (default: `white`)
- `--seed SEED` – Random seed for reproducible generation
- `--demo` – Generate a small preview with 8 training sets
- `--quiet` – Suppress all non-error output

For any task-specific help, use:

```bash
cogstim <task> --help
```

