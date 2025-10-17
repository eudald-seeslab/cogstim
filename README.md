# CogStim – Visual Cognitive-Stimulus Generator

CogStim is a small Python toolkit that produces **synthetic image datasets** commonly used in cognitive–neuroscience and psychophysics experiments, such as:

* Two–shape discrimination (e.g. *circle vs star*).
* Two–colour discrimination (e.g. *yellow vs blue* circles).
* Approximate Number System (ANS) dot arrays with two colours.
* Single-colour dot arrays for number-discrimination tasks.
* Custom combinations of geometrical *shapes × colours*.
* Rotated stripe patterns ("lines" dataset) for orientation discrimination.
* Fixation targets (A, B, C, AB, AC, BC, ABC) with configurable colours.

All stimuli are generated as 512 × 512 px PNG files ready to be fed into machine-learning pipelines or presented in behavioural experiments.

## Installation

```bash
pip install cogstim  
```
## Command-line interface

After installation the `cli` module is available as the *single entry-point* to create datasets. Run it either via `python -m cogstim.cli …` or directly if the `cogstim` package is on your `$PYTHONPATH`.

```text
usage: cli.py [-h] (--shape_recognition | --colour_recognition | --ans | --one_colour | --lines | --fixation | --custom)
              [--shapes {circle,star,triangle,square} ...]
              [--colours {yellow,blue,red,green,black,white,gray} ...]
              [--train_num TRAIN_NUM] [--test_num TEST_NUM] [--output_dir OUTPUT_DIR]
              [--background_colour BACKGROUND_COLOUR]
              [--symbol_colour {yellow,blue,red,green,black,white,gray}]
              [--min_surface MIN_SURFACE] [--max_surface MAX_SURFACE] [--no-jitter]
              [--easy] [--version_tag VERSION_TAG] [--min_point_num MIN_POINT_NUM] [--max_point_num MAX_POINT_NUM]
              [--min_point_radius MIN_POINT_RADIUS] [--max_point_radius MAX_POINT_RADIUS]
              [--dot_colour {yellow,blue,red,green,black,white,gray}]
              [--angles ANGLES [ANGLES ...]] [--min_stripes MIN_STRIPES] [--max_stripes MAX_STRIPES]
              [--img_size IMG_SIZE] [--tag TAG] [--min_thickness MIN_THICKNESS] [--max_thickness MAX_THICKNESS]
              [--min_spacing MIN_SPACING] [--max_attempts MAX_ATTEMPTS]
              [--types {A,B,C,AB,AC,BC,ABC} ...] [--all_types]
              [--dot_radius_px DOT_RADIUS_PX] [--disk_radius_px DISK_RADIUS_PX]
              [--cross_thickness_px CROSS_THICKNESS_PX] [--cross_arm_px CROSS_ARM_PX] [--jitter_px JITTER_PX]
```

> **Note**: train_num and test_num refer to the number of image _sets_ created. An image set is a group of images that comb all the possible parameter combinations. So, for shapes and colors, an image set is of about 200 images, whereas for ANS is of around 75 images, of course always depending on the other parameters.
> **Note**: All cli arguments use British spelling.

## Examples

### Shape recognition – *circle vs star* in yellow
```bash
python -m cogstim.cli --shape_recognition --train_num 60 --test_num 20
```

<table><tr>
  <td><img src="https://raw.githubusercontent.com/eudald-seeslab/cogstim/main/assets/examples/circle.png" alt="Yellow circle" width="220"/></td>
  <td><img src="https://raw.githubusercontent.com/eudald-seeslab/cogstim/main/assets/examples/star.png" alt="Yellow star" width="220"/></td>
</tr></table>

### Colour recognition – yellow vs blue circles (no positional jitter)
```bash
python -m cogstim.cli --colour_recognition --no-jitter
```

<table><tr>
  <td><img src="https://raw.githubusercontent.com/eudald-seeslab/cogstim/main/assets/examples/circle.png" alt="Yellow circle" width="220"/></td>
  <td><img src="https://raw.githubusercontent.com/eudald-seeslab/cogstim/main/assets/examples/circle_blue.png" alt="Blue circle" width="220"/></td>
</tr></table>

###  Approximate Number System (ANS) dataset with easy ratios only
```bash
python -m cogstim.cli --ans --easy --train_num 100 --test_num 40
```

<table><tr>
  <td><img src="https://raw.githubusercontent.com/eudald-seeslab/cogstim/main/assets/examples/ans_equalized.png" alt="ANS equalized" width="220"/></td>
  <td><img src="https://raw.githubusercontent.com/eudald-seeslab/cogstim/main/assets/examples/ans.png" alt="ANS non-equalized" width="220"/></td>
</tr></table>

> Note that on the left image, total surfaces are equalized, and, on the right image, dot size is random.

This is based on Halberda et al. (2008).

### Single-colour dot arrays numbered 1-5, total surface area held constant
```bash
python -m cogstim.cli --one_colour --min_point_num 1 --max_point_num 5
```

<table><tr>
  <td><img src="https://raw.githubusercontent.com/eudald-seeslab/cogstim/main/assets/examples/dots_two.png" alt="Two circles" width="220"/></td>
  <td><img src="https://raw.githubusercontent.com/eudald-seeslab/cogstim/main/assets/examples/dots_five.png" alt="Five circles" width="220"/></td>
</tr></table>

### Custom dataset – green/red triangles & squares
```bash
python -m cogstim.cli --custom --shapes triangle square --colours red green
```

<table><tr>
  <td><img src="https://raw.githubusercontent.com/eudald-seeslab/cogstim/main/assets/examples/triangle_red.png" alt="Red triangle" width="220"/></td>
  <td><img src="https://raw.githubusercontent.com/eudald-seeslab/cogstim/main/assets/examples/square_green.png" alt="Green square" width="220"/></td>
</tr></table>

### Lines dataset – rotated stripe patterns
```bash
python -m cogstim.cli --lines --train_num 50 --test_num 20 --angles 0 45 90 135 --min_stripes 3 --max_stripes 5
```

<table><tr>
  <td><img src="https://raw.githubusercontent.com/eudald-seeslab/cogstim/main/assets/examples/lines_vertical.png" alt="Vertical lines" width="220"/></td>
  <td><img src="https://raw.githubusercontent.com/eudald-seeslab/cogstim/main/assets/examples/lines_horizontal.png" alt="Horizontal lines" width="220"/></td>
</tr></table>

This is based on Srinivasan (2021).

### Fixation targets – A/B/C/AB/AC/BC/ABC
```bash
python -m cogstim.cli \
  --fixation \
  --all_types \
  --background_colour black --symbol_colour white \
  --img_size 512 --dot_radius_px 6 --disk_radius_px 128 --cross_thickness_px 24 \
  --cross_arm_px 128
```

- The symbol uses a single colour (`--symbol_colour`).
- Composite types BC/ABC are rendered by overdrawing the cross and/or central dot with the background colour to create cut-outs, matching the figure convention in Thaler et al. (2013).
- For fixation targets, exactly one image is generated regardless of `--train_num`/`--test_num`.
- Use `--all_types` to generate all seven types; otherwise, choose a subset via `--types`.
- Control cross bar length using `--cross_arm_px` (half-length from center), and thickness via `--cross_thickness_px`.

Output folder layout for fixation targets:
```
images/fixation/
```

These shapes are based on Thaler et al. (2013). They recommend using ABC.

<img src="https://raw.githubusercontent.com/eudald-seeslab/cogstim/main/assets/examples/fix_C.png" alt="Fixation point example" width="220"/>

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

## References

- Halberda, J., Mazzocco, M. M. M., & Feigenson, L. (2008). Individual differences in non-verbal number acuity correlate with maths achievement. Nature, 455(7213), 665-668. https://doi.org/10.1038/nature07246

- Srinivasan, M. V. (2021). Vision, perception, navigation and ‘cognition’ in honeybees and applications to aerial robotics. Biochemical and Biophysical Research Communications, 564, 4-17. https://doi.org/10.1016/j.bbrc.2020.09.052

- Thaler, L., Schütz, A. C., Goodale, M. A., & Gegenfurtner, K. R. (2013). What is the best fixation target? The effect of target shape on stability of fixational eye movements. Vision Research, 76, 31–42. https://doi.org/10.1016/j.visres.2012.10.012
