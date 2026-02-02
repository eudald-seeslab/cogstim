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
  - name: Innovamat Education, Sant Cugat del Vallès, Catalonia (Spain)
    index: 1
date: 2025-11-08
bibliography: paper.bib
---

# Summary

CogStim is an open‑source Python library for reproducible, parameterized offline generation of visual stimuli for psychology, neuroscience, and computer vision. It produces PNG/JPEG/SVG assets for common paradigms (two‑colour ANS arrays, match‑to‑sample pairs with optional total‑area equalization, single‑colour dot arrays, geometric shapes, oriented lines/stripes, and fixation targets). Deterministic seeding and robust geometric routines enforce non‑overlap, boundary validity, and equalization to minimise perceptual confounds. A compact Python API and command‑line interface make the tool accessible to both programmers and non‑programmers, enabling quick creation of controlled stimuli without special setup.

# Statement of need

Designing visual stimuli is a routine requirement in psychology, neuroscience, and vision research. It requires precise control over numerosity, size, spacing, color, and layout, alongside reproducible randomization and strict study dependent constraints. When built ad hoc, these demands make stimulus creation tedious and can introduce small inconsistencies that affect comparisons across studies and model evaluations. Researchers therefore benefit from a simple way to generate controlled stimuli offline as standard image assets ready to use wherever needed.

CogStim addresses this need by providing an offline, parameterized generator for a range of paradigms: Approximate Number System (ANS) [@halberda_individual_2008], Match‑To‑Sample (MTS) [@sella_enumeration_2013], geometric shapes, oriented lines [@srinivasan_vision_2021], and fixation targets [@thaler_what_2013]. It produces images in any major image format (e.g. PNG, JPEG, SVG) that can be dropped into experiment builders, web or desktop presentation software, and computer‑vision pipelines without heavy setup. A Python API and a command‑line interface enable both quick prototyping and large batch generation; deterministic seeds ensure the same configuration yields identical outputs; and built‑in algorithms enforce non‑overlap and allow total‑area equalization when required. In this way the library serves dual needs: controlled stimuli for behavioral and neuro‑cognitive experiments, and well‑specified synthetic datasets for model development and evaluation.

# State of the field

Several established frameworks dominate the landscape of behavioral research: `PsychoPy` [@peirce_psychopy2_2019] is the standard Python library for experiment creation, offering precise timing and a vast array of stimuli; `Psychtoolbox` [@brainard_psychophysics_1997] provides similar capabilities within the MATLAB/C environment with a focus on low-level hardware control; and `jsPsych` [@de_leeuw_jspsych_2015] has become the de facto standard for web-based behavioral experiments. These tools are designed primarily as runtime engines: they generate and render stimuli in real-time during the experimental loop, coupling the stimulus generation logic with the display backend.

CogStim was built rather than contributing to these existing projects for several strategic reasons. First, it decouples generation from presentation. While engines like PsychoPy are powerful, automating them to batch-export thousands of static images for external use (e.g., training a neural network or loading onto a tablet) often requires hacking the windowing system or running “headless” modes that are resource-intensive. CogStim is lightweight and backend-agnostic by design, treating file export as a first-class citizen. Second, CogStim fills a specific niche regarding algorithmic validity: it prioritizes the construction logic of the stimulus (e.g., ensuring area equalization in ANS arrays or preventing overlap in crowded scenes) over the rendering speed required for runtime presentation. Finally, by producing standard assets (PNG/SVG) rather than experiment code, it ensures interoperability; the resulting datasets can be deployed across different platforms, from a custom web app to machine learning pipelines, making CogStim a more versatile tool for researchers.


# Software design

CogStim architecture prioritizes modularity and simplicity to remain accessible to researchers with varying programming expertise. We adopted a template method pattern where a base generator class handles infrastructure concerns—such as file I/O, directory structure, and random seed management—while specialized subclasses focus solely on the geometric logic of specific stimuli. This design decouples the "how" of file management from the "what" of stimulus creation, allowing researchers to extend the library with new generators without navigating complex boilerplate code.

To ensure efficiency and maintainability, we minimized external dependencies, relying only on NumPy for vectorised geometric calculations and Pillow for rasterization. This lightweight footprint enables headless execution on servers or CI/CD pipelines, a trade-off we favoured over including heavy GUI dependencies often found in rendering engines.

# Research impact statement

CogStim has demonstrated its utility in diverse research contexts, bridging behavioral science and computational modeling. It has been used to generate stimuli for psychometric assessments in educational settings [@correig-fraga_development_2024; @correig-fraga_interplay_2025] and to create synthetic datasets for evaluating visual computation models in neuroscience (under review). These applications validate the library's capability to support both traditional psychological experiments and modern data-driven approaches.

To facilitate broad community adoption and ensure long-term reliability, CogStim adheres to rigorous software engineering standards. It includes a comprehensive test suite, continuous integration (CI) pipelines, and is distributed via PyPI under a permissive MIT license. Recognizing the varying technical expertise in the field, the project features a novel documentation strategy: an LLM-optimized manual designed to help non-programmers generate complex CLI commands via natural language prompting. This combination of robust engineering and accessibility effectively democratizes access to rigorous stimulus generation, ensuring that high-quality, reproducible stimuli are available to the wider research community.

# Software description

## Design and key features

- **Task coverage**: ANS two-colour dot arrays; single-colour dot arrays; MTS pairs with optional area equalization; geometric shapes (circle, star, triangle, square); oriented line/stripe patterns; fixation targets.
- **Determinism & reproducibility**: global seed handling for Python/NumPy; same parameters and same seed will yield identical images.
- **Robust dot engine**: `DotsCore` enforces non-overlap, boundary validity, optional area equalization, and (for MTS) pair equalization within tolerances. 
- **Stimulus equalization algorithms**: CogStim implements robust geometric equalization methods that adjust dot radii so that total surface areas are matched either within two-colour ANS arrays or between sample–match pairs. These procedures guarantee perceptually fair stimuli for numerosity and matching tasks, maintaining non-overlap and boundary validity while achieving precise area ratios within configurable tolerances.
- **CLI & Python API**: consistent configuration via dictionaries in code and ergonomic subcommands in the CLI.

## Implementation and dependencies
CogStim is implemented in Python ($\ge$ 3.10) [@python] and builds upon a small number of widely used open-source libraries. Image creation and drawing operations are handled through Pillow [@clark2015pillow], while all geometric computations and randomization routines rely on NumPy [@harris2020array]. The library uses tqdm [@tqdm] to provide progress bars during generation processes and adopts standard Python modules such as argparse for command-line interfaces and pytest for automated testing.

The codebase is organized around a small set of generator classes that call these dependencies through a unified interface. Each generator defines the parameters of a particular task (e.g., ANS, MTS, shapes, lines, fixation) and uses Pillow for rendering, NumPy for geometric calculations, and tqdm for user feedback. This results in a lightweight, portable implementation that can run on any system supporting Python without special dependencies or graphical backends.

All dependencies are open source, actively maintained, and available through the Python Package Index (PyPI), ensuring long-term accessibility and compatibility with typical research workflows. The project is licensed under MIT, and available as a Git repository in Github.

# Example figures

![Representative stimuli generated by CogStim.\label{fig:stimuli}](stimuli_panel.png)

**Figure 1.** Representative stimuli generated by CogStim across different task paradigms. **(a, b)** Approximate Number System (ANS) two-colour dot arrays for numerosity discrimination tasks, with (b) showing area-equalized dots between colours. **(c, d)** Single geometric shapes (circle) in different colours, used in shape discrimination tasks. **(e, f)** Single-colour dot arrays suitable for numerosity estimation, match-to-sample (MTS) paradigms, or as components in multi-feature discrimination tasks. **(g, h)** Oriented line/stripe patterns for orientation discrimination experiments. **(i, j, k)** Additional geometric shapes (square, star, triangle) in various colours, demonstrating the library's shape generation capabilities for categorical perception and visual search tasks. **(l)** Fixation cross stimulus for experimental trial preparation and gaze control.

# Availability

- Repository: https://github.com/eudald-seeslab/cogstim
- License: MIT
- Issue tracker: enabled and publicly readable
- Archive: upon acceptance, we will create a tagged release, archive on Zenodo and include the DOI here.

# Acknowledgements

We thank Innovamat Education for their support in the development of this open source work.

# AI usage disclosure

The core architecture and foundational algorithms of CogStim were developed prior to the widespread adoption of generative AI tools. However, during recent development cycles, AI assistants were utilized to assist in refactoring legacy code, homogenizing interfaces across generator modules, and expanding specific functionalities to ensure consistency. Regarding this manuscript, generative AI tools were employed to review and refine the English language and narrative flow. The authors have manually verified all AI-generated suggestions and retain full responsibility for the accuracy and integrity of both the software and the publication.

# Conflicts of Interest

Authors declare no competing interests.

# References

