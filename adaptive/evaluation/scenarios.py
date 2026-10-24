from __future__ import annotations

from adaptive.types import Event, GoldScenario


def ts(day: int, hour: int) -> str:
    return f"2026-08-{day:02d}T{hour:02d}:10:00+05:30"


def build_dsa_scenarios(pack) -> list[GoldScenario]:
    adapter = pack.evidence_adapter

    def code_ev(session, day, hour, **kw) -> Event:
        base = {"session_id": session, "timestamp": ts(day, hour), "concept": "binary_search", "concept_strengths": [1.0, 0.35, 0.2]}
        base.update(kw)
        return adapter(base)

    return [
        GoldScenario(
            id="dsa-01",
            subject="DSA",
            target_concept="binary_search",
            name="Recurring boundary-update stall",
            seed_history=[
                code_ev("dsa-s1", 10, 19, test_results={"passed": ["normal_asc"], "failed": ["left_boundary"]}, failure_classes=["left_boundary"], static_pattern="low_mid_no_increment", recurrence=True),
                code_ev("dsa-s2", 12, 18, test_results={"passed": ["normal_asc", "normal_desc"], "failed": ["left_boundary", "duplicate_values"]}, failure_classes=["left_boundary", "duplicate_values"], static_pattern="low_mid_no_increment", recurrence=True),
            ],
            current_evidence=code_ev(
                "dsa-s3", 17, 22,
                test_results={"passed": ["normal_asc", "normal_desc"], "failed": ["left_boundary", "single_element"]},
                failure_classes=["left_boundary", "single_element"],
                static_pattern="low_mid_no_increment",
                recurrence=True,
                code="while low < high:\n    mid = (low + high) // 2\n    if arr[mid] < target:\n        low = mid\n    else:\n        high = mid",
            ),
            true_gap_label="mc_boundary_update",
            valid_diagnostics=["bs_interval_shrink", "bs_missing_element", "bs_low_high_meaning"],
            acceptable_interventions=["HINT", "CONTRASTIVE_EXPLANATION", "REASSESS"],
            unacceptable_interventions=["full_solution"],
            expected_bkt_direction="down",
        ),
        GoldScenario(
            id="dsa-02",
            subject="DSA",
            target_concept="binary_search",
            name="One-off inclusive/exclusive bound slip",
            seed_history=[
                code_ev("dsa-s4", 13, 17, test_results={"passed": ["normal_asc"], "failed": []}, failure_classes=[], static_pattern=None, recurrence=False),
            ],
            current_evidence=code_ev(
                "dsa-s5", 18, 11,
                test_results={"passed": ["normal_asc", "normal_desc", "duplicate_values"], "failed": ["left_boundary"]},
                failure_classes=["left_boundary"],
                static_pattern="off_by_one_bound",
                recurrence=False,
                code="low, high = 0, n\nwhile low < high:\n    mid = (low + high) // 2\n    if arr[mid] < target:\n        low = mid + 1\n    else:\n        high = mid - 1",
            ),
            true_gap_label="mc_off_by_one",
            valid_diagnostics=["bs_interval_shrink", "bs_missing_element"],
            acceptable_interventions=["HINT", "CONTRASTIVE_EXPLANATION"],
            unacceptable_interventions=["PREREQUISITE_REWIND:arrays"],
            expected_bkt_direction="down",
        ),
        GoldScenario(
            id="dsa-03",
            subject="DSA",
            target_concept="binary_search",
            name="Recurring loop-invariant confusion",
            seed_history=[
                code_ev("dsa-s6", 9, 20, test_results={"passed": [], "failed": ["normal_asc"]}, failure_classes=["loop_never_terminates"], static_pattern="loop_never_terminates", recurrence=True),
                code_ev("dsa-s7", 11, 21, test_results={"passed": ["normal_asc"], "failed": ["single_element"]}, failure_classes=["single_element"], static_pattern="loop_never_terminates", recurrence=True),
            ],
            current_evidence=code_ev(
                "dsa-s8", 17, 20,
                test_results={"passed": [], "failed": ["normal_asc", "single_element"]},
                failure_classes=["loop_never_terminates"],
                static_pattern="loop_never_terminates",
                recurrence=True,
                code="while low <= high:\n    mid = (low + high) // 2\n    if arr[mid] == target:\n        return mid\n    elif arr[mid] < target:\n        low = mid\n    else:\n        high = mid",
            ),
            true_gap_label="mc_loop_invariant_misuse",
            valid_diagnostics=["bs_interval_shrink", "bs_low_high_meaning"],
            acceptable_interventions=["CONTRASTIVE_EXPLANATION", "HINT"],
            unacceptable_interventions=["full_solution"],
            expected_bkt_direction="down",
        ),
        GoldScenario(
            id="dsa-04",
            subject="DSA",
            target_concept="binary_search",
            name="Correct concept, implementation slip on single element",
            seed_history=[
                code_ev("dsa-s9", 8, 16, test_results={"passed": ["normal_asc", "normal_desc", "left_boundary"], "failed": []}, failure_classes=[], static_pattern=None, recurrence=False),
                code_ev("dsa-s10", 14, 15, test_results={"passed": ["normal_asc", "duplicate_values"], "failed": []}, failure_classes=[], static_pattern=None, recurrence=False),
            ],
            current_evidence=code_ev(
                "dsa-s11", 17, 23,
                test_results={"passed": ["normal_asc", "normal_desc"], "failed": ["single_element"]},
                failure_classes=["single_element"],
                static_pattern="comparison_then_binary",
                recurrence=False,
                code="while low < high:\n    mid = (low + high) // 2\n    if arr[mid] < target:\n        low = mid + 1\n    else:\n        high = mid\nreturn low if arr[low] == target else -1",
            ),
            true_gap_label="binary_search",
            valid_diagnostics=["bs_interval_shrink"],
            acceptable_interventions=["HINT"],
            unacceptable_interventions=["CONTRASTIVE_EXPLANATION:mc_boundary_update"],
            expected_bkt_direction="down",
        ),
        GoldScenario(
            id="dsa-05",
            subject="DSA",
            target_concept="binary_search",
            name="Careless one-off slip on healthy history (adversarial)",
            seed_history=[
                code_ev("dsa-s12", 9, 18, test_results={"passed": ["normal_asc", "normal_desc", "left_boundary", "single_element", "duplicate_values"], "failed": []}, failure_classes=[], static_pattern=None, recurrence=False),
                code_ev("dsa-s13", 15, 20, test_results={"passed": ["normal_asc", "normal_desc", "left_boundary", "single_element"], "failed": []}, failure_classes=[], static_pattern=None, recurrence=False),
            ],
            current_evidence=code_ev(
                "dsa-s14", 18, 10,
                test_results={"passed": ["normal_asc", "normal_desc"], "failed": ["single_element"]},
                failure_classes=["single_element"],
                static_pattern="off_by_one_bound",
                recurrence=False,
                code="low, high = 0, n - 1\nwhile low <= high:\n    mid = (low + high) // 2\n    if arr[mid] < target:\n        low = mid + 1\n    else:\n        high = mid - 1",
            ),
            true_gap_label=None,
            expects_abstention=True,
            expected_bkt_direction="down",
        ),
        GoldScenario(
            id="dsa-06",
            subject="DSA",
            target_concept="binary_search",
            name="Correct code, misunderstood invariant (adversarial: right answer, wrong reason)",
            seed_history=[
                code_ev("dsa-s15", 10, 21, test_results={"passed": ["normal_asc", "single_element"], "failed": []}, failure_classes=[], static_pattern=None, recurrence=False, evidence_extra={"explained_invariant_wrong": "loop_invariant_misuse_statement"}),
            ],
            current_evidence=code_ev(
                "dsa-s16", 18, 21,
                test_results={"passed": ["normal_asc", "normal_desc", "left_boundary", "single_element"], "failed": []},
                failure_classes=[],
                static_pattern=None,
                recurrence=True,
                evidence_extra={"explained_invariant_wrong": "loop_invariant_misuse_statement"},
                code="while low < high:\n    mid = (low + high) // 2\n    ...  # passes all tests but learner cannot state the invariant",
            ),
            true_gap_label="mc_loop_invariant_misuse",
            valid_diagnostics=["bs_interval_shrink", "bs_low_high_meaning"],
            acceptable_interventions=["CONTRASTIVE_EXPLANATION", "EXPLAIN"],
            unacceptable_interventions=["full_solution"],
            expected_bkt_direction="up",
        ),
    ]


def build_biology_scenarios(pack) -> list[GoldScenario]:
    adapter = pack.evidence_adapter

    def mc_ev(session, day, hour, **kw) -> Event:
        base = {"session_id": session, "timestamp": ts(day, hour), "concept": "golgi", "concept_strengths": [1.0, 0.35], "input_mode": "voice"}
        base.update(kw)
        return adapter(base)

    return [
        GoldScenario(
            id="bio-01",
            subject="Biology",
            target_concept="golgi",
            name="Recurring RER vs Golgi packaging confusion",
            seed_history=[
                mc_ev("bio-s1", 11, 12, question_id="q1", selected_option=1, correct_option=0, distractor_pattern="attributed_packaging_to_rer", recurrence=True),
                mc_ev("bio-s2", 13, 12, question_id="q2", selected_option=1, correct_option=0, distractor_pattern="attributed_packaging_to_rer", recurrence=True),
            ],
            current_evidence=mc_ev(
                "bio-s3", 17, 13,
                question_id="q3", selected_option=1, correct_option=0,
                distractor_pattern="attributed_packaging_to_rer", recurrence=True,
            ),
            true_gap_label="mc_rer_golgi_confusion",
            valid_diagnostics=["bio_golgi_function", "bio_rer_role", "bio_protein_path"],
            acceptable_interventions=["CONTRASTIVE_EXPLANATION", "REASSESS"],
            unacceptable_interventions=["PREREQUISITE_REWIND:organelles"],
            expected_bkt_direction="down",
        ),
        GoldScenario(
            id="bio-02",
            subject="Biology",
            target_concept="golgi",
            name="Golgi-does-synthesis misconception",
            seed_history=[
                mc_ev("bio-s4", 15, 14, question_id="q5", selected_option=0, correct_option=0, distractor_pattern=None, recurrence=False),
            ],
            current_evidence=mc_ev(
                "bio-s5", 18, 15,
                question_id="q6", selected_option=0, correct_option=1,
                distractor_pattern="attributed_synthesis_to_golgi", recurrence=False,
            ),
            true_gap_label="mc_golgi_synthesis_confusion",
            valid_diagnostics=["bio_golgi_function", "bio_rer_role"],
            acceptable_interventions=["CONTRASTIVE_EXPLANATION"],
            unacceptable_interventions=["full_solution"],
            expected_bkt_direction="down",
        ),
        GoldScenario(
            id="bio-03",
            subject="Biology",
            target_concept="rough_er",
            name="RER vs lysosome digestion confusion",
            seed_history=[
                mc_ev("bio-s6", 16, 16, question_id="q7", selected_option=3, correct_option=1, distractor_pattern="attributed_digestion_to_rer", recurrence=True),
            ],
            current_evidence=mc_ev(
                "bio-s7", 19, 17,
                question_id="q8", selected_option=3, correct_option=1,
                distractor_pattern="attributed_digestion_to_rer", recurrence=True,
            ),
            true_gap_label="mc_rer_lysosome_confusion",
            valid_diagnostics=["bio_rer_role", "bio_protein_path"],
            acceptable_interventions=["CONTRASTIVE_EXPLANATION"],
            unacceptable_interventions=["HINT:golgi"],
            expected_bkt_direction="down",
        ),
        GoldScenario(
            id="bio-04",
            subject="Biology",
            target_concept="golgi",
            name="Missing prerequisite on organelle roles",
            seed_history=[],
            current_evidence=mc_ev(
                "bio-s8", 20, 18,
                question_id="q9", selected_option=3, correct_option=0,
                distractor_pattern="incomplete_organelle_roles", recurrence=False,
            ),
            true_gap_label="rough_er",
            valid_diagnostics=["bio_rer_role", "bio_golgi_function"],
            acceptable_interventions=["PREREQUISITE_REWIND", "EXPLAIN"],
            unacceptable_interventions=["CONTRASTIVE_EXPLANATION:mc_rer_golgi_confusion"],
            expected_bkt_direction="down",
        ),
        GoldScenario(
            id="bio-05",
            subject="Biology",
            target_concept="golgi",
            name="Correct answer by guessing, no durable evidence (adversarial)",
            seed_history=[],
            current_evidence=mc_ev(
                "bio-s9", 21, 11,
                question_id="q10", selected_option=0, correct_option=0,
                distractor_pattern=None, recurrence=False,
            ),
            true_gap_label=None,
            expects_abstention=True,
            expected_bkt_direction="up",
        ),
        GoldScenario(
            id="bio-06",
            subject="Biology",
            target_concept="golgi",
            name="One weak confusing answer on strong history (adversarial careless)",
            seed_history=[
                mc_ev("bio-ra", 12, 10, question_id="q11", selected_option=0, correct_option=0, distractor_pattern=None, recurrence=False),
                mc_ev("bio-rb", 16, 10, question_id="q12", selected_option=0, correct_option=0, distractor_pattern=None, recurrence=False),
            ],
            current_evidence=mc_ev(
                "bio-s10", 21, 12,
                question_id="q13", selected_option=2, correct_option=0,
                distractor_pattern="attributed_secretion_to_peroxisome", recurrence=False,
            ),
            true_gap_label=None,
            expects_abstention=True,
            expected_bkt_direction="down",
        ),
    ]


def build_scenarios(subject: str, pack) -> list[GoldScenario]:
    if subject == "DSA":
        return build_dsa_scenarios(pack)
    if subject == "Biology":
        return build_biology_scenarios(pack)
    raise KeyError(f"no gold scenarios for {subject!r}")