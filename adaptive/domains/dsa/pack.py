from __future__ import annotations

from adaptive.core.diagnosis import SignalModel
from adaptive.core.domain_pack import DomainPack
from adaptive.core.learner_state import BKTParams
from adaptive.domains.dsa.corpus import build_dsa_corpus
from adaptive.domains.dsa.curriculum import build_dsa_graph
from adaptive.domains.dsa.evidence import normalize_code_event
from adaptive.domains.dsa.hints import DSA_HINTS
from adaptive.domains.dsa.items import build_dsa_items

DSA_BKT_DEFAULTS = {
    "binary_search": BKTParams(prior=0.30, slip=0.08, guess=0.15, learn=0.30),
    "boundary_handling": BKTParams(prior=0.20, slip=0.10, guess=0.20, learn=0.30),
    "loop_invariant": BKTParams(prior=0.20, slip=0.10, guess=0.20, learn=0.30),
    "arrays": BKTParams(prior=0.55, slip=0.05, guess=0.10, learn=0.25),
    "searching": BKTParams(prior=0.40, slip=0.06, guess=0.10, learn=0.25),
    "complexity_analysis": BKTParams(prior=0.35, slip=0.08, guess=0.15, learn=0.25),
    "recursion": BKTParams(prior=0.30, slip=0.08, guess=0.15, learn=0.30),
}

DSA_SIGNAL_MODEL = SignalModel(
    {
        "mc_boundary_update": {
            "__prior__": 0.30,
            "left_boundary": 0.75,
            "single_element": 0.70,
            "duplicate_values": 0.50,
            "empty_array": 0.30,
            "target_missing": 0.30,
            "low_mid_no_increment": 0.90,
            "high_mid_no_decrement": 0.90,
            "off_by_one_bound": 0.30,
            "loop_never_terminates": 0.80,
            "comparison_then_binary": 0.30,
        },
        "mc_off_by_one": {
            "__prior__": 0.20,
            "left_boundary": 0.70,
            "single_element": 0.50,
            "duplicate_values": 0.30,
            "off_by_one_bound": 0.90,
            "low_mid_no_increment": 0.40,
            "high_mid_no_decrement": 0.40,
            "loop_never_terminates": 0.40,
        },
        "mc_loop_invariant_misuse": {
            "__prior__": 0.20,
            "loop_never_terminates": 0.80,
            "low_mid_no_increment": 0.50,
            "high_mid_no_decrement": 0.50,
            "single_element": 0.40,
            "left_boundary": 0.40,
            "comparison_then_binary": 0.50,
            "loop_invariant_misuse_statement": 0.90,
        },
        "arrays": {
            "__prior__": 0.15,
            "left_boundary": 0.40,
            "off_by_one_bound": 0.50,
            "empty_array": 0.60,
            "target_missing": 0.50,
        },
        "searching": {
            "__prior__": 0.15,
            "target_missing": 0.50,
            "empty_array": 0.40,
        },
        "binary_search": {
            "low_mid_no_increment": 0.85,
            "high_mid_no_decrement": 0.85,
            "off_by_one_bound": 0.40,
        },
    }
)


def build_dsa_pack() -> DomainPack:
    return DomainPack(
        name="dsa",
        subject="DSA",
        version="0.1.0",
        graph=build_dsa_graph(),
        signal_model=DSA_SIGNAL_MODEL,
        items=build_dsa_items(),
        corpus=build_dsa_corpus(),
        bkt_defaults=DSA_BKT_DEFAULTS,
        evidence_adapter=normalize_code_event,
        hints=DSA_HINTS,
    )