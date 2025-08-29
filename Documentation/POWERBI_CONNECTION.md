# TAG Grading Scraper - PowerBI Connection Guide

## Overview

This guide provides comprehensive instructions for connecting Microsoft PowerBI to the TAG Grading Scraper database to create reports and dashboards for sports card population data analysis.

## Prerequisites

### Required Software
- **PowerBI Desktop**: Latest version (free download from Microsoft)
- **PowerBI Service**: Pro or Premium license for sharing and collaboration
- **PostgreSQL Driver**: ODBC driver for PostgreSQL connectivity

### Database Access
- **Database Host**: IP address or hostname of your database server
- **Database Port**: 5432 (default PostgreSQL port)
- **Database Name**: Your database name (e.g., `tag_grading_db`)
- **Username**: Database username with read permissions
- **Password**: Database password

## Database Connection Setup

### 1. Install PostgreSQL ODBC Driver

#### Windows
```bash
# Download and install PostgreSQL ODBC driver
# Visit: https://www.postgresql.org/ftp/odbc/versions/msi/

# 64-bit driver (recommended)
# Download: psqlodbc_15_02_0000-x64.msi

# Install with default settings
# Verify installation in ODBC Data Source Administrator
```

#### macOS
```bash
# Install using Homebrew
brew install postgresql-odbc

# Or download from PostgreSQL website
# https://www.postgresql.org/ftp/odbc/versions/msi/
```

### 2. Configure ODBC Data Source

#### Windows ODBC Configuration
```bash
# Open ODBC Data Source Administrator
# Windows Search: "ODBC Data Sources (64-bit)"

# Add new System DSN
# Driver: PostgreSQL Unicode(x64)
# Data Source Name: TAG_Grading_DB
# Server: your-database-host
# Port: 5432
# Database: tag_grading_db
# Username: your-username
# Password: your-password

# Test Connection
# Click "Test" to verify connectivity
```

#### macOS ODBC Configuration
```bash
# Edit ODBC configuration file
sudo nano /usr/local/etc/odbcinst.ini

# Add PostgreSQL driver
[PostgreSQL]
Description = PostgreSQL ODBC driver
Driver = /usr/local/lib/psqlodbcw.so
Setup = /usr/local/lib/psqlodbcw.so

# Edit odbc.ini
sudo nano /usr/local/etc/odbc.ini

# Add data source
[TAG_Grading_DB]
Description = TAG Grading Database
Driver = PostgreSQL
Server = your-database-host
Port = 5432
Database = tag_grading_db
Username = your-username
Password = your-password
```

## PowerBI Connection Methods

### Method 1: Direct Database Connection (Recommended)

#### Step 1: Open PowerBI Desktop
```bash
# Launch PowerBI Desktop
# Click "Get Data" from the Home ribbon
```

#### Step 2: Select Data Source
```bash
# Choose "Database" category
# Select "PostgreSQL database"
# Click "Connect"
```

#### Step 3: Configure Connection
```bash
# Server: your-database-host
# Database: tag_grading_db
# Data Connectivity mode: Import (recommended for small datasets)
# Click "OK"
```

#### Step 4: Authentication
```bash
# Username: your-database-username
# Password: your-database-password
# Click "Connect"
```

#### Step 5: Select Tables
```bash
# Choose tables to import:
# - categories
# - years
# - sets
# - cards
# - populations
# - grades
# - snapshots
# - years_index
# - sets_per_year
# - cards_per_set
# - card_grade_rows
# - totals_rollups

# Click "Load" to import data
```

### Method 2: ODBC Connection

#### Step 1: Configure ODBC
```bash
# Use the ODBC data source configured earlier
# In PowerBI, select "ODBC" as data source
# Choose your configured DSN: TAG_Grading_DB
```

#### Step 2: Import Data
```bash
# Select tables as in Method 1
# Import data using ODBC connection
```

### Method 3: SQL Query Import

#### Step 1: Advanced Editor
```bash
# In PowerBI, click "Get Data" > "Blank Query"
# Click "Advanced Editor"
```

#### Step 2: Custom SQL Query
```sql
-- Example: Import cards with population data
let
    Source = PostgreSQL.Database("your-database-host", "tag_grading_db", [
        Query="
            SELECT 
                c.player,
                c.card_number,
                s.set_name,
                y.year,
                cat.name as sport,
                g.grade_label,
                p.count as population_count,
                p.total_graded,
                s.captured_at
            FROM cards c
            JOIN sets s ON c.set_id = s.id
            JOIN years y ON c.year_id = y.id
            JOIN categories cat ON c.category_id = cat.id
            JOIN populations p ON c.card_uid = p.card_uid
            JOIN grades g ON p.grade_id = g.id
            JOIN snapshots s ON p.snapshot_id = s.id
            WHERE s.captured_at = (
                SELECT MAX(captured_at) FROM snapshots
            )
        "
    ])
in
    Source
```

## Data Model Design

### 1. Table Relationships

#### Primary Relationships
```sql
-- Categories (Sports) → Years → Sets → Cards → Populations
categories (1) → (many) years
years (1) → (many) sets
sets (1) → (many) cards
cards (1) → (many) populations
grades (1) → (many) populations
snapshots (1) → (many) populations
```

#### Multi-Level Scraping Relationships
```sql
-- Discovery flow relationships
years_index (1) → (many) sets_per_year
sets_per_year (1) → (many) cards_per_set
cards_per_set (1) → (many) card_grade_rows
```

### 2. Data Model Setup

#### Step 1: Create Relationships
```bash
# In PowerBI, go to "Model" view
# Drag and drop to create relationships:

# categories.id → years.category_id
# years.id → sets.year_id
# sets.id → cards.set_id
# cards.card_uid → populations.card_uid
# grades.id → populations.grade_id
# snapshots.id → populations.snapshot_id
```

#### Step 2: Set Cardinality
```bash
# Set relationship cardinality:
# categories → years: One to Many
# years → sets: One to Many
# sets → cards: One to Many
# cards → populations: One to Many
# grades → populations: One to Many
# snapshots → populations: One to Many
```

#### Step 3: Configure Cross-Filter Direction
```bash
# Set cross-filter direction:
# Single direction: categories → years → sets → cards → populations
# Bi-directional: populations ↔ grades, populations ↔ snapshots
```

## Report Design Examples

### 1. Sports Overview Dashboard

#### Key Metrics
```sql
-- Total cards by sport
SELECT 
    cat.name as sport,
    COUNT(DISTINCT c.id) as total_cards,
    COUNT(DISTINCT s.id) as total_sets,
    COUNT(DISTINCT y.id) as total_years
FROM categories cat
LEFT JOIN years y ON cat.id = y.category_id
LEFT JOIN sets s ON y.id = s.year_id
LEFT JOIN cards c ON s.id = c.set_id
GROUP BY cat.name
ORDER BY total_cards DESC
```

#### Visualizations
- **Bar Chart**: Total cards by sport
- **Pie Chart**: Distribution of sets by sport
- **Line Chart**: Cards over time by sport
- **KPI Cards**: Total cards, sets, years

### 2. Population Analysis Dashboard

#### Key Metrics
```sql
-- Population distribution by grade
SELECT 
    g.grade_label,
    SUM(p.count) as total_population,
    COUNT(DISTINCT p.card_uid) as unique_cards,
    AVG(p.count) as avg_population_per_card
FROM grades g
JOIN populations p ON g.id = p.grade_id
JOIN snapshots s ON p.snapshot_id = s.id
WHERE s.captured_at = (SELECT MAX(captured_at) FROM snapshots)
GROUP BY g.grade_label
ORDER BY total_population DESC
```

#### Visualizations
- **Histogram**: Population distribution by grade
- **Scatter Plot**: Population vs. Grade
- **Table**: Detailed population statistics
- **Gauge**: Overall population health

### 3. Set Performance Dashboard

#### Key Metrics
```sql
-- Set performance metrics
SELECT 
    s.set_name,
    y.year,
    cat.name as sport,
    COUNT(DISTINCT c.id) as card_count,
    AVG(p.count) as avg_population,
    MAX(p.count) as max_population,
    MIN(p.count) as min_population
FROM sets s
JOIN years y ON s.year_id = y.id
JOIN categories cat ON s.category_id = cat.id
JOIN cards c ON s.id = c.set_id
JOIN populations p ON c.card_uid = p.card_uid
JOIN snapshots snap ON p.snapshot_id = snap.id
WHERE snap.captured_at = (SELECT MAX(captured_at) FROM snapshots)
GROUP BY s.set_name, y.year, cat.name
ORDER BY avg_population DESC
```

#### Visualizations
- **Heat Map**: Set performance by year and sport
- **Bar Chart**: Top performing sets
- **Line Chart**: Set performance over time
- **Matrix**: Detailed set metrics

### 4. Player Analysis Dashboard

#### Key Metrics
```sql
-- Player card analysis
SELECT 
    c.player,
    cat.name as sport,
    COUNT(DISTINCT c.id) as total_cards,
    COUNT(DISTINCT s.set_name) as unique_sets,
    AVG(p.count) as avg_population,
    SUM(p.count) as total_population
FROM cards c
JOIN sets s ON c.set_id = s.id
JOIN years y ON s.year_id = y.id
JOIN categories cat ON s.category_id = cat.id
JOIN populations p ON c.card_uid = p.card_uid
JOIN snapshots snap ON p.snapshot_id = snap.id
WHERE snap.captured_at = (SELECT MAX(captured_at) FROM snapshots)
    AND c.player IS NOT NULL
GROUP BY c.player, cat.name
HAVING COUNT(DISTINCT c.id) > 1
ORDER BY total_population DESC
```

#### Visualizations
- **Bar Chart**: Top players by total population
- **Scatter Plot**: Cards vs. Population by player
- **Table**: Player card inventory
- **Treemap**: Player distribution by sport

## Advanced Analytics

### 1. Time Series Analysis

#### Population Trends
```sql
-- Population changes over time
SELECT 
    DATE_TRUNC('month', s.captured_at) as month,
    cat.name as sport,
    COUNT(DISTINCT p.card_uid) as cards_tracked,
    AVG(p.count) as avg_population,
    SUM(p.count) as total_population
FROM snapshots s
JOIN populations p ON s.id = p.snapshot_id
JOIN cards c ON p.card_uid = c.card_uid
JOIN sets set ON c.set_id = set.id
JOIN years y ON set.year_id = y.id
JOIN categories cat ON y.category_id = cat.id
GROUP BY DATE_TRUNC('month', s.captured_at), cat.name
ORDER BY month, sport
```

### 2. Statistical Analysis

#### Grade Distribution Analysis
```sql
-- Statistical analysis of grades
SELECT 
    g.grade_label,
    COUNT(*) as sample_size,
    AVG(p.count) as mean_population,
    STDDEV(p.count) as std_dev_population,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY p.count) as median_population,
    MIN(p.count) as min_population,
    MAX(p.count) as max_population
FROM grades g
JOIN populations p ON g.id = p.grade_id
JOIN snapshots s ON p.snapshot_id = s.id
WHERE s.captured_at = (SELECT MAX(captured_at) FROM snapshots)
GROUP BY g.grade_label
ORDER BY mean_population DESC
```

### 3. Predictive Analytics

#### Population Forecasting
```sql
-- Simple trend analysis for forecasting
WITH population_trends AS (
    SELECT 
        c.card_uid,
        DATE_TRUNC('month', s.captured_at) as month,
        AVG(p.count) as avg_population,
        ROW_NUMBER() OVER (PARTITION BY c.card_uid ORDER BY DATE_TRUNC('month', s.captured_at)) as month_rank
    FROM populations p
    JOIN snapshots s ON p.snapshot_id = s.id
    JOIN cards c ON p.card_uid = c.card_uid
    GROUP BY c.card_uid, DATE_TRUNC('month', s.captured_at)
)
SELECT 
    card_uid,
    month,
    avg_population,
    LAG(avg_population) OVER (PARTITION BY card_uid ORDER BY month) as prev_month_population,
    (avg_population - LAG(avg_population) OVER (PARTITION BY card_uid ORDER BY month)) as population_change
FROM population_trends
WHERE month_rank > 1
ORDER BY card_uid, month
```

## Data Refresh Configuration

### 1. Scheduled Refresh

#### PowerBI Service Configuration
```bash
# In PowerBI Service:
# 1. Go to your workspace
# 2. Select your dataset
# 3. Click "Settings" > "Scheduled refresh"
# 4. Enable "Keep your data up to date"
# 5. Set refresh frequency (daily, weekly, etc.)
# 6. Set refresh time (e.g., 2:00 AM UTC)
```

#### Gateway Configuration
```bash
# If using on-premises data gateway:
# 1. Install PowerBI Gateway
# 2. Configure database connection
# 3. Set up refresh schedule
# 4. Monitor gateway status
```

### 2. Manual Refresh
```bash
# In PowerBI Desktop:
# 1. Click "Refresh" button
# 2. Or use Ctrl+Alt+F5

# In PowerBI Service:
# 1. Select dataset
# 2. Click "Refresh now"
```

## Performance Optimization

### 1. Data Import Optimization

#### Incremental Refresh
```sql
-- Use incremental refresh for large datasets
-- In PowerBI, set up incremental refresh policy:
-- RangeStart: 1 year ago
-- RangeEnd: Today
-- RefreshType: Incremental
```

#### Data Reduction
```sql
-- Import only necessary columns
-- Use filters to reduce data volume
-- Consider aggregating data at database level
```

### 2. Query Optimization

#### Efficient Queries
```sql
-- Use indexed columns in WHERE clauses
-- Avoid SELECT * - specify needed columns
-- Use appropriate JOIN types
-- Consider materialized views for complex queries
```

#### Caching Strategy
```bash
# In PowerBI Desktop:
# 1. Use "Import" mode for small datasets
# 2. Use "DirectQuery" for large datasets
# 3. Configure query folding where possible
```

## Troubleshooting

### 1. Connection Issues

#### Common Problems
```bash
# Connection timeout
# - Check firewall settings
# - Verify network connectivity
# - Check database server status

# Authentication failed
# - Verify username/password
# - Check user permissions
# - Ensure user has read access to tables
```

#### Solutions
```bash
# Test connection outside PowerBI
# Use psql or pgAdmin to verify connectivity
# Check database logs for connection attempts
# Verify ODBC driver installation
```

### 2. Performance Issues

#### Slow Queries
```bash
# Analyze query performance
# - Use EXPLAIN ANALYZE in PostgreSQL
# - Check query execution plans
# - Optimize database indexes

# Reduce data volume
# - Apply filters at database level
# - Use incremental refresh
# - Aggregate data before import
```

#### Memory Issues
```bash
# Reduce memory usage
# - Import fewer columns
# - Use data type optimization
# - Consider DirectQuery mode for large datasets
```

## Best Practices

### 1. Data Management
- **Regular data refresh** to maintain report accuracy
- **Data validation** to ensure quality
- **Backup strategy** for critical reports
- **Version control** for report changes

### 2. Performance
- **Optimize queries** at database level
- **Use appropriate refresh schedules**
- **Monitor resource usage**
- **Scale infrastructure as needed**

### 3. Security
- **Secure database connections**
- **Limit user permissions**
- **Audit access logs**
- **Regular security reviews**

### 4. Maintenance
- **Monitor report performance**
- **Update data models** as needed
- **Clean up unused reports**
- **Archive historical data**

This PowerBI connection guide provides comprehensive coverage of connecting to and analyzing data from the TAG Grading Scraper database.
