# Enhanced Database Schema with Comprehensive Audit Logging

## Overview

The TAG Grading Scraper database has been significantly enhanced to provide comprehensive audit logging, improved data integrity, and better relationship management between all entities. This document outlines the key improvements and new capabilities.

## Key Enhancements

### 1. Comprehensive Audit Logging System

The new audit logging system provides detailed tracking of all system operations with the following capabilities:

#### Enhanced AuditLog Table Structure
```sql
CREATE TABLE audit_logs (
    id BIGINT PRIMARY KEY,
    level TEXT NOT NULL CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    component TEXT,                    -- Which component generated the log
    operation TEXT,                    -- Operation being performed
    status TEXT CHECK (status IN ('SUCCESS', 'FAILURE', 'PARTIAL')), -- Operation status
    error_code TEXT,                   -- Specific error code if applicable
    error_message TEXT,                -- Detailed error message
    context JSONB,                     -- Additional context data
    message TEXT NOT NULL,             -- Main log message
    stack_trace TEXT,                  -- Stack trace for errors
    user_agent TEXT,                   -- User agent if applicable
    ip_address TEXT,                   -- IP address if applicable
    execution_time_ms INTEGER CHECK (execution_time_ms >= 0), -- Execution time
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);
```

#### Audit Logging Features
- **Component Tracking**: Automatically identifies which component generated each log entry
- **Operation Monitoring**: Tracks specific operations with start/stop timing
- **Error Context**: Captures full error details including stack traces
- **Performance Monitoring**: Records execution times for performance analysis
- **Context Preservation**: Stores relevant context data in JSONB format
- **Dual Logging**: Logs to both database and file system for redundancy

#### Usage Examples

```python
from scraper.audit import get_audit_logger, audit_operation, audit_context

# Basic logging
audit_logger = get_audit_logger('scraper')
audit_logger.info("Starting scraping operation", sport="Baseball", year="1989")

# Operation decorator
@audit_operation("SCRAPE_CARDS")
def scrape_cards(sport, year):
    # Function implementation
    pass

# Context manager
with audit_context("DATA_PROCESSING", component="processor") as logger:
    # Processing logic
    logger.checkpoint("Data validation complete")
```

### 2. Enhanced Data Integrity and Constraints

#### New Check Constraints
- **Year Validation**: Ensures years are within reasonable range (1800-2100)
- **Positive Numbers**: Prevents negative counts and quantities
- **Logical Relationships**: Ensures total_graded >= count where applicable
- **Grade Format Validation**: Validates TAG grade formats using regex patterns

#### Improved Foreign Key Relationships
- **CASCADE DELETE**: Proper cleanup when parent records are deleted
- **Referential Integrity**: All relationships maintain data consistency
- **Soft Deletion**: `is_active` flags for safe record deactivation

### 3. Enhanced Table Structure

#### Core Tables with New Fields
```sql
-- Categories table
ALTER TABLE categories ADD COLUMN description TEXT;
ALTER TABLE categories ADD COLUMN is_active BOOLEAN DEFAULT TRUE NOT NULL;

-- Years table  
ALTER TABLE years ADD COLUMN is_active BOOLEAN DEFAULT TRUE NOT NULL;

-- Sets table
ALTER TABLE sets ADD COLUMN set_description TEXT;
ALTER TABLE sets ADD COLUMN is_active BOOLEAN DEFAULT TRUE NOT NULL;

-- Cards table
ALTER TABLE cards ADD COLUMN is_active BOOLEAN DEFAULT TRUE NOT NULL;

-- Grades table
ALTER TABLE grades ADD COLUMN grade_value SMALLINT; -- For numeric sorting
ALTER TABLE grades ADD COLUMN is_active BOOLEAN DEFAULT TRUE NOT NULL;

-- Snapshots table
ALTER TABLE snapshots ADD COLUMN source TEXT;
ALTER TABLE snapshots ADD COLUMN is_complete BOOLEAN DEFAULT FALSE NOT NULL;
```

#### Totals Tables with Timestamps
```sql
-- All totals tables now include last_updated timestamp
ALTER TABLE category_totals ADD COLUMN last_updated TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL;
ALTER TABLE year_totals ADD COLUMN last_updated TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL;
ALTER TABLE set_totals ADD COLUMN last_updated TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL;
```

### 4. Comprehensive Indexing Strategy

#### Performance Indexes
- **Active Record Indexes**: Fast filtering of active vs. inactive records
- **Composite Indexes**: Optimized for common query patterns
- **Time-based Indexes**: Efficient temporal queries
- **Text Search Indexes**: Fast text-based searches

#### Index Examples
```sql
-- Active record filtering
CREATE INDEX ix_categories_active ON categories (is_active);
CREATE INDEX ix_years_active ON years (is_active);

-- Composite queries
CREATE INDEX ix_sets_category_year ON sets (category_id, year_id);
CREATE INDEX ix_cards_category_year_set_player ON cards (category_id, year_id, set_id, player);

-- Time-based queries
CREATE INDEX ix_audit_logs_created_at_desc ON audit_logs (created_at DESC);
CREATE INDEX ix_card_grade_rows_discovered ON card_grade_rows (discovered_at);
```

### 5. Multi-Level Scraping System Improvements

#### Enhanced Discovery Tables
- **Active Status Tracking**: All discovery tables include `is_active` flags
- **Timestamp Tracking**: Comprehensive discovery timing information
- **Data Validation**: Regex-based validation for year formats and grade patterns
- **Relationship Integrity**: Proper foreign key relationships between discovery levels

#### Logical Relationship Validation
The system now validates that:
- `years_index` entries correspond to valid categories
- `sets_per_year` entries correspond to valid `years_index` entries
- `cards_per_set` entries correspond to valid `sets_per_year` entries
- `card_grade_rows` entries correspond to valid `cards_per_set` entries

### 6. Data Validation and Constraints

#### Comprehensive Validation Rules
```sql
-- Year format validation (4-digit years)
ALTER TABLE years_index ADD CONSTRAINT chk_years_index_year_format 
    CHECK (year ~ '^[0-9]{4}$');

-- Grade format validation (numeric grades with optional decimal)
ALTER TABLE card_grade_rows ADD CONSTRAINT chk_card_grade_rows_grade_format 
    CHECK (tag_grade ~ '^[0-9]+(\.[0-9])?$|^[0-9]+$');

-- Positive number constraints
ALTER TABLE populations ADD CONSTRAINT chk_populations_count 
    CHECK (count >= 0);

-- Logical relationship constraints
ALTER TABLE populations ADD CONSTRAINT chk_populations_total_graded 
    CHECK (total_graded IS NULL OR total_graded >= count);
```

## Database Migration Strategy

### Automatic Migration Script
The enhanced `create_tables.py` script provides comprehensive migration capabilities:

```bash
# Run all migrations
python src/create_tables.py

# This will automatically:
# 1. Create new tables with enhanced structure
# 2. Add new columns to existing tables
# 3. Create new indexes for performance
# 4. Add check constraints for data validation
# 5. Enhance audit logging capabilities
```

### Migration Features
- **Safe Column Addition**: Uses `ADD COLUMN IF NOT EXISTS` for safe migrations
- **Constraint Validation**: Adds check constraints with proper error handling
- **Index Creation**: Creates performance indexes without blocking operations
- **Rollback Support**: Proper transaction handling with rollback on errors
- **Logging**: Comprehensive logging of all migration steps

## Schema Validation

### Comprehensive Validation Script
The new `validate_schema.py` script provides thorough schema validation:

```bash
# Run comprehensive validation
python src/validate_schema.py

# This validates:
# 1. Table structure and existence
# 2. Foreign key relationships
# 3. Unique constraints
# 4. Check constraints
# 5. Index existence and performance
# 6. Data integrity (orphaned records)
# 7. Logical relationships
# 8. Audit logging capabilities
```

### Validation Features
- **Relationship Validation**: Ensures all foreign keys are properly configured
- **Constraint Validation**: Verifies check constraints are in place
- **Index Validation**: Confirms performance indexes exist
- **Data Integrity**: Checks for orphaned records and inconsistencies
- **Comprehensive Reporting**: Detailed validation report with actionable insights

## Performance Optimizations

### Query Optimization
- **Strategic Indexing**: Indexes on commonly queried columns
- **Composite Indexes**: Multi-column indexes for complex queries
- **Partial Indexes**: Indexes on active records only
- **Time-based Partitioning**: Population reports partitioned by date

### Monitoring and Analysis
- **Execution Time Tracking**: Monitor query performance
- **Audit Trail**: Track all database operations
- **Performance Metrics**: Identify slow operations and bottlenecks
- **Resource Usage**: Monitor database resource consumption

## Security and Compliance

### Audit Trail
- **Complete Operation Logging**: All operations are logged with full context
- **Error Tracking**: Comprehensive error logging with stack traces
- **Performance Monitoring**: Track execution times for performance analysis
- **User Activity**: Log user actions and system access

### Data Protection
- **Soft Deletion**: Records can be deactivated without data loss
- **Referential Integrity**: Maintains data consistency across all tables
- **Validation Rules**: Prevents invalid data from entering the system
- **Backup Support**: Comprehensive logging supports backup and recovery

## Usage Guidelines

### Best Practices
1. **Always Use Audit Logging**: Log all significant operations
2. **Validate Data**: Use check constraints to prevent invalid data
3. **Monitor Performance**: Track execution times for optimization
4. **Regular Validation**: Run schema validation regularly
5. **Backup Audit Logs**: Ensure audit logs are properly backed up

### Common Patterns
```python
# Error handling with audit logging
try:
    result = perform_operation()
    audit_logger.log_operation("OPERATION_NAME", status="SUCCESS")
except Exception as e:
    audit_logger.log_error_with_context("Operation failed", e, operation="OPERATION_NAME")
    raise

# Performance monitoring
with audit_context("LONG_OPERATION") as logger:
    logger.checkpoint("Step 1 complete")
    # ... operation steps ...
    logger.checkpoint("Step 2 complete")
```

## Troubleshooting

### Common Issues
1. **Missing Indexes**: Run validation script to identify missing indexes
2. **Constraint Violations**: Check data for constraint violations
3. **Performance Issues**: Monitor execution times in audit logs
4. **Relationship Errors**: Validate foreign key relationships

### Diagnostic Queries
```sql
-- Check audit log performance
SELECT level, COUNT(*), AVG(execution_time_ms) 
FROM audit_logs 
WHERE created_at > NOW() - INTERVAL '1 day'
GROUP BY level;

-- Find slow operations
SELECT operation, AVG(execution_time_ms) as avg_time, COUNT(*) as count
FROM audit_logs 
WHERE execution_time_ms IS NOT NULL
GROUP BY operation 
ORDER BY avg_time DESC;

-- Check for constraint violations
SELECT * FROM audit_logs 
WHERE level = 'ERROR' 
AND error_message LIKE '%constraint%'
ORDER BY created_at DESC;
```

## Conclusion

The enhanced database schema provides a robust foundation for the TAG Grading Scraper with comprehensive audit logging, improved data integrity, and better performance. The migration scripts ensure smooth upgrades, while the validation tools provide confidence in the system's integrity.

Key benefits include:
- **Complete Audit Trail**: Track all operations with full context
- **Data Integrity**: Comprehensive constraints and validation
- **Performance**: Strategic indexing and optimization
- **Maintainability**: Clear structure and comprehensive documentation
- **Scalability**: Support for large datasets and high-performance operations

This enhanced schema represents a significant improvement in the system's reliability, maintainability, and performance capabilities.
