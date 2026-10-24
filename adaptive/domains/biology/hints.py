from __future__ import annotations

BIOLOGY_HINTS = {
    "CONTRASTIVE_EXPLANATION": {
        "mc_rer_golgi_confusion": (
            "RER is associated with protein synthesis and initial processing. The Golgi modifies, "
            "sorts, and packages proteins for secretion. The packaging step happens at the Golgi, "
            "not the RER."
        ),
        "mc_golgi_synthesis_confusion": (
            "The Golgi does not make proteins; ribosomes on the rough ER do. The Golgi receives "
            "them and repackages them for release."
        ),
        "mc_rer_lysosome_confusion": (
            "Digestion happens in lysosomes, not the rough ER. RER is for protein synthesis and "
            "initial processing."
        ),
        "_default": "Here is a short distinction for the concept that is being confused.",
    },
    "EXPLAIN": {
        "golgi": (
            "The Golgi apparatus modifies, sorts, and packages proteins received from the rough ER "
            "into vesicles for secretion or for other destinations."
        ),
        "rough_er": (
            "Rough ER carries ribosomes on its surface and is where proteins are synthesized and "
            "initially processed."
        ),
        "_default": "Let us work on this together.",
    },
    "HINT": {
        "golgi": "Think about the last stop before a vesicle fuses with the membrane to release proteins.",
        "rough_er": "Look for the organelle that carries ribosomes.",
        "_default": "Try to recall the organelle's most specific job in the secretion pathway.",
    },
    "PREREQUISITE_REWIND": {
        "organelles": "Let us quickly re-check the role of each organelle before comparing two of them.",
        "_default": "Let us quickly revisit the prerequisite idea before continuing.",
    },
    "REASSESS": {
        "golgi": "Quick check: a protein was made on the rough ER. Where does it go next?",
        "_default": "Quick reassessment before we continue.",
    },
    "PRACTICE": {
        "golgi": "Now fill in the blank about where proteins are sorted and packaged.",
        "_default": "Let us apply this with one more practice item.",
    },
}