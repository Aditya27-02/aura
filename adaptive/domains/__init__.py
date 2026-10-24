from __future__ import annotations

from adaptive.domains.dsa import build_dsa_pack
from adaptive.domains.biology import build_biology_pack

PACK_BUILDERS = {
    "DSA": build_dsa_pack,
    "Biology": build_biology_pack,
}


def available_packs() -> list[str]:
    return list(PACK_BUILDERS)


def get_pack(subject: str, **kwargs):
    builder = PACK_BUILDERS.get(subject)
    if builder is None:
        raise KeyError(f"unknown domain pack: {subject!r}; available: {available_packs()}")
    return builder(**kwargs)


__all__ = ["available_packs", "get_pack", "build_dsa_pack", "build_biology_pack"]