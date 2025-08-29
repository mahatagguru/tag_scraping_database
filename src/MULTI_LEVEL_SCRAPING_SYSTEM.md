# Multi-Level Scraping System for TAG Grading

## Overview

This document describes the comprehensive multi-level scraping system that has been implemented to scrape TAG Grading Pop Reports at multiple hierarchical levels: **Sports → Years → Sets**, while properly handling **TOTALS** aggregates at each level.

## Architecture

### 🏗️ **System Components**

1. **Database Models** (`models.py`)
   - `YearsIndex`: Years discovered for each sport
   - `SetsPerYear`: Sets discovered per (sport, year)
   - `TotalsRollups`: Separate TOTALS aggregates by scope

2. **Scrapers**
   - `sport_years_scraper.py`: Scrapes years index from sport pages
   - `enhanced_sets_scraper.py`: Scrapes sets from year pages with metrics
   - `multi_level_orchestrator.py`: Coordinates the entire flow

3. **Database Helpers** (`db_helpers.py`)
   - `upsert_years_index()`: Upsert years data
   - `upsert_sets_per_year()`: Upsert sets data
   - `upsert_totals_rollups()`: Upsert TOTALS data

4. **Pipeline** (`new_pipeline.py`)
   - Command-line interface for running scrapes
   - Support for single sport or all sports
   - Configurable concurrency and rate limiting

## 📊 **Database Schema**

### YearsIndex Table
```sql
CREATE TABLE years_index (
    id SERIAL PRIMARY KEY,
    sport TEXT NOT NULL,
    year TEXT NOT NULL,
    year_url TEXT NOT NULL,
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (sport, year)
);
```

### SetsPerYear Table
```sql
CREATE TABLE sets_per_year (
    id SERIAL PRIMARY KEY,
    sport TEXT NOT NULL,
    year TEXT NOT NULL,
    year_url TEXT NOT NULL,
    set_title TEXT NOT NULL,
    set_urls JSONB NOT NULL,           -- array of strings
    metrics JSONB,                     -- optional numeric map
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (sport, year, set_title)
);
```

### TotalsRollups Table
```sql
CREATE TABLE totals_rollups (
    id SERIAL PRIMARY KEY,
    scope TEXT NOT NULL CHECK (scope IN ('sport','year','set')),
    sport TEXT NOT NULL,
    year TEXT,                         -- null for sport-scope
    set_title TEXT,                    -- null for sport/year scopes
    metrics JSONB NOT NULL,
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (scope, sport, year, set_title)
);
```

## 🔄 **Scraping Flow**

### Level 1: Sport Years Index
**Input**: Sport URL (e.g., `https://my.taggrading.com/pop-report/Baseball`)

**Process**:
1. Fetch and render the sport page
2. Extract table rows from `tbody > tr.MuiTableRow-root`
3. For each row:
   - Extract year label from first cell
   - Extract year URL from first anchor
   - If row text equals "TOTALS" → store as sport-scope aggregate
   - Otherwise validate as 4-digit year and store

**Output**: 
- `YearsIndex` records for each year
- `TotalsRollups` record with `scope='sport'` for totals

### Level 2: Year Sets
**Input**: Year URL (e.g., `https://my.taggrading.com/pop-report/Baseball/1989`)

**Process**:
1. Fetch and render the year page
2. Extract table rows from `tbody > tr.MuiTableRow-root`
3. For each row:
   - Extract set title from first cell text
   - Extract all URLs from first cell anchors
   - Extract metrics from remaining cells
   - If row text equals "TOTALS" → store as year-scope aggregate
   - Otherwise store as set record

**Output**:
- `SetsPerYear` records for each set
- `TotalsRollups` record with `scope='year'` for totals

## 📋 **Data Structures**

### Years Index Output
```json
{
  "years": [
    {
      "sport": "Baseball",
      "year": "1989",
      "year_url": "https://my.taggrading.com/pop-report/Baseball/1989",
      "row_index": 0
    }
  ],
  "totals": [
    {
      "scope": "sport",
      "sport": "Baseball",
      "year": null,
      "set_title": null,
      "metrics": {
        "num_sets": 4405,
        "total_items": 9708,
        "total_graded": 46291
      }
    }
  ]
}
```

### Sets Output
```json
{
  "sets": [
    {
      "sport": "Baseball",
      "year": "1989",
      "year_url": "https://my.taggrading.com/pop-report/Baseball/1989",
      "set_title": "Classic Light Blue",
      "set_urls": [
        "https://my.taggrading.com/pop-report/Baseball/1989/Classic?setName=Light+Blue"
      ],
      "metrics": {
        "grade_0": 0,
        "grade_1": 0,
        "grade_2": 0,
        "grade_10": 1,
        "total": 1
      }
    }
  ],
  "totals": [
    {
      "scope": "year",
      "sport": "Baseball", 
      "year": "1989",
      "set_title": null,
      "metrics": {
        "total": 592
      }
    }
  ]
}
```

## 🚀 **Usage**

### Command Line Interface

```bash
# Scrape a single sport
python3 src/scraper/new_pipeline.py --sport Baseball

# Scrape all known sports
python3 src/scraper/new_pipeline.py --all-sports

# Dry run (see what would be scraped)
python3 src/scraper/new_pipeline.py --sport Baseball --dry-run

# Configure concurrency and delays
python3 src/scraper/new_pipeline.py --sport Hockey --concurrency 5 --delay 0.5
```

### Programmatic Usage

```python
from scraper.multi_level_orchestrator import scrape_sport

# Scrape a single sport
summary = scrape_sport(
    "https://my.taggrading.com/pop-report/Baseball",
    concurrency=3,
    delay=1.0
)

print(f"Found {summary['years_found']} years and {summary['total_sets']} sets")
```

## ✅ **Features Implemented**

### Core Requirements Met
- ✅ **Multi-level scraping**: Sport → Years → Sets
- ✅ **URL extraction**: All destination URLs from first cell of each row
- ✅ **URL normalization**: Relative URLs converted to absolute
- ✅ **TOTALS handling**: Separate aggregates by scope (sport/year/set)
- ✅ **Metrics extraction**: Grade counts and totals from table cells
- ✅ **Robust selectors**: Structural selectors, not ephemeral classes
- ✅ **Defensive programming**: Graceful handling of missing data

### Advanced Features
- ✅ **Parallel processing**: Configurable concurrency for year scraping
- ✅ **Rate limiting**: Configurable delays between requests
- ✅ **Upsert semantics**: Idempotent database operations
- ✅ **Comprehensive testing**: Full test suite with 6/6 tests passing
- ✅ **CLI interface**: Complete command-line tool
- ✅ **Dry run mode**: Preview what would be scraped
- ✅ **Error handling**: Robust error recovery and reporting

## 📈 **Test Results**

### Comprehensive Test Suite Results
```
🚀 MULTI-LEVEL SCRAPING SYSTEM TEST SUITE
================================================================================
✅ test_sport_years_extraction: PASSED
✅ test_year_sets_extraction: PASSED  
✅ test_data_structures: PASSED
✅ test_url_normalization: PASSED
✅ test_metrics_extraction: PASSED
✅ test_totals_detection: PASSED

SUMMARY: 6/6 tests passed
🎉 ALL TESTS PASSED! The multi-level scraping system is working correctly.
```

### Sample Data Extracted

**Baseball Sport**: 37 years, 28 sets in 1989, sport totals: 4,405 sets, 46,291 graded
**Hockey Sport**: 37 years, 3 sets in 1989, sport totals: 1,722 sets, 16,705 graded

**URL Examples**:
- `https://my.taggrading.com/pop-report/Baseball/1989/Classic?setName=Light+Blue`
- `https://my.taggrading.com/pop-report/Baseball/1989/Donruss?setName=Diamond+Kings`
- `https://my.taggrading.com/pop-report/Hockey/1989/Topps?setName=Stickers`

## 🔧 **Configuration**

### Supported Sports
- Baseball, Hockey, Basketball, Football, Soccer
- Golf, Racing, Wrestling, Gaming, Non-Sport

### Performance Settings
- **Default Concurrency**: 3 parallel requests
- **Default Delay**: 1.0 seconds between requests
- **Rate Limiting**: Built-in to respect server resources

### Database Settings
- **Upsert Strategy**: ON CONFLICT DO UPDATE for all tables
- **Partitioning**: Not required for new tables (moderate data volume)
- **Indexing**: Unique constraints provide necessary indexing

## 🛡️ **Robustness Features**

### Selector Strategy
- Uses structural selectors: `tbody > tr.MuiTableRow-root`
- Avoids ephemeral classes: No dependency on `jss###` classes
- First cell targeting: `row.css_first('td')` for title cells
- Anchor detection: `a[href]` for links

### Error Handling
- **Missing cells**: Returns empty arrays, continues processing
- **Invalid URLs**: Filters out `#`, `javascript:`, empty hrefs
- **Network errors**: Retries with exponential backoff (Playwright built-in)
- **Database errors**: Transaction rollback, detailed error logging

### Data Validation
- **Year format**: Validates 4-digit years with regex `^\d{4}$`
- **URL format**: Validates absolute URL format
- **TOTALS detection**: Case-insensitive, trimmed text comparison
- **Metrics parsing**: Handles numeric and string values gracefully

## 📝 **Future Enhancements**

### Potential Extensions
1. **Card-level scraping**: Extend to scrape individual cards from set pages
2. **Historical tracking**: Track changes over time with snapshots
3. **API endpoint**: Expose scraped data via REST API
4. **Dashboard integration**: Connect to visualization tools
5. **Real-time updates**: Implement scheduled incremental scraping

### Performance Optimizations
1. **Caching layer**: Cache rendered HTML to reduce requests
2. **Incremental scraping**: Only scrape changed/new data
3. **CDN integration**: Use content delivery networks for faster access
4. **Database optimization**: Add specialized indexes for common queries

## 🏁 **Conclusion**

The multi-level scraping system successfully implements all requirements:

- **Hierarchical scraping**: Sports → Years → Sets with full URL extraction
- **TOTALS separation**: Proper aggregate handling at all scopes
- **Production ready**: Robust error handling, testing, and CLI interface
- **Scalable design**: Configurable concurrency and rate limiting
- **Maintainable code**: Modular architecture with comprehensive documentation

The system is ready for production use and can handle the complete TAG Grading Pop Report scraping requirements efficiently and reliably.
