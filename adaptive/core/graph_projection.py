from __future__ import annotations

from adaptive.core.curriculum_graph import NODE_CONCEPT, NODE_TOPIC, CurriculumGraph
from adaptive.core.learner_state import LearnerStateEngine
from adaptive.types import (
    STATUS_ACTIVE_BLOCKER,
    STATUS_DEVELOPING,
    STATUS_NEEDS_REVIEW,
    STATUS_STALE,
    STATUS_VERIFIED,
)

_MARKERS = {
    STATUS_VERIFIED: "OK",
    STATUS_DEVELOPING: "~~",
    STATUS_NEEDS_REVIEW: "  ",
    STATUS_ACTIVE_BLOCKER: "!!",
    STATUS_STALE: "??",
}


def concept_marker(state: LearnerStateEngine, concept_id: str) -> str:
    st = state.state(concept_id)
    if st.active_gap_state == "recurring":
        return "!!"
    return _MARKERS.get(st.current_status, "  ")


def render_learning_map(graph: CurriculumGraph, state: LearnerStateEngine, subject: str) -> str:
    """Derived, learner-visible projection of the curriculum graph (G_visible = Pi(G_K, B_u))."""
    lines: list[str] = []
    for nid, node in graph.nodes.items():
        if node.kind != NODE_TOPIC or node.subject != subject:
            continue
        lines.append(f"{node.name}")
        children = [e.source for e in graph.edges if e.target == nid and e.kind == "part_of"]
        for child in children:
            child_node = graph.concept(child)
            if child_node is None or child_node.kind != NODE_CONCEPT:
                continue
            marker = concept_marker(state, child)
            lines.append(f"  |-- {child_node.name} [{marker}]")
            sub = [e.source for e in graph.edges if e.target == child and e.kind == "part_of"]
            for s in sub:
                s_node = graph.concept(s)
                if s_node is None:
                    continue
                sub_marker = concept_marker(state, s)
                lines.append(f"      +-- {s_node.name} [{sub_marker}]")
            for pr in graph.prerequisites(child):
                pr_node = graph.concept(pr)
                if pr_node is not None and pr_node.kind == NODE_CONCEPT and pr not in sub:
                    lines.append(f"          (needs {pr_node.name})")
    return "\n".join(lines)


def render_abstention(top: str, posterior: float) -> str:
    return (
        "INSUFFICIENT EVIDENCE\n"
        f"  top hypothesis: {top} at {posterior:.0%}\n"
        "  no blocking gap cleared the confidence threshold.\n"
        "  -> ask one more diagnostic OR escalate to the supervisor OR mark 'needs more evidence'."
    )