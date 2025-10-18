#!/usr/bin/env python3
"""
Simple performance test script for the async scraping pipeline.
"""

import asyncio
import sys
import time

from src.scraper.async_pipeline import AsyncPipelineConfig, AsyncScrapingPipeline


async def run_pipeline_test(config: AsyncPipelineConfig, test_name: str) -> dict:
    """Run a pipeline test and return results."""
    print(f"\n🧪 Running {test_name}...")
    
    start_time = time.time()
    
    async with AsyncScrapingPipeline(config) as pipeline:
        try:
            # Run with a small subset for testing
            stats = await pipeline.run_pipeline(['Baseball'])  # Just Baseball for testing
            
            end_time = time.time()
            runtime = end_time - start_time
            
            return {
                'success': True,
                'runtime_seconds': runtime,
                'stats': stats,
                'test_name': test_name
            }
            
        except Exception as e:
            end_time = time.time()
            runtime = end_time - start_time
            
            return {
                'success': False,
                'error': str(e),
                'runtime_seconds': runtime,
                'test_name': test_name
            }


async def main():
    """Run performance tests."""
    print("🧪 Running performance tests for TAG Grading scraper...")
    
    # Test configurations
    test_configs = [
        {
            'name': 'Low Concurrency (3 requests)',
            'config': AsyncPipelineConfig(
                max_concurrent_requests=3,
                rate_limit=1.0,
                enable_caching=False,
                dry_run=True
            )
        },
        {
            'name': 'High Concurrency (10 requests)',
            'config': AsyncPipelineConfig(
                max_concurrent_requests=10,
                rate_limit=0.5,
                enable_caching=False,
                dry_run=True
            )
        },
        {
            'name': 'With Caching (10 requests)',
            'config': AsyncPipelineConfig(
                max_concurrent_requests=10,
                rate_limit=0.5,
                enable_caching=True,
                dry_run=True
            )
        }
    ]
    
    results = []
    
    # Run each test
    for test_config in test_configs:
        result = await run_pipeline_test(test_config['config'], test_config['name'])
        results.append(result)
        
        if result['success']:
            print(f"✅ {result['test_name']}: {result['runtime_seconds']:.2f}s")
            stats = result['stats']
            print(f"   Cards processed: {stats.get('cards_processed', 0)}")
            if result['runtime_seconds'] > 0:
                throughput = stats.get('cards_processed', 0) / result['runtime_seconds']
                print(f"   Throughput: {throughput:.2f} cards/sec")
        else:
            print(f"❌ {result['test_name']}: Failed - {result.get('error', 'Unknown error')}")
    
    # Print summary
    print("\n" + "="*80)
    print("📊 PERFORMANCE TEST SUMMARY")
    print("="*80)
    
    successful_tests = [r for r in results if r['success']]
    failed_tests = [r for r in results if not r['success']]
    
    print(f"\n✅ Successful tests: {len(successful_tests)}")
    print(f"❌ Failed tests: {len(failed_tests)}")
    
    if successful_tests:
        print("\nPerformance Results:")
        print("-" * 40)
        for result in successful_tests:
            print(f"  {result['test_name']}: {result['runtime_seconds']:.2f}s")
            
        # Find fastest and slowest
        fastest = min(successful_tests, key=lambda x: x['runtime_seconds'])
        slowest = max(successful_tests, key=lambda x: x['runtime_seconds'])
        
        print(f"\n🚀 Fastest: {fastest['test_name']} ({fastest['runtime_seconds']:.2f}s)")
        print(f"🐌 Slowest: {slowest['test_name']} ({slowest['runtime_seconds']:.2f}s)")
        
        # Calculate improvement
        if len(successful_tests) >= 2:
            improvement = (slowest['runtime_seconds'] - fastest['runtime_seconds']) / slowest['runtime_seconds'] * 100
            print(f"📈 Best improvement: {improvement:.1f}% faster")
    
    if failed_tests:
        print("\nFailed Tests:")
        print("-" * 40)
        for result in failed_tests:
            print(f"  {result['test_name']}: {result.get('error', 'Unknown error')}")
    
    print("\n" + "="*80)
    print("✅ Performance tests completed!")
    
    return 0 if len(failed_tests) == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)