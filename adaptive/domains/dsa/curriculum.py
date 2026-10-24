from __future__ import annotations

from adaptive.core.curriculum_graph import (
    NODE_CONCEPT,
    NODE_MISCONCEPTION,
    NODE_SUBJECT,
    NODE_TOPIC,
    ConceptNode,
    CurriculumGraph,
)


def build_dsa_graph() -> CurriculumGraph:
    g = CurriculumGraph()
    g.add_nodes(
        [
            ConceptNode("dsa", "DSA", "", "Data Structures & Algorithms", NODE_SUBJECT),
            ConceptNode("searching", "DSA", "Searching", "Searching Algorithms", NODE_TOPIC),
            ConceptNode("arrays", "DSA", "Arrays", "Arrays and Indexing", NODE_CONCEPT),
            ConceptNode("binary_search", "DSA", "Searching", "Binary Search", NODE_CONCEPT),
            ConceptNode("boundary_handling", "DSA", "Searching", "Boundary Handling", NODE_CONCEPT),
            ConceptNode("loop_invariant", "DSA", "Searching", "Loop Invariant", NODE_CONCEPT),
            ConceptNode("complexity_analysis", "DSA", "Complexity", "Time Complexity", NODE_CONCEPT),
            ConceptNode("recursion", "DSA", "Recursion", "Recursion and Base Cases", NODE_CONCEPT),
            ConceptNode("mc_boundary_update", "DSA", "Misconceptions", "Boundary update confusion", NODE_MISCONCEPTION),
            ConceptNode("mc_off_by_one", "DSA", "Misconceptions", "Off-by-one confusion", NODE_MISCONCEPTION),
            ConceptNode("mc_loop_invariant_misuse", "DSA", "Misconceptions", "Loop invariant misuse", NODE_MISCONCEPTION),
        ]
    )
    g.add_part("searching", "dsa")
    g.add_part("binary_search", "searching")
    g.add_part("arrays", "searching")
    g.add_prerequisite("arrays", "binary_search")
    g.add_prerequisite("binary_search", "boundary_handling")
    g.add_prerequisite("binary_search", "loop_invariant")
    g.add_related("complexity_analysis", "binary_search")
    g.add_related("recursion", "binary_search")
    g.add_confused("mc_boundary_update", "mc_off_by_one")
    g.add_confused("mc_boundary_update", "mc_loop_invariant_misuse")

    g.add_misconception("binary_search", "mc_boundary_update")
    g.add_misconception("binary_search", "mc_off_by_one")
    g.add_misconception("binary_search", "mc_loop_invariant_misuse")
    return g