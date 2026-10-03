"""float2/float3 -> System.Numerics Vector2/Vector3, the rename OpenRA bleed made in 90c4415b7e.

Cameo moved to bleed (+ .NET 10) in #569. Upstream CA did not: every file copied from CA still
says float2/float3. The CA sync tools therefore convert UPSTREAM text into the engine's vocabulary
before comparing or writing it, so that:
  * audit_ca_drift still recognises an unedited copy as unedited (Cameo's copy was converted);
  * ca_vendor_sync writes code in the vocabulary the engine compiles.

Only the mechanical part is automatic: type names, the renamed statics, ToFloat2() and the
`using System.Numerics;` directive. The API differences (a float3 + float2 implicit operator,
.Length property -> Length(), .XY.ToInt2() -> int2.FromVector, int2 passed where a vector is
expected) are left to the compiler, which finds every one. See AI_SYNTHESIS.md §4.4.
"""
from __future__ import annotations

import pathlib
import re

SUBS = [
    (re.compile(r"\bfloat3\.Ones\b"), "Vector3.One"),
    (re.compile(r"\bfloat3\.Zero\b"), "Vector3.Zero"),
    (re.compile(r"\bfloat2\.Zero\b"), "Vector2.Zero"),
    (re.compile(r"\.ToFloat2\(\)"), ".ToVector2()"),
    (re.compile(r"\bfloat3\b"), "Vector3"),
    (re.compile(r"\bfloat2\b"), "Vector2"),
]
NEEDS = re.compile(r"\bfloat[23]\b|\.ToFloat2\(\)")
USING = "using System.Numerics;"
SYSTEM_USING = re.compile(r"^using System[.\w]*;\r?\n", re.M)


def is_vector_engine(repo: pathlib.Path) -> bool:
    """True when the engine under repo/engine has no float3 (bleed after 90c4415b7e)."""
    game = repo / "engine" / "OpenRA.Game"
    if not game.is_dir():
        raise SystemExit("engine/ is missing: run make.cmd all first (the CA sync needs to know the engine's vector types)")
    return not (game / "Primitives" / "float3.cs").is_file()


def convert(text: str) -> str:
    """Convert one C# source text. Idempotent; text without float2/float3 is returned unchanged."""
    if not NEEDS.search(text):
        return text
    new = text
    for pat, rep in SUBS:
        new = pat.sub(rep, new)
    if USING not in new:
        nl = "\r\n" if "\r\n" in new else "\n"
        usings = list(SYSTEM_USING.finditer(new))
        if usings:
            # sorted position among the System.* usings; "using System;" sorts first
            pos = next((m.start() for m in usings if m.group(0).strip().rstrip(";") > USING.rstrip(";")),
                       usings[-1].end())
        else:
            first = re.search(r"^using ", new, re.M)
            pos = first.start() if first else 0
        new = new[:pos] + USING + nl + new[pos:]
    return new
