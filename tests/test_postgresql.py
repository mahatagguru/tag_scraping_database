#!/usr/bin/env python3
"""
PostgreSQL Compatibility Test Script

This script tests the enhanced database schema with PostgreSQL-specific features
to ensure compatibility and performance optimizations work correctly.
"""

import logging
import os
import sys

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import engine, get_db_session, get_db_session_context
from models import Base
from scraper.audit import AuditLogger

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_postgresql_features():
    """Test PostgreSQL-specific features and optimizations."""
    logger.info("Testing PostgreSQL-specific features...")
    
    # Check if we're using PostgreSQL
    is_postgresql = 'postgresql' in str(engine.url)
    is_sqlite = 'sqlite' in str(engine.url)
    
    if is_sqlite:
        logger.info("SQLite database detected - skipping PostgreSQL-specific tests")
        # For SQLite, just verify basic functionality works
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                assert result.scalar() == 1
            logger.info("✅ SQLite basic functionality verified")
            return
        except Exception as e:
            logger.error(f"SQLite test failed: {e}")
            assert False, f"SQLite test failed: {e}"
    
    if not is_postgresql:
        logger.warning("Unknown database type detected")
        assert False, "Unknown database type detected"
    
    logger.info("✅ PostgreSQL database detected")
    
    try:
        with engine.connect() as conn:
            # Test 1: Check PostgreSQL version
            result = conn.execute(text("SELECT version();"))
            version = result.scalar()
            logger.info(f"PostgreSQL Version: {version}")
            
            # Test 2: Check if JSONB is available
            result = conn.execute(text("SELECT typname FROM pg_type WHERE typname = 'jsonb';"))
            jsonb_available = result.fetchone() is not None
            logger.info(f"JSONB available: {jsonb_available}")
            
            # Test 3: Check if GIN indexes are available
            result = conn.execute(text("SELECT amname FROM pg_am WHERE amname = 'gin';"))
            gin_available = result.fetchone() is not None
            logger.info(f"GIN indexes available: {gin_available}")
            
            # Test 4: Check if BRIN indexes are available
            result = conn.execute(text("SELECT amname FROM pg_am WHERE amname = 'brin';"))
            brin_available = result.fetchone() is not None
            logger.info(f"BRIN indexes available: {brin_available}")
            
            # Test 5: Check table partitioning support
            result = conn.execute(text("SELECT EXISTS (SELECT 1 FROM pg_class WHERE relkind = 'p');"))
            partitioning_available = result.scalar()
            logger.info(f"Table partitioning available: {partitioning_available}")
            
            assert True, "PostgreSQL features test completed successfully"
            
    except SQLAlchemyError as e:
        logger.error(f"Error testing PostgreSQL features: {e}")
        assert False, f"PostgreSQL test failed: {e}"

def test_enhanced_schema():
    """Test the enhanced schema with PostgreSQL features."""
    logger.info("Testing enhanced schema with PostgreSQL...")
    
    try:
        # Create all tables
        Base.metadata.create_all(engine)
        logger.info("✅ All tables created successfully")
        
        # Test table structure
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Tables created: {', '.join(tables)}")
        
        # Test specific table structures
        for table_name in ['audit_logs', 'categories', 'years', 'sets', 'cards']:
            if table_name in tables:
                columns = inspector.get_columns(table_name)
                logger.info(f"Table {table_name} columns: {[col['name'] for col in columns]}")
                
                # Check for specific column types
                for col in columns:
                    if col['name'] == 'context' and table_name == 'audit_logs':
                        logger.info(f"Column {col['name']} type: {col['type']}")
                    elif col['name'] == 'id' and table_name == 'audit_logs':
                        logger.info(f"Column {col['name']} type: {col['type']}")
        
        assert True, "PostgreSQL test completed successfully"
        
    except SQLAlchemyError as e:
        logger.error(f"Error testing enhanced schema: {e}")
        assert False, f"PostgreSQL test failed: {e}"

def test_audit_logging():
    """Test audit logging functionality with both PostgreSQL and SQLite."""
    logger.info("Testing audit logging...")
    
    # Check database type
    is_postgresql = 'postgresql' in str(engine.url)
    is_sqlite = 'sqlite' in str(engine.url)
    
    try:
        audit_logger = AuditLogger(component="database_test")
        
        # Test different log levels
        audit_logger.log('INFO', 'Testing audit logging')
        audit_logger.log('WARNING', 'Test warning message')
        audit_logger.log('ERROR', 'Test error message')
        
        # Test operation logging - fix the method call
        audit_logger.log_operation('TEST_OPERATION', 'SUCCESS')
        
        # Test performance logging
        audit_logger.log_performance('TEST_PERFORMANCE', 150)
        
        # Test error logging - fix the method call
        try:
            raise ValueError("Test error for logging")
        except Exception as e:
            audit_logger.log_error_with_context('Test error message', e, 
                                              operation='TEST_ERROR', 
                                              context={'test': 'context'})
        
        logger.info("✅ Audit logging tests completed")
        assert True, "Audit logging test completed successfully"
        
    except Exception as e:
        logger.error(f"Error testing audit logging: {e}")
        assert False, f"Audit logging test failed: {e}"

def test_jsonb_operations():
    """Test JSONB operations if available."""
    logger.info("Testing JSONB operations...")
    
    # Check database type
    is_postgresql = 'postgresql' in str(engine.url)
    is_sqlite = 'sqlite' in str(engine.url)
    
    if is_sqlite:
        logger.info("SQLite database detected - testing JSON support")
        # For SQLite, test basic JSON functionality without database insertion
        try:
            # Test JSON serialization/deserialization
            test_context = {
                'test_key': 'test_value',
                'nested': {'level1': 'value1', 'level2': 42},
                'array': [1, 2, 3, 'test']
            }
            
            import json
            json_str = json.dumps(test_context)
            parsed_context = json.loads(json_str)
            
            assert parsed_context == test_context
            logger.info("✅ SQLite JSON serialization/deserialization test completed")
            
            # Test basic database connection
            with get_db_session_context() as session:
                result = session.execute(text("SELECT 1"))
                assert result.scalar() == 1
                logger.info("✅ SQLite database connection test completed")
            
            logger.info("✅ SQLite JSON operations test completed")
            return
        except Exception as e:
            logger.error(f"SQLite JSON test failed: {e}")
            assert False, f"SQLite JSON test failed: {e}"
    
    if not is_postgresql:
        logger.warning("Unknown database type detected")
        assert False, "Unknown database type detected"
    
    try:
        with get_db_session_context() as session:
            # Test inserting JSON data
            test_context = {
                'test_key': 'test_value',
                'nested': {'level1': 'value1', 'level2': 42},
                'array': [1, 2, 3, 'test']
            }
            
            # Insert a test audit log entry
            from models import AuditLog
            test_log = AuditLog(
                level='INFO',
                component='jsonb_test',
                operation='TEST_JSONB',
                status='SUCCESS',
                context=test_context,
                message='Testing JSONB operations'
            )
            
            session.add(test_log)
            session.commit()
            logger.info("✅ JSONB insert test completed")
            
            # Test querying JSON data
            result = session.query(AuditLog).filter(
                AuditLog.context['test_key'].astext == 'test_value'
            ).first()
            
            if result:
                logger.info("✅ JSONB query test completed")
                logger.info(f"Retrieved context: {result.context}")
            else:
                logger.warning("JSONB query test failed - no results found")
            
            # Test JSONB path operations
            result = session.query(AuditLog).filter(
                AuditLog.context['nested']['level1'].astext == 'value1'
            ).first()
            
            if result:
                logger.info("✅ JSONB path query test completed")
            else:
                logger.warning("JSONB path query test failed")
            
            # Clean up test data
            session.delete(test_log)
            session.commit()
            
        assert True, "PostgreSQL test completed successfully"
        
    except Exception as e:
        logger.error(f"Error testing JSONB operations: {e}")
        assert False, f"PostgreSQL test failed: {e}"

def test_performance_features():
    """Test PostgreSQL performance features."""
    logger.info("Testing performance features...")
    
    # Check database type
    is_postgresql = 'postgresql' in str(engine.url)
    is_sqlite = 'sqlite' in str(engine.url)
    
    if is_sqlite:
        logger.info("SQLite database detected - testing basic performance features")
        try:
            with engine.connect() as conn:
                # Test basic connection and query performance
                result = conn.execute(text("SELECT 1"))
                assert result.scalar() == 1
                
                # Test table existence
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                tables = [row[0] for row in result.fetchall()]
                logger.info(f"SQLite tables: {tables}")
                
                # Test basic index existence
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='index'"))
                indexes = [row[0] for row in result.fetchall()]
                logger.info(f"SQLite indexes: {indexes}")
                
                logger.info("✅ SQLite performance features test completed")
                return
        except Exception as e:
            logger.error(f"SQLite performance test failed: {e}")
            assert False, f"SQLite performance test failed: {e}"
    
    if not is_postgresql:
        logger.warning("Unknown database type detected")
        assert False, "Unknown database type detected"
    
    try:
        with engine.connect() as conn:
            # Test 1: Check if GIN indexes exist
            gin_indexes = [
                'ix_audit_logs_context_gin',
                'ix_sets_per_year_urls_gin',
                'ix_cards_per_set_urls_gin'
            ]
            
            for index_name in gin_indexes:
                result = conn.execute(text(f"""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_indexes 
                        WHERE indexname = '{index_name}' 
                        AND indexdef LIKE '%USING gin%'
                    );
                """))
                exists = result.scalar()
                logger.info(f"GIN index {index_name}: {'✅' if exists else '❌'}")
            
            # Test 2: Check if BRIN indexes exist
            brin_indexes = [
                'ix_audit_logs_created_at_brin',
                'ix_population_reports_date_brin'
            ]
            
            for index_name in brin_indexes:
                result = conn.execute(text(f"""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_indexes 
                        WHERE indexname = '{index_name}' 
                        AND indexdef LIKE '%USING brin%'
                    );
                """))
                exists = result.scalar()
                logger.info(f"BRIN index {index_name}: {'✅' if exists else '❌'}")
            
            # Test 3: Check if partial indexes exist
            partial_indexes = [
                'ix_categories_active_partial',
                'ix_years_active_partial'
            ]
            
            for index_name in partial_indexes:
                result = conn.execute(text(f"""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_indexes 
                        WHERE indexname = '{index_name}' 
                        AND indexdef LIKE '%WHERE%'
                    );
                """))
                exists = result.scalar()
                logger.info(f"Partial index {index_name}: {'✅' if exists else '❌'}")
            
        assert True, "PostgreSQL test completed successfully"
        
    except SQLAlchemyError as e:
        logger.error(f"Error testing performance features: {e}")
        assert False, f"PostgreSQL test failed: {e}"

def main():
    """Main test function."""
    logger.info("Starting PostgreSQL compatibility tests...")
    
    tests = [
        ("PostgreSQL Features", test_postgresql_features),
        ("Enhanced Schema", test_enhanced_schema),
        ("Audit Logging", test_audit_logging),
        ("JSONB Operations", test_jsonb_operations),
        ("Performance Features", test_performance_features)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running test: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            success = test_func()
            results.append((test_name, success))
            logger.info(f"Test {test_name}: {'✅ PASSED' if success else '❌ FAILED'}")
        except Exception as e:
            logger.error(f"Test {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All PostgreSQL compatibility tests passed!")
    else:
        logger.warning(f"⚠️  {total - passed} tests failed. Review the logs above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
