from __future__ import annotations

from adaptive.types import Chunk


def build_biology_corpus() -> list[Chunk]:
    return [
        Chunk(
            chunk_id="bio_corpus:rer_role",
            source_id="bio-301-001",
            subject="Biology",
            topic="Cell Biology",
            concept_ids=["rough_er"],
            content_type="explanation",
            text=(
                "The rough endoplasmic reticulum is covered with ribosomes and is the site of protein "
                "synthesis and initial folding/processing of proteins destined for secretion or "
                "membranes. It does not sort and package proteins for release."
            ),
            difficulty_band="foundation",
        ),
        Chunk(
            chunk_id="bio_corpus:golgi_packaging",
            source_id="bio-301-002",
            subject="Biology",
            topic="Cell Biology",
            concept_ids=["golgi"],
            content_type="explanation",
            text=(
                "The Golgi apparatus modifies, sorts, and packages proteins received from the rough ER "
                "into vesicles that travel to the plasma membrane for secretion or to other "
                "destinations. Attributing packaging to the rough ER is a common confusion."
            ),
            difficulty_band="foundation",
        ),
        Chunk(
            chunk_id="bio_corpus:protein_path",
            source_id="bio-301-003",
            subject="Biology",
            topic="Cell Biology",
            concept_ids=["protein_processing", "golgi", "rough_er"],
            content_type="explanation",
            text=(
                "The secretion pathway: ribosomes on the rough ER synthesize the protein, it folds "
                "inside the ER, is shipped in a vesicle to the Golgi, which modifies and repackages "
                "it, then a vesicle fuses with the membrane to release it outside the cell."
            ),
            difficulty_band="medium",
        ),
        Chunk(
            chunk_id="bio_corpus:smooth_er",
            source_id="bio-301-004",
            subject="Biology",
            topic="Cell Biology",
            concept_ids=["smooth_er"],
            content_type="explanation",
            text=(
                "Smooth ER lacks ribosomes; its roles include lipid synthesis, carbohydrate "
                "metabolism, calcium storage, and detoxification. It is not the packaging station."
            ),
            difficulty_band="easy",
        ),
        Chunk(
            chunk_id="bio_corpus:lysosome_digestion",
            source_id="bio-301-005",
            subject="Biology",
            topic="Cell Biology",
            concept_ids=["lysosome"],
            content_type="explanation",
            text=(
                "Lysosomes contain digestive enzymes that break down worn-out organelles and "
                "engulfed material. If their enzymes leaked freely into the cytoplasm, the cell "
                "would digest its own components."
            ),
            difficulty_band="medium",
        ),
        Chunk(
            chunk_id="bio_corpus:peroxisome",
            source_id="bio-301-006",
            subject="Biology",
            topic="Cell Biology",
            concept_ids=["peroxisome"],
            content_type="explanation",
            text=(
                "Peroxisomes detoxify harmful substances such as hydrogen peroxide and perform fatty "
                "acid oxidation. They are not part of the protein secretion pathway."
            ),
            difficulty_band="medium",
        ),
        Chunk(
            chunk_id="bio_corpus:organelle_overview",
            source_id="bio-300-001",
            subject="Biology",
            topic="Cell Biology",
            concept_ids=["organelles"],
            content_type="definition",
            text=(
                "Organelles are specialised structures inside eukaryotic cells. Nucleus stores DNA; "
                "ER, Golgi, lysosomes, peroxisomes, mitochondria and chloroplasts each carry out "
                "distinct functions that must be kept separate when explaining cell processes."
            ),
            difficulty_band="foundation",
        ),
    ]