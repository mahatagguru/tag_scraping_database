#!/usr/bin/env python3
"""
Test script to verify URL extraction from table rows.
Tests the updated crawlers to ensure they extract URLs from the first cell of each row.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper.card_crawler import extract_cards
from scraper.set_crawler import extract_sets, fetch_rendered_html
from scraper.year_crawler import extract_years


def test_set_url_extraction():
    """Test URL extraction from set table rows."""
    print("Testing set URL extraction...")
    
    # Test with the example URL from the user's requirements
    test_url = "https://my.taggrading.com/pop-report/Baseball/1989"
    
    try:
        html = fetch_rendered_html(test_url)
        sets = extract_sets(html)
        
        print(f"Found {len(sets)} sets:")
        for i, s in enumerate(sets):
            print(f"  {i+1}. Set: '{s['set_title']}'")
            print(f"     URLs: {s['set_urls']}")
            print(f"     Grades: {s['grades']}")
            print()
            
        # Verify the example row from user requirements
        for s in sets:
            if "Classic" in s['set_title'] and "Light Blue" in s['set_title']:
                print("✓ Found 'Classic Light Blue' set!")
                print(f"  Title: '{s['set_title']}'")
                print(f"  URLs: {s['set_urls']}")
                expected_url = "https://my.taggrading.com/pop-report/Baseball/1989/Classic?setName=Light+Blue"
                if expected_url in s['set_urls']:
                    print("✓ Expected URL found!")
                else:
                    print("✗ Expected URL not found!")
                break
        else:
            print("✗ 'Classic Light Blue' set not found")
            print("  Available sets with 'Classic' in name:")
            for s in sets:
                if "Classic" in s['set_title']:
                    print(f"    - {s['set_title']}")
            
    except Exception as e:
        print(f"Error testing set URL extraction: {e}")

def test_year_url_extraction():
    """Test URL extraction from year table rows."""
    print("\nTesting year URL extraction...")
    
    # Test with a category URL
    test_url = "https://my.taggrading.com/pop-report/Baseball"
    
    try:
        html = fetch_rendered_html(test_url)
        years = extract_years(html)
        
        print(f"Found {len(years)} years:")
        for i, y in enumerate(years):
            print(f"  {i+1}. Year: '{y['year']}'")
            print(f"     URLs: {y['year_urls']}")
            print(f"     Sets: {y['num_sets']} | Items: {y['total_items']} | Graded: {y['total_graded']}")
            print()
            
    except Exception as e:
        print(f"Error testing year URL extraction: {e}")

def test_card_url_extraction():
    """Test URL extraction from card table rows."""
    print("\nTesting card URL extraction...")
    
    # Test with a set URL
    test_url = "https://my.taggrading.com/pop-report/Baseball/1989/Classic?setName=Light+Blue"
    
    try:
        html = fetch_rendered_html(test_url)
        cards = extract_cards(html)
        
        print(f"Found {len(cards)} cards:")
        for i, c in enumerate(cards[:5]):  # Show first 5 cards
            print(f"  {i+1}. Card: #{c['card_number']} | {c['player']}")
            print(f"     URLs: {c['card_urls']}")
            print(f"     Grades: {c['grades']}")
            print()
            
    except Exception as e:
        print(f"Error testing card URL extraction: {e}")

def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing URL Extraction from Table Rows")
    print("=" * 60)
    
    test_set_url_extraction()
    test_year_url_extraction()
    test_card_url_extraction()
    
    print("=" * 60)
    print("Testing complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
