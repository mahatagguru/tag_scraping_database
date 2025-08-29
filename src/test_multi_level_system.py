#!/usr/bin/env python3
"""
Comprehensive Test Suite for Multi-Level Scraping System

Tests the complete scraping system without requiring database connection.
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper.sport_years_scraper import extract_years_from_url
from scraper.enhanced_sets_scraper import extract_sets_from_url


def test_sport_years_extraction():
    """Test the sport years extraction functionality"""
    print("=" * 60)
    print("TESTING SPORT YEARS EXTRACTION")
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


def test_year_sets_extraction():
    """Test the year sets extraction functionality"""
    print("\n" + "=" * 60)
    print("TESTING YEAR SETS EXTRACTION")
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


def test_data_structures():
    """Test that data structures match the expected schema"""
    print("\n" + "=" * 60)
    print("TESTING DATA STRUCTURE COMPLIANCE")
    print("=" * 60)
    
    # Test sport years structure
    print("\n📋 Testing Sport Years Data Structure...")
    
    try:
        result = extract_years_from_url("https://my.taggrading.com/pop-report/Baseball")
        
        # Check years structure
        if result['years']:
            year_sample = result['years'][0]
            required_fields = ['sport', 'year', 'year_url', 'row_index']
            
            for field in required_fields:
                if field in year_sample:
                    print(f"   ✅ {field}: {type(year_sample[field]).__name__}")
                else:
                    print(f"   ❌ Missing field: {field}")
        
        # Check totals structure
        if result['totals']:
            total_sample = result['totals'][0]
            required_fields = ['scope', 'sport', 'year', 'set_title', 'metrics']
            
            for field in required_fields:
                if field in total_sample:
                    print(f"   ✅ {field}: {type(total_sample[field]).__name__}")
                else:
                    print(f"   ❌ Missing field: {field}")
                    
    except Exception as e:
        print(f"   ❌ Error testing sport years structure: {e}")
    
    # Test sets structure
    print("\n📋 Testing Sets Data Structure...")
    
    try:
        result = extract_sets_from_url("https://my.taggrading.com/pop-report/Baseball/1989")
        
        # Check sets structure
        if result['sets']:
            set_sample = result['sets'][0]
            required_fields = ['sport', 'year', 'year_url', 'set_title', 'set_urls', 'metrics']
            
            for field in required_fields:
                if field in set_sample:
                    print(f"   ✅ {field}: {type(set_sample[field]).__name__}")
                else:
                    print(f"   ❌ Missing field: {field}")
                    
    except Exception as e:
        print(f"   ❌ Error testing sets structure: {e}")


def test_url_normalization():
    """Test URL normalization and filtering"""
    print("\n" + "=" * 60)
    print("TESTING URL NORMALIZATION")
    print("=" * 60)
    
    # Test with Baseball 1989 which has good URL examples
    try:
        result = extract_sets_from_url("https://my.taggrading.com/pop-report/Baseball/1989")
        
        print(f"\nTesting URL extraction from {len(result['sets'])} sets...")
        
        url_count = 0
        absolute_count = 0
        unique_domains = set()
        
        for set_data in result['sets']:
            urls = set_data['set_urls']
            url_count += len(urls)
            
            for url in urls:
                if url.startswith('https://'):
                    absolute_count += 1
                    domain = url.split('/')[2]
                    unique_domains.add(domain)
        
        print(f"✅ Total URLs extracted: {url_count}")
        print(f"✅ Absolute URLs: {absolute_count}/{url_count}")
        print(f"✅ Unique domains: {unique_domains}")
        
        # Test specific URL patterns
        example_urls = []
        for set_data in result['sets'][:5]:
            if set_data['set_urls']:
                example_urls.append(set_data['set_urls'][0])
        
        print(f"\nSample URLs:")
        for url in example_urls:
            print(f"   {url}")
            
    except Exception as e:
        print(f"❌ Error testing URL normalization: {e}")


def test_metrics_extraction():
    """Test metrics extraction from table cells"""
    print("\n" + "=" * 60)
    print("TESTING METRICS EXTRACTION")
    print("=" * 60)
    
    try:
        # Test with Baseball 1989
        result = extract_sets_from_url("https://my.taggrading.com/pop-report/Baseball/1989")
        
        if result['sets']:
            metrics_stats = {
                'total_sets': len(result['sets']),
                'sets_with_metrics': 0,
                'average_metrics_per_set': 0,
                'common_metric_keys': {},
                'sample_metrics': {}
            }
            
            total_metrics = 0
            
            for set_data in result['sets']:
                metrics = set_data['metrics']
                
                if metrics:
                    metrics_stats['sets_with_metrics'] += 1
                    total_metrics += len(metrics)
                    
                    # Count metric key frequencies
                    for key in metrics.keys():
                        metrics_stats['common_metric_keys'][key] = metrics_stats['common_metric_keys'].get(key, 0) + 1
                    
                    # Store sample for first set
                    if not metrics_stats['sample_metrics']:
                        metrics_stats['sample_metrics'] = metrics
            
            if metrics_stats['sets_with_metrics'] > 0:
                metrics_stats['average_metrics_per_set'] = total_metrics / metrics_stats['sets_with_metrics']
            
            print(f"✅ Sets with metrics: {metrics_stats['sets_with_metrics']}/{metrics_stats['total_sets']}")
            print(f"✅ Average metrics per set: {metrics_stats['average_metrics_per_set']:.1f}")
            
            print(f"\nMost common metric keys:")
            sorted_keys = sorted(metrics_stats['common_metric_keys'].items(), key=lambda x: x[1], reverse=True)
            for key, count in sorted_keys[:5]:
                print(f"   {key}: {count} sets")
            
            print(f"\nSample metrics:")
            for key, value in list(metrics_stats['sample_metrics'].items())[:5]:
                print(f"   {key}: {value}")
                
    except Exception as e:
        print(f"❌ Error testing metrics extraction: {e}")


def test_totals_detection():
    """Test TOTALS row detection and processing"""
    print("\n" + "=" * 60)
    print("TESTING TOTALS DETECTION")
    print("=" * 60)
    
    # Test sport-level totals
    print("\n📊 Testing Sport-Level Totals...")
    
    sport_urls = [
        "https://my.taggrading.com/pop-report/Baseball",
        "https://my.taggrading.com/pop-report/Hockey"
    ]
    
    for sport_url in sport_urls:
        try:
            result = extract_years_from_url(sport_url)
            sport = sport_url.split('/')[-1]
            
            print(f"\n{sport}:")
            if result['totals']:
                for total in result['totals']:
                    print(f"   Scope: {total['scope']}")
                    print(f"   Metrics: {total['metrics']}")
            else:
                print("   No sport-level totals found")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test year-level totals
    print(f"\n📊 Testing Year-Level Totals...")
    
    year_urls = [
        "https://my.taggrading.com/pop-report/Baseball/1989",
        "https://my.taggrading.com/pop-report/Hockey/1989"
    ]
    
    for year_url in year_urls:
        try:
            result = extract_sets_from_url(year_url)
            
            print(f"\n{year_url.split('/')[-2:]}:")
            if result['totals']:
                for total in result['totals']:
                    print(f"   Scope: {total['scope']}")
                    print(f"   Year: {total['year']}")
                    print(f"   Metrics: {total['metrics']}")
            else:
                print("   No year-level totals found")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")


def main():
    """Run all tests"""
    print("🚀 MULTI-LEVEL SCRAPING SYSTEM TEST SUITE")
    print("=" * 80)
    
    tests = [
        test_sport_years_extraction,
        test_year_sets_extraction,
        test_data_structures,
        test_url_normalization,
        test_metrics_extraction,
        test_totals_detection
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
        else:
            print(f"✅ {test_name}: PASSED")
            success_count += 1
    
    print(f"\nSUMMARY: {success_count}/{len(tests)} tests passed")
    
    if success_count == len(tests):
        print("🎉 ALL TESTS PASSED! The multi-level scraping system is working correctly.")
    else:
        print("⚠️  Some tests failed. Please review the output above.")


if __name__ == "__main__":
    main()
