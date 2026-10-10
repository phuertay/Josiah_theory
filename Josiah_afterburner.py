"""
Josiah_afterburner — fill missing Josiah theory outlines from josiah_us.json.

Loads only josiah_us.json as BASE (parent lookups). No other-dict awareness.
Plover stack order decides precedence; place this dict below numbers/Harri yourself.

SPELLING: "US" (default) or "UK" (Josiah Tan orthography) for literals this file invents.
Cheatsheet: https://github.com/phuertay/Josiah_theory/wiki/Cheatsheet
"""

from __future__ import annotations

import json
import re
from pathlib import Path

SPELLING = "US"  # "US" | "UK"

LONGEST_KEY = 2

_BASE_PATH = Path(__file__).with_name("josiah_us.json")
with _BASE_PATH.open(encoding="utf-8") as _f:
    BASE: dict[str, str] = json.load(_f)

# --- spelling literals (only strings this file invents) --------------------
_LIT = {
    "izing": {"US": "izing", "UK": "ising"},
    "ization": {"US": "ization", "UK": "isation"},
    "ize": {"US": "ize", "UK": "ise"},
    "ized": {"US": "ized", "UK": "ised"},
}


def lit(key: str) -> str:
    return _LIT[key][SPELLING]


# --- stroke helpers -------------------------------------------------------
# Optional layout prefixes used in josiah_us: ^ +
# Then standard steno: optional #, left STKPWHR, AO, *, EU, right FRPBLGTSDZ
# Digits appear when Plover encodes the number bar into the stroke.

_DIGIT_TO_LETTER = str.maketrans("1234506789", "STPHAOFPLT")
_LETTER_TO_DIGIT = {v: k for k, v in zip("STPHAOFPLT", "1234506789")}

_STROKE = re.compile(
    r"^(?P<pre>[^+#STKPWHRAO*EU0-9-]*)"  # ^ + etc. before steno body
    r"(?P<body>"
    r"(?P<hash>#)?"
    r"(?P<left>[STKPWHR0-9]*)"
    r"(?P<a>A?)"
    r"(?P<o>O?)"
    r"(?P<star>\*?)"
    r"(?P<e>E?)"
    r"(?P<u>U?)"
    r"(?P<hyphen>-?)"
    r"(?P<right>[FRPBLGTSDZ]*)"
    r")$"
)


def digits_to_letters(stroke: str) -> str:
    return stroke.translate(_DIGIT_TO_LETTER)


def _parse(stroke: str):
    m = _STROKE.match(stroke)
    if not m:
        return None
    return m.groupdict()


def _join(parts: dict) -> str:
    left = parts["left"]
    vowels = parts["a"] + parts["o"] + parts["star"] + parts["e"] + parts["u"]
    right = parts["right"]
    body = (parts["hash"] or "") + left + vowels
    if right:
        if not vowels and left:
            body += "-" + right
        else:
            body += right
    elif parts.get("hyphen") == "-" and not right:
        # bare left with trailing hyphen is unusual; omit
        pass
    return (parts["pre"] or "") + body


def strip_right(stroke: str, cluster: str) -> str | None:
    """Peel a right-hand cluster; return parent stroke or None."""
    p = _parse(stroke)
    if not p or not p["right"].endswith(cluster):
        return None
    p = dict(p)
    p["right"] = p["right"][: -len(cluster)]
    parent = _join(p)
    return parent if parent != stroke else None


def add_right(stroke: str, cluster: str) -> str | None:
    p = _parse(stroke)
    if not p:
        return None
    p = dict(p)
    p["right"] = p["right"] + cluster
    return _join(p)


def strip_left_prefix(stroke: str, prefix: str) -> str | None:
    """Peel a left-hand starter chord from the left keys (after pre/^)."""
    p = _parse(stroke)
    if not p or not p["left"].startswith(prefix):
        return None
    if len(p["left"]) == len(prefix) and not (p["a"] or p["o"] or p["e"] or p["u"] or p["right"]):
        # would leave empty stroke
        return None
    p = dict(p)
    p["left"] = p["left"][len(prefix) :]
    return _join(p)


def has_number_bar(stroke: str) -> bool:
    if "#" in stroke:
        return True
    # digit-encoded number bar (any digit in stroke)
    return any(c.isdigit() for c in stroke)


def strip_number_bar(stroke: str) -> str | None:
    """Remove one number-bar encoding; return letter-form parent without #/digits-as-bar."""
    s = digits_to_letters(stroke)
    if s.startswith("#"):
        return s[1:] or None
    # digits may sit inside left bank; digits_to_letters already mapped them
    # If original had digits, mapped form is the parent without bar semantics…
    # Parent for #PWOB / 3W0B is PWOB.
    if any(c.isdigit() for c in stroke):
        return s if s != stroke else None
    if "#" in s:
        return s.replace("#", "", 1)
    return None


def cap_first(text: str) -> str:
    if not text or text.startswith("{"):
        raise KeyError
    for i, ch in enumerate(text):
        if ch.isalpha():
            return text[:i] + ch.upper() + text[i + 1 :]
    raise KeyError


def _base_get(stroke: str) -> str | None:
    if stroke in BASE:
        return BASE[stroke]
    # try digit↔letter variants for lookup only
    alt = digits_to_letters(stroke)
    if alt != stroke and alt in BASE:
        return BASE[alt]
    return None


def _plain(text: str) -> bool:
    return bool(text) and not text.startswith("{")


# --- suffix / prefix tables (Cheatsheet phrase enders & starters) ---------
# Longer right clusters first.
RH_APPEND: list[tuple[str, str]] = [
    ("PBLGTS", " something"),  # before LGTS
    ("TSDZ", " this"),
    ("LGTS", " that"),
    ("RPG", " these"),
    ("FBL", " those"),
    ("BLS", " their"),
    ("RBG", " your"),
    ("FPL", " them"),
    ("PL", " me"),
    ("FR", " me"),  # Cheatsheet: -FR → me when -PL taken
]

# * + right cluster → translation glue (asterisk kept on parent strip)
RH_STAR_APPEND: list[tuple[str, str]] = [
    ("BLS", " they're"),
    ("RBG", " your"),
    ("FPL", " them"),
    ("PL", " my"),
    ("FR", " my"),  # Cheatsheet: *FR → my
    ("T", " the"),
]

RH_PLAIN_T = ("T", " it")  # -T → it when no star

LH_PREPEND: list[tuple[str, str]] = [
    ("PWR", "before "),
    ("PWH", "but "),
    ("KPW", "about "),
]

# Leading ^WR → over- (Cheatsheet); stroke already has pre ^
CARET_LEFT_PREPEND: list[tuple[str, str]] = [
    ("WR", "over"),  # glued: overview from ^WR-F etc. — prepend "over" without space when rest is affix
]


def _try_caret_wr_over(stroke: str) -> str | None:
    """Cheatsheet ^WR → over- fixed briefs + glue when parent without ^WR exists."""
    if not stroke.startswith("^WR"):
        return None
    fixed = {
        "^WR-F": "overview",
        "^WR-L": "overlay",
        "^WR*LG": "overlook",
        "^WR-FRL": "overwhelm",
    }
    if stroke in fixed:
        return fixed[stroke]
    rest = stroke[len("^WR") :]
    rest_stroke = rest[1:] if rest.startswith("-") else rest
    t = _base_get(rest_stroke) if rest_stroke else None
    if t is not None and _plain(t):
        return "over" + t.lstrip()
    return None


def _try_caret_as(stroke: str) -> str | None:
    """Cheatsheet: ^S… → as … (from so/is parent); trailing S → as … as."""
    if not stroke.startswith("^S"):
        return None
    bare = stroke[1:]  # drop ^
    t = _base_get(bare)
    as_as = False
    if t is None and bare.endswith("S") and not bare.endswith(("TS", "SZ", "TSDZ")):
        # ^SHROPBGS ← SHROPBG + S → as long as
        stem = bare[:-1]
        t = _base_get(stem)
        as_as = t is not None
    if t is None or not _plain(t):
        return None
    for lead in ("so ", "is "):
        if t.startswith(lead):
            body = t[len(lead) :]
            return ("as " + body + " as") if as_as else ("as " + body)
    return None

# Magnum-style -DZ → ing when parent exists without DZ
# ponytail: naive "ing" glue; bad for sock/sobbing — KeyError if parent missing


def _try_rh_append(stroke: str) -> str | None:
    # star-specific enders first
    p = _parse(stroke)
    if not p:
        return None
    if p["star"] == "*":
        for cluster, glue in RH_STAR_APPEND:
            parent = strip_right(stroke, cluster)
            if parent is None:
                continue
            # parent should still carry * for *T / *PL cases where * is the ender mark
            # Cheatsheet: TPH*T ← TPH with *T meaning "the"; strip *T → TPH
            pp = _parse(parent)
            if pp and cluster in ("T", "PL", "FPL", "BLS", "RBG"):
                # strip star from parent for lookup of bare left
                bare = dict(pp)
                bare["star"] = ""
                bare_stroke = _join(bare)
                t = _base_get(bare_stroke)
                if t is not None and _plain(t):
                    return t + glue
            t = _base_get(parent)
            if t is not None and _plain(t):
                return t + glue
    for cluster, glue in RH_APPEND:
        parent = strip_right(stroke, cluster)
        if parent is None:
            continue
        t = _base_get(parent)
        if t is not None and _plain(t):
            return t + glue
    # -T → it (no star)
    if p["star"] != "*" and p["right"].endswith("T") and not p["right"].endswith(("ST", "RT", "PT", "BT", "LT", "GT", "TSDZ")):
        # only pure trailing single T as ender — skip if right is longer ambiguous
        if p["right"] == "T" or (p["right"].endswith("T") and len(p["right"]) == 1):
            parent = strip_right(stroke, "T")
            if parent:
                t = _base_get(parent)
                if t is not None and _plain(t):
                    return t + " it"
    # TS + DZ → this (same as TSDZ)
    if p["right"].endswith("DZ") and not p["right"].endswith("TSDZ"):
        parent = strip_right(stroke, "DZ")
        if parent:
            pp = _parse(parent)
            if pp and pp["right"].endswith("TS"):
                t = _base_get(parent)
                if t is not None and _plain(t):
                    return t + " this"
    return None


def _try_lh_prepend(stroke: str) -> str | None:
    for prefix, glue in LH_PREPEND:
        rest = strip_left_prefix(stroke, prefix)
        if rest is None:
            continue
        t = _base_get(rest)
        if t is not None and _plain(t):
            return glue + t
        # also try rest with leading hyphen normalized
        if rest.startswith("-"):
            t = _base_get(rest[1:])
            if t is not None and _plain(t):
                return glue + t
    return None


def _try_lapwing_hash(stroke: str) -> str | None:
    if stroke in ("#", "#*"):
        return None
    if not has_number_bar(stroke):
        return None
    parent = strip_number_bar(stroke)
    if not parent:
        return None
    t = _base_get(parent)
    if t is None or not _plain(t):
        return None
    return cap_first(t)


def _try_asterisk_capitalize(stroke: str) -> str | None:
    """Cheatsheet first asterisk use: capitalize. Parent = stroke without *."""
    p = _parse(stroke)
    if not p or p["star"] != "*":
        return None
    # skip if right-hand star-enders already handle (checked earlier in RULES order)
    bare = dict(p)
    bare["star"] = ""
    parent = _join(bare)
    t = _base_get(parent)
    if t is None or not _plain(t):
        return None
    # contraction-shaped: "… is" → "'s" (Cheatsheet Contractions)
    if t.endswith(" is"):
        return t[: -len(" is")] + "'s"
    try:
        return cap_first(t)
    except KeyError:
        return None


def _try_dz_ing(stroke: str) -> str | None:
    """Magnum: -DZ → ing when parent without DZ exists."""
    parent = strip_right(stroke, "DZ")
    if parent is None:
        return None
    # avoid double-firing TSDZ / SDZ phrase enders
    p = _parse(stroke)
    if p and p["right"].endswith(("TSDZ", "SDZ")):
        return None
    t = _base_get(parent)
    if t is None or not _plain(t):
        return None
    if t.endswith("e") and not t.endswith(("ee", "ie")):
        return t[:-1] + "ing"
    if t.endswith("y") and len(t) > 1 and t[-2] not in "aeiou":
        return t[:-1] + "ing"
    return t + "ing"


def _try_z_plural(stroke: str) -> str | None:
    """Cheatsheet: -Z → s plural when parent with S (not -TS exception path)."""
    parent = strip_right(stroke, "Z")
    if parent is None:
        return None
    p = _parse(stroke)
    if p and len(p["right"]) != 1:
        return None  # only bare -Z ender
    # parent often ends with S in orthography sense via different stroke; try S↔Z swap
    ps = _parse(parent)
    if not ps:
        return None
    # AOEUS → ice / AOEUZ → eyes: parent is S-ending stroke
    s_parent = dict(ps)
    s_parent["right"] = s_parent["right"] + "S" if not s_parent["right"].endswith("S") else s_parent["right"]
    # Actually Z replaces S on right: strip Z, add S
    s_parent = dict(ps)
    if s_parent["right"].endswith("S"):
        return None
    s_parent["right"] = s_parent["right"] + "S"
    s_stroke = _join(s_parent)
    t = _base_get(s_stroke)
    if t is None or not _plain(t):
        t = _base_get(parent)
        if t is None or not _plain(t):
            return None
        return t + "s"
    # have S-stroke translation; Z form is irregular often — prefer +s on parent without S
    t2 = _base_get(parent)
    if t2 is not None and _plain(t2):
        return t2 + "s"
    return None


def _try_re_prefix(stroke: str) -> str | None:
    """*R or R* → re- on parent without that R involvement — Cheatsheet *R → re-."""
    p = _parse(stroke)
    if not p or p["star"] != "*":
        return None
    # *R in right: right starts with R after peel?
    if not p["right"].startswith("R"):
        return None
    bare = dict(p)
    bare["star"] = ""
    # remove one R from start of right
    bare["right"] = bare["right"][1:]
    parent = _join(bare)
    t = _base_get(parent)
    if t is None or not _plain(t):
        return None
    if t.startswith("re"):
        return None
    return "re" + t


# --- multi-stroke wildcards -----------------------------------------------
_PAIR_SECONDS = {
    "STOZ": " to ",
    "SP-Z": " by ",
    "SR-Z": " or ",
}

# Cheatsheet SKP-Z fixed pairs (not compositional)
_SKP_Z_PAIRS = {
    "U": "you and me",
    "UPZ": "ups and downs",
    "HREFT": "left and right",
    "PHOPL": "mom and dad",
}

# Cheatsheet SR-Z fixed pairs when second half ≠ first
_SR_Z_PAIRS = {
    "UP": "up or down",
    "TKED": "dead or alive",
}


def _try_wildcard(outline: tuple[str, ...]) -> str | None:
    if len(outline) != 2:
        return None
    a, b = outline
    if b == "SKP-Z" and a in _SKP_Z_PAIRS:
        return _SKP_Z_PAIRS[a]
    if b == "SR-Z" and a in _SR_Z_PAIRS:
        return _SR_Z_PAIRS[a]
    if b in _PAIR_SECONDS:
        ta = _base_get(a)
        if ta is None or not _plain(ta):
            return None
        return ta + _PAIR_SECONDS[b] + ta
    if b == "S-FPLZ":
        t = _base_get(a)
        if t is not None and _plain(t):
            return t + "{.}"
        return None
    if b == "S-RBGZ":
        t = _base_get(a)
        if t is not None and _plain(t):
            return t + ","
        return None
    # compound: second stroke has * → join without space (Cheatsheet compound words)
    p = _parse(b)
    if p and p["star"] == "*":
        bare = dict(p)
        bare["star"] = ""
        b2 = _join(bare)
        ta, tb = _base_get(a), _base_get(b2)
        if ta is not None and tb is not None and _plain(ta) and _plain(tb):
            return ta + tb
    return None


# --- ise/ize family (Cheatsheet -DZ/-GZ/-S/-FGS/-SZ) -----------------------
def _try_ise_family(stroke: str) -> str | None:
    """If parent + S → …ise/ize exists pattern via BASE parent stem."""
    # -S on adjective/noun → verb: parent without S
    for cluster, suffix in (
        ("FGS", lit("ization")),
        ("GDZ", lit("izing")),  # sometimes GZ
        ("GZ", lit("izing")),
        ("DZ", lit("ized")),
        ("SZ", lit("ize") + "s"),
        ("S", lit("ize")),
    ):
        parent = strip_right(stroke, cluster)
        if parent is None:
            continue
        t = _base_get(parent)
        if t is None or not _plain(t):
            continue
        # only if parent looks like a stem that takes ise (heuristic: in BASE as adj/noun)
        if cluster == "S" and t.endswith("s"):
            continue
        return t + suffix
    return None


# RULES order matters (Cheatsheet asterisk order ≈ first match wins among these)
def _try_star_z_his_has(stroke: str) -> str | None:
    """Cheatsheet: *Z → his, -Z → has (when parent exists)."""
    p = _parse(stroke)
    if not p or p["right"] != "Z":
        return None
    bare = dict(p)
    bare["right"] = ""
    bare["star"] = ""
    parent = _join(bare)
    t = _base_get(parent)
    if t is None or not _plain(t):
        return None
    if p["star"] == "*":
        return t + " his"
    return t + " has"


def _rules_one(stroke: str) -> str | None:
    for fn in (
        _try_rh_append,
        _try_lh_prepend,
        _try_caret_wr_over,
        _try_caret_as,
        _try_lapwing_hash,
        _try_asterisk_capitalize,
        _try_star_z_his_has,
        _try_re_prefix,
        _try_dz_ing,
        _try_ise_family,
        _try_z_plural,
    ):
        got = fn(stroke)
        if got is not None:
            return got
    return None


def lookup(key):
    assert len(key) <= LONGEST_KEY
    outline = tuple(key)
    joined = "/".join(outline)
    if joined in BASE or (len(outline) == 1 and outline[0] in BASE):
        raise KeyError
    if len(outline) == 1 and digits_to_letters(outline[0]) in BASE:
        raise KeyError

    if len(outline) == 2:
        got = _try_wildcard(outline)
        if got is not None:
            return got
        raise KeyError

    stroke = outline[0]
    got = _rules_one(stroke)
    if got is not None:
        return got
    raise KeyError


def reverse_lookup(text):
    return []


# --- self-check -----------------------------------------------------------
if __name__ == "__main__":
    def expect_raise(strokes):
        try:
            lookup(strokes)
        except KeyError:
            return True
        raise AssertionError(f"expected KeyError for {strokes!r}")

    def expect(strokes, value):
        got = lookup(strokes)
        assert got == value, f"{strokes!r}: {got!r} != {value!r}"

    # BASE precedence
    expect_raise(("#",))
    expect_raise(("TPR-TSDZ",))  # already in BASE
    expect_raise(("UTSDZ",))

    # RH ender invent
    if "WR-LGTS" not in BASE and "WR" in BASE:
        expect(("WR-LGTS",), "where that")

    # Lapwing # — only if parent exists and hash form missing
    if "PWOB" in BASE and "#PWOB" not in BASE and "3W0B" not in BASE:
        expect(("#PWOB",), cap_first(BASE["PWOB"]))
        # digit-bar form of same outline
        if "3W0B" not in BASE:
            expect(("3W0B",), cap_first(BASE["PWOB"]))

    # ^WR fixed
    if "^WR-F" not in BASE:
        expect(("^WR-F",), "overview")

    # wildcard
    if "SAOEUD" in BASE:
        expect(("SAOEUD", "STOZ"), BASE["SAOEUD"] + " to " + BASE["SAOEUD"])
    if "U/SKP-Z" not in BASE and "U" in BASE:
        expect(("U", "SKP-Z"), "you and me")

    print("ok", "SPELLING=", SPELLING, "BASE entries=", len(BASE))
