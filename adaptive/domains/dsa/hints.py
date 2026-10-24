from __future__ import annotations

DSA_HINTS = {
    "HINT": {
        "binary_search": (
            "Keep the interval strictly shrinking: when you move past mid, use mid + 1 or mid - 1. "
            "Now try the case where the remaining interval has length one."
        ),
        "boundary_handling": (
            "On an interval of length one, low == high. Check what your update does to that interval."
        ),
        "_default": "Focus your next attempt on the failing edge case without jumping to the full solution.",
    },
    "PREREQUISITE_REWIND": {
        "arrays": (
            "Indexing is 0-based and the candidate interval is [low, high]. Trace a two-element "
            "array by hand before writing code."
        ),
        "_default": "Let us quickly revisit the prerequisite idea before continuing.",
    },
    "CONTRASTIVE_EXPLANATION": {
        "mc_boundary_update": (
            "A loop that never shrinks its interval is not binary search. The shrink comes from the "
            "update rule, not from the while condition."
        ),
        "mc_off_by_one": (
            "Off-by-one usually means inclusive and exclusive bounds are mixed. Pick one convention "
            "for [low, high] and keep it everywhere."
        ),
        "mc_loop_invariant_misuse": (
            "The loop condition decides when to stop; the updates decide whether the interval "
            "actually shrinks. Both matter."
        ),
        "_default": "Here is a short distinction for the concept that is being confused.",
    },
    "EXPLAIN": {
        "binary_search": (
            "Binary search maintains a candidate interval; each step compares arr[mid] and halves "
            "the interval, keeping the search O(log n)."
        ),
        "_default": "Let us work on this together.",
    },
    "REASSESS": {
        "binary_search": "Quick check: write a correct binary search for a single-element array.",
        "_default": "Quick reassessment before we continue.",
    },
    "PRACTICE": {
        "binary_search": "Now implement the first-occurrence variant from the same invariant.",
        "_default": "Let us apply this with one more practice item.",
    },
}