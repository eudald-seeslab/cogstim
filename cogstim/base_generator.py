from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Mapping, MutableMapping, Optional, Sequence, Union


RelativePath = Union[str, Path, Sequence[Union[str, Path]]]


class BaseGenerator(ABC):
    """Shared functionality for stimulus generators.

    The base class encapsulates common concerns such as configuration storage,
    output directory resolution, and directory creation helpers. Subclasses are
    expected to implement the :meth:`generate_images` method and may extend
    :meth:`setup_directories` as needed while reusing the provided utilities.
    """

    #: Keys that may contain an output directory in a configuration mapping.
    OUTPUT_DIR_KEYS: Sequence[str] = ("output_dir", "IMG_DIR")

    def __init__(
        self,
        config: Optional[MutableMapping[str, object]] = None,
        output_dir: Optional[Union[str, Path]] = None,
    ) -> None:
        self.config: MutableMapping[str, object] = config or {}
        self.output_dir: Path = self._resolve_output_dir(output_dir)
        self.output_paths: Dict[str, Path] = {}

    # ------------------------------------------------------------------
    # Directory helpers
    # ------------------------------------------------------------------
    def _resolve_output_dir(
        self, explicit_output_dir: Optional[Union[str, Path]]
    ) -> Path:
        """Resolve the directory where generated assets are written.

        Precedence order:
        1. Explicit ``output_dir`` argument.
        2. Known configuration keys (``output_dir`` or ``IMG_DIR``).

        Raises:
            ValueError: if no directory can be resolved.
        """

        if explicit_output_dir is not None:
            return Path(explicit_output_dir)

        for key in self.OUTPUT_DIR_KEYS:
            value = self.config.get(key)
            if value:
                return Path(str(value))

        raise ValueError(
            "Output directory must be provided either explicitly or via config"
        )

    def setup_directories(
        self,
        directories: Optional[Mapping[str, RelativePath]] = None,
    ) -> Dict[str, Path]:
        """Ensure that the base output directory and optional sub-directories exist.

        Args:
            directories: Mapping of keys to relative paths expressed either as a
                string, :class:`pathlib.Path`, or a sequence of path components.

        Returns:
            Dictionary containing the materialised :class:`Path` objects for the
            provided ``directories`` mapping.
        """

        self.output_dir.mkdir(parents=True, exist_ok=True)

        if not directories:
            return {}

        created: Dict[str, Path] = {}
        for key, relative_path in directories.items():
            if isinstance(relative_path, (str, Path)):
                parts: Sequence[Union[str, Path]] = (relative_path,)
            else:
                parts = tuple(relative_path)

            materialised = self.output_dir.joinpath(*map(str, parts))
            materialised.mkdir(parents=True, exist_ok=True)
            self.output_paths[key] = materialised
            created[key] = materialised

        return created

    def register_path(self, key: str, *relative: Union[str, Path]) -> Path:
        """Register and ensure a sub-directory relative to ``output_dir`` exists."""

        path = self.output_dir.joinpath(*map(str, relative)) if relative else self.output_dir
        path.mkdir(parents=True, exist_ok=True)
        self.output_paths[key] = path
        return path

    def get_output_path(self, key: str) -> Path:
        """Return a previously registered output path."""

        return self.output_paths[key]

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------
    @abstractmethod
    def generate_images(self) -> None:
        """Generate stimuli assets and persist them to disk."""


