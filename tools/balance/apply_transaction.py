"""Small, recoverable file transaction for the balance writer.

No game process may read the intermediate YAML, and no other writer may modify
the affected files. This is exception-safe, not a filesystem-wide atomic commit
or a replacement for the required boot gate. Optimistic byte checks are not an
OS lock or atomic compare-and-swap: another writer can race a check and replace.
"""
from __future__ import annotations

import os
import pathlib
import tempfile


class ApplyError(ValueError):
    """An unsupported plan or failed write must never report APPLIED."""


def atomic_write(path: pathlib.Path, data: bytes) -> None:
    """Replace one existing file without exposing a partially written file."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".balance_", delete=False) as stream:
            temporary = pathlib.Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


class Transaction:
    """Detect changes optimistically; preserve changes observed during rollback.

    Requires exclusive file ownership: byte comparisons do not lock out writers.
    """

    def __init__(self, originals: dict[pathlib.Path, bytes]):
        self.originals = originals
        self.written: dict[pathlib.Path, bytes] = {}

    def check_unchanged(self) -> None:
        for path, original in self.originals.items():
            if path.read_bytes() != self.written.get(path, original):
                raise ApplyError(f"concurrent edit: {path}; nothing overwritten")

    def write(self, path: pathlib.Path, data: bytes) -> None:
        expected = self.written.get(path, self.originals[path])
        if path.read_bytes() != expected:
            raise ApplyError(f"concurrent edit: {path}; nothing overwritten")
        if data != expected:
            # Register intent first: an interrupt may arrive immediately after
            # os.replace succeeds, before Python executes the next statement.
            self.written[path] = data
            atomic_write(path, data)

    def rollback(self) -> list[str]:
        conflicts = []
        for path, written in reversed(list(self.written.items())):
            try:
                current = path.read_bytes()
                if current == self.originals[path]:
                    continue  # replacement failed before changing the destination
                if current != written:
                    conflicts.append(str(path))
                    continue
                atomic_write(path, self.originals[path])
            except OSError as error:
                conflicts.append(f"{path}: {error}")
        return conflicts
