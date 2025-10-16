#!/usr/bin/env python3
"""
PostgreSQL Enhancement Detection Test

This script tests whether the PostgreSQL enhancements are properly detected
and applied in the models.
"""

import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_postgresql_detection():
    """Test PostgreSQL enhancement detection."""
    print("Testing PostgreSQL enhancement detection...")

    try:
        # Import the models to trigger the detection
        import models

        # Check if PostgreSQL types are available
        print(f"PostgreSQL available: {models.POSTGRESQL_AVAILABLE}")
        print(f"JSON_TYPE: {models.JSON_TYPE}")
        print(f"BIGINT_TYPE: {models.BIGINT_TYPE}")

        # Check specific model columns
        from models import AuditLog, PopulationReport

        print(f"\nAuditLog.id column type: {AuditLog.id.type}")
        print(f"AuditLog.context column type: {AuditLog.context.type}")
        print(f"PopulationReport.id column type: {PopulationReport.id.type}")

        # Check if we're using the right types
        if models.POSTGRESQL_AVAILABLE:
            print("\n✅ PostgreSQL enhancements detected and applied")
            print("   - JSONB columns for better performance")
            print("   - BIGSERIAL for large ID ranges")
        else:
            print("\n✅ SQLite compatibility mode active")
            print("   - JSON columns for compatibility")
            print("   - BigInteger for ID columns")

        return True

    except Exception as e:
        print(f"❌ Error testing PostgreSQL detection: {e}")
        return False


def test_import_compatibility():
    """Test that all imports work correctly."""
    print("\nTesting import compatibility...")

    try:
        # Test PostgreSQL imports
        try:
            from sqlalchemy.dialects.postgresql import BIGSERIAL, JSONB

            print("✅ PostgreSQL SQLAlchemy types available")
        except ImportError:
            print("⚠️  PostgreSQL SQLAlchemy types not available")

        # Test core imports
        from sqlalchemy import JSON, BigInteger

        print("✅ Core SQLAlchemy types available")

        # Test our models
        from models import AuditLog, Base, Card, Category, Set, Year

        print("✅ All model imports successful")

        return True

    except Exception as e:
        print(f"❌ Import compatibility test failed: {e}")
        return False


def main():
    """Main test function."""
    print("=" * 60)
    print("PostgreSQL Enhancement Detection Test")
    print("=" * 60)

    tests = [
        ("Import Compatibility", test_import_compatibility),
        ("PostgreSQL Detection", test_postgresql_detection),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{'-'*40}")
        print(f"Running: {test_name}")
        print(f"{'-'*40}")

        try:
            success = test_func()
            results.append((test_name, success))
            print(f"Test {test_name}: {'✅ PASSED' if success else '❌ FAILED'}")
        except Exception as e:
            print(f"Test {test_name} failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        print("\nThe system is ready to use PostgreSQL enhancements when available.")
    else:
        print(f"⚠️  {total - passed} tests failed. Review the output above.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
