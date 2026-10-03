#!/usr/bin/env python3
"""cameo_model.py — Cameo-specific model on top of miniyaml.Ruleset.

Provides the shared concepts every audit needs:
- faction registry (from FactionCA@/Faction@ world definitions)
- per-faction buildable rosters via prerequisite-closure fixpoint
- actor ownership attribution (ContentPack folder or gate-token heuristic)
- trait/actor classification helpers (template? buildable? unit type?)
"""

from __future__ import annotations

import pathlib
import re
from dataclasses import dataclass, field
from functools import lru_cache

from miniyaml import Node, Ruleset, find_repo_root


# --------------------------------------------------------------------------- #
# Faction registry
# --------------------------------------------------------------------------- #

@dataclass
class Faction:
    internal: str
    name: str
    side: str = ""
    selectable: bool = True
    random_members: list[str] = field(default_factory=list)
    file: str = ""

    @property
    def is_meta(self) -> bool:
        """Random/RTF-style pseudo factions."""
        return bool(self.random_members) or self.side.lower() == "random"


class Model:
    def __init__(self, repo_root: pathlib.Path | None = None):
        self.root = repo_root or find_repo_root()
        self.rs = Ruleset(self.root)
        self.factions = self._load_factions()
        self._provides: dict[str, set[str]] | None = None
        self._rosters: dict[tuple, set[str]] = {}
        self._lobby_tokens: set[str] | None = None

    # ---- factions --------------------------------------------------------- #

    def _load_factions(self) -> dict[str, Faction]:
        out: dict[str, Faction] = {}
        world = self.rs.actors.get("World")
        if world is None:
            return out
        resolved = self.rs.resolve("World")
        for c in resolved.children:
            if not (c.key.startswith("Faction@") or c.key.startswith("FactionCA@")):
                continue
            internal = c.get("InternalName") or c.key.split("@", 1)[1]
            selectable = (c.get("Selectable") or "true").lower() != "false"
            members = [m.strip() for m in (c.get("RandomFactionMembers") or "").split(",") if m.strip()]
            out[internal] = Faction(
                internal=internal,
                name=c.get("Name") or internal,
                side=c.get("Side") or "",
                selectable=selectable,
                random_members=members,
                file=c.file,
            )
        return out

    def real_factions(self) -> list[Faction]:
        return [f for f in self.factions.values() if not f.is_meta]

    def random_pool(self) -> set[str]:
        f = self.factions.get("Random")
        return set(f.random_members) if f else set()

    def tournament_pool(self) -> set[str]:
        f = self.factions.get("RandomTournament")
        return set(f.random_members) if f else set()

    # ---- starting units --------------------------------------------------- #

    def starting_actors(self, faction: str) -> set[str]:
        """BaseActor + SupportActors of every StartingUnits set naming the faction."""
        world = self.rs.resolve("World")
        out: set[str] = set()
        for c in world.children:
            if not c.key.startswith("StartingUnits"):
                continue
            facs = [x.strip().lower() for x in (c.get("Factions") or "").split(",") if x.strip()]
            if faction.lower() not in facs:
                continue
            for fieldname in ("BaseActor", "SupportActors", "InnerSupportActors"):
                v = c.get(fieldname)
                if v:
                    out.update(x.strip().lower() for x in v.split(",") if x.strip())
        return out

    # ---- prerequisite closure --------------------------------------------- #

    # Tokens satisfied by lobby/map options rather than owned actors.
    OPTION_TOKEN_PREFIXES = (
        "techlevel.", "global-", "gamemode", "enable-", "rules-",
        "difficulty", "shortgame", "crates", "domination", "kotch",
    )

    # Trait roots whose fields grant prerequisite tokens only when the player
    # picks/enables the option in the lobby (checkboxes, dropdowns, tech level).
    LOBBY_TRAIT_PREFIXES = ("lobbyprerequisite", "providestechprerequisite")

    def lobby_tokens(self) -> set[str]:
        """Prerequisite tokens any lobby option can grant: `Prerequisites:`
        on `LobbyPrerequisiteCheckbox`/`ProvidesTechPrerequisite` traits, plus
        every `Values:` key of `LobbyPrerequisiteDropdown` (each value is the
        token granted when that option is selected)."""
        if self._lobby_tokens is not None:
            return self._lobby_tokens
        toks: set[str] = set()
        for name in self.rs.actors:
            if name.startswith(("^", "$", "-")):
                continue
            res = self.rs.resolve(name)
            if res is None:
                continue
            for c in res.children:
                root = c.key.split("@", 1)[0].lower()
                if not root.startswith(self.LOBBY_TRAIT_PREFIXES):
                    continue
                for tok in (c.get("Prerequisites") or "").split(","):
                    tok = tok.strip().lstrip("~").strip().lower()
                    if tok and not tok.startswith("!"):
                        toks.add(tok)
                vals = c.child("Values")
                if vals is not None:
                    for v in vals.children:
                        toks.add(v.key.lower())
        self._lobby_tokens = toks
        return toks

    def _provider_tokens(self, name: str, resolved: Node) -> set[str]:
        """Every prerequisite token owning this actor grants."""
        toks = {name.lower()}
        for c in resolved.children_named("ProvidesPrerequisite"):
            explicit = c.get("Prerequisite")
            toks.add((explicit or name).lower())
        for c in resolved.children_named("ProvidesTeamProxyActor"):
            proxy = c.get("Actor")
            if proxy:
                prox = self.rs.resolve(proxy)
                if prox is not None:
                    toks |= self._provider_tokens(proxy, prox)
        return toks

    def _expansions(self, resolved: Node) -> set[str]:
        """Actors that owning this actor makes available without building
        (deploys, free actors, produced-by-power actors)."""
        out: set[str] = set()
        for c in resolved.children_named("Transforms"):
            v = c.get("IntoActor")
            if v:
                out.add(v.lower())
        for c in resolved.children_named("TransformOnCondition"):
            v = c.get("IntoActor")
            if v:
                out.add(v.lower())
        for c in resolved.children_named("FreeActor"):
            v = c.get("Actor")
            if v:
                out.add(v.lower())
        for c in resolved.children:
            if c.key.startswith("ProduceActorPower"):
                v = c.get("Actors")
                if v:
                    out.update(x.strip().lower() for x in v.split(",") if x.strip())
        return out

    @staticmethod
    def positive_prereqs(resolved: Node) -> list[str]:
        """Positive (non-negated) prerequisite tokens from Buildable, ~ stripped."""
        out: list[str] = []
        b = resolved.child("Buildable")
        if b is None:
            return out
        raw = b.get("Prerequisites") or ""
        for tok in raw.split(","):
            tok = tok.strip().lstrip("~").strip()
            if not tok or tok.startswith("!"):
                continue
            out.append(tok.lower())
        return out

    @staticmethod
    def is_buildable(resolved: Node) -> bool:
        b = resolved.child("Buildable")
        return b is not None and bool(b.get("Queue"))

    @staticmethod
    def _factions_allows(resolved: Node, faction: str) -> bool:
        """`Buildable.Factions` is an engine-level roster gate the prereq
        closure does not see: a buildable listing other factions' InternalNames
        is unobtainable here even when its prereq tokens are satisfied."""
        b = resolved.child("Buildable")
        if b is None:
            return True
        raw = (b.get("Factions") or "").split("#", 1)[0]
        allowed = {x.strip().lower() for x in raw.split(",") if x.strip()}
        return not allowed or faction.lower() in allowed

    def roster(self, faction: str,
               extra_tokens: frozenset[str] = frozenset()) -> set[str]:
        """Fixpoint prerequisite closure: every actor the faction can obtain.
        `extra_tokens` are treated as already satisfied (e.g. lobby_tokens()
        to model "live when the option is ticked")."""
        key = (faction, extra_tokens)
        if key in self._rosters:
            return self._rosters[key]

        owned: set[str] = set()
        tokens: set[str] = set()

        def own(actor_name: str) -> None:
            lname = actor_name.lower()
            if lname in owned:
                return
            owned.add(lname)
            res = self.rs.resolve(lname)
            if res is None:
                return
            tokens.update(self._provider_tokens(lname, res))
            for extra in self._expansions(res):
                own(extra)

        for s in self.starting_actors(faction):
            own(s)
        # Player-level provisions (rank tokens etc.) are always present.
        player = self.rs.resolve("Player")
        if player is not None:
            tokens.update(self._provider_tokens("player", player) - {"player"})

        def satisfied(tok: str) -> bool:
            if tok in tokens or tok in extra_tokens:
                return True
            return tok.startswith(self.OPTION_TOKEN_PREFIXES)

        buildables = [
            (name.lower(), res) for name, res in
            ((n, self.rs.resolve(n)) for n in self.rs.actors if not n.startswith("^"))
            if res is not None and self.is_buildable(res)
        ]
        changed = True
        while changed:
            changed = False
            for lname, res in buildables:
                if lname in owned:
                    continue
                if not self._factions_allows(res, faction):
                    continue
                if all(satisfied(t) for t in self.positive_prereqs(res)):
                    own(lname)
                    changed = True

        self._rosters[key] = owned
        return owned

    def buildable_roster(self, faction: str,
                         extra_tokens: frozenset[str] = frozenset()) -> set[str]:
        out = set()
        for lname in self.roster(faction, extra_tokens):
            res = self.rs.resolve(lname)
            if res is not None and self.is_buildable(res):
                out.add(lname)
        return out

    def faction_tokens(self, faction: str) -> set[str]:
        """All prerequisite tokens attainable by the faction's closure."""
        toks: set[str] = set()
        for lname in self.roster(faction):
            res = self.rs.resolve(lname)
            if res is not None:
                toks |= self._provider_tokens(lname, res)
        player = self.rs.resolve("Player")
        if player is not None:
            toks |= self._provider_tokens("player", player) - {"player"}
        return toks

    # ---- ownership -------------------------------------------------------- #

    # Root gate tokens for the monolithic rule files (hand-verified anchors).
    GATE_TOKEN_FACTION: dict[str, str] = {
        "tsgtcnstgdi": "ts_gdi", "tsgtcnstnod": "ts_nod",
        "tsgtcnstcabal": "cabal", "tsgtcnstmutant": "forgotten",
    }

    def owner_of(self, actor_name: str) -> str | None:
        """Best-effort owning faction: ContentPack folder, ~fact.X gate,
        or monolith conyard gate token. None = shared/undetermined."""
        node = self.rs.actor(actor_name)
        if node is None:
            return None
        rel = pathlib.PurePosixPath(str(node.file).replace("\\", "/"))
        parts = rel.parts
        if "ContentPacks" in parts:
            i = parts.index("ContentPacks")
            theme = parts[i + 1] if i + 1 < len(parts) else ""
            sub = parts[i + 2] if i + 2 < len(parts) else ""
            if sub not in ("rules", "content.yaml", "Shared", "Core") and sub:
                return f"{theme}/{sub}".lower()
            return f"{theme}/shared".lower() if sub == "Shared" else None
        res = self.rs.resolve(actor_name)
        if res is None:
            return None
        for tok in self.positive_prereqs(res):
            if tok.startswith("fact."):
                return tok.split(".", 1)[1]
            if tok in self.GATE_TOKEN_FACTION:
                return self.GATE_TOKEN_FACTION[tok]
        return None

    # ---- classification --------------------------------------------------- #

    # The unit-class templates in defaults.yaml are the authoritative
    # classification (e.g. scgoliath2 walks and animates like infantry but
    # inherits ^HighTechTankTemplate => vehicle). Trait heuristics are only
    # the fallback for actors without a class template.
    TEMPLATE_CATEGORY = {
        "antitankantiairinfantrytemplate": "inf", "flyinginfantrytemplate": "inf",
        "grenadierinfantrytemplate": "inf", "heavyinfantrytemplate": "inf",
        "heroinfantrytemplate": "inf", "meleeinfantrytemplate": "inf",
        "mortarinfantrytemplate": "inf", "scoutinfantrytemplate": "inf",
        "sniperinfantrytemplate": "inf", "dogtemplate": "inf",
        "medictemplate": "inf", "mechanictemplate": "inf",
        "artillerytemplate": "veh", "epicvehicletemplate": "veh",
        "firesupporttemplate": "veh", "harvestertemplate": "veh",
        "hightechtanktemplate": "veh", "linebreakertemplate": "veh",
        "mainbattletanktemplate": "veh", "scoutvehicletemplate": "veh",
        "supportvehicletemplate": "veh",
        "bombertemplate": "air", "epicairunittemplate": "air",
        "fightertemplate": "air", "helicoptertemplate": "air",
        "spaceshiptemplate": "air", "unarmedtransporthelicoptertemplate": "air",
        "artilleryshiptemplate": "nav", "battleshiptemplate": "nav",
        "scoutshiptemplate": "nav",
        "advanceddefensetemplate": "def", "antiairdefensetemplate": "def",
        "basicdefensetemplate": "def", "bunkertemplate": "def",
        "superdefensetemplate": "def",
    }

    def template_category(self, actor_name: str,
                          _seen: frozenset = frozenset()) -> str | None:
        """Category from unit-class template ancestry, or None."""
        node = self.rs.actor(actor_name)
        if node is None or actor_name.lower() in _seen:
            return None
        root = self.rs.resolve(actor_name) if not _seen else None
        has_inf_body = root is not None and root.child("WithInfantryBody") is not None
        for _, target in self.rs.inherits_of(node):
            tname = target.lstrip("^").lower()
            cat = self.TEMPLATE_CATEGORY.get(tname)
            # LineBreakerTemplate is used by both vehicles and infantry;
            # actors with an infantry body should fall back to structural inf.
            if cat and not (tname == "linebreakertemplate" and cat == "veh" and has_inf_body):
                return cat
        for _, target in self.rs.inherits_of(node):
            cat = self.template_category(target, _seen | {actor_name.lower()})
            if cat:
                return cat
        return None

    def unit_type(self, actor_name: str) -> str:
        """§9.4 structural type: inf/veh/air/nav/bld/def/upg/husk/prop/hero/sup."""
        res = self.rs.resolve(actor_name)
        if res is None:
            return "prop"
        lname = actor_name.lower()
        b = res.child("Buildable")
        queue = (b.get("Queue") or "").lower() if b else ""
        if any(q in queue for q in ("upgrade", "research", "promotion")):
            return "upg"
        if ".husk" in lname or lname.endswith("husk") or res.child("Husk") is not None:
            return "husk"
        cat = self.template_category(actor_name)
        if cat is not None:
            return cat
        if res.child("Building") is not None:
            if "defence" in queue or "defense" in queue:
                return "def"
            return "bld"
        if res.child("Aircraft") is not None:
            return "air"
        mobile = res.child("Mobile")
        if mobile is not None:
            loco = (mobile.get("Locomotor") or "").lower()
            if "naval" in loco or "ship" in loco or "boat" in loco:
                return "nav"
            if loco in ("foot", "scout", "doggie", "immobile") or res.child("TakeCover") is not None \
               or res.child("WithInfantryBody") is not None:
                return "inf"
            return "veh"
        if res.child("WithInfantryBody") is not None:
            return "inf"
        if self.is_buildable(res):
            return "veh"
        return "prop"

    def display_name(self, actor_name: str) -> str:
        res = self.rs.resolve(actor_name)
        if res is None:
            return actor_name
        return res.get("Tooltip", "Name") or actor_name


_slug_re = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    return _slug_re.sub("_", text.lower()).strip("_")


if __name__ == "__main__":
    m = Model()
    print(f"factions: {len(m.factions)} ({len(m.real_factions())} real)")
    print(f"random pool: {sorted(m.random_pool())}")
    for probe in ("cabal", "forgotten"):
        r = m.buildable_roster(probe)
        print(f"{probe}: {len(r)} buildables, e.g. {sorted(r)[:12]}")
