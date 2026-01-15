"""Fuzzy deduplication for similar listings within a batch."""

from __future__ import annotations

import re
from typing import List, Tuple

from rapidfuzz import fuzz

from ..normalization.schema import Listing


def _normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    if not text:
        return ""
    # Lowercase, remove extra whitespace, remove common filler words
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    # Remove common variations
    text = re.sub(r'\bfor sale\b', '', text)
    text = re.sub(r'\bor trade\b', '', text)
    text = re.sub(r'\bby owner\b', '', text)
    return text.strip()


def _are_similar(listing1: Listing, listing2: Listing, threshold: int = 80) -> bool:
    """Check if two listings are similar enough to be duplicates."""
    # Compare titles/descriptions
    text1 = _normalize_text(listing1.address.raw or listing1.description_raw or "")
    text2 = _normalize_text(listing2.address.raw or listing2.description_raw or "")

    if not text1 or not text2:
        return False

    # Use token set ratio for better matching of reordered words
    title_ratio = fuzz.token_set_ratio(text1, text2)

    if title_ratio >= threshold:
        return True

    # Also check if one is substring of another (partial match)
    partial_ratio = fuzz.partial_ratio(text1, text2)
    if partial_ratio >= 90:
        return True

    return False


def dedupe_batch(listings: List[Listing], threshold: int = 80) -> Tuple[List[Listing], int]:
    """
    Remove duplicate listings from a batch using fuzzy matching.

    Returns:
        Tuple of (deduplicated listings, number of duplicates removed)
    """
    if not listings:
        return [], 0

    # Track which listings to keep
    keep_indices = []
    seen_groups: List[List[int]] = []  # Groups of similar listing indices

    for i, listing in enumerate(listings):
        # Check if this listing is similar to any existing group
        found_group = False
        for group in seen_groups:
            # Compare against first listing in group (representative)
            if _are_similar(listing, listings[group[0]], threshold):
                group.append(i)
                found_group = True
                break

        if not found_group:
            # Start a new group with this listing
            seen_groups.append([i])

    # Keep only the first listing from each group
    for group in seen_groups:
        keep_indices.append(group[0])

    # Sort to maintain original order
    keep_indices.sort()

    deduped = [listings[i] for i in keep_indices]
    removed = len(listings) - len(deduped)

    return deduped, removed
