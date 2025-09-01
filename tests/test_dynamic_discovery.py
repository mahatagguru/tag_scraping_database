#!/usr/bin/env python3
"""
Test script to verify dynamic discovery capabilities of the TAG Grading Scraper.
Tests:
1. Dynamic category discovery
2. Dynamic year discovery
3. Dynamic set discovery
4. Dynamic card discovery
5. Report URL capture and storage
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import time

from sqlalchemy.orm import Session

from scraper.card_grade_rows_scraper import extract_grade_rows_from_url
from scraper.cards_scraper import extract_cards_from_url
from scraper.db_helpers import upsert_card_grade_row, upsert_cards_per_set, upsert_sets_per_year, upsert_years_index
from scraper.enhanced_sets_scraper import extract_sets_from_url
from scraper.pipeline import discover_categories
from scraper.sport_years_scraper import extract_years_from_url
from src.db import SessionLocal


def test_dynamic_category_discovery():
    """Test 1: Dynamic category discovery"""
    print("\n" + "=" * 60)
    print("TEST 1: DYNAMIC CATEGORY DISCOVERY")
    print("=" * 60)
    
    try:
        categories = discover_categories()
        print(f"✅ Discovered {len(categories)} categories: {categories}")
        

        # Verify we have the expected core categories
        expected_categories = ['Baseball', 'Hockey', 'Basketball', 'Football']
        for expected in expected_categories:
            if expected in categories:
                print(f"   ✅ Found expected category: {expected}")
            else:
                print(f"   ❌ Missing expected category: {expected}")
        
                # Verify we have additional categories
        additional_categories = ['Soccer', 'Tennis', 'Golf', 'Wrestling', 'Boxing', 'MMA', 
                                'Star Wars', 'Video Games', 'Music', 'Disney', 'Pokémon', 
                                'Magic the Gathering', 'Dragon Ball', 'One Piece', 'Digimon']
        for additional in additional_categories:
            if additional in categories:
                print(f"   ✅ Found additional category: {additional}")
            else:
                print(f"   ⚠️  Additional category not found: {additional}")

        assert len(categories) > 0, f"Expected to find categories, but found {len(categories)}"
        assert len(categories) >= 32, f"Expected at least 32 categories, but found {len(categories)}"
        
    except Exception as e:
        print(f"❌ Category discovery failed: {e}")
        assert False, f"Category discovery failed: {e}"

def test_dynamic_year_discovery():
    """Test 2: Dynamic year discovery for Baseball"""
    print("\n" + "=" * 60)
    print("TEST 2: DYNAMIC YEAR DISCOVERY (Baseball)")
    print("=" * 60)
    
    try:
        sport_url = "https://my.taggrading.com/pop-report/Baseball"
        result = extract_years_from_url(sport_url)
        
        years = result.get('years', [])
        print(f"✅ Discovered {len(years)} years for Baseball")
        
        # Show first few years
        if years:
            print(f"   Sample years: {[y['year'] for y in years[:5]]}")
            
            # Verify year data structure
            first_year = years[0]
            required_fields = ['sport', 'year', 'year_url']
            for field in required_fields:
                if field in first_year and first_year[field]:
                    print(f"   ✅ {field}: {first_year[field]}")
                else:
                    print(f"   ❌ Missing {field}")
        
        return len(years) > 0
        
    except Exception as e:
        print(f"❌ Year discovery failed: {e}")
        return False

def test_dynamic_set_discovery():
    """Test 3: Dynamic set discovery for Baseball 1989"""
    print("\n" + "=" * 60)
    print("TEST 3: DYNAMIC SET DISCOVERY (Baseball 1989)")
    print("=" * 60)
    
    try:
        year_url = "https://my.taggrading.com/pop-report/Baseball/1989"
        result = extract_sets_from_url(year_url)
        
        sets = result.get('sets', [])
        print(f"✅ Discovered {len(sets)} sets for Baseball 1989")
        
        # Show first few sets
        if sets:
            print(f"   Sample sets: {[s['set_title'] for s in sets[:5]]}")
            
            # Verify set data structure
            first_set = sets[0]
            required_fields = ['sport', 'year', 'set_title', 'set_urls']
            for field in required_fields:
                if field in first_set and first_set[field]:
                    if field == 'set_urls':
                        print(f"   ✅ {field}: {len(first_set[field])} URLs")
                    else:
                        print(f"   ✅ {field}: {first_set[field]}")
                else:
                    print(f"   ❌ Missing {field}")
        
        return len(sets) > 0
        
    except Exception as e:
        print(f"❌ Set discovery failed: {e}")
        return False

def test_dynamic_card_discovery():
    """Test 4: Dynamic card discovery for Baseball 1989 Donruss"""
    print("\n" + "=" * 60)
    print("TEST 4: DYNAMIC CARD DISCOVERY (Baseball 1989 Donruss)")
    print("=" * 60)
    
    try:
        set_url = "https://my.taggrading.com/pop-report/Baseball/1989/Donruss"
        result = extract_cards_from_url(set_url, "Donruss")
        
        cards = result.get('cards', [])
        print(f"✅ Discovered {len(cards)} cards for Baseball 1989 Donruss")
        
        # Show first few cards
        if cards:
            print(f"   Sample cards: {[c['card_name'] for c in cards[:5]]}")
            
            # Verify card data structure
            first_card = cards[0]
            required_fields = ['sport', 'year', 'set_title', 'card_name', 'card_urls']
            for field in required_fields:
                if field in first_card and first_card[field]:
                    if field == 'card_urls':
                        print(f"   ✅ {field}: {len(first_card[field])} URLs")
                    else:
                        print(f"   ✅ {field}: {first_card[field]}")
                else:
                    print(f"   ❌ Missing {field}")
        
        return len(cards) > 0
        
    except Exception as e:
        print(f"❌ Card discovery failed: {e}")
        return False

def test_report_url_capture():
    """Test 5: Report URL capture and storage"""
    print("\n" + "=" * 60)
    print("TEST 5: REPORT URL CAPTURE AND STORAGE")
    print("=" * 60)
    
    try:
        # Test with a known card that should have report URLs
        card_url = "https://my.taggrading.com/pop-report/Baseball/1989/Donruss/Gary Carter/53"
        grade_rows = extract_grade_rows_from_url(card_url, "Donruss")
        
        if not grade_rows:
            print("❌ No grade rows found")
            return False
        
        print(f"✅ Found {len(grade_rows)} grade rows")
        
        # Check for report URLs
        report_urls_found = 0
        for i, row in enumerate(grade_rows):
            if row.get('report_url'):
                report_urls_found += 1
                print(f"   ✅ Row {i+1}: Report URL found: {row['report_url']}")
                
                # Verify URL format
                if row['report_url'].startswith('http'):
                    print(f"      ✅ Valid absolute URL format")
                else:
                    print(f"      ❌ Invalid URL format: {row['report_url']}")
            else:
                print(f"   ⚠️  Row {i+1}: No report URL")
        
        print(f"\n📊 Report URL Summary:")
        print(f"   Total rows: {len(grade_rows)}")
        print(f"   Rows with report URLs: {report_urls_found}")
        print(f"   Report URL coverage: {report_urls_found/len(grade_rows)*100:.1f}%")
        
        return report_urls_found > 0
        
    except Exception as e:
        print(f"❌ Report URL capture test failed: {e}")
        return False

def test_database_storage():
    """Test 6: Database storage of discovered data"""
    print("\n" + "=" * 60)
    print("TEST 6: DATABASE STORAGE OF DISCOVERED DATA")
    print("=" * 60)
    
    try:
        # Create a test session
        session = SessionLocal()
        
        # Test storing discovered years
        test_year = {
            'sport': 'TestSport',
            'year': '2024',
            'year_url': 'https://my.taggrading.com/pop-report/TestSport/2024'
        }
        
        year_record = upsert_years_index(
            session, 
            sport=test_year['sport'],
            year=test_year['year'],
            year_url=test_year['year_url']
        )
        print(f"✅ Stored year: {year_record.sport} {year_record.year}")
        
        # Test storing discovered sets
        test_set = {
            'sport': 'TestSport',
            'year': '2024',
            'year_url': 'https://my.taggrading.com/pop-report/TestSport/2024',
            'set_title': 'TestSet',
            'set_urls': ['https://my.taggrading.com/pop-report/TestSport/2024/TestSet'],
            'metrics': {'total_items': 100}
        }
        
        set_record = upsert_sets_per_year(
            session,
            sport=test_set['sport'],
            year=test_set['year'],
            year_url=test_set['year_url'],
            set_title=test_set['set_title'],
            set_urls=test_set['set_urls'],
            metrics=test_set['metrics']
        )
        print(f"✅ Stored set: {set_record.set_title}")
        
        # Test storing discovered cards
        test_card = {
            'sport': 'TestSport',
            'year': '2024',
            'set_title': 'TestSet',
            'set_url': 'https://my.taggrading.com/pop-report/TestSport/2024/TestSet',
            'card_name': 'TestCard',
            'card_urls': ['https://my.taggrading.com/pop-report/TestSport/2024/TestSet/TestCard'],
            'metrics': {'total_items': 50}
        }
        
        card_record = upsert_cards_per_set(
            session,
            sport=test_card['sport'],
            year=test_card['year'],
            set_title=test_card['set_title'],
            set_url=test_card['set_url'],
            card_name=test_card['card_name'],
            card_urls=test_card['card_urls'],
            metrics=test_card['metrics']
        )
        print(f"✅ Stored card: {card_record.card_name}")
        
        # Test storing grade rows with report URLs
        test_grade_row = {
            'sport': 'TestSport',
            'year': '2024',
            'set_title': 'TestSet',
            'card_name': 'TestCard',
            'card_url': 'https://my.taggrading.com/pop-report/TestSport/2024/TestSet/TestCard',
            'cert_number': 'TEST123',
            'rank': '1',
            'tag_grade': '10',
            'report_url': 'https://my.taggrading.com/card/TEST123',
            'completed_date_raw': '01-01-2024'
        }
        
        grade_row_record = upsert_card_grade_row(
            session,
            sport=test_grade_row['sport'],
            year=test_grade_row['year'],
            set_title=test_grade_row['set_title'],
            card_name=test_grade_row['card_name'],
            card_url=test_grade_row['card_url'],
            cert_number=test_grade_row['cert_number'],
            rank=test_grade_row['rank'],
            tag_grade=test_grade_row['tag_grade'],
            report_url=test_grade_row['report_url'],
            completed_date_raw=test_grade_row['completed_date_raw']
        )
        print(f"✅ Stored grade row: {grade_row_record.cert_number}")
        print(f"   Report URL: {grade_row_record.report_url}")
        
        # Commit and close
        session.commit()
        session.close()
        
        print("\n✅ All database storage tests passed!")
        assert True, "Database storage test completed successfully"
        
    except Exception as e:
        print(f"❌ Database storage test failed: {e}")
        assert False, f"Database storage test failed: {e}"

def main():
    """Run all dynamic discovery tests"""
    print("🚀 DYNAMIC DISCOVERY TEST SUITE")
    print("=" * 80)
    print("Testing pipeline capabilities for:")
    print("1. Dynamic category discovery")
    print("2. Dynamic year discovery")
    print("3. Dynamic set discovery")
    print("4. Dynamic card discovery")
    print("5. Report URL capture and storage")
    print("6. Database storage of discovered data")
    print("=" * 80)
    
    tests = [
        test_dynamic_category_discovery,
        test_dynamic_year_discovery,
        test_dynamic_set_discovery,
        test_dynamic_card_discovery,
        test_report_url_capture,
        test_database_storage
    ]
    
    results = {}
    
    for test_func in tests:
        try:
            start_time = time.time()
            result = test_func()
            duration = time.time() - start_time
            
            results[test_func.__name__] = {
                'passed': result,
                'duration': duration
            }
            
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed with exception: {e}")
            results[test_func.__name__] = {
                'passed': False,
                'error': str(e),
                'duration': 0
            }
    
    print("\n" + "=" * 80)
    print("🏁 DYNAMIC DISCOVERY TEST RESULTS")
    print("=" * 80)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        if result['passed']:
            print(f"✅ {test_name}: PASSED ({result['duration']:.2f}s)")
            passed += 1
        else:
            if 'error' in result:
                print(f"❌ {test_name}: FAILED - {result['error']}")
            else:
                print(f"❌ {test_name}: FAILED")
    
    print(f"\n📊 SUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! The pipeline has full dynamic discovery capabilities!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
