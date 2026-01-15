from __future__ import annotations

import json
import os
import re
from typing import Dict

from ..normalization.schema import Listing


def _build_prompt(listing: Listing, profile: Dict) -> str:
    """Build prompt for LLM scoring."""
    listing_info = f"""
LISTING:
- Title: {listing.title}
- Price: ${listing.price or 'Unknown'}
- Location: {listing.address.raw if listing.address else 'Unknown'}
- URL: {listing.listing_url}
- Description: {listing.description_raw or 'No description'}
"""

    profile_summary = f"""
BUYER PROFILE:
- Location: Within {profile.get('location', {}).get('max_drive_time_to_anchor_minutes', 30)} min of {profile.get('location', {}).get('anchor_city', 'Unknown')}, {profile.get('location', {}).get('anchor_state', '')}
- Max Price: ${profile.get('price', {}).get('max_list_price_usd', 'Unknown')}
- Property Types: {', '.join(profile.get('core_filters_for_basic_search_ai', {}).get('property_type_include', []))}
- Min Bedrooms: {profile.get('core_filters_for_basic_search_ai', {}).get('bedrooms_min', 'Any')}
- Min Bathrooms: {profile.get('core_filters_for_basic_search_ai', {}).get('bathrooms_min', 'Any')}
- Min Lot Size: {profile.get('core_filters_for_basic_search_ai', {}).get('lot_size_acres_min', 'Any')} acres
- Deal Breakers: {', '.join(profile.get('deal_breakers_summary', [])[:5])}
"""

    return f"""You are a real estate matching assistant. Score how well this listing matches the buyer's profile.

{listing_info}
{profile_summary}

Respond in this exact JSON format:
{{"confidence": 0.0-1.0, "reasons": ["reason1", "reason2", "reason3"]}}

- confidence: 0.0 = terrible match, 1.0 = perfect match
- reasons: 2-4 short bullet points explaining the score

JSON response:"""


def _parse_response(response_text: str) -> Dict:
    """Parse LLM response into confidence and reasons."""
    # Try to extract JSON from response
    try:
        # Look for JSON object in response
        match = re.search(r'\{[^{}]*"confidence"[^{}]*\}', response_text, re.DOTALL)
        if match:
            data = json.loads(match.group())
            confidence = float(data.get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))  # Clamp to 0-1
            reasons = data.get("reasons", ["Unable to parse reasons"])
            if isinstance(reasons, str):
                reasons = [reasons]
            return {"confidence": confidence, "reasons": reasons}
    except (json.JSONDecodeError, ValueError, KeyError):
        pass

    # Fallback if parsing fails
    return {"confidence": 0.5, "reasons": ["Could not parse LLM response"]}


def score_listing(listing: Listing, profile: Dict) -> Dict:
    """Score a listing against the buyer profile using LLM."""
    # Check if API key is available
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        # Fail open - return neutral score if no API key
        return {
            "confidence": 0.5,
            "reasons": ["AI scoring unavailable - no API key configured"],
        }

    try:
        import litellm

        prompt = _build_prompt(listing, profile)

        # Use OpenAI by default, fallback to Anthropic
        model = "gpt-4o-mini" if os.environ.get("OPENAI_API_KEY") else "claude-3-haiku-20240307"

        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.3,
        )

        response_text = response.choices[0].message.content
        return _parse_response(response_text)

    except ImportError:
        return {
            "confidence": 0.5,
            "reasons": ["litellm not installed"],
        }
    except Exception as e:
        # Fail open on any API error
        return {
            "confidence": 0.5,
            "reasons": [f"AI scoring error: {str(e)[:50]}"],
        }
