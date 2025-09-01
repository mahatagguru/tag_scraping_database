#!/usr/bin/env python3
"""
Simple test script to debug card URL extraction from set pages.
This bypasses the full pipeline and focuses just on the extraction logic.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from selectolax.parser import HTMLParser

from scraper.card_crawler import extract_card_urls
from scraper.set_crawler import fetch_rendered_html


def test_card_extraction():
    """Test card URL extraction from a specific set page."""
    
    # Test with a specific set URL that should have cards
    set_url = "https://my.taggrading.com/pop-report/Baseball/1989/Classic?setName=Light+Blue"
    
    print(f"Testing card extraction from: {set_url}")
    print("=" * 60)
    
    try:
        # Fetch the set page HTML
        print("1. Fetching set page HTML...")
        html = fetch_rendered_html(set_url)
        print(f"   ✓ HTML fetched successfully ({len(html)} characters)")
        
        # Save HTML for inspection
        with open("debug_test_set_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("   ✓ HTML saved to debug_test_set_page.html")
        
        # Test the current extraction function
        print("\n2. Testing current extract_card_urls function...")
        card_urls = extract_card_urls(html)
        print(f"   ✓ Found {len(card_urls)} card URLs")
        
        if card_urls:
            print("   Card URLs found:")
            for i, url in enumerate(card_urls[:5], 1):  # Show first 5
                print(f"     {i}. {url}")
            if len(card_urls) > 5:
                print(f"     ... and {len(card_urls) - 5} more")
        else:
            print("   ❌ No card URLs found - this is the problem!")
        
        # Manual HTML inspection
        print("\n3. Manual HTML inspection...")
        tree = HTMLParser(html)
        
        # Look for common patterns
        print("   Looking for <a> tags with href attributes...")
        all_links = tree.css('a[href]')
        print(f"   ✓ Found {len(all_links)} total links")
        
        # Show first few links
        print("   First 5 links found:")
        for i, link in enumerate(all_links[:5], 1):
            href = link.attributes.get('href', '')
            text = link.text().strip()[:50]  # First 50 chars
            print(f"     {i}. href='{href}' | text='{text}'")
        
        # Look for links that might be card links
        print("\n   Looking for potential card links...")
        potential_card_links = []
        
        for link in all_links:
            href = link.attributes.get('href', '')
            text = link.text().strip()
            
            # Check if this looks like a card link
            if any(pattern in href.lower() for pattern in ['/card/', '/pop-report/', 'craig', 'biggio']):
                potential_card_links.append({
                    'href': href,
                    'text': text,
                    'classes': link.attributes.get('class', ''),
                    'parent_tag': link.parent.tag if link.parent else 'None'
                })
        
        print(f"   ✓ Found {len(potential_card_links)} potential card links")
        
        if potential_card_links:
            print("   Potential card links:")
            for i, link_info in enumerate(potential_card_links[:10], 1):
                print(f"     {i}. href='{link_info['href']}'")
                print(f"        text='{link_info['text']}'")
                print(f"        classes='{link_info['classes']}'")
                print(f"        parent='{link_info['parent_tag']}'")
                print()
        
        # Look for table structures
        print("\n4. Looking for table structures...")
        tables = tree.css('table')
        print(f"   ✓ Found {len(tables)} tables")
        
        for i, table in enumerate(tables):
            rows = table.css('tr')
            print(f"   Table {i+1}: {len(rows)} rows")
            
            # Look at first few rows
            for j, row in enumerate(rows[:3]):
                cells = row.css('td, th')
                cell_texts = [cell.text().strip() for cell in cells]
                print(f"     Row {j+1}: {cell_texts}")
        
        print("\n" + "=" * 60)
        print("Analysis complete!")
        print("\nNext steps:")
        print("1. Open debug_test_set_page.html in your browser")
        print("2. Look for card links and their HTML structure")
        print("3. Share the relevant HTML snippet with me")
        print("4. I'll update the extract_card_urls function")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_card_extraction()
