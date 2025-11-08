# Quick Start

Welcome to CogStim! This guide will get you up and running in no time.

## Installation

```bash
pip install cogstim
```

## Verify Installation

Check that CogStim is installed and see available subcommands:

```bash
cogstim -h
```

You should see a list of available tasks: `shapes`, `colours`, `ans`, `one-colour`, `match-to-sample`, `lines`, `fixation`, and `custom`.

## Quick Examples

### Example 1: Shape Recognition Dataset

Generate a shape discrimination dataset (circle vs star):

```bash
cogstim shapes
```

**What it produces:** 10 training image sets containing circles and stars in yellow, organised into `images/shapes/train/` with subdirectories for each shape class. By default, `--train-num 10` and `--test-num 0`.

### Example 2: ANS Dot Arrays with Easy Ratios

Generate approximate number system (ANS) dot arrays with easy discrimination ratios:

```bash
cogstim ans --ratios easy
```

**What it produces:** 10 training image sets with two-colour dot arrays (yellow and blue), organised by the dominant colour. Half of the images have equalized total surfaces; the other half use random dot sizes.

## Key Tips

### Reproducibility

Use `--seed` with an integer value to make your generation deterministic and reproducible:

```bash
cogstim shapes --train-num 10 --test-num 5 --seed 1234
```

Without a seed, each run produces different random variations.

### Understanding Image Sets

The `--train-num` and `--test-num` options specify the number of **image sets**, not individual images. An image set is a group of images combining all possible parameter combinations:

- **shapes/colours:** ~200 images per set
- **ans:** ~75 images per set (depending on ratios and point ranges)
- **one-colour:** varies by point number range
- **match-to-sample:** pairs of sample/match images

### Quick Preview

Use `--demo` to generate a small preview dataset (8 training image sets) without specifying counts:

```bash
cogstim shapes --demo
```

This is helpful for quickly checking output before generating larger datasets.

## What's Next?

- **[User Guide](guide.md)** – Detailed documentation for each task with all options
- **[Recipes](recipes.md)** – Copy-paste commands for common research goals
- **[FAQ](faq.md)** – Troubleshooting and common questions

## Output Structure

Generated images are organised by phase and class:

```
images/<task>/
  ├── train/
  │   ├── <class_1>/
  │   └── <class_2>/
  └── test/
      ├── <class_1>/
      └── <class_2>/
```

For example, shapes generates:

```
images/shapes/
  ├── train/
  │   ├── circle/
  │   └── star/
  └── test/
      ├── circle/
      └── star/
```

