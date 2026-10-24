from __future__ import annotations

from adaptive.core.curriculum_graph import (
    NODE_CONCEPT,
    NODE_MISCONCEPTION,
    NODE_SUBJECT,
    NODE_TOPIC,
    ConceptNode,
    CurriculumGraph,
)


def build_biology_graph() -> CurriculumGraph:
    g = CurriculumGraph()
    g.add_nodes(
        [
            ConceptNode("biology", "Biology", "", "Cell Biology", NODE_SUBJECT),
            ConceptNode("cell_biology", "Biology", "Cell Biology", "Cell Biology", NODE_TOPIC),
            ConceptNode("organelles", "Biology", "Cell Biology", "Organelles", NODE_CONCEPT),
            ConceptNode("rough_er", "Biology", "Cell Biology", "Rough ER", NODE_CONCEPT),
            ConceptNode("smooth_er", "Biology", "Cell Biology", "Smooth ER", NODE_CONCEPT),
            ConceptNode("golgi", "Biology", "Cell Biology", "Golgi Apparatus", NODE_CONCEPT),
            ConceptNode("lysosome", "Biology", "Cell Biology", "Lysosome", NODE_CONCEPT),
            ConceptNode("peroxisome", "Biology", "Cell Biology", "Peroxisome", NODE_CONCEPT),
            ConceptNode("protein_processing", "Biology", "Cell Biology", "Protein Processing", NODE_CONCEPT),
            ConceptNode("mc_rer_golgi_confusion", "Biology", "Misconceptions", "RER vs Golgi confusion", NODE_MISCONCEPTION),
            ConceptNode("mc_golgi_synthesis_confusion", "Biology", "Misconceptions", "Golgi does synthesis confusion", NODE_MISCONCEPTION),
            ConceptNode("mc_rer_lysosome_confusion", "Biology", "Misconceptions", "RER vs lysosome confusion", NODE_MISCONCEPTION),
        ]
    )
    g.add_part("cell_biology", "biology")
    g.add_part("organelles", "cell_biology")
    g.add_part("rough_er", "organelles")
    g.add_part("smooth_er", "organelles")
    g.add_part("golgi", "organelles")
    g.add_part("lysosome", "organelles")
    g.add_part("peroxisome", "organelles")
    g.add_prerequisite("organelles", "rough_er")
    g.add_prerequisite("organelles", "smooth_er")
    g.add_prerequisite("organelles", "golgi")
    g.add_prerequisite("rough_er", "golgi")
    g.add_prerequisite("rough_er", "protein_processing")
    g.add_prerequisite("golgi", "protein_processing")
    g.add_related("rough_er", "golgi")
    g.add_related("rough_er", "smooth_er")
    g.add_confused("mc_rer_golgi_confusion", "mc_golgi_synthesis_confusion")

    g.add_misconception("golgi", "mc_rer_golgi_confusion")
    g.add_misconception("golgi", "mc_golgi_synthesis_confusion")
    g.add_misconception("rough_er", "mc_rer_golgi_confusion")
    g.add_misconception("rough_er", "mc_rer_lysosome_confusion")
    return g