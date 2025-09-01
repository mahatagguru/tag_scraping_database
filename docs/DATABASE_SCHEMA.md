# TAG Grading Scraper - Database Schema Documentation

## Overview

The TAG Grading Scraper uses a PostgreSQL database with a comprehensive schema designed to store hierarchical sports card data and population reports. The system captures data at multiple levels: Categories (Sports) → Years → Sets → Cards → Grade Rows.

## Database Tables

### Core Entity Tables

#### 1. categories
Stores the main sports categories (Baseball, Hockey, Basketball, Football, etc.)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier |
| name | TEXT | UNIQUE, NOT NULL | Sport name (e.g., "Baseball") |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

#### 2. years
Stores years for each sport category

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier |
| category_id | INTEGER | FOREIGN KEY → categories.id | Reference to sport category |
| year | INTEGER | NOT NULL | Year (e.g., 1989, 1990) |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Unique Constraint**: `(category_id, year)` - Each sport can only have one entry per year

#### 3. sets
Stores card sets for each year

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier |
| category_id | INTEGER | FOREIGN KEY → categories.id | Reference to sport category |
| year_id | INTEGER | FOREIGN KEY → years.id | Reference to year |
| set_name | TEXT | NOT NULL | Set name (e.g., "Topps") |
| num_sets | INTEGER | NULL | Number of sets available |
| total_items | INTEGER | NULL | Total items in set |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Unique Constraint**: `(year_id, set_name)` - Each year can only have one set with the same name

#### 4. cards
Stores individual cards within sets

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier |
| card_uid | TEXT | UNIQUE, NOT NULL | Unique card identifier |
| category_id | INTEGER | FOREIGN KEY → categories.id | Reference to sport category |
| year_id | INTEGER | FOREIGN KEY → years.id | Reference to year |
| set_id | INTEGER | FOREIGN KEY → sets.id | Reference to set |
| card_number | TEXT | NULL | Card number in set |
| player | TEXT | NULL | Player name |
| detail_url | TEXT | NULL | URL to card details |
| image_url | TEXT | NULL | URL to card image |
| subset_name | TEXT | NULL | Subset name if applicable |
| variation | TEXT | NULL | Card variation |
| cert_number | TEXT | NULL | Certification number |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Index**: `(category_id, year_id, set_id, player)` for efficient queries

#### 5. grades
Stores available grade labels

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier |
| grade_label | TEXT | UNIQUE, NOT NULL | Grade label (e.g., "10", "9.5", "9") |

#### 6. snapshots
Stores population report snapshots

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier |
| captured_at | TIMESTAMP | UNIQUE, NOT NULL | Snapshot timestamp |

#### 7. populations
Stores population counts for each card at each grade level

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| snapshot_id | INTEGER | PRIMARY KEY, FOREIGN KEY → snapshots.id | Reference to snapshot |
| card_uid | TEXT | PRIMARY KEY, FOREIGN KEY → cards.card_uid | Reference to card |
| grade_id | INTEGER | PRIMARY KEY, FOREIGN KEY → grades.id | Reference to grade |
| count | INTEGER | NOT NULL | Population count at this grade |
| total_graded | INTEGER | NULL | Total graded count for this card |

**Index**: `(card_uid, snapshot_id)` for efficient queries

### Multi-Level Scraping Tables

#### 8. years_index
Stores discovered years for each sport

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier |
| sport | TEXT | NOT NULL | Sport name |
| year | TEXT | NOT NULL | Year discovered |
| year_url | TEXT | NOT NULL | URL to year page |
| discovered_at | TIMESTAMP | NOT NULL | Discovery timestamp |

**Unique Constraint**: `(sport, year)` - Each sport can only have one entry per year

#### 9. sets_per_year
Stores sets discovered for each sport/year combination

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier |
| sport | TEXT | NOT NULL | Sport name |
| year | TEXT | NOT NULL | Year |
| year_url | TEXT | NOT NULL | URL to year page |
| set_title | TEXT | NOT NULL | Set title |
| set_urls | JSONB | NOT NULL | Array of set URLs |
| metrics | JSONB | NULL | Optional numeric metrics |
| discovered_at | TIMESTAMP | NOT NULL | Discovery timestamp |

**Unique Constraint**: `(sport, year, set_title)` - Each sport/year can only have one set with the same title

#### 10. cards_per_set
Stores cards discovered for each sport/year/set combination

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier |
| sport | TEXT | NOT NULL | Sport name |
| year | TEXT | NOT NULL | Year |
| set_title | TEXT | NOT NULL | Set title |
| set_url | TEXT | NOT NULL | Set URL |
| card_name | TEXT | NOT NULL | Card name |
| card_urls | JSONB | NOT NULL | Array of card URLs |
| metrics | JSONB | NULL | Optional numeric metrics |
| discovered_at | TIMESTAMP | NOT NULL | Discovery timestamp |

**Unique Constraint**: `(sport, year, set_title, card_name)` - Each sport/year/set can only have one card with the same name

#### 11. card_grade_rows
Stores individual grade rows for each card

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier |
| sport | TEXT | NOT NULL | Sport name |
| year | TEXT | NOT NULL | Year |
| set_title | TEXT | NOT NULL | Set title |
| card_name | TEXT | NOT NULL | Card name |
| card_url | TEXT | NOT NULL | Card URL |
| rank | TEXT | NULL | Rank by grade |
| tag_grade | TEXT | NULL | TAG grade |
| report_url | TEXT | NULL | Report URL |
| rank_by_grade | TEXT | NULL | Rank within grade |
| chronology | TEXT | NULL | Chronological rank |
| chron_by_grade | TEXT | NULL | Chronological rank within grade |
| completed_date_raw | TEXT | NULL | Raw completion date |
| completed_date_iso | TIMESTAMP | NULL | ISO completion date |
| cert_number | TEXT | NOT NULL | Certification number |
| discovered_at | TIMESTAMP | NOT NULL | Discovery timestamp |

**Unique Constraint**: `(sport, year, set_title, card_name, cert_number)` - Each card can only have one entry per certification number

### Rollup and Summary Tables

#### 12. totals_rollups
Stores aggregated metrics at different scopes

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier |
| scope | TEXT | NOT NULL | Scope level ('sport', 'year', 'set', 'card') |
| sport | TEXT | NOT NULL | Sport name |
| year | TEXT | NULL | Year (null for sport scope) |
| set_title | TEXT | NULL | Set title (null for sport/year scopes) |
| card_name | TEXT | NULL | Card name (null for sport/year/set scopes) |
| metrics | JSONB | NOT NULL | Aggregated metrics |
| computed_at | TIMESTAMP | NOT NULL | Computation timestamp |

**Unique Constraint**: `(scope, sport, year, set_title, card_name)` - Each scope combination can only have one entry

#### 13. category_totals
Stores totals for each category

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier |
| category_id | INTEGER | UNIQUE, FOREIGN KEY → categories.id | Reference to category |
| num_sets | INTEGER | NULL | Number of sets |
| total_items | INTEGER | NULL | Total items |
| total_graded | INTEGER | NULL | Total graded items |

#### 14. year_totals
Stores totals for each year

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier |
| year_id | INTEGER | UNIQUE, FOREIGN KEY → years.id | Reference to year |
| num_sets | INTEGER | NULL | Number of sets |
| total_items | INTEGER | NULL | Total items |
| total_graded | INTEGER | NULL | Total graded items |

#### 15. set_totals
Stores totals for each set

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier |
| set_id | INTEGER | UNIQUE, FOREIGN KEY → sets.id | Reference to set |
| num_cards | INTEGER | NULL | Number of cards |
| total_items | INTEGER | NULL | Total items |
| total_graded | INTEGER | NULL | Total graded items |

### Audit and Logging Tables

#### 16. audit_logs
Stores system audit logs

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BIGINT | PRIMARY KEY | Unique identifier |
| level | TEXT | NOT NULL | Log level (INFO, WARNING, ERROR) |
| context | JSONB | NULL | Contextual data |
| message | TEXT | NOT NULL | Log message |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |

**Index**: `created_at DESC` for efficient time-based queries

#### 17. population_reports
Stores historical population reports (partitioned by date)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BIGINT | NULL | Unique identifier |
| card_uid | TEXT | PRIMARY KEY | Card UID |
| grade_label | TEXT | PRIMARY KEY | Grade label |
| snapshot_date | TIMESTAMP | PRIMARY KEY | Snapshot date |
| population_count | INTEGER | NOT NULL | Population count |
| total_graded | INTEGER | NULL | Total graded count |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Update timestamp |

**Partitioning**: Table is partitioned by `snapshot_date` for efficient time-based queries

## Database Relationships

### Primary Relationships
- **categories** → **years** (1:many)
- **years** → **sets** (1:many)
- **sets** → **cards** (1:many)
- **cards** → **populations** (1:many)
- **grades** → **populations** (1:many)
- **snapshots** → **populations** (1:many)

### Multi-Level Scraping Relationships
- **years_index** → **sets_per_year** (1:many)
- **sets_per_year** → **cards_per_set** (1:many)
- **cards_per_set** → **card_grade_rows** (1:many)

### Rollup Relationships
- **categories** → **category_totals** (1:1)
- **years** → **year_totals** (1:1)
- **sets** → **set_totals** (1:1)

## Database Design Principles

### 1. Normalization
- Tables are normalized to reduce data redundancy
- Foreign keys maintain referential integrity
- Unique constraints prevent duplicate data

### 2. Performance Optimization
- Strategic indexing on frequently queried columns
- Partitioning on time-based tables (population_reports)
- JSONB columns for flexible metadata storage

### 3. Data Integrity
- NOT NULL constraints on required fields
- Unique constraints prevent duplicates
- Foreign key constraints maintain relationships
- Timestamps track data freshness

### 4. Scalability
- Partitioned tables for large datasets
- Efficient indexing strategy
- Support for concurrent operations

## Data Flow

1. **Discovery Phase**: Multi-level scraping discovers new years, sets, and cards
2. **Storage Phase**: Data is stored in the appropriate tables with upsert logic
3. **Aggregation Phase**: Totals and rollups are computed and stored
4. **Reporting Phase**: Data is queried for analysis and reporting

## Query Examples

### Basic Card Query
```sql
SELECT c.player, c.card_number, s.set_name, y.year, cat.name as sport
FROM cards c
JOIN sets s ON c.set_id = s.id
JOIN years y ON c.year_id = y.id
JOIN categories cat ON c.category_id = cat.id
WHERE cat.name = 'Baseball' AND y.year = 1989;
```

### Population Report Query
```sql
SELECT c.player, g.grade_label, p.count, p.total_graded
FROM populations p
JOIN cards c ON p.card_uid = c.card_uid
JOIN grades g ON p.grade_id = g.id
JOIN snapshots s ON p.snapshot_id = s.id
WHERE s.captured_at = (SELECT MAX(captured_at) FROM snapshots);
```

### Set Summary Query
```sql
SELECT s.set_name, y.year, cat.name as sport, st.num_cards, st.total_graded
FROM sets s
JOIN years y ON s.year_id = y.id
JOIN categories cat ON s.category_id = cat.id
LEFT JOIN set_totals st ON s.id = st.set_id
WHERE cat.name = 'Hockey' AND y.year = 1990;
```

This schema provides a robust foundation for storing, querying, and analyzing sports card population data while maintaining data integrity and performance.
