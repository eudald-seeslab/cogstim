"""Tests for reproducing a generation run from its recorded configuration.

Reviewer @srvanderplas argued in JOSS review openjournals/joss-reviews#10532
that a bare command line gives no assurance that what was generated is
recorded. Every run now writes the configuration it used, including a seed
drawn on its behalf when none was given, and `cogstim run` replays it.
"""

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from cogstim.helpers.run_config import CONFIG_FILENAME, argv_from_config


def run_cli(*argv):
    """Invoke the CLI in a subprocess and return the completed process."""
    result = subprocess.run(
        [sys.executable, "-m", "cogstim.cli", *map(str, argv)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert result.returncode == 0, f"CLI failed:\n{result.stdout}\n{result.stderr}"
    return result


def digest(directory):
    """Map image filename to content hash, for comparing two runs."""
    return {
        path.name: hashlib.md5(path.read_bytes()).hexdigest()
        for path in sorted(Path(directory).rglob("*.png"))
    }


BASE_ARGS = ["one-colour", "--train-num", 1, "--test-num", 0,
             "--min-dot-num", 1, "--max-dot-num", 3]


def test_run_records_its_configuration(tmp_path):
    """A generation writes the options it used next to its output."""
    run_cli(*BASE_ARGS, "--seed", 4321, "--output-dir", tmp_path)

    config_path = tmp_path / CONFIG_FILENAME
    assert config_path.exists(), "Every run must record how it was produced"

    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert config["task"] == "one-colour"
    assert config["options"]["seed"] == 4321
    assert config["cogstim_version"]


def test_seed_is_recorded_even_when_not_supplied(tmp_path):
    """A run started without --seed is still reproducible afterwards.

    Previously no seed was set at all in that case, so such a run could never
    be repeated -- a problem for stimuli that end up in a published experiment.
    """
    run_cli(*BASE_ARGS, "--output-dir", tmp_path)

    config = yaml.safe_load((tmp_path / CONFIG_FILENAME).read_text(encoding="utf-8"))
    assert isinstance(config["options"]["seed"], int)


def test_replaying_a_config_reproduces_the_images(tmp_path):
    """`cogstim run` on a recorded config reproduces the run byte for byte."""
    first = tmp_path / "first"
    second = tmp_path / "second"

    # Deliberately no --seed: the interesting case is reproducing a run the
    # user never made reproducible themselves.
    run_cli(*BASE_ARGS, "--output-dir", first)
    run_cli("run", first / CONFIG_FILENAME, "--output-dir", second)

    original, replayed = digest(first), digest(second)
    assert original, "The first run produced no images"
    assert original == replayed, "Replaying the configuration changed the output"


def test_replay_uses_canonical_flags(tmp_path):
    """Replay must not go through deprecated option spellings.

    dest names and flags no longer correspond one-to-one, so deriving a flag by
    replacing underscores would silently resurrect the deprecated names.
    """
    run_cli(*BASE_ARGS, "--seed", 99, "--output-dir", tmp_path)
    argv = argv_from_config(tmp_path / CONFIG_FILENAME)

    assert argv[0] == "one-colour"
    for deprecated in ("--min-point-num", "--max-point-num",
                       "--min-point-radius", "--max-point-radius"):
        assert deprecated not in argv, (
            f"Replay would use the deprecated flag {deprecated}"
        )


def test_unknown_option_in_config_is_rejected(tmp_path):
    """A config naming an option the task does not have fails clearly."""
    config = tmp_path / "bad.yaml"
    config.write_text(
        yaml.safe_dump({"task": "one-colour", "options": {"not_an_option": 1}}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="not an option"):
        argv_from_config(config)


def test_config_without_a_task_is_rejected(tmp_path):
    """A config that does not say what to generate fails clearly."""
    config = tmp_path / "bad.yaml"
    config.write_text(yaml.safe_dump({"options": {"train_num": 1}}), encoding="utf-8")
    with pytest.raises(ValueError, match="does not name a task"):
        argv_from_config(config)
