"""Verify that a built bm wheel contains the optional PyO3 extension."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path


def _has_native_extension(wheel: Path) -> bool:
    suffixes = (".so", ".pyd", ".dll", ".dylib")
    with zipfile.ZipFile(wheel) as archive:
        return any(
            name.startswith("bm/_native") and name.endswith(suffixes) for name in archive.namelist()
        )


def main() -> int:
    wheels = [Path(arg) for arg in sys.argv[1:]]
    if not wheels:
        print("usage: verify_native_wheel.py <wheel> [...]", file=sys.stderr)
        return 2

    failed: list[Path] = []
    for wheel in wheels:
        if not wheel.exists():
            print(f"missing wheel: {wheel}", file=sys.stderr)
            failed.append(wheel)
            continue
        if not _has_native_extension(wheel):
            print(f"missing bm._native extension: {wheel}", file=sys.stderr)
            failed.append(wheel)

    if failed:
        return 1

    print(f"verified native extension in {len(wheels)} wheel(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
