from __future__ import annotations

from adaptive.core.diagnosis import SignalModel
from adaptive.core.domain_pack import DomainPack
from adaptive.core.learner_state import BKTParams
from adaptive.domains.biology.corpus import build_biology_corpus
from adaptive.domains.biology.curriculum import build_biology_graph
from adaptive.domains.biology.evidence import normalize_mcq_event
from adaptive.domains.biology.hints import BIOLOGY_HINTS
from adaptive.domains.biology.items import build_biology_items

BIOLOGY_BKT_DEFAULTS = {
    "organelles": BKTParams(prior=0.45, slip=0.08, guess=0.15, learn=0.25),
    "rough_er": BKTParams(prior=0.35, slip=0.10, guess=0.20, learn=0.25),
    "smooth_er": BKTParams(prior=0.30, slip=0.10, guess=0.20, learn=0.25),
    "golgi": BKTParams(prior=0.30, slip=0.10, guess=0.20, learn=0.25),
    "lysosome": BKTParams(prior=0.35, slip=0.10, guess=0.20, learn=0.25),
    "peroxisome": BKTParams(prior=0.30, slip=0.10, guess=0.20, learn=0.25),
    "protein_processing": BKTParams(prior=0.25, slip=0.10, guess=0.20, learn=0.30),
}

BIOLOGY_SIGNAL_MODEL = SignalModel(
    {
        "mc_rer_golgi_confusion": {
            "__prior__": 0.35,
            "attributed_packaging_to_rer": 0.90,
            "attributed_secretion_to_peroxisome": 0.30,
            "confused_rer_golgi": 0.90,
            "attributed_synthesis_to_golgi": 0.20,
        },
        "mc_golgi_synthesis_confusion": {
            "__prior__": 0.20,
            "attributed_synthesis_to_golgi": 0.90,
            "confused_rer_golgi": 0.40,
        },
        "mc_rer_lysosome_confusion": {
            "__prior__": 0.15,
            "attributed_digestion_to_rer": 0.90,
            "attributed_packaging_to_rer": 0.30,
        },
        "rough_er": {
            "__prior__": 0.15,
            "attributed_synthesis_to_golgi": 0.30,
            "confused_rer_golgi": 0.35,
        },
        "golgi": {
            "__prior__": 0.15,
            "attributed_packaging_to_rer": 0.30,
            "attributed_secretion_to_peroxisome": 0.40,
        },
        "organelles": {
            "__prior__": 0.10,
            "attributed_packaging_to_rer": 0.25,
            "attributed_synthesis_to_golgi": 0.25,
        },
    }
)


def build_biology_pack() -> DomainPack:
    return DomainPack(
        name="biology",
        subject="Biology",
        version="0.1.0",
        graph=build_biology_graph(),
        signal_model=BIOLOGY_SIGNAL_MODEL,
        items=build_biology_items(),
        corpus=build_biology_corpus(),
        bkt_defaults=BIOLOGY_BKT_DEFAULTS,
        evidence_adapter=normalize_mcq_event,
        hints=BIOLOGY_HINTS,
    )