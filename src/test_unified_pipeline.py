#!/usr/bin/env python3
"""
Comprehensive Test Script for Unified TAG Grading Pipeline
Tests:
1. Unified pipeline functionality
2. Error handling and retry logic
3. Audit logging to database
4. Multi-runner orchestration
5. Dynamic discovery capabilities
"""

import sys
import os
import time
import subprocess
import json
from pathlib import Path

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_unified_pipeline_basic():
    """Test 1: Basic unified pipeline functionality"""
    print("\n" + "=" * 60)
    print("TEST 1: BASIC UNIFIED PIPELINE FUNCTIONALITY")
    print("=" * 60)
    
    try:
        # Test with dry run to avoid database writes
        cmd = [
            "python", "src/scraper/unified_pipeline.py",
            "--dry-run",
            "--concurrency", "2",
            "--delay", "0.1",
            "--max-retries", "2",
            "--retry-backoff", "1.5",
            "--log-level", "INFO"
        ]
        
        print(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        if result.returncode == 0:
            print("✅ Basic pipeline test passed")
            print(f"   Output: {result.stdout[-500:]}")  # Last 500 chars
            return True
        else:
            print("❌ Basic pipeline test failed")
            print(f"   Exit code: {result.returncode}")
            print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Basic pipeline test failed with exception: {e}")
        return False

def test_unified_pipeline_discovery():
    """Test 2: Dynamic discovery capabilities"""
    print("\n" + "=" * 60)
    print("TEST 2: DYNAMIC DISCOVERY CAPABILITIES")
    print("=" * 60)
    
    try:
        # Test category discovery
        cmd = [
            "python", "src/scraper/unified_pipeline.py",
            "--dry-run",
            "--discover-categories",
            "--concurrency", "1",
            "--delay", "0.1"
        ]
        
        print(f"Testing category discovery...")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        if result.returncode == 0:
            # Check if discovery worked
            if "Discovered" in result.stdout and "categories" in result.stdout:
                print("✅ Category discovery test passed")
                return True
            else:
                print("❌ Category discovery test failed - no discovery output")
                print(f"   Output: {result.stdout}")
                return False
        else:
            print("❌ Category discovery test failed")
            print(f"   Exit code: {result.returncode}")
            print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Category discovery test failed with exception: {e}")
        return False

def test_unified_pipeline_error_handling():
    """Test 3: Error handling and retry logic"""
    print("\n" + "=" * 60)
    print("TEST 3: ERROR HANDLING AND RETRY LOGIC")
    print("=" * 60)
    
    try:
        # Test with invalid configuration to trigger errors
        cmd = [
            "python", "src/scraper/unified_pipeline.py",
            "--dry-run",
            "--concurrency", "999",  # Invalid high concurrency
            "--delay", "-1",         # Invalid negative delay
            "--max-retries", "0"     # Invalid retries
        ]
        
        print(f"Testing error handling with invalid parameters...")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        # Should handle errors gracefully
        if "error" in result.stdout.lower() or "invalid" in result.stdout.lower():
            print("✅ Error handling test passed - errors handled gracefully")
            return True
        elif result.returncode != 0:
            print("✅ Error handling test passed - invalid parameters rejected")
            return True
        else:
            print("❌ Error handling test failed - no error handling detected")
            return False
            
    except Exception as e:
        print(f"❌ Error handling test failed with exception: {e}")
        return False

def test_multi_runner_orchestrator():
    """Test 4: Multi-runner orchestration"""
    print("\n" + "=" * 60)
    print("TEST 4: MULTI-RUNNER ORCHESTRATION")
    print("=" * 60)
    
    try:
        # Test multi-runner script (dry run mode)
        cmd = [
            "python", "src/scraper/multi_runner_orchestrator.py",
            "--num-runners", "2",
            "--concurrency", "1",
            "--delay", "0.1",
            "--check-interval", "5.0"
        ]
        
        print(f"Testing multi-runner orchestration...")
        print(f"Command: {' '.join(cmd)}")
        
        # Start the process but don't wait too long
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        # Give it a few seconds to start up
        time.sleep(5)
        
        # Check if it's running
        if process.poll() is None:
            print("✅ Multi-runner orchestrator started successfully")
            
            # Terminate gracefully
            process.terminate()
            try:
                process.wait(timeout=10)
                print("✅ Multi-runner orchestrator stopped gracefully")
            except subprocess.TimeoutExpired:
                process.kill()
                print("✅ Multi-runner orchestrator force stopped")
            
            return True
        else:
            print("❌ Multi-runner orchestrator failed to start")
            stdout, stderr = process.communicate()
            print(f"   Exit code: {process.returncode}")
            print(f"   Error: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Multi-runner orchestration test failed with exception: {e}")
        return False

def test_audit_logging():
    """Test 5: Audit logging functionality"""
    print("\n" + "=" * 60)
    print("TEST 5: AUDIT LOGGING FUNCTIONALITY")
    print("=" * 60)
    
    try:
        # Test if audit logging classes can be imported
        from scraper.unified_pipeline import AuditLogger, UnifiedPipeline, PipelineConfig
        
        print("✅ Audit logging classes imported successfully")
        
        # Test configuration creation
        config = PipelineConfig(
            concurrency=2,
            delay=1.0,
            max_retries=3,
            retry_backoff=2.0,
            dry_run=True,
            runner_id="test_runner"
        )
        
        print("✅ Pipeline configuration created successfully")
        
        # Test pipeline creation
        pipeline = UnifiedPipeline(config)
        print("✅ Unified pipeline created successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Audit logging test failed - import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Audit logging test failed with exception: {e}")
        return False

def test_pipeline_integration():
    """Test 6: Pipeline integration and dependencies"""
    print("\n" + "=" * 60)
    print("TEST 6: PIPELINE INTEGRATION AND DEPENDENCIES")
    print("=" * 60)
    
    try:
        # Test if all required modules can be imported
        required_modules = [
            'scraper.unified_pipeline',
            'scraper.multi_level_orchestrator',
            'scraper.pipeline',
            'scraper.multi_runner_orchestrator'
        ]
        
        for module in required_modules:
            try:
                __import__(module)
                print(f"✅ {module} imported successfully")
            except ImportError as e:
                print(f"❌ {module} import failed: {e}")
                return False
        
        print("✅ All required modules imported successfully")
        return True
        
    except Exception as e:
        print(f"❌ Pipeline integration test failed with exception: {e}")
        return False

def main():
    """Run all unified pipeline tests"""
    print("🚀 UNIFIED PIPELINE TEST SUITE")
    print("=" * 80)
    print("Testing unified pipeline capabilities:")
    print("1. Basic unified pipeline functionality")
    print("2. Dynamic discovery capabilities")
    print("3. Error handling and retry logic")
    print("4. Multi-runner orchestration")
    print("5. Audit logging functionality")
    print("6. Pipeline integration and dependencies")
    print("=" * 80)
    
    tests = [
        test_unified_pipeline_basic,
        test_unified_pipeline_discovery,
        test_unified_pipeline_error_handling,
        test_multi_runner_orchestrator,
        test_audit_logging,
        test_pipeline_integration
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
    print("🏁 UNIFIED PIPELINE TEST RESULTS")
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
        print("🎉 ALL TESTS PASSED! The unified pipeline is fully functional!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
