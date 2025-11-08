---
title: "CogStim: Reproducible visual stimulus generation for cognitive science, neuroscience, and vision research"
tags:
  - Python
  - cognitive science
  - neuroscience
  - psychophysics
  - computer vision
authors:
  - name: Eudald Correig-Fraga
    orcid: 0000-0001-8556-0469
    affiliation: 1
affiliations:
  - name: Innovamat Educaiton SL, Barcelona, Catalonia (Spain)
    index: 1
date: 2025-11-08
bibliography: paper.bib
---

# Summary

**CogStim** is a Python library to generate *reproducible*, parameterized image datasets of visual stimuli for research in cognitive science, neuroscience, psychophysics, and machine learning. It produces images for common experimental paradigms – including two-colour dot arrays for Approximate Number System (ANS) numerosity tasks, single-colour dot arrays, match-to-sample (MTS) pairs with optional area equalization, geometric shapes, oriented line/stripe patterns, and fixation targets – and organizes outputs into standard `train/` and `test/` directories by class. A unified Python API and a comprehensive CLI enable deterministic generation via random seeds, facilitating transparent, replicable pipelines and dataset versioning.

# Statement of need

Designing visual stimuli is a routine requirement in psychology, neuroscience, and vision research. It requires precise control over numerosity, size, spacing, color, and layout, alongside reproducible randomization and strict study dependent constraints. When built ad hoc, these demands make stimulus creation tedious and can introduce small inconsistencies that affect comparisons across studies and model evaluations. Researchers therefore benefit from a simple way to generate controlled stimuli offline as standard image assets ready to use wherever needed.

CogStim addresses this need by providing an offline, parameterized generator for a range of paradigms: approximate number system [@halberda_individual_2008], match‑to‑sample [@sella_enumeration_2013], geometric shapes, oriented lines [@srinivasan_vision_2021], and fixation targets [@thaler_what_2013]. It produces images in any major image format (e.g. PNG, JPEG, SVG) that can be dropped into experiment builders, web or desktop presentation software, and computer‑vision pipelines without heavy setup. A Python API and a command‑line interface enable both quick prototyping and large batch generation; deterministic seeds ensure the same configuration yields identical outputs; and built‑in algorithms enforce non‑overlap and allow total‑area equalization when required. In this way the library serves dual needs: controlled stimuli for behavioral and neuro‑cognitive experiments, and well‑specified synthetic datasets for model development and evaluation.

CogStim provides a single, extensible library that:
1. covers widely used paradigms (ANS, MTS, shapes, orientation discrimination, fixation).
1. guarantees determinism via seed control and consistent planning logic.
1. outputs ready‑to‑use datasets with standard train/test splits and stable file names.
1. offers both a CLI and a Python API, minimizing ramp‑up time for non‑specialists.
1. implements stimulus equalization algorithms that balance total surface areas within or between dot arrays, ensuring fair comparisons in numerosity and match‑to‑sample tasks.
1. supports common image formats, including PNG and JPEG via a configurable img_format parameter, and SVG for vector export.
1. reduces manual stimulus‑creation effort by automating parameter sweeps, placement rules, and file organization.

The library is designed for: (i) behavioral and neuro‑cognitive tasks such as numerosity discrimination, (ii) model evaluation in computational neuroscience and computer vision, and (iii) dataset creation for machine‑learning workflows that require well‑controlled synthetic stimuli. It is equally accessible to users with and without programming experience, thanks to its dual API/CLI design and comprehensive documentation, which includes an LLM-optimized manual that users can feed to their LLM's of preference to generate the instructions needed to create their stimuli.

# State of the field & relation to similar software

General‑purpose experiment frameworks such as PsychoPy, Psychtoolbox, and jsPsych focus on stimulus presentation and timing during runtime, while various domain‑specific generators target single paradigms. CogStim complements these tools by producing offline, parameterized image assets that drop into any workflow with minimal setup. It emphasizes reproducibility through explicit seeding and systematic parameter sweeps, and it reduces perceptual confounds via robust non‑overlap placement, boundary checks, and stimulus equalization for numerosity and match‑to‑sample tasks. The library spans multiple paradigms (ANS, MTS, geometric shapes, oriented lines, fixation targets) and exports PNG, JPEG, and SVG for portability across experimental platforms and computer‑vision pipelines. A dual interface (command line and Python API), together with documentation tailored for LLM‑assisted use, makes it accessible to both programmers and non‑programmers and provides a clear template for extending to new stimulus classes.

> This library has been used both for the creation of psychometric tests for children [@correig-fraga_development_2024] [@correig-fraga_interplay_2025], as well as for computer vision tasks [@correig-fraga_structure_nodate].

# Software description

## Design and key features

- **Task coverage**: ANS two-colour dot arrays; single-colour dot arrays; MTS pairs with optional area equalization; geometric shapes (circle, star, triangle, square); oriented line/stripe patterns; fixation targets.  
- **Determinism & reproducibility**: global seed handling for Python/NumPy; same parameters + same seed ⇒ identical images.  
- **Robust dot engine**: `DotsCore` enforces non-overlap, boundary validity, optional area equalization, and (for MTS) pair equalization within tolerances. 
- **Stimulus equalization algorithms**: CogStim implements robust geometric equalization methods that adjust dot radii so that total surface areas are matched either within two-colour ANS arrays or between sample–match pairs. These procedures guarantee perceptually fair stimuli for numerosity and matching tasks, maintaining non-overlap and boundary validity while achieving precise area ratios within configurable tolerances.
- **CLI & Python API**: consistent configuration via dictionaries in code and ergonomic subcommands in the CLI.

##Implementation and dependencies
CogStim is implemented in Python (≥3.10) [@python] and builds upon a small number of widely used open-source libraries. Image creation and drawing operations are handled through Pillow [@clark2015pillow], while all geometric computations and randomization routines rely on NumPy [@harris2020array]. The library uses tqdm [@tqdm] to provide progress bars processes and adopts standard Python modules such as argparse for command-line interfaces and pytest for automated testing.

The codebase is organized around a small set of generator classes that call these dependencies through a unified interface. Each generator defines the parameters of a particular task (e.g., ANS, match-to-sample, shapes, lines, fixation) and uses Pillow for rendering, NumPy for geometric calculations, and tqdm for user feedback. This results in a lightweight, portable implementation that can run on any system supporting Python without special dependencies or graphical backends.

All dependencies are open source, actively maintained, and available through the Python Package Index (PyPI), ensuring long-term accessibility and compatibility with typical research workflows.

## Implementation & dependencies
- **Language**: Python (≥3.10)  
- **Core deps**: Pillow (image generation), NumPy (numerics), tqdm (progress).  
- **License**: MIT (OSI-compliant).  
- **Repository**: public Git repository with browsable source and open issue tracker.


## Example figures

![Representative stimuli generated by CogStim.\label{fig:stimuli}](stimuli_panel.png)

**Figure 1.** Representative stimuli generated by CogStim across different task paradigms. **(a, b)** Approximate Number System (ANS) two-colour dot arrays for numerosity discrimination tasks, with (b) showing area-equalized dots between colours. **(c, d)** Single geometric shapes (circle) in different colours, used in shape discrimination tasks. **(e, f)** Single-colour dot arrays suitable for numerosity estimation, match-to-sample (MTS) paradigms, or as components in multi-feature discrimination tasks. **(g, h)** Oriented line/stripe patterns for orientation discrimination experiments. **(i, j, k)** Additional geometric shapes (square, star, triangle) in various colours, demonstrating the library's shape generation capabilities for categorical perception and visual search tasks. **(l)** Fixation cross stimulus for experimental trial preparation and gaze control.

## Availability

- Repository: https://github.com/eudald-seeslab/cogstim
- License: MIT
- Issue tracker: enabled and publicly readable
- Archive: upon acceptance, we will create a tagged release, archive on Zenodo and include the DOI here.

## Acknowledgements

We thank Innovamat Education for their support in the development of this open source work.

## Conflicts of Interest

Authors declare no competing interests.

## References

