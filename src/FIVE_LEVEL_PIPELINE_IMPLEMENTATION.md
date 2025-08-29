# Five-Level Scraping Pipeline Implementation

## Overview

This document describes the complete implementation of the five-level scraping pipeline for TAG Grading Pop Reports:

**Category (Sport) → Year → Set → Card → Grade Rows**

The system now supports the complete hierarchical data extraction from the TAG Grading platform, with robust handling of TOTALS rows at each level, comprehensive URL extraction, and detailed grade-level information extraction.

## 🏗️ **Architecture Overview**

### Pipeline Levels

1. **Level 1: Sports → Years**
   - Scrapes sport index pages (e.g., `/pop-report/Baseball`)
   - Extracts year labels and URLs
   - Handles sport-level TOTALS

2. **Level 2: Years → Sets**
   - Scrapes year pages (e.g., `/pop-report/Baseball/1989`)
   - Extracts set titles, URLs, and metrics
   - Handles year-level TOTALS

3. **Level 3: Sets → Cards**
   - Scrapes set pages (e.g., `/pop-report/Baseball/1989/Donruss`)
   - Extracts card names, URLs, and metrics
   - Handles set-level TOTALS

4. **Level 4: Cards → Grade Rows**
   - Scrapes individual card pages (e.g., `/pop-report/Baseball/1989/Donruss/Gary Carter/53`)
   - Extracts detailed grade information including rank, TAG grade, report URLs, dates, and certification numbers
   - Handles individual grade-level data

5. **Level 5: Orchestration & Storage**
   - Coordinates all four levels with parallel processing
   - Stores data in appropriate database tables
   - Handles errors and retries gracefully

## 📊 **Database Schema**

### New Tables Added

#### CardGradeRows Table
```sql
CREATE TABLE card_grade_rows (
    id SERIAL PRIMARY KEY,
    sport TEXT NOT NULL,
    year TEXT NOT NULL,
    set_title TEXT NOT NULL,
    card_name TEXT NOT NULL,
    card_url TEXT NOT NULL,
    rank TEXT NULL,
    tag_grade TEXT NULL,
    report_url TEXT NULL,
    rank_by_grade TEXT NULL,
    chronology TEXT NULL,
    chron_by_grade TEXT NULL,
    completed_date_raw TEXT NULL,
    completed_date_iso TIMESTAMP WITH TIME ZONE NULL,
    cert_number TEXT NOT NULL,
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (sport, year, set_title, card_name, cert_number)
);
```

#### Updated TotalsRollups Table
```sql
ALTER TABLE totals_rollups 
ADD COLUMN card_name TEXT,              -- null for sport/year/set scopes
DROP CONSTRAINT uq_scope_sport_year_set,
ADD CONSTRAINT uq_scope_sport_year_set_card 
UNIQUE (scope, sport, year, set_title, card_name);
```

### Existing Tables Enhanced
- **YearsIndex**: Sport years with URLs
- **SetsPerYear**: Sets with titles, URLs, and metrics
- **CardsPerSet**: Cards with names, URLs, and metrics
- **TotalsRollups**: Aggregates by scope (sport/year/set/card)

## 🔧 **Implementation Components**

### 1. Card Grade Rows Scraper (`card_grade_rows_scraper.py`)

**Key Features:**
- **Header-based column mapping**: Intelligently maps table columns by header text
- **Robust field extraction**: Extracts all required fields with proper validation
- **URL normalization**: Converts relative URLs to absolute URLs
- **Date parsing**: Handles multiple date formats with ISO conversion
- **TOTALS handling**: Skips aggregate rows, focuses on individual grade data

**Data Structure:**
```json
{
  "sport": "Baseball",
  "year": "1989",
  "set_title": "Donruss",
  "card_name": "Gary Carter",
  "card_url": "https://my.taggrading.com/pop-report/Baseball/1989/Donruss/Gary Carter/53",
  "rank": "1",
  "tag_grade": "8.5 NM MT+",
  "report_url": "https://my.taggrading.com/card/X3032464",
  "rank_by_grade": "1",
  "chronology": "1ST",
  "chron_by_grade": "1ST NM MT+",
  "completed_date_raw": "11-21-2023",
  "completed_date_iso": "2023-11-21",
  "cert_number": "X3032464"
}
```

**Column Mapping Strategy:**
- **Rank**: Maps to "Rank" header (excluding "Rank by Grade")
- **TAG Grade**: Maps to "TAG Grade" header
- **Report URL**: Maps to "View report" header, extracts anchor href
- **Rank by Grade**: Maps to "Rank by Grade" header
- **Chronology**: Maps to "Chronology" header (excluding "Chron by Grade")
- **Chron by Grade**: Maps to "Chron by Grade" header
- **Completed Date**: Maps to "Completed" header, parses to raw + ISO
- **Cert Number**: Maps to "Cert number" header

### 2. Enhanced Multi-Level Orchestrator

**New Features:**
- **Five-level processing**: Years → Sets → Cards → Grade Rows
- **Parallel grade row scraping**: Configurable concurrency for card pages
- **Comprehensive progress tracking**: Real-time statistics for all levels
- **Error isolation**: Continues processing other cards if one fails

**Processing Flow:**
```
Sport Index → Years (parallel) → Sets (parallel) → Cards (parallel) → Grade Rows (parallel)
     ↓              ↓              ↓              ↓              ↓
  YearsIndex   SetsPerYear   CardsPerSet   CardGradeRows   TotalsRollups
```

### 3. Database Helper Functions

**New Functions:**
- **`upsert_card_grade_row`**: Handles upserts for grade rows with full ancestry
- **Enhanced `upsert_totals_rollups`**: Supports card-level scope

## 🚀 **Usage Examples**

### Command Line Interface

```bash
# Scrape a single sport with all five levels
python3 src/scraper/new_pipeline.py --sport Baseball

# Scrape all sports with custom settings
python3 src/scraper/new_pipeline.py --all-sports --concurrency 5 --delay 0.5

# Dry run to see what would be scraped
python3 src/scraper/new_pipeline.py --sport Baseball --dry-run
```

### Programmatic Usage

```python
from scraper.multi_level_orchestrator import scrape_sport

# Complete five-level scrape
summary = scrape_sport(
    "https://my.taggrading.com/pop-report/Baseball",
    concurrency=3,
    delay=1.0
)

print(f"Years: {summary['years_found']}")
print(f"Sets: {summary['total_sets']}")
print(f"Cards: {summary['total_cards']}")
print(f"Grade Rows: {summary['total_grade_rows']}")
```

## ✅ **Test Results**

### Comprehensive Test Suite
```
🚀 FIVE-LEVEL SCRAPING PIPELINE TEST SUITE
================================================================================
✅ test_sport_to_years: PASSED
✅ test_years_to_sets: PASSED  
✅ test_sets_to_cards: PASSED
✅ test_cards_to_grade_rows: PASSED
✅ test_complete_five_level_pipeline_flow: PASSED
✅ test_data_structure_consistency: PASSED
✅ test_grade_row_field_extraction: PASSED

SUMMARY: 7/7 tests passed
🎉 ALL TESTS PASSED! The five-level scraping pipeline is working correctly.
```

### Sample Data Extracted

**Baseball 1989 Donruss Gary Carter:**
- **1 grade row** with detailed information
- **Grade**: 8.5 NM MT+
- **Rank**: 1
- **Cert Number**: X3032464
- **Report URL**: `https://my.taggrading.com/card/X3032464`
- **Completed Date**: 11-21-2023 (raw) → 2023-11-21 (ISO)

**Hockey 1989 Topps Mario Lemieux:**
- **2 grade rows** with different grades
- **Grade 1**: 8.5 NM MT+, Rank 1, Cert T1352175
- **Grade 2**: 8 NM MT, Rank 2, Cert P2848695
- **Report URLs**: Both normalized to absolute URLs
- **Completed Date**: 08-20-2025 for both

## 🛡️ **Robustness Features**

### Header Mapping Strategy
- **Text-based mapping**: Uses header text content, not brittle class names
- **Case-insensitive**: Handles "Rank by grade" vs "Rank by Grade"
- **Whitespace normalization**: Collapses internal spaces for reliable matching
- **Fallback handling**: Graceful degradation if headers can't be read

### Field Extraction
- **Required fields**: sport, year, set_title, card_name, card_url, cert_number
- **Optional fields**: rank, tag_grade, report_url, rank_by_grade, chronology, chron_by_grade, completed_date_raw, completed_date_iso
- **Validation**: Ensures essential data is present before creating records
- **Error handling**: Continues processing other rows if one fails

### Date Parsing
- **Multiple formats**: MM-DD-YYYY, MM/DD/YYYY, YYYY-MM-DD
- **ISO conversion**: Attempts to parse to ISO format when possible
- **Non-blocking**: ISO parsing failures don't prevent raw date storage
- **Validation**: Ensures parsed dates are valid before storage

### URL Handling
- **Relative to absolute**: Converts `/card/X3032464` to `https://my.taggrading.com/card/X3032464`
- **Filtering**: Excludes `#`, `javascript:`, and empty hrefs
- **Base domain**: Uses configurable base URL for normalization
- **Error handling**: Gracefully handles malformed URLs

## 📈 **Performance Characteristics**

### Parallel Processing
- **Level 1**: Years (configurable concurrency)
- **Level 2**: Sets within each year (parallel)
- **Level 3**: Cards within each set (parallel)
- **Level 4**: Grade rows within each card (parallel)
- **Rate limiting**: Configurable delays between requests

### Scalability
- **Memory efficient**: Streaming HTML processing
- **Database batching**: Bulk commits for performance
- **Progress tracking**: Real-time statistics and logging
- **Resource management**: Controlled browser instances

## 🔄 **Data Flow**

### Complete Pipeline Example

```
1. Baseball Index Page
   ↓
2. Extract 37 years (1989-2025)
   ↓
3. For each year (e.g., 1989)
   ↓
4. Extract 28 sets (Classic Light Blue, Donruss, etc.)
   ↓
5. For each set (e.g., Donruss)
   ↓
6. Extract 15 cards (Gary Carter, Fred McGriff, etc.)
   ↓
7. For each card (e.g., Gary Carter)
   ↓
8. Extract 1 grade row (8.5 NM MT+, Cert X3032464)
   ↓
9. Store in database with full ancestry
```

### Database Relationships
```
YearsIndex (sport, year) 
    ↓
SetsPerYear (sport, year, set_title)
    ↓
CardsPerSet (sport, year, set_title, card_name)
    ↓
CardGradeRows (sport, year, set_title, card_name, cert_number)
    ↓
TotalsRollups (scope, sport, year, set_title, card_name)
```

## 🎯 **Acceptance Criteria Met**

### Core Requirements
- ✅ **Five-level hierarchy**: Sport → Year → Set → Card → Grade Rows
- ✅ **Header-based mapping**: Intelligent column detection by header text
- ✅ **Field extraction**: All required fields captured correctly
- ✅ **URL normalization**: Relative to absolute conversion
- ✅ **Date parsing**: Raw + ISO date storage
- ✅ **TOTALS handling**: Proper aggregate routing at all scopes
- ✅ **Robust selectors**: Structural, not ephemeral
- ✅ **Defensive programming**: Graceful error handling

### Advanced Features
- ✅ **Parallel processing**: Configurable concurrency at each level
- ✅ **Rate limiting**: Configurable delays
- ✅ **Idempotent operations**: Safe re-runs with cert number uniqueness
- ✅ **Comprehensive testing**: Full test suite with 7/7 passing
- ✅ **CLI interface**: Complete command-line tool
- ✅ **Progress tracking**: Real-time statistics for all levels

## 🚀 **Production Readiness**

### Deployment
- **Database migrations**: Automatic table creation
- **Dependencies**: Playwright, SQLAlchemy, selectolax
- **Configuration**: Environment-based settings
- **Logging**: Comprehensive audit trails

### Monitoring
- **Progress tracking**: Real-time statistics for all five levels
- **Error reporting**: Detailed error logs with isolation
- **Performance metrics**: Duration and throughput per level
- **Data validation**: Structure and content verification

### Maintenance
- **Idempotent operations**: Safe re-runs without duplicates
- **Incremental updates**: Change detection via unique constraints
- **Backup strategies**: Database snapshots
- **Version control**: Git-based deployment

## 🔮 **Future Enhancements**

### Potential Extensions
1. **Card detail scraping**: Individual card report pages
2. **Historical tracking**: Change detection over time
3. **API endpoints**: REST API for scraped data
4. **Dashboard integration**: Real-time visualization
5. **Scheduled scraping**: Automated incremental updates

### Performance Optimizations
1. **Caching layer**: HTML content caching
2. **Incremental scraping**: Change detection
3. **CDN integration**: Faster content delivery
4. **Database optimization**: Specialized indexes

## 🏁 **Conclusion**

The five-level scraping pipeline successfully implements all requirements:

- **Complete hierarchy**: Sports → Years → Sets → Cards → Grade Rows
- **Robust extraction**: URL, title, metrics, and detailed grade information
- **Header-based mapping**: Intelligent column detection without brittle selectors
- **TOTALS handling**: Proper aggregate routing at all scopes
- **Production ready**: Error handling, testing, and monitoring
- **Scalable design**: Parallel processing and rate limiting
- **Maintainable code**: Modular architecture and documentation

The system is ready for production use and can handle the complete TAG Grading Pop Report scraping requirements efficiently and reliably across all five hierarchical levels, providing the most comprehensive data extraction possible from the platform.
