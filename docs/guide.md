# User Guide

This guide provides detailed documentation for each CogStim task, including relevant options, examples, and usage patterns.

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

**What it produces:** 15 image sets (10 training, 5 test) containing circles and stars in yellow, organised into `train/circle/`, `train/star/`, `test/circle/`, and `test/star/` subdirectories.

### Relevant Options

- `--shapes` – Two shapes for discrimination (default: `circle star`)
- `--colours` – Single colour for both shapes (default: `yellow`)
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
  --colours red \
  --seed 1234
```

This generates 80 image sets of red triangles and squares with reproducible randomness.

### Shapes Options Reference

| Flag | Meaning | Default | When to use |
|------|---------|---------|-------------|
| `--shapes` | Two shapes for discrimination | `circle star` | To choose different shape pairs |
| `--colours` | Single colour for shapes | `yellow` | To change shape colour |
| `--min-surface` | Minimum shape area (px²) | `10000` | To adjust shape sizes |
| `--max-surface` | Maximum shape area (px²) | `20000` | To adjust shape sizes |
| `--no-jitter` | Disable positional jitter | Off (jitter enabled) | For fixed-position shapes |
| `--seed` | Random seed | None (random) | For reproducible generation |
| `--train-num` | Number of training image sets | `10` | To generate training data |
| `--test-num` | Number of test image sets | `0` | To generate test data |

---

## Colours – Colour Discrimination

Generate images of the same shape in different colours for colour recognition tasks. Use this for paradigms where only colour varies (e.g., yellow vs blue circles). Based on standard colour discrimination paradigms.

### Minimal Command

```bash
cogstim colours --train-num 10 --test-num 5
```

**What it produces:** 15 image sets (10 training, 5 test) containing circles in yellow and blue, organised by colour class.

### Relevant Options

- `--shape` – Shape to use for both classes (default: `circle`)
- `--colours` – Two colours for discrimination (default: `yellow blue`)
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
  --colours red green \
  --no-jitter \
  --seed 1234
```

This generates red and green stars in fixed positions with reproducible randomness.

### Colours Options Reference

| Flag | Meaning | Default | When to use |
|------|---------|---------|-------------|
| `--shape` | Shape for both colour classes | `circle` | To change the base shape |
| `--colours` | Two colours for discrimination | `yellow blue` | To use different colour pairs |
| `--min-surface` | Minimum shape area (px²) | `10000` | To adjust shape sizes |
| `--max-surface` | Maximum shape area (px²) | `20000` | To adjust shape sizes |
| `--no-jitter` | Disable positional jitter | Off (jitter enabled) | For fixed-position stimuli |
| `--seed` | Random seed | None (random) | For reproducible generation |
| `--train-num` | Number of training image sets | `10` | To generate training data |
| `--test-num` | Number of test image sets | `0` | To generate test data |

---

## ANS – Approximate Number System

Generate two-colour dot arrays for approximate number system tasks. Use this for paradigms investigating numerical cognition where participants discriminate quantities by dominant colour. Based on Halberda et al. (2008).

### Minimal Command

```bash
cogstim ans --train-num 10 --test-num 5
```

**What it produces:** 15 image sets with yellow and blue dots, organised by dominant colour. Half have equalized total dot surface; half have random dot sizes.

### Relevant Options

- `--ratios` – Ratio set: `easy`, `hard`, `all`, or custom comma-separated ratios (default: `all`)
  - **easy**: 1:5, 1:4, 1:3, 2:5, 1:2, 3:5, 2:3, 3:4
  - **hard**: 4:5, 5:6, 6:7, 7:8, 8:9, 9:10, 10:11, 11:12
  - **all**: Both easy and hard ratios combined
  - **Custom**: Comma-separated fractions, e.g., `--ratios 1/2,2/3,3/4` (see Advanced Tweak below)
- `--min-point-num` / `--max-point-num` – Range of dots per colour (defaults: 1–10)
- `--dot-colour1` / `--dot-colour2` – Dot colours (defaults: `yellow`, `blue`)
- `--min-point-radius` / `--max-point-radius` – Dot radius range in pixels (defaults: 20–30)
- `--attempts-limit` – Maximum placement attempts before giving up (default: 10000)
- `--seed` – Random seed for reproducibility

### Note on Equalization

For each trial, half the images equalize total surface area between the two colours, controlling for cumulative surface as a cue. The other half use random dot sizes. This is detailed in the file-naming convention: filenames include `_equalized` or no suffix.

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
  --min-point-num 5 --max-point-num 15 \
  --seed 1234
```

This generates a large dataset with only easy ratios and 5–15 dots per colour.

### ANS Options Reference

| Flag | Meaning | Default | When to use |
|------|---------|---------|-------------|
| `--ratios` | Ratio difficulty set | `all` | Use `easy` for simpler tasks, `hard` for difficult discrimination |
| `--min-point-num` | Min dots per colour | `1` | To set quantity range |
| `--max-point-num` | Max dots per colour | `10` | To set quantity range |
| `--dot-colour1` | First dot colour | `yellow` | To customize colours |
| `--dot-colour2` | Second dot colour | `blue` | To customize colours |
| `--min-point-radius` | Min dot radius (px) | `20` | To adjust dot sizes |
| `--max-point-radius` | Max dot radius (px) | `30` | To adjust dot sizes |
| `--attempts-limit` | Max placement attempts | `10000` | Increase if dots fail to place |
| `--seed` | Random seed | None | For reproducibility |

---

## One-Colour – Single-Colour Dot Arrays

Generate single-colour dot arrays where the class is the quantity of dots. Use this for number discrimination tasks without colour cues. Total surface area is held constant across quantities when possible.

### Minimal Command

```bash
cogstim one-colour --train-num 10 --test-num 5
```

**What it produces:** 15 image sets with yellow dots, organised by quantity (1, 2, 3, ... up to `max-point-num`).

### Relevant Options

- `--min-point-num` / `--max-point-num` – Range of dot quantities (defaults: 1–10)
- `--dot-colour` – Dot colour (default: `yellow`)
- `--min-point-radius` / `--max-point-radius` – Dot radius range in pixels (defaults: 20–30)
- `--attempts-limit` – Maximum placement attempts (default: 10000)
- `--seed` – Random seed for reproducibility

### Advanced Tweak: Limited Quantity Range with Constant Surface

Use a small quantity range (e.g., 1–5) with surface equalization to ensure stimuli vary only in numerosity:

```bash
cogstim one-colour \
  --min-point-num 1 --max-point-num 5 \
  --train-num 50 --test-num 20
```

### Fuller Example

```bash
cogstim one-colour \
  --train-num 50 --test-num 20 \
  --min-point-num 1 --max-point-num 5 \
  --dot-colour red \
  --seed 1234
```

This generates red dot arrays numbered 1–5 with constant total surface area.

### One-Colour Options Reference

| Flag | Meaning | Default | When to use |
|------|---------|---------|-------------|
| `--min-point-num` | Min number of dots | `1` | To set quantity range |
| `--max-point-num` | Max number of dots | `10` | To set quantity range |
| `--dot-colour` | Dot colour | `yellow` | To customize colour |
| `--min-point-radius` | Min dot radius (px) | `20` | To adjust dot sizes |
| `--max-point-radius` | Max dot radius (px) | `30` | To adjust dot sizes |
| `--attempts-limit` | Max placement attempts | `10000` | Increase if dots fail to place |
| `--seed` | Random seed | None | For reproducibility |

---

## Match-to-Sample – Dot Array Pairs

Generate sample/match image pairs for match-to-sample tasks. Each trial produces two images: a sample (`*_s.png`) and a match (`*_m.png`). For half the trials, total dot surface is equalized between sample and match; for the other half, dot sizes are random. Based on Sella et al. (2013).

### Minimal Command

```bash
cogstim match-to-sample --train-num 10 --test-num 5
```

**What it produces:** 15 image pairs (10 training, 5 test) in the flat directory structure: `images/match_to_sample/train/` and `images/match_to_sample/test/`. Each pair consists of `img_n_m_k_[...]_s.png` (sample) and `img_n_m_k_[...]_m.png` (match).

### Relevant Options

- `--ratios` – Ratio set: `easy`, `hard`, or `all` (default: `all`)
- `--min-point-num` / `--max-point-num` – Range of dot quantities (defaults: 1–10)
- `--dot-colour` – Dot colour (default: `black`)
- `--min-point-radius` / `--max-point-radius` – Dot radius range (defaults: 5–15)
- `--tolerance` – Relative tolerance for area equalization (default: 0.01, i.e., 1%)
- `--abs-tolerance` – Absolute area tolerance in pixels (default: 2)
- `--attempts-limit` – Maximum placement attempts (default: 5000)
- `--seed` – Random seed for reproducibility

### File Naming

Filenames encode the trial structure: `img_{n}_{m}_{k}[...]_s.png` and `img_{n}_{m}_{k}[...]_m.png`, where:
- `n` = number of dots in the sample
- `m` = number of dots in the match
- `k` = trial index for this (n, m) pair
- `_s` = sample image
- `_m` = match image

Filenames also include `_equalized` when surface area is controlled.

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
  --min-point-num 1 --max-point-num 10 \
  --dot-colour yellow \
  --seed 1234
```

This generates yellow dot array pairs with easy ratios and controlled surface equalization.

### Match-to-Sample Options Reference

| Flag | Meaning | Default | When to use |
|------|---------|---------|-------------|
| `--ratios` | Ratio difficulty set | `all` | Use `easy` for simpler discrimination |
| `--min-point-num` | Min number of dots | `1` | To set quantity range |
| `--max-point-num` | Max number of dots | `10` | To set quantity range |
| `--dot-colour` | Dot colour | `black` | To customize colour |
| `--min-point-radius` | Min dot radius (px) | `5` | To adjust dot sizes |
| `--max-point-radius` | Max dot radius (px) | `15` | To adjust dot sizes |
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

**What it produces:** 15 image sets with stripe patterns at angles 0°, 45°, 90°, and 135°, organised by angle class.

### Relevant Options

- `--angles` – Rotation angles for stripes (default: `0 45 90 135`)
- `--min-stripes` / `--max-stripes` – Number of stripes per image (defaults: 2–10)
- `--min-thickness` / `--max-thickness` – Stripe thickness in pixels (defaults: 10–30)
- `--min-spacing` – Minimum spacing between stripes in pixels (default: 5)
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
  --min-stripes 3 --max-stripes 5 \
  --seed 1234
```

This generates stripe patterns at four angles with 3–5 stripes per image.

### Lines Options Reference

| Flag | Meaning | Default | When to use |
|------|---------|---------|-------------|
| `--angles` | Rotation angles (degrees) | `0 45 90 135` | To specify custom angles |
| `--min-stripes` | Min stripes per image | `2` | To control stripe density |
| `--max-stripes` | Max stripes per image | `10` | To control stripe density |
| `--min-thickness` | Min stripe thickness (px) | `10` | To adjust stripe width |
| `--max-thickness` | Max stripe thickness (px) | `30` | To adjust stripe width |
| `--min-spacing` | Min spacing between stripes (px) | `5` | To control stripe separation |
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
cogstim custom --shapes circle star --colours red green --train-num 10 --test-num 5
```

**What it produces:** 15 image sets containing all combinations of the specified shapes and colours (red circles, red stars, green circles, green stars), organised by shape-colour class.

### Relevant Options

- `--shapes` – List of shapes (required; choices: `circle`, `star`, `triangle`, `square`)
- `--colours` – List of colours (required; choices: `yellow`, `blue`, `red`, `green`, `black`, `white`, `gray`)
- `--min-surface` / `--max-surface` – Shape surface area range (defaults: 10000–20000)
- `--no-jitter` – Disable positional jitter
- `--seed` – Random seed for reproducibility

### Advanced Tweak: Multi-Class Datasets

Generate datasets with more than two classes for multi-class classification:

```bash
cogstim custom \
  --shapes triangle square circle \
  --colours red green blue \
  --train-num 50 --test-num 20
```

This produces 9 classes (3 shapes × 3 colours).

### Fuller Example

```bash
cogstim custom \
  --shapes triangle square \
  --colours red green \
  --train-num 50 --test-num 20 \
  --no-jitter \
  --seed 1234
```

This generates red and green triangles and squares in fixed positions.

### Custom Options Reference

| Flag | Meaning | Default | When to use |
|------|---------|---------|-------------|
| `--shapes` | List of shapes | Required | To specify shape set |
| `--colours` | List of colours | Required | To specify colour set |
| `--min-surface` | Min shape area (px²) | `10000` | To adjust shape sizes |
| `--max-surface` | Max shape area (px²) | `20000` | To adjust shape sizes |
| `--no-jitter` | Disable positional jitter | Off | For fixed positions |
| `--seed` | Random seed | None | For reproducibility |

---

## Common Options (All Tasks)

These options are available across all tasks:

- `--output-dir PATH` – Custom output directory (default varies by task)
- `--img-size SIZE` – Image size in pixels (default: 512)
- `--background-colour COLOUR` – Background colour (default: `white`)
- `--seed SEED` – Random seed for reproducible generation
- `--demo` – Generate a small preview with 8 training image sets
- `--quiet` – Suppress all non-error output

For any task-specific help, use:

```bash
cogstim <task> --help
```

