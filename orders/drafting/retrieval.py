import math
import re
from collections import defaultdict
from dataclasses import dataclass

_TOKEN_RE = re.compile(r"[а-яёa-z]+|\d+")
_STEM_LEN = 4  # crude Russian stemming: "коронка"/"коронки"/"коронку" -> "коро"
_MIN_TOKEN_LEN = 3


@dataclass(frozen=True)
class Candidate:
    id: object
    name: str
    usage: int = 0  # how many works of this type exist; a popularity prior


def _stems(text: str) -> set[str]:
    # Numbers are kept whole and at any length: names like "Работа 3" or "Винир 3D" differ only by them.
    # Tooth numbers in the request ("21") are harmless: they only match names containing that exact number.
    return {
        t if t.isdigit() else t[:_STEM_LEN]
        for t in _TOKEN_RE.findall(text.lower())
        if t.isdigit() or len(t) >= _MIN_TOKEN_LEN
    }


def select_candidates(text: str, catalog: list[Candidate], limit: int) -> list[Candidate]:
    """Return at most `limit` candidates, sorted by name (stable order -> stable prompt -> cache friendly)."""
    if len(catalog) <= limit:
        return sorted(catalog, key=lambda c: c.name)

    name_stems = [_stems(c.name) for c in catalog]
    index: dict[str, int] = defaultdict(int)  # stem -> number of names containing it
    for stems in name_stems:
        for stem in stems:
            index[stem] += 1

    # Rare words are more informative: "циркониевая" beats "коронка" if only one name has it
    query = _stems(text)
    n = len(catalog)
    scored = []
    for i, stems in enumerate(name_stems):
        score = sum(math.log(1 + n / index[s]) for s in stems & query)
        if score > 0:
            scored.append((score, i))
    scored.sort(key=lambda p: (-p[0], -catalog[p[1]].usage, catalog[p[1]].name))

    chosen = [catalog[i] for _, i in scored[:limit]]
    if len(chosen) < limit:
        taken = {c.id for c in chosen}
        popular = sorted((c for c in catalog if c.id not in taken), key=lambda c: (-c.usage, c.name))
        chosen += popular[: limit - len(chosen)]

    return sorted(chosen, key=lambda c: c.name)
