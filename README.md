# CogStim – Visual Cognitive-Stimulus Generator

CogStim is a small Python toolkit that produces **synthetic image datasets** commonly used in cognitive–neuroscience and psychophysics experiments, such as:

* Two–shape discrimination (e.g. *circle vs star*).
* Two–colour discrimination (e.g. *yellow vs blue* circles).
* Approximate Number System (ANS) dot arrays with two colours.
* Single-colour dot arrays for number-discrimination tasks.
* Custom combinations of geometrical *shapes × colours*.

All stimuli are generated as 512 × 512 px PNG files ready to be fed into machine-learning pipelines or presented in behavioural experiments.

## Installation

```bash
# Python ≥ 3.9 is required
pip install cogstim  # once published to PyPI
# or, from a local checkout / Git repository
pip install -e .
```

The main runtime dependencies are `Pillow`, `numpy`, and `tqdm`. They are installed automatically through the `pyproject.toml`.

## Command-line interface

After installation the `cli` module is available as the *single entry-point* to create datasets. Run it either via `python -m cogstim.cli …` or directly if the `cogstim` package is on your `$PYTHONPATH`.

```text
usage: cli.py [-h] (--shape_recognition | --color_recognition | --ans | --one_colour | --custom) [--shapes {circle,star,triangle,square} ...]
              [--colors {yellow,blue,red,green} ...] [--train_num TRAIN_NUM] [--test_num TEST_NUM] [--output_dir OUTPUT_DIR]
              [--min_surface MIN_SURFACE] [--max_surface MAX_SURFACE] [--no-jitter] [--easy]
              [--version_tag VERSION_TAG] [--min_point_num MIN_POINT_NUM] [--max_point_num MAX_POINT_NUM]
```

### Examples

Shape recognition – *circle vs star* in yellow:
```bash
python -m cogstim.cli \
    --shape_recognition \
    --train_num 60 --test_num 20
```

Colour recognition – yellow vs blue circles (no positional jitter):
```bash
python -m cogstim.cli \
    --color_recognition --no-jitter
```

Approximate Number System (ANS) dataset with easy ratios only:
```bash
python -m cogstim.cli \
    --ans --easy \
    --train_num 100 --test_num 40
```

Single-colour dot arrays numbered 1-5, total surface area held constant:
```bash
python -m cogstim.cli \
    --one_colour \
    --min_point_num 1 --max_point_num 5 \
    --total_area 20000
```

Custom dataset – green/red triangles & squares:
```bash
python -m cogstim.cli \
    --custom --shapes triangle square --colors red green
```

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

Similar helpers exist for dot-array datasets (`PointsGenerator` and `OneColourImageGenerator`).

## License

This project is distributed under the **MIT License** – see the `LICENSE` file for details.
