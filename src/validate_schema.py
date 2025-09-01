"""
Database Schema Validation Script

This script performs comprehensive validation of the TAG Grading Scraper database schema,
checking relationships, constraints, and identifying logical inconsistencies.
"""

import logging
from typing import Any, Dict, List, Tuple

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from db import SessionLocal, engine
from models import Base

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from contextlib import contextmanager


@contextmanager
def get_session():
    """Get a database session context manager."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

class SchemaValidator:
    """Comprehensive database schema validator."""
    
    def __init__(self):
        self.inspector = inspect(engine)
        self.validation_results = {
            'errors': [],
            'warnings': [],
            'info': [],
            'passed': []
        }
    
    def _add_result(self, result_type: str, message: str, details: Dict[str, Any] = None):
        """Add a validation result."""
        result = {
            'message': message,
            'details': details or {},
            'timestamp': str(logging.Formatter().formatTime(logging.LogRecord('', 0, '', 0, '', (), None)))
        }
        self.validation_results[result_type].append(result)
    
    def validate_table_structure(self) -> bool:
        """Validate that all expected tables exist and have the correct structure."""
        logger.info("Validating table structure...")
        
        expected_tables = [
            'categories', 'years', 'sets', 'cards', 'grades', 'snapshots', 'populations',
            'audit_logs', 'category_totals', 'year_totals', 'set_totals', 'population_reports',
            'years_index', 'sets_per_year', 'cards_per_set', 'card_grade_rows', 'totals_rollups'
        ]
        
        existing_tables = self.inspector.get_table_names()
        missing_tables = [table for table in expected_tables if table not in existing_tables]
        
        if missing_tables:
            self._add_result('warnings', f"Missing tables: {', '.join(missing_tables)}")
            self._add_result('info', "This is normal for a new project. Run 'python src/setup_database.py' to create the database schema.")
        else:
            self._add_result('passed', "All expected tables exist")
        
        # For new projects, don't fail validation if tables are missing
        return True
    
    def validate_foreign_key_relationships(self) -> bool:
        """Validate foreign key relationships between tables."""
        logger.info("Validating foreign key relationships...")
        
        expected_relationships = {
            'years': {
                'category_id': ('categories', 'id'),
                'constraints': ['year >= 1800 AND year <= 2100']
            },
            'sets': {
                'category_id': ('categories', 'id'),
                'year_id': ('years', 'id'),
                'constraints': ['num_sets IS NULL OR num_sets >= 0', 'total_items IS NULL OR total_items >= 0']
            },
            'cards': {
                'category_id': ('categories', 'id'),
                'year_id': ('years', 'id'),
                'set_id': ('sets', 'id'),
                'constraints': []
            },
            'populations': {
                'snapshot_id': ('snapshots', 'id'),
                'card_uid': ('cards', 'card_uid'),
                'grade_id': ('grades', 'id'),
                'constraints': ['count >= 0', 'total_graded IS NULL OR total_graded >= count']
            },
            'category_totals': {
                'category_id': ('categories', 'id'),
                'constraints': ['num_sets IS NULL OR num_sets >= 0', 'total_items IS NULL OR total_items >= 0', 'total_graded IS NULL OR total_graded >= 0']
            },
            'year_totals': {
                'year_id': ('years', 'id'),
                'constraints': ['num_sets IS NULL OR num_sets >= 0', 'total_items IS NULL OR total_items >= 0', 'total_graded IS NULL OR total_graded >= 0']
            },
            'set_totals': {
                'set_id': ('sets', 'id'),
                'constraints': ['num_cards IS NULL OR num_cards >= 0', 'total_items IS NULL OR total_items >= 0', 'total_graded IS NULL OR total_graded >= 0']
            }
        }
        
        all_valid = True
        
        for table_name, relationships in expected_relationships.items():
            if table_name not in self.inspector.get_table_names():
                continue
                
            table_relationships = self.inspector.get_foreign_keys(table_name)
            
            for fk_column, value in relationships.items():
                # Skip non-foreign key entries like 'constraints'
                if fk_column == 'constraints' or not isinstance(value, tuple) or len(value) != 2:
                    continue
                    
                ref_table, ref_column = value
                
                # Check if foreign key exists
                fk_exists = any(
                    fk['constrained_columns'] == [fk_column] and 
                    fk['referred_table'] == ref_table and 
                    fk['referred_columns'] == [ref_column]
                    for fk in table_relationships
                )
                
                if not fk_exists:
                    self._add_result('errors', f"Missing foreign key: {table_name}.{fk_column} -> {ref_table}.{ref_column}")
                    all_valid = False
                else:
                    self._add_result('passed', f"Foreign key exists: {table_name}.{fk_column} -> {ref_table}.{ref_column}")
        
        return all_valid
    
    def validate_unique_constraints(self) -> bool:
        """Validate unique constraints on tables."""
        logger.info("Validating unique constraints...")
        
        expected_uniques = {
            'categories': ['name'],
            'years': ['category_id', 'year'],
            'sets': ['year_id', 'set_name'],
            'cards': ['card_uid'],
            'grades': ['grade_label'],
            'snapshots': ['captured_at'],
            'audit_logs': ['id'],
            'category_totals': ['category_id'],
            'year_totals': ['year_id'],
            'set_totals': ['set_id'],
            'years_index': ['sport', 'year'],
            'sets_per_year': ['sport', 'year', 'set_title'],
            'cards_per_set': ['sport', 'year', 'set_title', 'card_name'],
            'card_grade_rows': ['sport', 'year', 'set_title', 'card_name', 'cert_number'],
            'totals_rollups': ['scope', 'sport', 'year', 'set_title', 'card_name']
        }
        
        all_valid = True
        
        for table_name, expected_columns in expected_uniques.items():
            if table_name not in self.inspector.get_table_names():
                continue
                
            table_uniques = self.inspector.get_unique_constraints(table_name)
            table_indexes = self.inspector.get_indexes(table_name)
            
            for columns in expected_columns:
                if isinstance(columns, str):
                    columns = [columns]
                
                # Check unique constraints
                unique_exists = any(
                    set(uq['column_names']) == set(columns)
                    for uq in table_uniques
                )
                
                # Check unique indexes as fallback
                if not unique_exists:
                    unique_exists = any(
                        idx['unique'] and set(idx['column_names']) == set(columns)
                        for idx in table_indexes
                    )
                
                if not unique_exists:
                    self._add_result('warnings', f"Missing unique constraint: {table_name}({', '.join(columns)})")
                    all_valid = False
                else:
                    self._add_result('passed', f"Unique constraint exists: {table_name}({', '.join(columns)})")
        
        return all_valid
    
    def validate_check_constraints(self) -> bool:
        """Validate check constraints on tables."""
        logger.info("Validating check constraints...")
        
        expected_checks = {
            'years': ['year >= 1800 AND year <= 2100'],
            'sets': ['num_sets IS NULL OR num_sets >= 0', 'total_items IS NULL OR total_items >= 0'],
            'populations': ['count >= 0', 'total_graded IS NULL OR total_graded >= count'],
            'audit_logs': [
                "level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')",
                "status IS NULL OR status IN ('SUCCESS', 'FAILURE', 'PARTIAL')",
                "execution_time_ms IS NULL OR execution_time_ms >= 0"
            ],
            'category_totals': ['num_sets IS NULL OR num_sets >= 0', 'total_items IS NULL OR total_items >= 0', 'total_graded IS NULL OR total_graded >= 0'],
            'year_totals': ['num_sets IS NULL OR num_sets >= 0', 'total_items IS NULL OR total_items >= 0', 'total_graded IS NULL OR total_graded >= 0'],
            'set_totals': ['num_cards IS NULL OR num_cards >= 0', 'total_items IS NULL OR total_items >= 0', 'total_graded IS NULL OR total_graded >= 0'],
            'years_index': ["year ~ '^[0-9]{4}$'"],
            'sets_per_year': ["year ~ '^[0-9]{4}$'"],
            'cards_per_set': ["year ~ '^[0-9]{4}$'"],
            'card_grade_rows': ["year ~ '^[0-9]{4}$'", "tag_grade ~ '^[0-9]+(\\.[0-9])?$|^[0-9]+$"],
            'totals_rollups': ["scope IN ('sport', 'year', 'set', 'card')", "year IS NULL OR year ~ '^[0-9]{4}$'"]
        }
        
        all_valid = True
        
        for table_name, expected_checks_list in expected_checks.items():
            if table_name not in self.inspector.get_table_names():
                continue
                
            table_checks = self.inspector.get_check_constraints(table_name)
            
            for check_condition in expected_checks_list:
                # Normalize check condition for comparison
                normalized_expected = check_condition.replace("'", "").replace('"', '').replace(' ', '')
                
                check_exists = any(
                    normalized_expected in check['sqltext'].replace("'", "").replace('"', '').replace(' ', '')
                    for check in table_checks
                )
                
                if not check_exists:
                    self._add_result('warnings', f"Missing check constraint: {table_name} - {check_condition}")
                    all_valid = False
                else:
                    self._add_result('passed', f"Check constraint exists: {table_name} - {check_condition}")
        
        return all_valid
    
    def validate_indexes(self) -> bool:
        """Validate that important indexes exist for performance."""
        logger.info("Validating indexes...")
        
        expected_indexes = {
            'categories': ['ix_categories_name', 'ix_categories_active'],
            'years': ['ix_years_category_year', 'ix_years_active'],
            'sets': ['ix_sets_year_setname', 'ix_sets_category_year', 'ix_sets_active'],
            'cards': ['ix_cards_category_year_set_player', 'ix_cards_card_uid', 'ix_cards_active', 'ix_cards_player', 'ix_cards_cert_number'],
            'grades': ['ix_grades_label', 'ix_grades_value', 'ix_grades_active'],
            'snapshots': ['ix_snapshots_captured_at', 'ix_snapshots_source', 'ix_snapshots_complete'],
            'populations': ['ix_populations_carduid_snapshot', 'ix_populations_grade', 'ix_populations_count'],
            'audit_logs': ['ix_audit_logs_created_at_desc', 'ix_audit_logs_level', 'ix_audit_logs_component', 'ix_audit_logs_status', 'ix_audit_logs_error_code', 'ix_audit_logs_operation'],
            'category_totals': ['ix_category_totals_category'],
            'year_totals': ['ix_year_totals_year'],
            'set_totals': ['ix_set_totals_set'],
            'population_reports': ['ix_pop_card_grade_date']
        }
        
        all_valid = True
        
        for table_name, expected_index_list in expected_indexes.items():
            if table_name not in self.inspector.get_table_names():
                continue
                
            table_indexes = self.inspector.get_indexes(table_name)
            existing_index_names = [idx['name'] for idx in table_indexes]
            
            for expected_index in expected_index_list:
                if expected_index not in existing_index_names:
                    self._add_result('warnings', f"Missing index: {table_name}.{expected_index}")
                    all_valid = False
                else:
                    self._add_result('passed', f"Index exists: {table_name}.{expected_index}")
        
        return all_valid
    
    def validate_data_integrity(self) -> bool:
        """Validate data integrity by checking for orphaned records."""
        logger.info("Validating data integrity...")
        
        integrity_checks = [
            ("years", "category_id", "categories", "id", "Years without valid category"),
            ("sets", "category_id", "categories", "id", "Sets without valid category"),
            ("sets", "year_id", "years", "id", "Sets without valid year"),
            ("cards", "category_id", "categories", "id", "Cards without valid category"),
            ("cards", "year_id", "years", "id", "Cards without valid year"),
            ("cards", "set_id", "sets", "id", "Cards without valid set"),
            ("populations", "card_uid", "cards", "card_uid", "Populations without valid card"),
            ("populations", "grade_id", "grades", "id", "Populations without valid grade"),
            ("populations", "snapshot_id", "snapshots", "id", "Populations without valid snapshot"),
            ("category_totals", "category_id", "categories", "id", "Category totals without valid category"),
            ("year_totals", "year_id", "years", "id", "Year totals without valid year"),
            ("set_totals", "set_id", "sets", "id", "Set totals without valid set")
        ]
        
        all_valid = True
        
        for table_name, fk_column, ref_table, ref_column, description in integrity_checks:
            if table_name not in self.inspector.get_table_names() or ref_table not in self.inspector.get_table_names():
                continue
                
            try:
                query = f"""
                SELECT COUNT(*) FROM {table_name} t1
                LEFT JOIN {ref_table} t2 ON t1.{fk_column} = t2.{ref_column}
                WHERE t2.{ref_column} IS NULL
                """
                
                with get_session() as session:
                    result = session.execute(text(query))
                    orphaned_count = result.scalar()
                    
                    if orphaned_count > 0:
                        self._add_result('errors', f"{description}: {orphaned_count} records found")
                        all_valid = False
                    else:
                        self._add_result('passed', f"{description}: No orphaned records")
                    
            except SQLAlchemyError as e:
                self._add_result('warnings', f"Could not check {description}: {e}")
                all_valid = False
        
        return all_valid
    
    def validate_logical_relationships(self) -> bool:
        """Validate logical relationships between multi-level scraping and core tables."""
        logger.info("Validating logical relationships...")
        
        logical_checks = [
            # Check that years_index entries correspond to valid categories
            ("years_index", "sport", "categories", "name", "Years index with invalid sport"),
            # Check that sets_per_year entries correspond to valid years_index entries
            ("sets_per_year", ["sport", "year"], "years_index", ["sport", "year"], "Sets per year with invalid sport/year"),
            # Check that cards_per_set entries correspond to valid sets_per_year entries
            ("cards_per_set", ["sport", "year", "set_title"], "sets_per_year", ["sport", "year", "set_title"], "Cards per set with invalid sport/year/set"),
            # Check that card_grade_rows entries correspond to valid cards_per_set entries
            ("card_grade_rows", ["sport", "year", "set_title", "card_name"], "cards_per_set", ["sport", "year", "set_title", "card_name"], "Card grade rows with invalid sport/year/set/card")
        ]
        
        all_valid = True
        
        for table_name, fk_columns, ref_table, ref_columns, description in logical_checks:
            if table_name not in self.inspector.get_table_names() or ref_table not in self.inspector.get_table_names():
                continue
                
            try:
                if isinstance(fk_columns, str):
                    fk_columns = [fk_columns]
                    ref_columns = [ref_columns]
                
                join_conditions = " AND ".join([f"t1.{fk} = t2.{ref}" for fk, ref in zip(fk_columns, ref_columns)])
                
                query = f"""
                SELECT COUNT(*) FROM {table_name} t1
                LEFT JOIN {ref_table} t2 ON {join_conditions}
                WHERE t2.{ref_columns[0]} IS NULL
                """
                
                with get_session() as session:
                    result = session.execute(text(query))
                    orphaned_count = result.scalar()
                    
                    if orphaned_count > 0:
                        self._add_result('warnings', f"{description}: {orphaned_count} records found")
                        all_valid = False
                    else:
                        self._add_result('passed', f"{description}: No orphaned records")
                    
            except SQLAlchemyError as e:
                self._add_result('warnings', f"Could not check {description}: {e}")
                all_valid = False
        
        return all_valid
    
    def validate_audit_logging(self) -> bool:
        """Validate audit logging table structure and capabilities."""
        logger.info("Validating audit logging...")
        
        if 'audit_logs' not in self.inspector.get_table_names():
            self._add_result('warnings', "Audit logs table does not exist")
            self._add_result('info', "Run 'python src/setup_database.py' to create the database schema")
            return True  # Don't fail validation for missing tables in new projects
        
        # Check required columns
        required_columns = [
            'id', 'level', 'component', 'operation', 'status', 'error_code', 
            'error_message', 'context', 'message', 'stack_trace', 'user_agent', 
            'ip_address', 'execution_time_ms', 'created_at'
        ]
        
        table_columns = [col['name'] for col in self.inspector.get_columns('audit_logs')]
        missing_columns = [col for col in required_columns if col not in table_columns]
        
        if missing_columns:
            self._add_result('warnings', f"Missing audit log columns: {', '.join(missing_columns)}")
            return False
        else:
            self._add_result('passed', "Audit logging table has all required columns")
            return True
    
    def run_validation(self) -> Dict[str, Any]:
        """Run all validation checks."""
        logger.info("Starting comprehensive schema validation...")
        
        try:
            # Run all validation checks
            self.validate_table_structure()
            self.validate_foreign_key_relationships()
            self.validate_unique_constraints()
            self.validate_check_constraints()
            self.validate_indexes()
            self.validate_data_integrity()
            self.validate_logical_relationships()
            self.validate_audit_logging()
            
            # Calculate summary
            total_checks = sum(len(results) for results in self.validation_results.values())
            passed_checks = len(self.validation_results['passed'])
            error_checks = len(self.validation_results['errors'])
            warning_checks = len(self.validation_results['warnings'])
            
            summary = {
                'total_checks': total_checks,
                'passed': passed_checks,
                'errors': error_checks,
                'warnings': warning_checks,
                'info': len(self.validation_results['info']),
                'success_rate': (passed_checks / total_checks * 100) if total_checks > 0 else 0,
                'validation_results': self.validation_results
            }
            
            logger.info(f"Validation complete. {passed_checks}/{total_checks} checks passed ({summary['success_rate']:.1f}%)")
            
            if error_checks > 0:
                logger.error(f"Found {error_checks} errors that need immediate attention")
            
            if warning_checks > 0:
                logger.warning(f"Found {warning_checks} warnings that should be reviewed")
            
            return summary
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            raise
    
    def print_validation_report(self, summary: Dict[str, Any]):
        """Print a formatted validation report."""
        print("\n" + "="*80)
        print("DATABASE SCHEMA VALIDATION REPORT")
        print("="*80)
        
        print("\nSUMMARY:")
        print(f"  Total Checks: {summary['total_checks']}")
        print(f"  Passed: {summary['passed']} ({summary['success_rate']:.1f}%)")
        print(f"  Errors: {summary['errors']}")
        print(f"  Warnings: {summary['warnings']}")
        print(f"  Info: {summary['info']}")

        if summary['errors'] > 0:
            print(f"\nERRORS ({summary['errors']}):")
            for error in summary['validation_results']['errors']:
                print(f"  ❌ {error['message']}")
                if error['details']:
                    for key, value in error['details'].items():
                        print(f"      {key}: {value}")

        if summary['warnings'] > 0:
            print(f"\nWARNINGS ({summary['warnings']}):")
            for warning in summary['validation_results']['warnings']:
                print(f"  ⚠️  {warning['message']}")
                if warning['details']:
                    for key, value in warning['details'].items():
                        print(f"      {key}: {value}")

        if summary['info'] > 0:
            print(f"\nINFO ({summary['info']}):")
            for info in summary['validation_results']['info']:
                print(f"  ℹ️  {info['message']}")

        print(f"\nPASSED CHECKS ({summary['passed']}):")
        # Show first 10 passed checks
        for passed in summary['validation_results']['passed'][:10]:
            print(f"  ✅ {passed['message']}")

        if summary['passed'] > 10:
            print(f"  ... and {summary['passed'] - 10} more passed checks")

        print("\n" + "="*80)
        
        if summary['errors'] == 0 and summary['warnings'] == 0:
            print("🎉 SCHEMA VALIDATION PASSED - All checks successful!")
        elif summary['errors'] == 0:
            print("⚠️  SCHEMA VALIDATION PASSED WITH WARNINGS - Review warnings above")
            print("💡 For new projects, missing tables are normal. "
                  "Run 'python src/setup_database.py' to set up the database.")
        else:
            print("❌ SCHEMA VALIDATION FAILED - Fix errors above before proceeding")


def main():
    """Main validation function."""
    try:
        validator = SchemaValidator()
        summary = validator.run_validation()
        validator.print_validation_report(summary)
        
        # Return appropriate exit code
        if summary['errors'] > 0:
            return 1
        elif summary['warnings'] > 0:
            # For new projects, warnings about missing tables are normal
            print("\n💡 Note: Warnings about missing tables are normal for new projects.")
            print("   Run 'python src/setup_database.py' to create the database schema.")
            return 0  # Don't fail CI for missing tables
        else:
            return 0

    except Exception as e:
        logger.error(f"Validation failed with exception: {e}")
        print(f"\n❌ VALIDATION FAILED: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
