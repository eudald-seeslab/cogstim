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

You should see a list of available tasks: `shapes`, `colours`, `ans`, `one-colour`, `match-to-sample`, `mask`, `lines`, `fixation`, and `custom`, plus `run` for replaying a saved configuration.

## Quick Examples

### Example 1: Shape Recognition Dataset

Generate a shape discrimination dataset (circle vs star):

```bash
cogstim shapes
```

**What it produces:** 10 training sets containing circles and stars in yellow, organised into `images/shapes/train/` with subdirectories for each shape class. By default, `--train-num 10` and `--test-num 0`.

### Example 2: ANS Dot Arrays with Easy Ratios

Generate approximate number system (ANS) dot arrays with easy discrimination ratios:

```bash
cogstim ans --ratios easy
```

**What it produces:** 10 training sets with two-colour dot arrays (yellow and blue), organised by the dominant colour. Half of the images have equalized total surfaces; the other half use random dot sizes.

## Key Tips

### Reproducibility

Use `--seed` with an integer value to make your generation deterministic and reproducible:

```bash
cogstim shapes --train-num 10 --test-num 5 --seed 1234
```

If you do not pass one, a seed is drawn for you and recorded, so a run is
reproducible even when you did not plan for it. Every run writes the options it
used to `cogstim_config.yaml` in the output directory, and you can repeat it
exactly with:

```bash
cogstim run images/shapes/cogstim_config.yaml
```

### Understanding Image Sets

The `--train-num` and `--test-num` options specify the number of **sets**, not
individual images. A set is one sweep of every condition the paradigm defines,
so a set is many images. With the default options:

- **shapes/colours:** 200 images per set
- **ans:** 112 images per set
- **match-to-sample:** 192 images per set (96 sample/match pairs)
- **lines:** 36 images per set
- **one-colour:** 10 images per set

These figures change with the options you pass. To see the exact count for a
command before it writes anything:

```bash
cogstim shapes --train-num 10 --test-num 5 --dry-run
```

### Quick Preview

Use `--demo` to generate a small preview dataset (8 training sets) without specifying counts:

```bash
cogstim shapes --demo
```

This is helpful for quickly checking output before generating larger datasets.

## What's Next?

- **[User Guide](guide.md)** – Detailed documentation for each task with all options
- **[Options reference](options.md)** – Every option of every task, generated from the CLI
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

