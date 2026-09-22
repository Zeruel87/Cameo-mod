"""Restricted, non-overwriting output for read-only balance diagnostics."""
from pathlib import Path


def validate_path(root, path):
    root, path = Path(root).resolve(), Path(path).resolve()
    allowed = (root / "docs/audit/latest", root / "docs/balance/anchors")
    if path.suffix not in (".json", ".md"):
        raise ValueError(f"diagnostic output must be .json or .md: {path}")
    if path.is_relative_to(root) and not any(path.is_relative_to(directory) for directory in allowed):
        raise ValueError("in-repository diagnostic output must be under docs/audit/latest or docs/balance/anchors")
    return path


def write_outputs(root, outputs):
    """Preflight the entire batch; never overwrite a differing existing artifact.

    Exclusive creation protects against a file appearing after preflight. An I/O
    failure can leave an incomplete batch of newly created diagnostics, but cannot
    replace an existing file. No transactional gameplay-write claim is made here.
    """
    paths = {}
    for path, text in outputs.items():
        path = validate_path(root, path)
        if path in paths:
            raise ValueError(f"duplicate diagnostic output: {path}")
        paths[path] = text
        if path.exists() and path.read_text(encoding="utf-8") != text:
            raise ValueError(f"refusing to overwrite existing different diagnostic: {path}")
    for path, text in paths.items():
        if path.exists():
            # Recheck instead of silently accepting a post-preflight external edit.
            if path.read_text(encoding="utf-8") != text:
                raise ValueError(f"diagnostic changed after preflight: {path}")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
