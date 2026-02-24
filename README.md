# CogStim – Visual Cognitive-Stimulus Generator

[![PyPI version](https://img.shields.io/pypi/v/cogstim.svg)](https://pypi.org/project/cogstim/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/eudald-seeslab/cogstim/workflows/CI/badge.svg)](https://github.com/eudald-seeslab/cogstim/actions)
[![Coverage Status](https://coveralls.io/repos/github/eudald-seeslab/cogstim/badge.svg?branch=main)](https://coveralls.io/github/eudald-seeslab/cogstim?branch=main)

CogStim is a small Python toolkit that produces **synthetic image datasets** commonly used in cognitive–neuroscience and psychophysics experiments, such as:

* Shape discrimination (e.g. *circle vs star*).
* Colour discrimination (e.g. *yellow vs blue* circles).
* Approximate Number System (ANS) dot arrays with two colours.
* Single-colour dot arrays for number-discrimination tasks.
* Custom combinations of geometrical *shapes × colours*.
* Rotated stripe patterns ("lines" dataset) for orientation discrimination.
* Fixation targets (A, B, C, AB, AC, BC, ABC) with configurable colours.

All stimuli are generated as PNG files with a default size of 512 × 512 pixels (configurable via `--img-size`).

## Installation

```bash
pip install cogstim  
```
## Documentation

- **[Quick Start](docs/index.md)** – Installation and first steps
- **[User Guide](docs/guide.md)** – Detailed documentation for each task
- **[Recipes](docs/recipes.md)** – Copy-paste commands for common goals
- **[FAQ](docs/faq.md)** – Troubleshooting and common questions

### For LLM/AI Agents

- **[LLM Documentation](docs/LLM_DOCUMENTATION.md)** – Single-file comprehensive documentation optimized for feeding to Large Language Models (Context + Architecture + API Reference)

## Command-line interface

CogStim provides a simple command-line interface with task-specific subcommands:

```bash
cogstim <task> [options]
```

Available tasks:
- `shapes` – Shape discrimination (e.g., circles vs stars)
- `colours` – Colour discrimination (same shape, different colours)
- `ans` – Two-colour dot arrays (Approximate Number System)
- `one-colour` – Single-colour dot arrays (quantity discrimination)
- `match-to-sample` – Match-to-sample dot array pairs
- `lines` – Rotated stripe/line patterns
- `fixation` – Fixation target images
- `custom` – Custom shape/colour combinations

For help on a specific task:
```bash
cogstim <task> --help
```

### Common options

Most tasks accept these options:
- `--train-num N` – Number of training image sets (default: 10)
- `--test-num N` – Number of test image sets (default: 0)
- `--output-dir PATH` – Output directory (default: `images/<task>`)
- `--img-size SIZE` – Image size in pixels (default: 512)
- `--background-colour COLOUR` – Background colour (default: white)
- `--seed SEED` – Random seed for reproducible generation
- `--demo` – Generate a quick preview with 8 training images

> **Note**: `--train-num` and `--test-num` refer to the number of image _sets_ created. An image set is a group of images that combines all the possible parameter combinations. For shapes and colours, an image set is about 200 images, whereas for ANS it's around 75 images, depending on the parameters.

> **Note**: All CLI arguments use British spelling.

> **Note**: Use `--seed SEED` (where SEED is an integer) to make generation deterministic and reproducible. Without a seed, each run will produce different random variations.

### Task specification from CSV

For some tasks, you can specify exactly which stimuli to generate via a CSV file instead of using ratios or parameter ranges. You can do this with the `--tasks-csv PATH` to point to a CSV (find below the format of the CSV depending on the task). This method allows to create "n" copies of the tasks in the CSV (`--tasks-copies N` (default: 1) to repeat the distribution N times). When `--tasks-csv` is set, `--ratios` and `--min-point-num` / `--max-point-num` are ignored.

For now, this is supported only for the following tasks, with the CSV specifications

| Task             | CSV columns                 |
|------------------|-----------------------------|
| Match to sample  | sample, match, equalized    |


## Examples

### Shape recognition – *circle vs star* in yellow
```bash
cogstim shapes --train-num 60 --test-num 20
```

For reproducible results, add the `--seed` option:
```bash
cogstim shapes --train-num 60 --test-num 20 --seed 1234
```

<table><tr>
  <td><img src="https://raw.githubusercontent.com/eudald-seeslab/cogstim/main/assets/examples/circle.png" alt="Yellow circle" width="220"/></td>
  <td><img src="https://raw.githubusercontent.com/eudald-seeslab/cogstim/main/assets/examples/star.png" alt="Yellow star" width="220"/></td>
</tr></table>

### Colour recognition – yellow vs blue circles (no positional jitter)
```bash
cogstim colours --train-num 60 --test-num 20 --no-jitter
```

<table><tr>
  <td><img src="https://raw.githubusercontent.com/eudald-seeslab/cogstim/main/assets/examples/circle.png" alt="Yellow circle" width="220"/></td>
  <td><img src="https://raw.githubusercontent.com/eudald-seeslab/cogstim/main/assets/examples/circle_blue.png" alt="Blue circle" width="220"/></td>
</tr></table>

###  Approximate Number System (ANS) dataset with easy ratios only
```bash
cogstim ans --ratios easy --train-num 100 --test-num 40
```

<table><tr>
  <td><img src="https://raw.githubusercontent.com/eudald-seeslab/cogstim/main/assets/examples/ans_equalized.png" alt="ANS equalized" width="220"/></td>
  <td><img src="https://raw.githubusercontent.com/eudald-seeslab/cogstim/main/assets/examples/ans.png" alt="ANS non-equalized" width="220"/></td>
</tr></table>

> Note that on the left image, total surfaces are equalized, and, on the right image, dot size is random.

This is based on Halberda et al. (2008).

### Match-to-sample (MTS) – dot arrays (sample/match) with controlled total surface
```bash
cogstim match-to-sample \
  --ratios easy \
  --train-num 50 --test-num 20 \
  --min-point-num 1 --max-point-num 10 \
  --dot-colour yellow
```

- Generates pairs of images per trial: match (`*_a_*.png`) and sample (`*_b_*.png`).
- For half of the trials, total dot surface is equalized between sample and match; for the other half, dot sizes are random.
- The target total surface for the match is derived from the sample image of the same trial.
- Unequal pairs are built from the same ratio set used by ANS, with both orders (n→m and m→n) included, and equal (n=m) trials added to balance labels.
- Output layout: `images/match_to_sample/{train|test}/mts_{trial_id:05d}_{r|e}_{a|b}_{n_dots}[_version].png` (each image self-described; pairs share trial_id).

This task is based on Sella et al. (2013).

### Single-colour dot arrays numbered 1-5, total surface area held constant
```bash
cogstim one-colour --train-num 50 --test-num 20 --min-point-num 1 --max-point-num 5
```

<table><tr>
  <td><img src="https://raw.githubusercontent.com/eudald-seeslab/cogstim/main/assets/examples/dots_two.png" alt="Two circles" width="220"/></td>
  <td><img src="https://raw.githubusercontent.com/eudald-seeslab/cogstim/main/assets/examples/dots_five.png" alt="Five circles" width="220"/></td>
</tr></table>

### Custom dataset – green/red triangles & squares
```bash
cogstim custom --shapes triangle square --colours red green --train-num 50 --test-num 20
```

<table><tr>
  <td><img src="https://raw.githubusercontent.com/eudald-seeslab/cogstim/main/assets/examples/triangle_red.png" alt="Red triangle" width="220"/></td>
  <td><img src="https://raw.githubusercontent.com/eudald-seeslab/cogstim/main/assets/examples/square_green.png" alt="Green square" width="220"/></td>
</tr></table>

### Lines dataset – rotated stripe patterns
```bash
cogstim lines --train-num 50 --test-num 20 --angles 0 45 90 135 --min-stripes 3 --max-stripes 5
```

<table><tr>
  <td><img src="https://raw.githubusercontent.com/eudald-seeslab/cogstim/main/assets/examples/lines_vertical.png" alt="Vertical lines" width="220"/></td>
  <td><img src="https://raw.githubusercontent.com/eudald-seeslab/cogstim/main/assets/examples/lines_horizontal.png" alt="Horizontal lines" width="220"/></td>
</tr></table>

This task is based on Srinivasan (2021).

### Fixation targets – A/B/C/AB/AC/BC/ABC
```bash
cogstim fixation \
  --all-types \
  --background-colour black --symbol-colour white \
  --img-size 512 --dot-radius-px 6 --disk-radius-px 128 --cross-thickness-px 24 \
  --cross-arm-px 128
```

- The symbol uses a single colour (`--symbol-colour`).
- Composite types BC/ABC are rendered by overdrawing the cross and/or central dot with the background colour to create cut-outs, matching the figure convention in Thaler et al. (2013).
- For fixation targets, exactly one image is generated per type.
- Use `--all-types` to generate all seven types; otherwise, choose a subset via `--types`.
- Control cross bar length using `--cross-arm-px` (half-length from center), and thickness via `--cross-thickness-px`.

Output folder layout for fixation targets:
```
images/fixation/
```

These shapes are based on Thaler et al. (2013). They recommend using ABC.

<img src="https://raw.githubusercontent.com/eudald-seeslab/cogstim/main/assets/examples/fix_ABC.png" alt="Fixation point example" width="220"/>

## Output
The generated folder structure is organised by *phase / class*, e.g.
```
images/two_shapes/
  ├── train/
  │   ├── circle/
  │   └── star/
  └── test/
      ├── circle/
      └── star/
```

## License

This project is distributed under the **MIT License** – see the `LICENCE` file for details.

## TODO's

- The equalization algorithm of match-to-sample could be improved.
- Extend CSV-based task specification to other tasks (ANS, one-colour, shapes, etc.).
- Check that the image is big enough for the parameters set.


## References

- Halberda, J., Mazzocco, M. M. M., & Feigenson, L. (2008). Individual differences in non-verbal number acuity correlate with maths achievement. Nature, 455(7213), 665-668. https://doi.org/10.1038/nature07246

- Sella, F., Lanfranchi, S., & Zorzi, M. (2013). Enumeration skills in Down syndrome. Research in Developmental Disabilities, 34(11), 3798-3806. https://doi.org/10.1016/j.ridd.2013.07.038

- Srinivasan, M. V. (2021). Vision, perception, navigation and ‘cognition’ in honeybees and applications to aerial robotics. Biochemical and Biophysical Research Communications, 564, 4-17. https://doi.org/10.1016/j.bbrc.2020.09.052

- Thaler, L., Schütz, A. C., Goodale, M. A., & Gegenfurtner, K. R. (2013). What is the best fixation target? The effect of target shape on stability of fixational eye movements. Vision Research, 76, 31–42. https://doi.org/10.1016/j.visres.2012.10.012
