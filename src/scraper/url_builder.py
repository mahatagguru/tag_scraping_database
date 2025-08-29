#!/usr/bin/env python3
"""
URL construction utilities for the scraper.
Handles the complex logic of parsing set names and building correct URLs.
"""

import re
from urllib.parse import quote

# Common base set names that appear in multiple variations
COMMON_BASE_SETS = {
    'Donruss': ['Donruss'],
    'Topps': ['Topps', 'Topps Chrome', 'Topps Finest', 'Topps Now', 'Topps Total Football'],
    'Panini': ['Panini', 'Panini Prizm', 'Panini Select', 'Panini Instant'],
    'Upper Deck': ['Upper Deck'],
    'Fleer': ['Fleer'],
    'Score': ['Score'],
    'Stadium Club': ['Stadium Club'],
    'Bowman': ['Bowman', 'Bowman Chrome'],
    'Leaf': ['Leaf'],
    'Playoff': ['Playoff'],
    'Skybox': ['Skybox'],
    'Pacific': ['Pacific'],
    'Collector\'s Edge': ['Collector\'s Edge'],
    'Pinnacle': ['Pinnacle'],
    'Studio': ['Studio'],
    'Flair': ['Flair'],
    'SP': ['SP'],
    'Ultra': ['Ultra'],
    'Collector\'s Choice': ['Collector\'s Choice'],
    'Classic': ['Classic'],
    'TSC': ['TSC'],
    'Parkside': ['Parkside'],
    'Wild Card': ['Wild Card'],
    'Futera': ['Futera'],
    'NSCC': ['NSCC'],
    'Platinum': ['Platinum'],
    'Pristine': ['Pristine'],
    'Deco': ['Deco'],
    'Showtime': ['Showtime'],
    'Knockout': ['Knockout'],
    'Living': ['Living'],
    'Merlin': ['Merlin', 'Merlin Chrome', 'Merlin Heritage'],
    'Impact': ['Impact'],
    'Jade Edition': ['Jade Edition'],
    'Gold': ['Gold'],
    'Focus': ['Focus'],
    'FuGenZ': ['FuGenZ'],
    'Match Attax': ['Match Attax'],
    'Adrenalyn XL': ['Adrenalyn XL'],
}

def find_base_set(set_name):
    """
    Find the base set name from a set name.
    Returns (base_set, variation) tuple.
    """
    # First, try to find exact matches with common base sets
    for base_group, variations in COMMON_BASE_SETS.items():
        for variation in variations:
            if set_name.startswith(variation):
                remaining = set_name[len(variation):].strip()
                if remaining:
                    return variation, remaining
                else:
                    return variation, None
    
    # If no exact match, try to find patterns
    # Look for camelCase transitions (e.g., "DonrussOptic" -> "Donruss" + "Optic")
    camel_case_match = re.match(r'^([A-Z][a-z]+)([A-Z][a-zA-Z]*.*)$', set_name)
    if camel_case_match:
        base = camel_case_match.group(1)
        variation = camel_case_match.group(2)
        return base, variation
    
    # Look for patterns like "BaseSetVariation" where there's no space
    # Try to find where a word boundary might be
    for i in range(1, len(set_name)):
        if set_name[i].isupper() and set_name[i-1].islower():
            base = set_name[:i]
            variation = set_name[i:]
            return base, variation
    
    # If all else fails, try to split on first space
    if ' ' in set_name:
        parts = set_name.split(' ', 1)
        return parts[0], parts[1]
    
    # No variation found, treat entire name as base
    return set_name, None

def build_set_page_url(category_name, year, set_name, base_url="https://my.taggrading.com"):
    """
    Build the correct set page URL based on the set name structure.
    """
    base_set, variation = find_base_set(set_name)
    
    if variation:
        # URL encode the variation (replace spaces with +)
        encoded_variation = quote(variation, safe='')
        url = f"{base_url}/pop-report/{category_name.title()}/{year}/{base_set}?setName={encoded_variation}"
    else:
        # No variation, just use the base set
        url = f"{base_url}/pop-report/{category_name.title()}/{year}/{base_set}"
    
    return url

def test_url_builder():
    """Test the URL builder with various set name patterns."""
    test_cases = [
        "DonrussNight Moves",
        "DonrussOptic Rated Rookie", 
        "Topps Chrome MLS",
        "Topps Finest Road to UEFA Euro 2024Finest Dual Autographs",
        "Panini Prizm CONMEBOL Copa AmericaManga",
        "Topps Chrome UEFA Club CompetitionsWonderkids",
        "Wild Card LAMiNE YAMAL ComixGoalB",
        "Topps Now MLS",
        "Upper Deck",
        "ClassicLight Blue"
    ]
    
    print("Testing URL Builder:")
    print("=" * 80)
    
    for set_name in test_cases:
        base, variation = find_base_set(set_name)
        url = build_set_page_url("Soccer", "2024", set_name)
        print(f"Set: {set_name}")
        print(f"  Base: '{base}'")
        print(f"  Variation: '{variation}'")
        print(f"  URL: {url}")
        print()

if __name__ == "__main__":
    test_url_builder()

