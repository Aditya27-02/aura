from __future__ import annotations

from adaptive.types import Chunk


def build_dsa_corpus() -> list[Chunk]:
    return [
        Chunk(
            chunk_id="dsa_corpus:bs_what",
            source_id="dsa-101-001",
            subject="DSA",
            topic="Searching",
            concept_ids=["binary_search"],
            content_type="explanation",
            text=(
                "Binary search works on a sorted array. It maintains a candidate interval [low, high] "
                "that must contain the target if the target is present. At each step it compares "
                "arr[mid] with the target and halves the interval, keeping the search O(log n)."
            ),
            difficulty_band="foundation",
        ),
        Chunk(
            chunk_id="dsa_corpus:bs_invariant",
            source_id="dsa-101-002",
            subject="DSA",
            topic="Searching",
            concept_ids=["binary_search", "loop_invariant"],
            content_type="explanation",
            text=(
                "The loop invariant of binary search: before every iteration, if the target is present "
                "in the array, it lies in the interval [low, high]. The while condition only decides "
                "whether the interval is still non-empty; it does not by itself shrink the interval."
            ),
            difficulty_band="medium",
        ),
        Chunk(
            chunk_id="dsa_corpus:bs_boundary",
            source_id="dsa-101-003",
            subject="DSA",
            topic="Searching",
            concept_ids=["binary_search", "boundary_handling"],
            content_type="explanation",
            text=(
                "To guarantee progress, the update must move the boundary strictly past mid: when "
                "arr[mid] < target use low = mid + 1, and when arr[mid] > target use high = mid - 1. "
                "If you write low = mid, an interval of length two can stay the same forever."
            ),
            difficulty_band="medium",
        ),
        Chunk(
            chunk_id="dsa_corpus:bs_first",
            source_id="dsa-102-001",
            subject="DSA",
            topic="Searching",
            concept_ids=["binary_search", "boundary_handling"],
            content_type="worked_example",
            text=(
                "First-occurrence search: find the leftmost index of a repeated value. Use inclusive "
                "bounds, prefer the left half when arr[mid] == target, and only tighten with "
                "high = mid in that case so you do not skip the first copy."
            ),
            difficulty_band="hard",
        ),
        Chunk(
            chunk_id="dsa_corpus:bs_missing",
            source_id="dsa-101-004",
            subject="DSA",
            topic="Searching",
            concept_ids=["binary_search", "boundary_handling"],
            content_type="hint",
            text=(
                "If the target is not in the array, correct binary search keeps shrinking the interval "
                "until low > high, then reports that the target is absent. It never needs a sentinel."
            ),
            difficulty_band="medium",
        ),
        Chunk(
            chunk_id="dsa_corpus:bs_complexity",
            source_id="dsa-101-005",
            subject="DSA",
            topic="Complexity",
            concept_ids=["binary_search", "complexity_analysis"],
            content_type="explanation",
            text=(
                "Each step halves the candidate interval, so the number of comparisons is bounded by "
                "log2(n). Binary search is therefore O(log n) in the worst case, provided every step "
                "truly halves the interval."
            ),
            difficulty_band="easy",
        ),
        Chunk(
            chunk_id="dsa_corpus:recursion_base",
            source_id="dsa-201-001",
            subject="DSA",
            topic="Recursion",
            concept_ids=["recursion"],
            content_type="explanation",
            text=(
                "A recursive function needs a base case that terminates without another call, and every "
                "recursive call must move the input closer to that base case. A missing or wrong base "
                "case is the most common source of infinite recursion and wrong results."
            ),
            difficulty_band="medium",
        ),
    ]