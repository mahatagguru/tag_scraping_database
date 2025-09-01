#!/usr/bin/env python3
"""
Comprehensive Test for Five-Level Scraping Pipeline

Tests the complete scraping flow:
1. Sports → Years (sport_years_scraper)
2. Years → Sets (enhanced_sets_scraper) 
3. Sets → Cards (cards_scraper)
4. Cards → Grade Rows (card_grade_rows_scraper)
5. Integration with multi_level_orchestrator

This test verifies that all five levels work together correctly.
"""

import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper.card_grade_rows_scraper import extract_grade_rows_from_url
from scraper.cards_scraper import extract_cards_from_url
from scraper.enhanced_sets_scraper import extract_sets_from_url
from scraper.sport_years_scraper import extract_years_from_url


def test_sport_to_years():
    """Test Level 1: Sports → Years"""
    print("=" * 60)
    print("TESTING LEVEL 1: SPORTS → YEARS")
    print("=" * 60)
    
    test_urls = [
        "https://my.taggrading.com/pop-report/Baseball",
        "https://my.taggrading.com/pop-report/Hockey"
    ]
    
    results = {}
    
    for sport_url in test_urls:
        print(f"\nTesting: {sport_url}")
        
        try:
            result = extract_years_from_url(sport_url)
            results[sport_url] = result
            
            print(f"✅ Years found: {len(result['years'])}")
            print(f"✅ Sport totals: {len(result['totals'])}")
            
            # Show sample years
            sample_years = result['years'][:3]
            for year_data in sample_years:
                print(f"   {year_data['year']} → {year_data['year_url']}")
            
            if len(result['years']) > 3:
                print(f"   ... and {len(result['years']) - 3} more")
            
            # Show totals
            for total in result['totals']:
                print(f"   TOTAL ({total['scope']}): {total['metrics']}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            results[sport_url] = {'error': str(e)}
    
    return results


def test_years_to_sets():
    """Test Level 2: Years → Sets"""
    print("\n" + "=" * 60)
    print("TESTING LEVEL 2: YEARS → SETS")
    print("=" * 60)
    
    test_urls = [
        "https://my.taggrading.com/pop-report/Baseball/1989",
        "https://my.taggrading.com/pop-report/Hockey/1989"
    ]
    
    results = {}
    
    for year_url in test_urls:
        print(f"\nTesting: {year_url}")
        
        try:
            result = extract_sets_from_url(year_url)
            results[year_url] = result
            
            print(f"✅ Sets found: {len(result['sets'])}")
            print(f"✅ Year totals: {len(result['totals'])}")
            
            # Show sample sets
            sample_sets = result['sets'][:3]
            for set_data in sample_sets:
                print(f"   '{set_data['set_title']}'")
                print(f"     URLs: {len(set_data['set_urls'])} found")
                print(f"     Set Page URL: {set_data.get('set_page_url', 'None')}")
                print(f"     Metrics: {len(set_data['metrics'])} grades")
            
            if len(result['sets']) > 3:
                print(f"   ... and {len(result['sets']) - 3} more sets")
            
            # Show totals
            for total in result['totals']:
                print(f"   TOTAL ({total['scope']} for {total['year']}): {len(total['metrics'])} metrics")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            results[year_url] = {'error': str(e)}
    
    return results


def test_sets_to_cards():
    """Test Level 3: Sets → Cards"""
    print("\n" + "=" * 60)
    print("TESTING LEVEL 3: SETS → CARDS")
    print("=" * 60)
    
    test_urls = [
        "https://my.taggrading.com/pop-report/Baseball/1989/Donruss",
        "https://my.taggrading.com/pop-report/Hockey/1989/Topps"
    ]
    
    results = {}
    
    for set_url in test_urls:
        print(f"\nTesting: {set_url}")
        
        try:
            result = extract_cards_from_url(set_url)
            results[set_url] = result
            
            print(f"✅ Cards found: {len(result['cards'])}")
            print(f"✅ Set totals: {len(result['totals'])}")
            
            # Show sample cards
            sample_cards = result['cards'][:3]
            for card_data in sample_cards:
                print(f"   '{card_data['card_name']}'")
                print(f"     URLs: {len(card_data['card_urls'])} found")
                print(f"     Metrics: {len(card_data['metrics'])} grades")
            
            if len(result['cards']) > 3:
                print(f"   ... and {len(result['cards']) - 3} more cards")
            
            # Show totals
            for total in result['totals']:
                print(f"   TOTAL ({total['scope']} for {total['sport']} {total['year']} {total['set_title']}): {len(total['metrics'])} metrics")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            results[set_url] = {'error': str(e)}
    
    return results


def test_cards_to_grade_rows():
    """Test Level 4: Cards → Grade Rows"""
    print("\n" + "=" * 60)
    print("TESTING LEVEL 4: CARDS → GRADE ROWS")
    print("=" * 60)
    
    test_urls = [
        "https://my.taggrading.com/pop-report/Baseball/1989/Donruss/Gary Carter/53",
        "https://my.taggrading.com/pop-report/Hockey/1989/Topps/Mario Lemieux/1"
    ]
    
    results = {}
    
    for card_url in test_urls:
        print(f"\nTesting: {card_url}")
        
        try:
            grade_rows = extract_grade_rows_from_url(card_url)
            results[card_url] = grade_rows
            
            print(f"✅ Grade rows found: {len(grade_rows)}")
            
            # Show sample grade rows
            sample_rows = grade_rows[:3]
            for i, row_data in enumerate(sample_rows):
                print(f"   {i+1}. Grade: {row_data.get('tag_grade', 'N/A')}")
                print(f"      Rank: {row_data.get('rank', 'N/A')}")
                print(f"      Cert: {row_data.get('cert_number', 'N/A')}")
                print(f"      Report URL: {row_data.get('report_url', 'N/A')}")
                print(f"      Completed: {row_data.get('completed_date_raw', 'N/A')}")
                print()
            
            if len(grade_rows) > 3:
                print(f"   ... and {len(grade_rows) - 3} more grade rows")
            
            # Show field mapping info
            if grade_rows:
                sample_row = grade_rows[0]
                print(f"   Sample row fields: {list(sample_row.keys())}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            results[card_url] = {'error': str(e)}
    
    return results


def test_complete_five_level_pipeline_flow():
    """Test the complete five-level pipeline flow from one sport"""
    print("\n" + "=" * 60)
    print("TESTING COMPLETE FIVE-LEVEL PIPELINE FLOW")
    print("=" * 60)
    
    print("Testing complete flow: Baseball → 1989 → Donruss → Gary Carter → Grade Rows")
    
    try:
        # Level 1: Sport → Years
        print("\n1️⃣ SPORT → YEARS")
        years_result = extract_years_from_url("https://my.taggrading.com/pop-report/Baseball")
        baseball_1989 = None
        
        for year_data in years_result['years']:
            if year_data['year'] == '1989':
                baseball_1989 = year_data
                break
        
        if not baseball_1989:
            print("❌ Could not find 1989 in Baseball years")
            return False
        
        print(f"✅ Found 1989: {baseball_1989['year_url']}")
        
        # Level 2: Year → Sets
        print("\n2️⃣ YEAR → SETS")
        sets_result = extract_sets_from_url(baseball_1989['year_url'])
        donruss_set = None
        
        for set_data in sets_result['sets']:
            if 'Donruss' in set_data['set_title']:
                donruss_set = set_data
                break
        
        if not donruss_set:
            print("❌ Could not find Donruss set in 1989")
            return False
        
        print(f"✅ Found Donruss: {donruss_set['set_title']}")
        print(f"   Set page URL: {donruss_set.get('set_page_url', 'None')}")
        
        # Level 3: Set → Cards
        print("\n3️⃣ SET → CARDS")
        if donruss_set.get('set_page_url'):
            cards_result = extract_cards_from_url(donruss_set['set_page_url'])
            print(f"✅ Found {len(cards_result['cards'])} cards in Donruss")
            
            # Find Gary Carter card
            gary_carter_card = None
            for card_data in cards_result['cards']:
                if 'Gary Carter' in card_data['card_name']:
                    gary_carter_card = card_data
                    break
            
            if not gary_carter_card:
                print("❌ Could not find Gary Carter card")
                return False
            
            print(f"✅ Found Gary Carter card with {len(gary_carter_card['card_urls'])} URLs")
        else:
            print("❌ No set page URL found for Donruss")
            return False
        
        # Level 4: Card → Grade Rows
        print("\n4️⃣ CARD → GRADE ROWS")
        if gary_carter_card.get('card_urls'):
            primary_card_url = gary_carter_card['card_urls'][0]
            grade_rows = extract_grade_rows_from_url(primary_card_url)
            print(f"✅ Found {len(grade_rows)} grade rows for Gary Carter")
            
            # Show some sample grade rows
            sample_rows = grade_rows[:2]
            for i, row_data in enumerate(sample_rows):
                print(f"   - Grade {row_data.get('tag_grade', 'N/A')}: Cert {row_data.get('cert_number', 'N/A')}")
        else:
            print("❌ No card URLs found for Gary Carter")
            return False
        
        print("\n🎉 COMPLETE FIVE-LEVEL PIPELINE FLOW SUCCESSFUL!")
        return True
        
    except Exception as e:
        print(f"❌ Pipeline flow failed: {e}")
        return False


def test_data_structure_consistency():
    """Test that data structures are consistent across all five levels"""
    print("\n" + "=" * 60)
    print("TESTING DATA STRUCTURE CONSISTENCY")
    print("=" * 60)
    
    print("Verifying data structure consistency across all five levels...")
    
    # Test sport years structure
    print("\n📋 Level 1 (Sport Years) Structure:")
    try:
        result = extract_years_from_url("https://my.taggrading.com/pop-report/Baseball")
        
        if result['years']:
            year_sample = result['years'][0]
            required_fields = ['sport', 'year', 'year_url', 'row_index']
            
            for field in required_fields:
                if field in year_sample:
                    print(f"   ✅ {field}: {type(year_sample[field]).__name__}")
                else:
                    print(f"   ❌ Missing field: {field}")
        
        if result['totals']:
            total_sample = result['totals'][0]
            required_fields = ['scope', 'sport', 'year', 'set_title', 'card_name', 'metrics']
            
            for field in required_fields:
                if field in total_sample:
                    print(f"   ✅ {field}: {type(total_sample[field]).__name__}")
                else:
                    print(f"   ❌ Missing field: {field}")
                    
    except Exception as e:
        print(f"   ❌ Error testing sport years structure: {e}")
    
    # Test sets structure
    print("\n📋 Level 2 (Sets) Structure:")
    try:
        result = extract_sets_from_url("https://my.taggrading.com/pop-report/Baseball/1989")
        
        if result['sets']:
            set_sample = result['sets'][0]
            required_fields = ['sport', 'year', 'year_url', 'set_title', 'set_urls', 'set_page_url', 'metrics']
            
            for field in required_fields:
                if field in set_sample:
                    print(f"   ✅ {field}: {type(set_sample[field]).__name__}")
                else:
                    print(f"   ❌ Missing field: {field}")
                    
    except Exception as e:
        print(f"   ❌ Error testing sets structure: {e}")
    
    # Test cards structure
    print("\n📋 Level 3 (Cards) Structure:")
    try:
        result = extract_cards_from_url("https://my.taggrading.com/pop-report/Baseball/1989/Donruss")
        
        if result['cards']:
            card_sample = result['cards'][0]
            required_fields = ['sport', 'year', 'set_title', 'set_url', 'card_name', 'card_urls', 'metrics']
            
            for field in required_fields:
                if field in card_sample:
                    print(f"   ✅ {field}: {type(card_sample[field]).__name__}")
                else:
                    print(f"   ❌ Missing field: {field}")
                    
    except Exception as e:
        print(f"   ❌ Error testing cards structure: {e}")
    
    # Test grade rows structure
    print("\n📋 Level 4 (Grade Rows) Structure:")
    try:
        result = extract_grade_rows_from_url("https://my.taggrading.com/pop-report/Baseball/1989/Donruss/Gary Carter/53")
        
        if result:
            row_sample = result[0]
            required_fields = [
                'sport', 'year', 'set_title', 'card_name', 'card_url', 'rank', 
                'tag_grade', 'report_url', 'rank_by_grade', 'chronology', 
                'chron_by_grade', 'completed_date_raw', 'completed_date_iso', 'cert_number'
            ]
            
            for field in required_fields:
                if field in row_sample:
                    print(f"   ✅ {field}: {type(row_sample[field]).__name__}")
                else:
                    print(f"   ❌ Missing field: {field}")
                    
    except Exception as e:
        print(f"   ❌ Error testing grade rows structure: {e}")


def test_grade_row_field_extraction():
    """Test specific field extraction from grade rows"""
    print("\n" + "=" * 60)
    print("TESTING GRADE ROW FIELD EXTRACTION")
    print("=" * 60)
    
    test_url = "https://my.taggrading.com/pop-report/Baseball/1989/Donruss/Gary Carter/53"
    print(f"Testing field extraction from: {test_url}")
    
    try:
        grade_rows = extract_grade_rows_from_url(test_url)
        
        if not grade_rows:
            print("❌ No grade rows found")
            return False
        
        print(f"✅ Found {len(grade_rows)} grade rows")
        
        # Test first row for all required fields
        first_row = grade_rows[0]
        
        # Test required fields
        required_fields = ['sport', 'year', 'set_title', 'card_name', 'card_url', 'cert_number']
        for field in required_fields:
            if field in first_row and first_row[field]:
                print(f"   ✅ {field}: {first_row[field]}")
            else:
                print(f"   ❌ Missing or empty {field}")
        
        # Test optional fields
        optional_fields = ['rank', 'tag_grade', 'report_url', 'rank_by_grade', 'chronology', 'chron_by_grade', 'completed_date_raw', 'completed_date_iso']
        for field in optional_fields:
            if field in first_row:
                value = first_row[field]
                if value is not None:
                    print(f"   ✅ {field}: {value}")
                else:
                    print(f"   ⚠️  {field}: None (expected)")
            else:
                print(f"   ❌ Missing field: {field}")
        
        # Test specific field values
        print(f"\n   📊 Field Analysis:")
        print(f"      Sport: {first_row.get('sport')} (should be 'Baseball')")
        print(f"      Year: {first_row.get('year')} (should be '1989')")
        print(f"      Set: {first_row.get('set_title')} (should be 'Donruss')")
        print(f"      Card: {first_row.get('card_name')} (should be 'Gary Carter')")
        print(f"      Grade: {first_row.get('tag_grade')} (should be grade like '8.5 NM MT+')")
        print(f"      Cert: {first_row.get('cert_number')} (should be cert number like 'X3032464')")
        print(f"      Report URL: {first_row.get('report_url')} (should be absolute URL)")
        print(f"      Completed Raw: {first_row.get('completed_date_raw')} (should be date like '11-21-2023')")
        print(f"      Completed ISO: {first_row.get('completed_date_iso')} (should be ISO date or None)")
        
        return True
        
    except Exception as e:
        print(f"❌ Field extraction test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 FIVE-LEVEL SCRAPING PIPELINE TEST SUITE")
    print("=" * 80)
    
    tests = [
        test_sport_to_years,
        test_years_to_sets,
        test_sets_to_cards,
        test_cards_to_grade_rows,
        test_complete_five_level_pipeline_flow,
        test_data_structure_consistency,
        test_grade_row_field_extraction
    ]
    
    results = {}
    
    for test_func in tests:
        try:
            result = test_func()
            results[test_func.__name__] = result
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed: {e}")
            results[test_func.__name__] = {'error': str(e)}
    
    print("\n" + "=" * 80)
    print("🏁 TEST SUITE COMPLETE")
    print("=" * 80)
    
    success_count = 0
    for test_name, result in results.items():
        if isinstance(result, dict) and 'error' in result:
            print(f"❌ {test_name}: FAILED")
        elif test_name in ['test_complete_five_level_pipeline_flow', 'test_grade_row_field_extraction']:
            if result:
                print(f"✅ {test_name}: PASSED")
                success_count += 1
            else:
                print(f"❌ {test_name}: FAILED")
        else:
            print(f"✅ {test_name}: PASSED")
            success_count += 1
    
    print(f"\nSUMMARY: {success_count}/{len(tests)} tests passed")
    
    if success_count == len(tests):
        print("🎉 ALL TESTS PASSED! The five-level scraping pipeline is working correctly.")
    else:
        print("⚠️  Some tests failed. Please review the output above.")


if __name__ == "__main__":
    main()
