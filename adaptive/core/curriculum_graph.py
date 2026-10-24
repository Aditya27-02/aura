from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

EDGE_PREREQUISITE = "prerequisite_of"
EDGE_PART = "part_of"
EDGE_RELATED = "related_to"
EDGE_ASSESSED = "assessed_by"
EDGE_CONFUSED = "commonly_confused_with"

EDGE_KINDS = {
    EDGE_PREREQUISITE,
    EDGE_PART,
    EDGE_RELATED,
    EDGE_ASSESSED,
    EDGE_CONFUSED,
}

NODE_SUBJECT = "subject"
NODE_TOPIC = "topic"
NODE_CONCEPT = "concept"
NODE_SKILL = "skill"
NODE_MISCONCEPTION = "misconception_class"
NODE_QUESTION = "question_template"


@dataclass
class ConceptNode:
    id: str
    subject: str
    topic: str
    name: str
    kind: str = NODE_CONCEPT


@dataclass
class Edge:
    source: str
    target: str
    kind: str


@dataclass
class CurriculumGraph:
    """Static description of the domain (G_K). Describes the domain, not the learner."""

    nodes: dict[str, ConceptNode] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    _misconceptions: dict[str, list[str]] = field(default_factory=dict)

    def add_node(self, node: ConceptNode) -> None:
        self.nodes[node.id] = node

    def add_nodes(self, nodes: Iterable[ConceptNode]) -> None:
        for node in nodes:
            self.add_node(node)

    def add_edge(self, source: str, target: str, kind: str) -> None:
        if kind not in EDGE_KINDS:
            raise ValueError(f"unknown edge kind: {kind}")
        if source not in self.nodes or target not in self.nodes:
            raise KeyError("edge endpoint must exist as a node")
        self.edges.append(Edge(source=source, target=target, kind=kind))

    def add_prerequisite(self, source: str, target: str) -> None:
        self.add_edge(source, target, EDGE_PREREQUISITE)

    def add_part(self, source: str, target: str) -> None:
        self.add_edge(source, target, EDGE_PART)

    def add_related(self, source: str, target: str) -> None:
        self.add_edge(source, target, EDGE_RELATED)

    def add_confused(self, source: str, target: str) -> None:
        self.add_edge(source, target, EDGE_CONFUSED)

    def add_misconception(self, concept_id: str, misconception_id: str) -> None:
        self._misconceptions.setdefault(concept_id, []).append(misconception_id)

    def concept(self, cid: str) -> Optional[ConceptNode]:
        return self.nodes.get(cid)

    def prerequisites(self, cid: str) -> list[str]:
        return [e.source for e in self.edges if e.target == cid and e.kind == EDGE_PREREQUISITE]

    def prereq_closure(self, cid: str) -> list[str]:
        seen: set[str] = set()
        stack = list(self.prerequisites(cid))
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n)
            stack.extend(self.prerequisites(n))
        return list(seen)

    def relatives(self, cid: str) -> list[str]:
        return [
            e.target if e.source == cid else e.source
            for e in self.edges
            if e.kind == EDGE_RELATED and (e.source == cid or e.target == cid)
        ]

    def misconceptions(self, cid: str) -> list[str]:
        return list(self._misconceptions.get(cid, []))

    def all_concepts(self) -> list[str]:
        return [nid for nid, n in self.nodes.items() if n.kind in (NODE_CONCEPT, NODE_SKILL)]

    def concept_neighborhood(self, cid: str, depth: int = 1) -> set[str]:
        seen: set[str] = {cid}
        frontier = {cid}
        for _ in range(depth):
            nxt: set[str] = set()
            for n in frontier:
                nxt.update(self.prerequisites(n))
                nxt.update(self.relatives(n))
                for child in self.edges:
                    if child.source == n and child.kind == EDGE_PREREQUISITE:
                        nxt.add(child.target)
            frontier = nxt - seen
            seen.update(nxt)
        return seen

    def path_depth(self, source: str, target: str) -> Optional[int]:
        if source == target:
            return 0
        best: Optional[int] = None
        stack = [(source, 0)]
        while stack:
            node, d = stack.pop()
            for pr in self.prerequisites(node):
                if pr == target:
                    best = d + 1 if best is None else min(best, d + 1)
                elif d < 4:
                    stack.append((pr, d + 1))
        return best