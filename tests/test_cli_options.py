"""Tests that keep the command-line interface internally consistent.

Reviewer @srvanderplas rejected the CLI as inconsistent in JOSS review
openjournals/joss-reviews#10532: the same concept was spelled differently in
different subcommands, size options carried no units, and the same flag meant
different things depending on where you met it. Fixing that once is not enough
-- nothing stopped it recurring. These tests encode the naming rules so that a
new option or subcommand that breaks them fails CI.
"""

import argparse
import re

import pytest

from cogstim.cli import create_parser
from cogstim.helpers import cli_options as opts
from cogstim.helpers.cli_options import Option


def subcommand_parsers():
    """Return {subcommand name: parser} for every registered subcommand."""
    parser = create_parser()
    sub = [a for a in parser._actions if isinstance(a, argparse._SubParsersAction)][0]
    return dict(sub.choices)


def actions_of(parser):
    """Return the real options of a parser, excluding argparse's own --help."""
    return [a for a in parser._actions
            if a.dest != "help" and a.option_strings]


# 'run' replays a saved configuration instead of generating stimuli of its own,
# so the naming rules for stimulus options do not apply to it.
NON_STIMULUS_SUBCOMMANDS = {"run"}

SUBCOMMANDS = sorted(set(subcommand_parsers()) - NON_STIMULUS_SUBCOMMANDS)


def stimulus_parsers():
    """Subcommand parsers that actually generate stimuli."""
    return {
        name: parser
        for name, parser in subcommand_parsers().items()
        if name not in NON_STIMULUS_SUBCOMMANDS
    }

# Options predating the naming rules whose spelling is fixed by other concerns.
# Kept explicit so the exemption is a decision on the record, not an oversight.
NAMING_EXEMPT = {
    "--output-dir", "--img-size", "--img-format", "--seed", "--version-tag",
    "--verbose", "--quiet", "--dry-run", "--demo", "--ratios", "--layout",
    "--gap", "--tasks-csv", "--tasks-copies", "--train-num", "--test-num",
    "--shapes", "--colours", "--shape", "--types", "--all-types", "--angles",
    "--tolerance", "--abs-tolerance", "--attempts-limit", "--no-jitter",
    "--random-rotation",
}


@pytest.mark.parametrize("name", SUBCOMMANDS)
def test_subcommand_defines_no_options_of_its_own(name):
    """Every option must come from the registry, not from an inline definition.

    This is the property that keeps the rest of these tests meaningful: an
    option defined inline inside a setup_*_subcommand() would escape the
    registry and could reintroduce any of the inconsistencies below.
    """
    registry_flags = set()
    for value in vars(opts).values():
        if isinstance(value, Option):
            registry_flags.update([value.name, *value.aliases])
        elif isinstance(value, list) and value and isinstance(value[0], Option):
            for option in value:
                registry_flags.update([option.name, *option.aliases])

    parser = subcommand_parsers()[name]
    for action in actions_of(parser):
        for flag in action.option_strings:
            assert flag in registry_flags, (
                f"{name} defines {flag} outside cli_options.py. "
                "Declare it in the registry so it stays consistent with the rest."
            )


@pytest.mark.parametrize("name", SUBCOMMANDS)
def test_colour_options_follow_one_pattern(name):
    """Colour options must be --<element>-colour, optionally numbered.

    Previously ans used --dot-colour1 while mask used --dot-colour-2 for the
    very same concept.
    """
    pattern = re.compile(r"^--[a-z]+(-[a-z]+)*-colours?(-[1-9])?$")
    parser = subcommand_parsers()[name]
    for action in actions_of(parser):
        flag = action.option_strings[0]
        if "colour" not in flag:
            continue
        assert pattern.match(flag), (
            f"{name}{flag} does not match --<element>-colour[-N]. "
            "Numbered colours use a separator, e.g. --dot-colour-1."
        )


@pytest.mark.parametrize("name", SUBCOMMANDS)
def test_pixel_options_declare_their_unit(name):
    """Options measuring a pixel distance must end in -px.

    Fixation said --cross-thickness-px while lines said --min-thickness for the
    same kind of quantity, leaving the user to guess the unit.
    """
    parser = subcommand_parsers()[name]
    for action in actions_of(parser):
        flag = action.option_strings[0]
        if flag in NAMING_EXEMPT:
            continue
        if not re.search(r"(radius|thickness|spacing|arm|jitter)", flag):
            continue
        assert flag.endswith("-px"), (
            f"{name}{flag} measures pixels but does not say so; it should end in -px"
        )


def test_same_flag_means_the_same_thing_everywhere():
    """A flag shared by several subcommands must agree on arity and choices.

    --colours took one value in shapes, two in colours and any number in
    custom, so the same command line meant three different things.
    """
    seen = {}
    problems = []
    for name, parser in stimulus_parsers().items():
        for action in actions_of(parser):
            flag = action.option_strings[0]
            signature = (action.nargs, tuple(action.choices) if action.choices else None)
            if flag in seen:
                other_name, other_signature = seen[flag]
                if other_signature != signature:
                    field = "nargs" if other_signature[0] != signature[0] else "choices"
                    index = 0 if field == "nargs" else 1
                    problems.append(
                        f"{flag}: {other_name} has {field}={other_signature[index]} "
                        f"but {name} has {field}={signature[index]}"
                    )
            else:
                seen[flag] = (name, signature)
    assert not problems, "Same flag, different meaning:\n  " + "\n  ".join(problems)


def test_every_stimulus_task_can_set_its_colour():
    """No task may leave the colour of its stimulus unconfigurable.

    `lines` had no colour option at all, so its stripes were drawn white on a
    white default background, producing blank images.
    """
    missing = []
    for name, parser in stimulus_parsers().items():
        flags = [f for a in actions_of(parser) for f in a.option_strings]
        stimulus_colours = [
            f for f in flags if "colour" in f and f != "--background-colour"
        ]
        if not stimulus_colours:
            missing.append(name)
    assert not missing, (
        f"These tasks cannot have their stimulus colour set: {missing}"
    )


@pytest.mark.parametrize("name", SUBCOMMANDS)
def test_stimulus_colour_differs_from_background_by_default(name):
    """Defaults must produce a visible stimulus.

    `cogstim lines` drew white stripes on the default white background, so the
    out-of-the-box output was blank images.
    """
    parser = subcommand_parsers()[name]
    defaults = {a.dest: a.default for a in actions_of(parser)}
    background = defaults.get("background_colour")

    for action in actions_of(parser):
        flag = action.option_strings[0]
        if "colour" not in flag or flag == "--background-colour":
            continue
        value = action.default
        if value is None:
            continue
        values = value if isinstance(value, list) else [value]
        assert background not in values, (
            f"{name}{flag} defaults to {background}, the same as the background, "
            "so the default output would be invisible"
        )


# Constraints rather than range endpoints: a floor the layout must respect, not
# one end of a span to sample from. There is no meaningful maximum to pair them
# with, so requiring one would mean inventing a feature to satisfy a rule.
UNPAIRED_MINIMUMS = {"--min-line-spacing-px"}


def test_min_and_max_options_come_in_pairs():
    """A --min-X should have a --max-X, so ranges are always fully controllable."""
    problems = []
    for name, parser in stimulus_parsers().items():
        flags = {a.option_strings[0] for a in actions_of(parser)}
        for flag in flags:
            if not flag.startswith("--min-") or flag in UNPAIRED_MINIMUMS:
                continue
            counterpart = flag.replace("--min-", "--max-", 1)
            if counterpart not in flags:
                problems.append(f"{name}: {flag} has no {counterpart}")
    assert not problems, "Unpaired range options:\n  " + "\n  ".join(problems)


def test_deprecated_aliases_still_work_and_warn():
    """Renamed options keep accepting their old spelling, with a warning.

    Renaming without this would break every existing script, including the
    reviewers' own.
    """
    parser = create_parser()
    aliased = [
        option
        for value in vars(opts).values()
        for option in (value if isinstance(value, list) else [value])
        if isinstance(option, Option) and option.aliases
    ]
    if not aliased:
        pytest.skip("No deprecated aliases declared yet")

    for option in aliased:
        for alias in option.aliases:
            assert alias != option.name, f"{alias} is not an alias of anything"


# ---------------------------------------------------------------------------
# The property the naming rules exist to protect
# ---------------------------------------------------------------------------

DEFAULT_RUN_ARGS = {
    "shapes": ["--train-num", "1", "--test-num", "0",
               "--min-surface", "10000", "--max-surface", "10200"],
    "colours": ["--train-num", "1", "--test-num", "0",
                "--min-surface", "10000", "--max-surface", "10200"],
    "ans": ["--train-num", "1", "--test-num", "0",
            "--min-dot-num", "1", "--max-dot-num", "2"],
    "one-colour": ["--train-num", "1", "--test-num", "0",
                   "--min-dot-num", "1", "--max-dot-num", "2"],
    "match-to-sample": ["--train-num", "1", "--test-num", "0",
                        "--min-dot-num", "2", "--max-dot-num", "4"],
    "lines": ["--train-num", "1", "--test-num", "0", "--angles", "0"],
    "fixation": ["--types", "B"],
    "mask": ["--mask-num", "1"],
    "custom": ["--train-num", "1", "--test-num", "0",
               "--shapes", "circle", "--shape-colours", "red",
               "--min-surface", "10000", "--max-surface", "10200"],
}


@pytest.mark.parametrize("subcommand", sorted(DEFAULT_RUN_ARGS))
@pytest.mark.parametrize("background", ["white", "black"])
def test_default_options_produce_a_visible_stimulus(tmp_path, subcommand, background):
    """Running a task with default colours must not produce blank images.

    `cogstim lines` drew white stripes on the default white background, and
    `cogstim fixation --all-types` drew white symbols on white, so both wrote
    entirely blank images out of the box. @srvanderplas reported the first;
    the second had gone unnoticed. Checking both backgrounds also covers the
    inverse mistake, where a fix for white breaks black.
    """
    import subprocess
    import sys

    from PIL import Image

    out = tmp_path / subcommand
    result = subprocess.run(
        [sys.executable, "-m", "cogstim.cli", subcommand,
         *DEFAULT_RUN_ARGS[subcommand],
         "--background-colour", background,
         "--seed", "7", "--output-dir", str(out)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert result.returncode == 0, f"{subcommand} failed:\n{result.stderr}"

    images = sorted(out.rglob("*.png"))
    assert images, f"{subcommand} generated no images"

    for path in images[:3]:
        with Image.open(path) as img:
            colours = img.convert("RGB").getcolors(maxcolors=1_000_000)
        assert len(colours) > 1, (
            f"{subcommand} on a {background} background produced a blank "
            f"single-colour image: {path.name}"
        )


# ---------------------------------------------------------------------------
# Deprecations
# ---------------------------------------------------------------------------

def test_every_deprecated_alias_still_parses():
    """Renaming must not break existing scripts, including the reviewers' own."""
    import warnings

    parser = create_parser()
    aliased = [
        option
        for value in vars(opts).values()
        for option in (value if isinstance(value, list) else [value])
        if isinstance(option, Option) and option.aliases
    ]
    assert aliased, "Expected some options to carry deprecated aliases"

    for option in aliased:
        for alias in option.aliases:
            # Find a task that offers this option, and a value it accepts.
            for name, sub in stimulus_parsers().items():
                action = next(
                    (a for a in actions_of(sub) if alias in a.option_strings), None
                )
                if action is None:
                    continue
                value = str(action.choices[0]) if action.choices else "1"
                argv = [name, alias] + ([] if action.nargs == 0 else [value])
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always")
                    parsed = parser.parse_args(argv)
                assert getattr(parsed, action.dest) is not None
                assert any(
                    issubclass(w.category, DeprecationWarning) for w in caught
                ), f"{alias} should warn that it is deprecated"
                break


def test_legacy_python_entry_points_warn():
    """Legacy API kept for compatibility must announce that it is going away."""
    import warnings

    from cogstim.generators.dots_one_colour import DotsOneColourGenerator

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            DotsOneColourGenerator({"output_dir": ".", "img_format": "png"})
        except Exception:
            pass
    assert any(issubclass(w.category, DeprecationWarning) for w in caught), (
        "DotsOneColourGenerator should warn that it is deprecated"
    )
