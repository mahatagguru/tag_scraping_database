# Database Schema Documentation

This document describes the PostgreSQL schema for the TAG Pop Report system as of the latest update.

---

## Table: categories
- **id** (PK, integer)
- **name** (text, unique, not null)
- **updated_at** (timestamptz, not null, auto-updated)

---

## Table: years
- **id** (PK, integer)
- **category_id** (FK → categories.id, not null)
- **year** (integer, not null)
- **updated_at** (timestamptz, not null, auto-updated)
- **UNIQUE (category_id, year)**

---

## Table: sets
- **id** (PK, integer)
- **category_id** (FK → categories.id, not null)
- **year_id** (FK → years.id, not null)
- **set_name** (text, not null)
- **num_sets** (integer, nullable)
- **total_items** (integer, nullable)
- **updated_at** (timestamptz, not null, auto-updated)
- **UNIQUE (year_id, set_name)**

---

## Table: cards
- **id** (PK, integer)
- **card_uid** (text, unique, not null)
- **category_id** (FK → categories.id, not null)
- **year_id** (FK → years.id, not null)
- **set_id** (FK → sets.id, not null)
- **card_number** (text, nullable)
- **player** (text, nullable)
- **detail_url** (text, nullable)
- **image_url** (text, nullable)
- **subset_name** (text, nullable)
- **variation** (text, nullable)
- **cert_number** (text, nullable)
- **updated_at** (timestamptz, not null, auto-updated)
- **INDEX (category_id, year_id, set_id, player)**

---

## Table: grades
- **id** (PK, integer)
- **grade_label** (text, unique, not null)

---

## Table: snapshots
- **id** (PK, integer)
- **captured_at** (timestamptz, unique, not null)

---

## Table: populations
- **snapshot_id** (FK → snapshots.id, PK)
- **card_uid** (text, FK → cards.card_uid, PK)
- **grade_id** (FK → grades.id, PK)
- **count** (integer, not null)
- **total_graded** (integer, nullable)
- **INDEX (card_uid, snapshot_id)**

---

## Table: population_reports (partitioned, BI/reporting)
- **id** (bigserial, not unique, not PK)
- **card_uid** (text, PK, not FK)
- **grade_label** (text, PK)
- **snapshot_date** (timestamptz, PK, partition key)
- **population_count** (integer, not null)
- **total_graded** (integer, nullable)
- **created_at** (timestamptz, not null, default now())
- **updated_at** (timestamptz, not null, auto-updated)
- **INDEX (card_uid, grade_label, snapshot_date)**
- **Partitioned by RANGE (snapshot_date), with monthly partitions**
- **No foreign key constraints on card_uid (allows rollup rows like 'ALL')**

---

## Table: audit_logs
- **id** (PK, bigint)
- **level** (text, not null)
- **context** (jsonb, nullable)
- **message** (text, not null)
- **created_at** (timestamptz, not null, default now())
- **INDEX (created_at DESC)**

---

## Table: category_totals, year_totals, set_totals
- **category_totals**: category_id (FK, unique), num_sets, total_items, total_graded
- **year_totals**: year_id (FK, unique), num_sets, total_items, total_graded
- **set_totals**: set_id (FK, unique), num_cards, total_items, total_graded

---

## Relationships
- **categories** → **years**, **sets**, **cards**
- **years** → **sets**, **cards**
- **sets** → **cards**
- **cards** → **populations**
- **grades** → **populations**
- **snapshots** → **populations**
- **population_reports**: no FKs, allows rollup/aggregate rows for BI

---

## Notes
- All main tables have `updated_at` for audit and incremental scraping.
- `population_reports` is optimized for BI/trend analysis, with partitioning and rollup support.
- Upserts use natural keys (e.g., name, year, set_name, card_uid, grade_label, snapshot_date).
- Indexes and unique constraints are in place for efficient querying and deduplication.
