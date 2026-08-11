#!/usr/bin/env python3
"""Reading and writing the configuration of a generation run.

Reviewer @srvanderplas argued for configuration files over bare command lines
in JOSS review openjournals/joss-reviews#10532:

    "I think YML would be a better choice, because it would preserve the
    generation options for experimental reproducibility purposes. [...] This
    ensures that users are encouraged to generate stimuli reproducibly and in a
    way that ensures that the documentation of what was generated is recorded;
    simple command-line execution does not provide this assurance."

Both halves of that are handled here. ``cogstim run config.yaml`` generates
from a file, and *every* run -- including plain command-line ones -- writes the
configuration it actually used next to its output, with the resolved seed. So
the record exists whether or not the user opted into config files.
"""

import argparse
from pathlib import Path
from typing import Any, Dict, List

CONFIG_FILENAME = "cogstim_config.yaml"

# Options that describe where and how to run rather than what to generate, so
# replaying a config does not drag along the original machine's paths or noise.
NON_STIMULUS_OPTIONS = {
    "func", "task", "quiet", "verbose", "dry_run", "demo", "output_dir",
}


def _require_yaml():
    """Import PyYAML, with an actionable message when it is missing."""
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - depends on the environment
        raise ImportError(
            "Reading and writing run configurations needs PyYAML. "
            "Install it with 'pip install pyyaml', or reinstall cogstim."
        ) from exc
    return yaml


def _package_version() -> str:
    try:
        from importlib.metadata import version

        return version("cogstim")
    except Exception:  # pragma: no cover - editable installs without metadata
        return "unknown"


def config_from_args(args: argparse.Namespace, seed: int) -> Dict[str, Any]:
    """Build the record of a run from its parsed arguments.

    Args:
        args: Parsed CLI arguments.
        seed: The seed actually used, which may have been drawn rather than given.

    Returns:
        dict: A mapping suitable for writing to YAML and replaying later.
    """
    options = {
        key: value
        for key, value in vars(args).items()
        if key not in NON_STIMULUS_OPTIONS
    }
    options["seed"] = seed

    return {
        "cogstim_version": _package_version(),
        "task": args.task,
        "options": dict(sorted(options.items())),
    }


def write_run_config(output_dir: str, args: argparse.Namespace, seed: int) -> str:
    """Write the configuration a run used into its output directory.

    Args:
        output_dir: Directory the images were written to.
        args: Parsed CLI arguments.
        seed: The seed actually used.

    Returns:
        str: Path of the file written.
    """
    yaml = _require_yaml()

    path = Path(output_dir) / CONFIG_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        yaml.safe_dump(
            config_from_args(args, seed), handle, sort_keys=False, allow_unicode=True
        )
    return str(path)


def canonical_flags_for(task: str) -> Dict[str, str]:
    """Map each option's dest to its canonical flag for one task.

    Args:
        task: Subcommand name.

    Returns:
        dict: {dest: canonical flag}.

    Raises:
        ValueError: If the task is not a cogstim subcommand.
    """
    # Imported here because cogstim.cli imports this module.
    from cogstim.cli import create_parser

    parser = create_parser()
    subparsers = [
        action for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    ][0]

    if task not in subparsers.choices:
        raise ValueError(
            f"'{task}' is not a cogstim task. Available: "
            + ", ".join(sorted(subparsers.choices))
        )

    return {
        action.dest: action.option_strings[0]
        for action in subparsers.choices[task]._actions
        if action.option_strings
    }


def argv_from_config(path: str) -> List[str]:
    """Turn a saved configuration back into command-line arguments.

    Replaying through the normal parser, rather than feeding the mapping
    straight to a generator, means a config file gets exactly the same
    validation, defaults and deprecation handling as a typed command.

    Args:
        path: Path to a YAML configuration.

    Returns:
        list: Arguments to pass to the CLI parser, starting with the task name.

    Raises:
        ValueError: If the file is not a valid cogstim configuration.
    """
    yaml = _require_yaml()

    with open(path, encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"{path} does not contain a cogstim configuration")

    task = data.get("task")
    if not task:
        raise ValueError(
            f"{path} does not name a task. Expected a top-level 'task:' key, "
            "for example 'task: shapes'."
        )

    options = data.get("options") or {}
    if not isinstance(options, dict):
        raise ValueError(f"'options' in {path} must be a mapping of option to value")

    flags = canonical_flags_for(task)

    argv: List[str] = [task]
    for key, value in options.items():
        # dest names no longer match their flags one-to-one; deriving the flag by
        # replacing underscores would emit the deprecated spellings.
        flag = flags.get(key)
        if flag is None:
            raise ValueError(
                f"'{key}' in {path} is not an option of the '{task}' task"
            )
        if isinstance(value, bool):
            if value:
                argv.append(flag)
        elif value is None:
            continue
        elif isinstance(value, (list, tuple)):
            argv.append(flag)
            argv.extend(str(item) for item in value)
        else:
            argv.extend([flag, str(value)])
    return argv
