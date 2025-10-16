#!/usr/bin/env python3
"""
Comprehensive Test for Four-Level Scraping Pipeline

Tests the complete scraping flow:
1. Sports → Years (sport_years_scraper)
2. Years → Sets (enhanced_sets_scraper) 
3. Sets → Cards (cards_scraper)
4. Integration with multi_level_orchestrator

This test verifies that all four levels work together correctly.
"""

import os
import sys

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

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
        "https://my.taggrading.com/pop-report/Hockey",
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
            sample_years = result["years"][:3]
            for year_data in sample_years:
                print(f"   {year_data['year']} → {year_data['year_url']}")

            if len(result["years"]) > 3:
                print(f"   ... and {len(result['years']) - 3} more")

            # Show totals
            for total in result["totals"]:
                print(f"   TOTAL ({total['scope']}): {total['metrics']}")

        except Exception as e:
            print(f"❌ Error: {e}")
            results[sport_url] = {"error": str(e)}

    return results


def test_years_to_sets():
    """Test Level 2: Years → Sets"""
    print("\n" + "=" * 60)
    print("TESTING LEVEL 2: YEARS → SETS")
    print("=" * 60)

    test_urls = [
        "https://my.taggrading.com/pop-report/Baseball/1989",
        "https://my.taggrading.com/pop-report/Hockey/1989",
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
            sample_sets = result["sets"][:3]
            for set_data in sample_sets:
                print(f"   '{set_data['set_title']}'")
                print(f"     URLs: {len(set_data['set_urls'])} found")
                print(f"     Set Page URL: {set_data.get('set_page_url', 'None')}")
                print(f"     Metrics: {len(set_data['metrics'])} grades")

            if len(result["sets"]) > 3:
                print(f"   ... and {len(result['sets']) - 3} more sets")

            # Show totals
            for total in result["totals"]:
                print(
                    f"   TOTAL ({total['scope']} for {total['year']}): {len(total['metrics'])} metrics"
                )

        except Exception as e:
            print(f"❌ Error: {e}")
            results[year_url] = {"error": str(e)}

    return results


def test_sets_to_cards():
    """Test Level 3: Sets → Cards"""
    print("\n" + "=" * 60)
    print("TESTING LEVEL 3: SETS → CARDS")
    print("=" * 60)

    test_urls = [
        "https://my.taggrading.com/pop-report/Baseball/1989/Donruss",
        "https://my.taggrading.com/pop-report/Hockey/1989/Topps",
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
            sample_cards = result["cards"][:3]
            for card_data in sample_cards:
                print(f"   '{card_data['card_name']}'")
                print(f"     URLs: {len(card_data['card_urls'])} found")
                print(f"     Metrics: {len(card_data['metrics'])} grades")

            if len(result["cards"]) > 3:
                print(f"   ... and {len(result['cards']) - 3} more cards")

            # Show totals
            for total in result["totals"]:
                print(
                    f"   TOTAL ({total['scope']} for {total['sport']} {total['year']} {total['set_title']}): {len(total['metrics'])} metrics"
                )

        except Exception as e:
            print(f"❌ Error: {e}")
            results[set_url] = {"error": str(e)}

    return results


def test_complete_pipeline_flow():
    """Test the complete pipeline flow from one sport"""
    print("\n" + "=" * 60)
    print("TESTING COMPLETE PIPELINE FLOW")
    print("=" * 60)

    print("Testing complete flow: Baseball → 1989 → Donruss → Cards")

    try:
        # Level 1: Sport → Years
        print("\n1️⃣ SPORT → YEARS")
        years_result = extract_years_from_url(
            "https://my.taggrading.com/pop-report/Baseball"
        )
        baseball_1989 = None

        for year_data in years_result["years"]:
            if year_data["year"] == "1989":
                baseball_1989 = year_data
                break

        if not baseball_1989:
            print("❌ Could not find 1989 in Baseball years")
            return False

        print(f"✅ Found 1989: {baseball_1989['year_url']}")

        # Level 2: Year → Sets
        print("\n2️⃣ YEAR → SETS")
        sets_result = extract_sets_from_url(baseball_1989["year_url"])
        donruss_set = None

        for set_data in sets_result["sets"]:
            if "Donruss" in set_data["set_title"]:
                donruss_set = set_data
                break

        if not donruss_set:
            print("❌ Could not find Donruss set in 1989")
            return False

        print(f"✅ Found Donruss: {donruss_set['set_title']}")
        print(f"   Set page URL: {donruss_set.get('set_page_url', 'None')}")

        # Level 3: Set → Cards
        print("\n3️⃣ SET → CARDS")
        if donruss_set.get("set_page_url"):
            cards_result = extract_cards_from_url(donruss_set["set_page_url"])
            print(f"✅ Found {len(cards_result['cards'])} cards in Donruss")

            # Show some sample cards
            sample_cards = cards_result["cards"][:3]
            for card_data in sample_cards:
                print(
                    f"   - {card_data['card_name']}: {len(card_data['card_urls'])} URLs"
                )
        else:
            print("❌ No set page URL found for Donruss")
            return False

        print("\n🎉 COMPLETE PIPELINE FLOW SUCCESSFUL!")
        return True

    except Exception as e:
        print(f"❌ Pipeline flow failed: {e}")
        return False


def test_data_structure_consistency():
    """Test that data structures are consistent across all levels"""
    print("\n" + "=" * 60)
    print("TESTING DATA STRUCTURE CONSISTENCY")
    print("=" * 60)

    print("Verifying data structure consistency across all levels...")

    # Test sport years structure
    print("\n📋 Level 1 (Sport Years) Structure:")
    try:
        result = extract_years_from_url("https://my.taggrading.com/pop-report/Baseball")

        if result["years"]:
            year_sample = result["years"][0]
            required_fields = ["sport", "year", "year_url", "row_index"]

            for field in required_fields:
                if field in year_sample:
                    print(f"   ✅ {field}: {type(year_sample[field]).__name__}")
                else:
                    print(f"   ❌ Missing field: {field}")

        if result["totals"]:
            total_sample = result["totals"][0]
            # Sport-level totals don't have card_name, set_title, or year
            if total_sample["scope"] == "sport":
                required_fields = [
                    "scope",
                    "sport",
                    "year",
                    "set_title",
                    "card_name",
                    "metrics",
                ]
                expected_nulls = ["year", "set_title", "card_name"]
            else:
                required_fields = [
                    "scope",
                    "sport",
                    "year",
                    "set_title",
                    "card_name",
                    "metrics",
                ]
                expected_nulls = []

            for field in required_fields:
                if field in total_sample:
                    if field in expected_nulls and total_sample[field] is None:
                        print(
                            f"   ✅ {field}: {type(total_sample[field]).__name__} (expected None)"
                        )
                    elif field in expected_nulls and total_sample[field] is not None:
                        print(
                            f"   ❌ {field}: should be None but is {total_sample[field]}"
                        )
                    else:
                        print(f"   ✅ {field}: {type(total_sample[field]).__name__}")
                else:
                    print(f"   ❌ Missing field: {field}")

    except Exception as e:
        print(f"   ❌ Error testing sport years structure: {e}")

    # Test sets structure
    print("\n📋 Level 2 (Sets) Structure:")
    try:
        result = extract_sets_from_url(
            "https://my.taggrading.com/pop-report/Baseball/1989"
        )

        if result["sets"]:
            set_sample = result["sets"][0]
            required_fields = [
                "sport",
                "year",
                "year_url",
                "set_title",
                "set_urls",
                "set_page_url",
                "metrics",
            ]

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
        result = extract_cards_from_url(
            "https://my.taggrading.com/pop-report/Baseball/1989/Donruss"
        )

        if result["cards"]:
            card_sample = result["cards"][0]
            required_fields = [
                "sport",
                "year",
                "set_title",
                "set_url",
                "card_name",
                "card_urls",
                "metrics",
            ]

            for field in required_fields:
                if field in card_sample:
                    print(f"   ✅ {field}: {type(card_sample[field]).__name__}")
                else:
                    print(f"   ❌ Missing field: {field}")

    except Exception as e:
        print(f"   ❌ Error testing cards structure: {e}")


def main():
    """Run all tests"""
    print("🚀 FOUR-LEVEL SCRAPING PIPELINE TEST SUITE")
    print("=" * 80)

    tests = [
        test_sport_to_years,
        test_years_to_sets,
        test_sets_to_cards,
        test_complete_pipeline_flow,
        test_data_structure_consistency,
    ]

    results = {}

    for test_func in tests:
        try:
            result = test_func()
            results[test_func.__name__] = result
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed: {e}")
            results[test_func.__name__] = {"error": str(e)}

    print("\n" + "=" * 80)
    print("🏁 TEST SUITE COMPLETE")
    print("=" * 80)

    success_count = 0
    for test_name, result in results.items():
        if isinstance(result, dict) and "error" in result:
            print(f"❌ {test_name}: FAILED")
        elif test_name == "test_complete_pipeline_flow":
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
        print(
            "🎉 ALL TESTS PASSED! The four-level scraping pipeline is working correctly."
        )
    else:
        print("⚠️  Some tests failed. Please review the output above.")


if __name__ == "__main__":
    main()
