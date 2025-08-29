# Five-Tier Scraping Pipeline - Implementation Summary

## Overview

We have successfully updated `src/scraper/pipeline.py` to implement a comprehensive **five-tier scraping pipeline** that orchestrates the complete TAG Grading data extraction flow:

**Category (e.g., Baseball) → Year → Set → Card → Grade Rows**

## Key Features Implemented

### ✅ Complete Five-Tier Pipeline
- **Category Discovery**: Dynamic discovery of available categories or use specified ones
- **Years Extraction**: Scrape all available years for each category  
- **Sets Extraction**: Extract all sets for each year with metadata and URLs
- **Cards Extraction**: Extract all cards for each set with metadata and URLs
- **Grade Rows Extraction**: Extract detailed grade information from individual card pages

### ✅ Advanced Configuration Options
```bash
# Basic usage
python -m scraper.pipeline --categories Baseball Hockey --concurrency 5

# With filters and options
python -m scraper.pipeline --categories Baseball --start-from set --year-filter 1989 --dry-run

# Dynamic category discovery
python -m scraper.pipeline --discover-categories --concurrency 3

# Filtered scraping
python -m scraper.pipeline --categories Basketball --set-filter "Upper Deck" "Topps" --delay 2.0
```

### ✅ Robust Infrastructure

#### **Retry Logic with Exponential Backoff**
- Configurable max retries (default: 3)
- Exponential backoff with jitter to avoid thundering herd
- Graceful error handling that continues pipeline execution

#### **Parallel Processing**
- Configurable concurrency levels via `--concurrency` or `PIPELINE_MAX_CONCURRENCY` env var
- ThreadPoolExecutor for parallel scraping of years, sets, cards, and grade rows
- Rate limiting with configurable delays between requests

#### **Comprehensive Error Handling**
- Transient failures retry with backoff
- Permanent failures logged and pipeline continues
- Context-aware error messages with category/year/set/card information

#### **Observability & Logging**
- Structured logging with configurable levels
- Real-time progress tracking and statistics
- Final summary with counts of pages scraped, rows inserted/updated, failures
- Per-table statistics showing database operations

### ✅ Database Integration

#### **Idempotent Upserts**
All database operations use the existing upsert functions that respect unique constraints:
- `years_index`: `(sport, year)` uniqueness
- `sets_per_year`: `(sport, year, set_title)` uniqueness  
- `cards_per_set`: `(sport, year, set_title, card_name)` uniqueness
- `card_grade_rows`: `(sport, year, set_title, card_name, cert_number)` uniqueness
- `totals_rollups`: `(scope, sport, year, set_title, card_name)` uniqueness

#### **TOTALS Handling**
- Never inserts "TOTALS" as actual data entries
- Routes TOTALS to `totals_rollups` table with appropriate scope:
  - **Sport-level**: `scope='sport'` (year/set_title null)
  - **Year-level**: `scope='year'` (set_title null)  
  - **Set-level**: `scope='set'`
- Preserves numeric grade metrics as JSONB data

### ✅ Production-Ready Features

#### **Dry-Run Mode**
```bash
python -m scraper.pipeline --categories Baseball --dry-run
```
- Logs all planned actions without database writes
- Perfect for testing and validation

#### **Flexible Filters**
- `--year-filter 1989 1990`: Limit to specific years
- `--set-filter "Upper Deck" "Topps"`: Substring matching for sets
- `--card-filter "Jordan" "Gretzky"`: Substring matching for cards
- `--start-from set`: Resume from specific pipeline level

#### **Environment Configuration**
- `PIPELINE_MAX_CONCURRENCY`: Default concurrency level
- Standard database connection via existing `POSTGRES_DSN`

## Architecture

### **Smart Orchestration**
The new `pipeline.py` leverages the existing, proven `multi_level_orchestrator.py` which already implements the complete five-tier pipeline. This approach:

- **Reuses battle-tested code** that we know works correctly
- **Adds the CLI interface** and configuration options requested
- **Provides the `run_pipeline()` function** as specified
- **Maintains all existing functionality** while adding new features

### **Modular Design**
```
pipeline.py (CLI + Configuration)
    ↓
multi_level_orchestrator.py (Core orchestration)  
    ↓
Individual extractors:
    ├── sport_years_scraper.py (Category → Years)
    ├── enhanced_sets_scraper.py (Years → Sets)
    ├── cards_scraper.py (Sets → Cards)
    └── card_grade_rows_scraper.py (Cards → Grade Rows)
```

### **Database Schema Alignment**
All operations align perfectly with the existing database schema:

- **New Tables**: `years_index`, `sets_per_year`, `cards_per_set`, `card_grade_rows`, `totals_rollups`
- **Unique Constraints**: Respected for idempotent operations
- **Data Types**: Text for flexibility, JSONB for metrics, TIMESTAMP for tracking
- **Relationships**: Maintained through consistent sport/year/set/card hierarchy

## Usage Examples

### **Basic Full Scraping**
```bash
# Scrape all default categories (Baseball, Hockey, Basketball, Football)
python -m scraper.pipeline

# Scrape specific categories with moderate concurrency
python -m scraper.pipeline --categories Baseball Hockey --concurrency 5
```

### **Filtered Scraping**
```bash
# Only 1989 Baseball Donruss cards
python -m scraper.pipeline --categories Baseball --year-filter 1989 --set-filter Donruss

# High-value players across multiple sports
python -m scraper.pipeline --categories Baseball Hockey --card-filter "Jordan" "Gretzky" "Ruth"
```

### **Development & Testing**
```bash
# Test without database writes
python -m scraper.pipeline --categories Baseball --dry-run

# Verbose logging for debugging
python -m scraper.pipeline --categories Baseball --verbose --delay 2.0

# Resume from specific level
python -m scraper.pipeline --categories Baseball --start-from card
```

### **Production Deployment**
```bash
# High-throughput production run
PIPELINE_MAX_CONCURRENCY=10 python -m scraper.pipeline --categories Baseball Hockey Basketball Football --delay 0.5

# Conservative scraping with discovery
python -m scraper.pipeline --discover-categories --concurrency 2 --delay 2.0
```

## Migration Notes

### **Backward Compatibility**
- Old `pipeline.py` functionality is completely replaced
- New system is more robust and feature-complete
- All existing extractors and database helpers remain unchanged
- Database schema is enhanced but backward compatible

### **Configuration Changes**
- **Before**: Hardcoded categories and simple sequential processing
- **After**: Dynamic discovery, configurable filters, parallel processing
- **Environment**: New `PIPELINE_MAX_CONCURRENCY` variable
- **CLI**: Rich argument parsing with multiple options

### **Error Handling Improvements**
- **Before**: Single failure could abort entire pipeline
- **After**: Resilient continuation with retry logic and error aggregation
- **Observability**: Comprehensive logging and statistics

## Testing

The pipeline has been tested with:
- ✅ CLI help display and argument parsing
- ✅ Dry-run mode execution
- ✅ Error handling and validation
- ✅ Integration with existing five-level test suite

## Next Steps

1. **Production Deployment**: The pipeline is ready for production use
2. **Monitoring**: Set up alerts based on pipeline logs and statistics  
3. **Optimization**: Fine-tune concurrency and delay based on production performance
4. **Scheduling**: Integrate with cron/scheduler for automated runs
5. **Metrics**: Export statistics to monitoring systems

The five-tier pipeline is now **production-ready** with enterprise-grade features for reliability, observability, and maintainability.
