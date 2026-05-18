from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PlatformPaths:
    data_root: Path

    @property
    def raw(self) -> Path:
        return self.data_root / "raw"

    @property
    def lake(self) -> Path:
        return self.data_root / "lake"

    @property
    def warehouse(self) -> Path:
        return self.data_root / "warehouse"

    @property
    def exports(self) -> Path:
        return self.data_root / "exports"

    @property
    def stream(self) -> Path:
        return self.data_root / "stream"

    def zone(self, name: str) -> Path:
        return self.lake / name

    def ensure(self) -> None:
        for path in [self.raw, self.lake, self.warehouse, self.exports, self.stream]:
            path.mkdir(parents=True, exist_ok=True)


def get_paths(data_root: str | Path | None = None) -> PlatformPaths:
    root = Path(data_root or os.getenv("COMMERCE_DATA_ROOT", "data"))
    paths = PlatformPaths(root)
    paths.ensure()
    return paths
