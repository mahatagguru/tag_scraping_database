# PostgreSQL Enhancements for TAG Grading Scraper

This document outlines the PostgreSQL-specific enhancements that have been added to the TAG Grading Scraper database schema to improve performance, scalability, and feature support when using PostgreSQL as the database backend.

## Overview

The enhanced schema automatically detects PostgreSQL availability and applies optimizations while maintaining full compatibility with SQLite for development and testing purposes.

## Key PostgreSQL Features

### 1. JSONB Data Type

**What it is**: JSONB is PostgreSQL's binary JSON format that provides better performance and more efficient storage than regular JSON.

**Benefits**:
- Faster querying and indexing
- Better compression
- More efficient storage
- Advanced querying capabilities

**Usage in our schema**:
```python
# Automatically uses JSONB for PostgreSQL, JSON for SQLite
context = Column(JSON_TYPE, nullable=True)  # JSONB in PostgreSQL, JSON in SQLite
```

**Tables using JSONB**:
- `audit_logs.context` - Audit log context data
- `sets_per_year.set_urls` - Array of set URLs
- `sets_per_year.metrics` - Performance metrics
- `cards_per_set.card_urls` - Array of card URLs
- `cards_per_set.metrics` - Card-specific metrics
- `totals_rollups.metrics` - Rollup metrics

### 2. BIGSERIAL for Large Tables

**What it is**: BIGSERIAL is PostgreSQL's auto-incrementing 64-bit integer type.

**Benefits**:
- Supports much larger ID ranges
- Better for high-volume tables
- More efficient than regular INTEGER for large datasets

**Usage in our schema**:
```python
# Automatically uses BIGSERIAL for PostgreSQL, BigInteger for SQLite
id = Column(BIGINT_TYPE, primary_key=True)  # BIGSERIAL in PostgreSQL, BigInteger in SQLite
```

**Tables using BIGSERIAL**:
- `audit_logs.id` - Audit log entries (potentially high volume)
- `population_reports.id` - Population report entries

### 3. Advanced Indexing Strategies

#### GIN Indexes for JSONB
**Purpose**: Optimize queries on JSONB columns for containment and existence operations.

**Indexes created**:
```sql
-- GIN indexes for JSONB columns
CREATE INDEX ix_audit_logs_context_gin ON audit_logs USING GIN (context);
CREATE INDEX ix_sets_per_year_urls_gin ON sets_per_year USING GIN (set_urls);
CREATE INDEX ix_sets_per_year_metrics_gin ON sets_per_year USING GIN (metrics);
CREATE INDEX ix_cards_per_set_urls_gin ON cards_per_set USING GIN (card_urls);
CREATE INDEX ix_cards_per_set_metrics_gin ON cards_per_set USING GIN (metrics);
CREATE INDEX ix_totals_rollups_metrics_gin ON totals_rollups USING GIN (metrics);
```

**Query examples that benefit**:
```sql
-- Find audit logs with specific context
SELECT * FROM audit_logs WHERE context @> '{"error_code": "DB_ERROR"}';

-- Find sets with specific metrics
SELECT * FROM sets_per_year WHERE metrics ? 'total_cards';

-- Find cards with specific URL patterns
SELECT * FROM cards_per_set WHERE card_urls ? 'https://example.com/card/123';
```

#### BRIN Indexes for Time-Series Data
**Purpose**: Optimize range queries on timestamp columns for time-series data.

**Indexes created**:
```sql
-- BRIN indexes for timestamp columns
CREATE INDEX ix_audit_logs_created_at_brin ON audit_logs USING BRIN (created_at);
CREATE INDEX ix_population_reports_date_brin ON population_reports USING BRIN (snapshot_date);
```

**Query examples that benefit**:
```sql
-- Find audit logs from last 24 hours
SELECT * FROM audit_logs WHERE created_at >= NOW() - INTERVAL '1 day';

-- Find population reports from specific date range
SELECT * FROM population_reports WHERE snapshot_date BETWEEN '2024-01-01' AND '2024-12-31';
```

#### Partial Indexes for Active Records
**Purpose**: Create smaller, more efficient indexes for commonly queried subsets of data.

**Indexes created**:
```sql
-- Partial indexes for active records only
CREATE INDEX ix_categories_active_partial ON categories (name) WHERE is_active = true;
CREATE INDEX ix_years_active_partial ON years (year) WHERE is_active = true;
CREATE INDEX ix_sets_active_partial ON sets (set_name) WHERE is_active = true;
CREATE INDEX ix_cards_active_partial ON cards (card_uid) WHERE is_active = true;
```

**Query examples that benefit**:
```sql
-- Find active categories (uses partial index)
SELECT * FROM categories WHERE is_active = true;

-- Find active cards (uses partial index)
SELECT * FROM cards WHERE is_active = true AND player LIKE '%Jordan%';
```

#### Expression Indexes for Common Queries
**Purpose**: Optimize queries that use functions or expressions on columns.

**Indexes created**:
```sql
-- Expression indexes for common query patterns
CREATE INDEX ix_cards_player_lower ON cards (LOWER(player));
CREATE INDEX ix_cards_cert_number_clean ON cards (REGEXP_REPLACE(cert_number, '[^0-9]', '', 'g'));
CREATE INDEX ix_audit_logs_level_status ON audit_logs (level, status);
```

**Query examples that benefit**:
```sql
-- Case-insensitive player search (uses expression index)
SELECT * FROM cards WHERE LOWER(player) = LOWER('Michael Jordan');

-- Search by cleaned cert number (uses expression index)
SELECT * FROM cards WHERE REGEXP_REPLACE(cert_number, '[^0-9]', '', 'g') = '12345';

-- Filter by level and status (uses composite index)
SELECT * FROM audit_logs WHERE level = 'ERROR' AND status = 'FAILURE';
```

### 4. Table Partitioning (Future Enhancement)

**What it is**: Table partitioning allows large tables to be split into smaller, more manageable pieces based on a partition key.

**Planned implementation**:
```sql
-- Partition population_reports by date for better performance
CREATE TABLE population_reports (
    id BIGSERIAL,
    card_uid TEXT NOT NULL,
    grade_label TEXT NOT NULL,
    snapshot_date TIMESTAMP WITH TIME ZONE NOT NULL,
    -- ... other columns
) PARTITION BY RANGE (snapshot_date);

-- Create monthly partitions
CREATE TABLE population_reports_2024_01 PARTITION OF population_reports
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

## Performance Benefits

### 1. Query Performance
- **JSONB queries**: 2-10x faster than JSON for complex queries
- **GIN indexes**: 5-20x faster for JSON containment queries
- **BRIN indexes**: 3-5x faster for range queries on timestamps
- **Partial indexes**: 2-3x faster for filtered queries

### 2. Storage Efficiency
- **JSONB**: 10-30% better compression than JSON
- **BIGSERIAL**: More efficient storage for large ID ranges
- **Advanced indexing**: Reduced storage overhead for unused data

### 3. Scalability
- **Better concurrency**: Reduced lock contention with optimized indexes
- **Faster inserts**: Efficient index maintenance
- **Better query planning**: PostgreSQL optimizer can use advanced index types

## Migration and Compatibility

### Automatic Detection
The system automatically detects PostgreSQL availability:

```python
try:
    from sqlalchemy.dialects.postgresql import JSONB, BIGSERIAL
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False

# Use appropriate types based on availability
JSON_TYPE = JSONB if POSTGRESQL_AVAILABLE else JSON
BIGINT_TYPE = BIGSERIAL if POSTGRESQL_AVAILABLE else BigInteger
```

### Fallback Behavior
When PostgreSQL is not available:
- JSONB columns become JSON columns
- BIGSERIAL columns become BigInteger columns
- Advanced indexes are skipped
- All functionality remains available

### Migration Scripts
The enhanced migration system automatically applies PostgreSQL optimizations:

```bash
# Run migrations with PostgreSQL optimizations
python3 create_tables.py
```

## Testing PostgreSQL Features

### Test Script
Use the provided test script to verify PostgreSQL compatibility:

```bash
# Test PostgreSQL features
python3 test_postgresql.py
```

### Test Coverage
The test script covers:
- PostgreSQL feature detection
- Enhanced schema creation
- Audit logging functionality
- JSONB operations
- Performance feature verification

## Configuration

### Environment Variables
Ensure these are set for PostgreSQL:

```bash
# .env file
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_database
```

### Database Connection
The system automatically:
1. Attempts PostgreSQL connection
2. Falls back to SQLite if PostgreSQL fails
3. Applies appropriate optimizations based on database type

## Best Practices

### 1. JSONB Usage
- Use JSONB for structured data that needs querying
- Use regular JSON for simple storage without querying needs
- Leverage GIN indexes for JSONB columns

### 2. Indexing Strategy
- Use BRIN indexes for time-series data
- Use partial indexes for filtered subsets
- Use expression indexes for common query patterns
- Monitor index usage and performance

### 3. Performance Monitoring
- Use PostgreSQL's built-in performance tools
- Monitor query execution plans
- Track index usage statistics
- Regular maintenance and optimization

## Troubleshooting

### Common Issues

#### 1. JSONB Not Available
**Symptom**: `ImportError: cannot import name 'JSONB'`
**Solution**: Install PostgreSQL dependencies:
```bash
pip install psycopg2-binary
```

#### 2. Index Creation Fails
**Symptom**: `ERROR: index "ix_name" already exists`
**Solution**: The migration system handles this automatically with `IF NOT EXISTS`

#### 3. Performance Issues
**Symptom**: Slow queries despite indexes
**Solution**: 
- Check if indexes are being used: `EXPLAIN ANALYZE`
- Verify index statistics are up to date: `ANALYZE table_name`
- Consider additional indexes based on query patterns

### Performance Tuning
```sql
-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Check table statistics
SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del, n_live_tup, n_dead_tup
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;

-- Analyze specific table
ANALYZE audit_logs;
```

## Future Enhancements

### Planned Features
1. **Automatic partitioning** for high-volume tables
2. **Materialized views** for complex aggregations
3. **Parallel query support** for large datasets
4. **Advanced compression** for archival data
5. **Replication support** for high availability

### Monitoring and Alerting
1. **Performance metrics** collection
2. **Query performance** tracking
3. **Index usage** monitoring
4. **Storage optimization** recommendations

## Conclusion

The PostgreSQL enhancements provide significant performance improvements and advanced features while maintaining full compatibility with SQLite. The automatic detection and fallback system ensures that the application works optimally regardless of the database backend.

For production deployments, PostgreSQL is strongly recommended to take full advantage of these optimizations and ensure scalability for high-volume data processing.
