import datetime
import logging
from dotenv import load_dotenv
from sqlalchemy import text

from db import Base, engine  # ensures engine and Base are loaded

load_dotenv()

# Check if PostgreSQL is available
try:
    from sqlalchemy.dialects.postgresql import JSONB  # noqa: F401

    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_add_card_fields() -> None:
    """Add new card fields if they don't exist."""
    with engine.connect() as conn:
        try:
            # Check if we're using SQLite
            if "sqlite" in str(engine.url):
                # For SQLite, check if columns exist first
                existing_columns = [
                    row[1]
                    for row in conn.execute(text("PRAGMA table_info(cards)")).fetchall()
                ]

                if "image_url" not in existing_columns:
                    conn.execute(text("ALTER TABLE cards ADD COLUMN image_url TEXT;"))
                if "subset_name" not in existing_columns:
                    conn.execute(text("ALTER TABLE cards ADD COLUMN subset_name TEXT;"))
                if "variation" not in existing_columns:
                    conn.execute(text("ALTER TABLE cards ADD COLUMN variation TEXT;"))
                if "cert_number" not in existing_columns:
                    conn.execute(text("ALTER TABLE cards ADD COLUMN cert_number TEXT;"))
            else:
                # For PostgreSQL, use IF NOT EXISTS
                conn.execute(
                    text("ALTER TABLE cards ADD COLUMN IF NOT EXISTS image_url TEXT;")
                )
                conn.execute(
                    text("ALTER TABLE cards ADD COLUMN IF NOT EXISTS subset_name TEXT;")
                )
                conn.execute(
                    text("ALTER TABLE cards ADD COLUMN IF NOT EXISTS variation TEXT;")
                )
                conn.execute(
                    text("ALTER TABLE cards ADD COLUMN IF NOT EXISTS cert_number TEXT;")
                )

            conn.commit()
            logger.info("Successfully added new card fields")
        except Exception as e:
            logger.error(f"Error adding card fields: {e}")
            conn.rollback()
            raise


def migrate_add_updated_at() -> None:
    """Add updated_at columns to core tables if they don't exist."""
    with engine.connect() as conn:
        try:
            for table in ["categories", "years", "sets", "cards"]:
                if "sqlite" in str(engine.url):
                    # For SQLite, check if columns exist first
                    existing_columns = [
                        row[1]
                        for row in conn.execute(
                            text(f"PRAGMA table_info({table})")
                        ).fetchall()
                    ]
                    if "updated_at" not in existing_columns:
                        conn.execute(
                            text(
                                f"ALTER TABLE {table} ADD COLUMN updated_at TEXT DEFAULT (datetime('now'));"
                            )
                        )
                else:
                    # For PostgreSQL, use IF NOT EXISTS
                    conn.execute(
                        text(
                            f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS "
                            f"updated_at TIMESTAMP WITH TIME ZONE DEFAULT now();"
                        )
                    )

            conn.commit()
            logger.info("Successfully added updated_at columns")
        except Exception as e:
            logger.error(f"Error adding updated_at columns: {e}")
            conn.rollback()
            raise


def migrate_create_population_reports() -> None:
    """Create the population_reports table if it doesn't exist."""
    with engine.connect() as conn:
        try:
            if "sqlite" in str(engine.url):
                # For SQLite, create a simple table without partitioning
                conn.execute(
                    text(
                        """
                CREATE TABLE IF NOT EXISTS population_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    card_uid TEXT NOT NULL,
                    grade_label TEXT NOT NULL,
                    snapshot_date TEXT NOT NULL,
                    population_count INTEGER NOT NULL,
                    total_graded INTEGER,
                    created_at TEXT DEFAULT (datetime('now')) NOT NULL,
                    updated_at TEXT DEFAULT (datetime('now')) NOT NULL,
                    UNIQUE(card_uid, grade_label, snapshot_date)
                );
                """
                    )
                )
                logger.info("Successfully created SQLite population_reports table")
            else:
                # For PostgreSQL, create the partitioned table
                conn.execute(
                    text(
                        """
                CREATE TABLE IF NOT EXISTS population_reports (
                    id BIGSERIAL,
                    card_uid TEXT NOT NULL,
                    grade_label TEXT NOT NULL,
                    snapshot_date TIMESTAMP WITH TIME ZONE NOT NULL,
                    population_count INTEGER NOT NULL,
                    total_graded INTEGER,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
                    PRIMARY KEY (card_uid, grade_label, snapshot_date)
                ) PARTITION BY RANGE (snapshot_date);
                """
                    )
                )

                # Create a default partition for the current month if it doesn't exist
                now = datetime.datetime.now(datetime.timezone.utc)
                first_of_month = now.replace(
                    day=1, hour=0, minute=0, second=0, microsecond=0
                )
                next_month = (first_of_month + datetime.timedelta(days=32)).replace(
                    day=1
                )
                partition_name = (
                    f"population_reports_{first_of_month.strftime('%Y_%m')}"
                )

                conn.execute(
                    text(
                        f"""
                    CREATE TABLE IF NOT EXISTS {partition_name} PARTITION OF population_reports
                    FOR VALUES FROM ('{first_of_month.isoformat()}') TO ('{next_month.isoformat()}');
                    """
                    )
                )
                logger.info(
                    "Successfully created PostgreSQL population_reports table and partition"
                )

            conn.commit()
        except Exception as e:
            logger.error(f"Error creating population_reports table: {e}")
            conn.rollback()
            raise


def migrate_create_population_report_partitions(months_ahead: int = 12) -> None:
    """Create population report partitions for future months."""
    with engine.connect() as conn:
        try:
            # SQLite doesn't support partitioning, so skip
            if "sqlite" in str(engine.url):
                logger.info("Skipping partition creation for SQLite (not supported)")
                return

            now = datetime.datetime.now(datetime.timezone.utc)
            for i in range(months_ahead):
                first_of_month = (
                    now.replace(day=1, hour=0, minute=0, microsecond=0)
                    + datetime.timedelta(days=32 * i)
                ).replace(day=1)
                next_month = (first_of_month + datetime.timedelta(days=32)).replace(
                    day=1
                )
                partition_name = (
                    f"population_reports_{first_of_month.strftime('%Y_%m')}"
                )

                conn.execute(
                    text(
                        f"""
                    CREATE TABLE IF NOT EXISTS {partition_name} PARTITION OF population_reports
                    FOR VALUES FROM ('{first_of_month.isoformat()}') TO ('{next_month.isoformat()}');
                    """
                    )
                )

            conn.commit()
            logger.info(
                f"Successfully created {months_ahead} population report partitions"
            )
        except Exception as e:
            logger.error(f"Error creating population report partitions: {e}")
            conn.rollback()
            raise


def migrate_enhance_audit_logs() -> None:
    """Enhance the audit_logs table with new fields for comprehensive error handling."""
    with engine.connect() as conn:
        try:
            # Add new columns to audit_logs table
            new_columns = [
                "component TEXT",
                "operation TEXT",
                "status TEXT",
                "error_code TEXT",
                "error_message TEXT",
                "stack_trace TEXT",
                "user_agent TEXT",
                "ip_address TEXT",
                "execution_time_ms INTEGER",
            ]

            for column_def in new_columns:
                column_name = column_def.split()[0]
                try:
                    if "sqlite" in str(engine.url):
                        # For SQLite, check if column exists first
                        existing_columns = [
                            row[1]
                            for row in conn.execute(
                                text("PRAGMA table_info(audit_logs)")
                            ).fetchall()
                        ]
                        if column_name not in existing_columns:
                            conn.execute(
                                text(f"ALTER TABLE audit_logs ADD COLUMN {column_def};")
                            )
                            logger.info(f"Added column: {column_name}")
                    else:
                        # For PostgreSQL, use IF NOT EXISTS
                        conn.execute(
                            text(
                                f"ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS {column_def};"
                            )
                        )
                        logger.info(f"Added column: {column_name}")
                except Exception as e:
                    logger.warning(f"Column {column_name} may already exist: {e}")

            # Add check constraints (PostgreSQL only)
            if "sqlite" not in str(engine.url):
                constraints = [
                    (
                        "chk_audit_level",
                        "level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')",
                    ),
                    (
                        "chk_audit_status",
                        "status IS NULL OR status IN ('SUCCESS', 'FAILURE', 'PARTIAL')",
                    ),
                    (
                        "chk_audit_execution_time",
                        "execution_time_ms IS NULL OR execution_time_ms >= 0",
                    ),
                ]

                for constraint_name, constraint_def in constraints:
                    try:
                        conn.execute(
                            text(
                                f"ALTER TABLE audit_logs ADD CONSTRAINT {constraint_name} CHECK ({constraint_def});"
                            )
                        )
                        logger.info(f"Added constraint: {constraint_name}")
                    except Exception as e:
                        logger.warning(
                            f"Constraint {constraint_name} may already exist: {e}"
                        )
            else:
                logger.info("Skipping CHECK constraints for SQLite (not supported)")

            # Add indexes
            indexes = [
                ("ix_audit_logs_level", "level"),
                ("ix_audit_logs_component", "component"),
                ("ix_audit_logs_status", "status"),
                ("ix_audit_logs_error_code", "error_code"),
                ("ix_audit_logs_operation", "operation"),
            ]

            for index_name, columns in indexes:
                try:
                    conn.execute(
                        text(
                            f"CREATE INDEX IF NOT EXISTS {index_name} ON audit_logs ({columns});"
                        )
                    )
                    logger.info(f"Added index: {index_name}")
                except Exception as e:
                    logger.warning(f"Index {index_name} may already exist: {e}")

            conn.commit()
            logger.info("Successfully enhanced audit_logs table")
        except Exception as e:
            logger.error(f"Error enhancing audit_logs table: {e}")
            conn.rollback()
            raise


def migrate_add_active_flags() -> None:
    """Add is_active flags to core tables for soft deletion support."""
    with engine.connect() as conn:
        try:
            tables_with_active = ["categories", "years", "sets", "cards", "grades"]

            for table in tables_with_active:
                if "sqlite" in str(engine.url):
                    # For SQLite, check if columns exist first
                    existing_columns = [
                        row[1]
                        for row in conn.execute(
                            text(f"PRAGMA table_info({table})")
                        ).fetchall()
                    ]
                    if "is_active" not in existing_columns:
                        conn.execute(
                            text(
                                f"ALTER TABLE {table} ADD COLUMN is_active INTEGER DEFAULT 1 NOT NULL;"
                            )
                        )
                else:
                    # For PostgreSQL, use IF NOT EXISTS
                    conn.execute(
                        text(
                            f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE NOT NULL;"
                        )
                    )

                logger.info(f"Added is_active column to {table}")

            # Add indexes for is_active columns
            for table in tables_with_active:
                try:
                    conn.execute(
                        text(
                            f"CREATE INDEX IF NOT EXISTS ix_{table}_active ON {table} (is_active);"
                        )
                    )
                    logger.info(f"Added active index to {table}")
                except Exception as e:
                    logger.warning(f"Active index may already exist for {table}: {e}")

            conn.commit()
            logger.info("Successfully added is_active flags and indexes")
        except Exception as e:
            logger.error(f"Error adding is_active flags: {e}")
            conn.rollback()
            raise


def migrate_add_description_fields():
    """Add description fields to categories and sets tables."""
    with engine.connect() as conn:
        try:
            if "sqlite" in str(engine.url):
                # For SQLite, check if columns exist first
                existing_columns = [
                    row[1]
                    for row in conn.execute(
                        text("PRAGMA table_info(categories)")
                    ).fetchall()
                ]
                if "description" not in existing_columns:
                    conn.execute(
                        text("ALTER TABLE categories ADD COLUMN description TEXT;")
                    )

                existing_columns = [
                    row[1]
                    for row in conn.execute(text("PRAGMA table_info(sets)")).fetchall()
                ]
                if "set_description" not in existing_columns:
                    conn.execute(
                        text("ALTER TABLE sets ADD COLUMN set_description TEXT;")
                    )
            else:
                # For PostgreSQL, use IF NOT EXISTS
                conn.execute(
                    text(
                        "ALTER TABLE categories ADD COLUMN IF NOT EXISTS description TEXT;"
                    )
                )
                conn.execute(
                    text(
                        "ALTER TABLE sets ADD COLUMN IF NOT EXISTS set_description TEXT;"
                    )
                )

            conn.commit()
            logger.info("Successfully added description fields")
        except Exception as e:
            logger.error(f"Error adding description fields: {e}")
            conn.rollback()
            raise


def migrate_add_grade_value():
    """Add grade_value field to grades table for numeric sorting."""
    with engine.connect() as conn:
        try:
            if "sqlite" in str(engine.url):
                # For SQLite, check if columns exist first
                existing_columns = [
                    row[1]
                    for row in conn.execute(
                        text("PRAGMA table_info(grades)")
                    ).fetchall()
                ]
                if "grade_value" not in existing_columns:
                    conn.execute(
                        text("ALTER TABLE grades ADD COLUMN grade_value INTEGER;")
                    )
            else:
                # For PostgreSQL, use IF NOT EXISTS
                conn.execute(
                    text(
                        "ALTER TABLE grades ADD COLUMN IF NOT EXISTS grade_value SMALLINT;"
                    )
                )

            # Add index for grade_value
            try:
                conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_grades_value ON grades (grade_value);"
                    )
                )
                logger.info("Added grade_value index")
            except Exception as e:
                logger.warning(f"grade_value index may already exist: {e}")

            conn.commit()
            logger.info("Successfully added grade_value field")
        except Exception as e:
            logger.error(f"Error adding grade_value field: {e}")
            conn.rollback()
            raise


def migrate_add_snapshot_fields():
    """Add additional fields to snapshots table."""
    with engine.connect() as conn:
        try:
            if "sqlite" in str(engine.url):
                # For SQLite, check if columns exist first
                existing_columns = [
                    row[1]
                    for row in conn.execute(
                        text("PRAGMA table_info(snapshots)")
                    ).fetchall()
                ]
                if "source" not in existing_columns:
                    conn.execute(text("ALTER TABLE snapshots ADD COLUMN source TEXT;"))
                if "is_complete" not in existing_columns:
                    conn.execute(
                        text(
                            "ALTER TABLE snapshots ADD COLUMN is_complete INTEGER DEFAULT 0;"
                        )
                    )
            else:
                # For PostgreSQL, use IF NOT EXISTS
                conn.execute(
                    text("ALTER TABLE snapshots ADD COLUMN IF NOT EXISTS source TEXT;")
                )
                conn.execute(
                    text(
                        "ALTER TABLE snapshots ADD COLUMN IF NOT EXISTS is_complete BOOLEAN DEFAULT FALSE NOT NULL;"
                    )
                )

            # Add indexes
            try:
                conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_snapshots_source ON snapshots (source);"
                    )
                )
                conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_snapshots_complete ON snapshots (is_complete);"
                    )
                )
                logger.info("Added snapshot indexes")
            except Exception as e:
                logger.warning(f"Snapshot indexes may already exist: {e}")

            conn.commit()
            logger.info("Successfully added snapshot fields")
        except Exception as e:
            logger.error(f"Error adding snapshot fields: {e}")
            conn.rollback()
            raise


def migrate_add_totals_timestamps():
    """Add last_updated timestamps to totals tables."""
    with engine.connect() as conn:
        try:
            totals_tables = ["category_totals", "year_totals", "set_totals"]

            for table in totals_tables:
                if "sqlite" in str(engine.url):
                    # For SQLite, check if columns exist first
                    existing_columns = [
                        row[1]
                        for row in conn.execute(
                            text(f"PRAGMA table_info({table})")
                        ).fetchall()
                    ]
                    if "last_updated" not in existing_columns:
                        conn.execute(
                            text(
                                f'ALTER TABLE {table} ADD COLUMN last_updated TEXT DEFAULT (datetime("now"));'
                            )
                        )
                else:
                    # For PostgreSQL, use IF NOT EXISTS
                    conn.execute(
                        text(
                            f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS last_updated TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL;"
                        )
                    )

                logger.info(f"Added last_updated to {table}")

            conn.commit()
            logger.info("Successfully added totals timestamps")
        except Exception as e:
            logger.error(f"Error adding totals timestamps: {e}")
            conn.rollback()
            raise


def migrate_add_check_constraints():
    """Add check constraints for data validation."""
    with engine.connect() as conn:
        try:
            # Year range constraints
            try:
                conn.execute(
                    text(
                        "ALTER TABLE years ADD CONSTRAINT chk_year_range CHECK (year >= 1800 AND year <= 2100);"
                    )
                )
                logger.info("Added year range constraint")
            except Exception as e:
                logger.warning(f"Year range constraint may already exist: {e}")

            # Positive number constraints
            constraints = [
                ("sets", "chk_sets_num_sets", "num_sets IS NULL OR num_sets >= 0"),
                (
                    "sets",
                    "chk_sets_total_items",
                    "total_items IS NULL OR total_items >= 0",
                ),
                ("populations", "chk_populations_count", "count >= 0"),
                (
                    "populations",
                    "chk_populations_total_graded",
                    "total_graded IS NULL OR total_graded >= count",
                ),
                (
                    "category_totals",
                    "chk_category_totals_num_sets",
                    "num_sets IS NULL OR num_sets >= 0",
                ),
                (
                    "category_totals",
                    "chk_category_totals_total_items",
                    "total_items IS NULL OR total_items >= 0",
                ),
                (
                    "category_totals",
                    "chk_category_totals_total_graded",
                    "total_graded IS NULL OR total_graded >= 0",
                ),
                (
                    "year_totals",
                    "chk_year_totals_num_sets",
                    "num_sets IS NULL OR num_sets >= 0",
                ),
                (
                    "year_totals",
                    "chk_year_totals_total_items",
                    "total_items IS NULL OR total_items >= 0",
                ),
                (
                    "year_totals",
                    "chk_year_totals_total_graded",
                    "total_graded IS NULL OR total_graded >= 0",
                ),
                (
                    "set_totals",
                    "chk_set_totals_num_cards",
                    "num_cards IS NULL OR num_cards >= 0",
                ),
                (
                    "set_totals",
                    "chk_set_totals_total_items",
                    "total_items IS NULL OR total_items >= 0",
                ),
                (
                    "set_totals",
                    "chk_set_totals_total_graded",
                    "total_graded IS NULL OR total_graded >= 0",
                ),
            ]

            for table, constraint_name, constraint_def in constraints:
                try:
                    conn.execute(
                        text(
                            f"ALTER TABLE {table} ADD CONSTRAINT {constraint_name} CHECK ({constraint_def});"
                        )
                    )
                    logger.info(f"Added constraint: {constraint_name}")
                except Exception as e:
                    logger.warning(
                        f"Constraint {constraint_name} may already exist: {e}"
                    )

            conn.commit()
            logger.info("Successfully added check constraints")
        except Exception as e:
            logger.error(f"Error adding check constraints: {e}")
            conn.rollback()
            raise


def migrate_add_cascade_deletes():
    """Update foreign key constraints to include CASCADE DELETE."""
    with engine.connect() as conn:
        try:
            # Note: PostgreSQL doesn't support ALTER TABLE to change foreign key constraints
            # This would require recreating the tables, which is complex
            # For now, we'll just log that this needs manual attention
            logger.info("CASCADE DELETE constraints require manual table recreation")
            logger.info("Consider using the new models.py for fresh table creation")

        except Exception as e:
            logger.error(f"Error with cascade delete migration: {e}")
            raise


def migrate_add_multi_level_indexes():
    """Add indexes for multi-level scraping tables."""
    with engine.connect() as conn:
        try:
            # Add indexes for multi-level tables if they exist
            multi_level_tables = [
                ("years_index", ["sport", "year"], "ix_years_index_sport_year"),
                ("years_index", ["is_active"], "ix_years_index_active"),
                ("years_index", ["discovered_at"], "ix_years_index_discovered"),
                ("sets_per_year", ["sport", "year"], "ix_sets_per_year_sport_year"),
                ("sets_per_year", ["set_title"], "ix_sets_per_year_set_title"),
                ("sets_per_year", ["is_active"], "ix_sets_per_year_active"),
                ("sets_per_year", ["discovered_at"], "ix_sets_per_year_discovered"),
                (
                    "cards_per_set",
                    ["sport", "year", "set_title"],
                    "ix_cards_per_set_sport_year_set",
                ),
                ("cards_per_set", ["card_name"], "ix_cards_per_set_card_name"),
                ("cards_per_set", ["is_active"], "ix_cards_per_set_active"),
                ("cards_per_set", ["discovered_at"], "ix_cards_per_set_discovered"),
                (
                    "card_grade_rows",
                    ["sport", "year", "set_title", "card_name"],
                    "ix_card_grade_rows_sport_year_set_card",
                ),
                ("card_grade_rows", ["cert_number"], "ix_card_grade_rows_cert_number"),
                ("card_grade_rows", ["tag_grade"], "ix_card_grade_rows_tag_grade"),
                ("card_grade_rows", ["is_active"], "ix_card_grade_rows_active"),
                ("card_grade_rows", ["discovered_at"], "ix_card_grade_rows_discovered"),
            ]

            for table, columns, index_name in multi_level_tables:
                try:
                    # Check if table exists first
                    if "sqlite" in str(engine.url):
                        # For SQLite, use PRAGMA to check table existence
                        result = conn.execute(
                            text(
                                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';"
                            )
                        )
                        table_exists = result.fetchone() is not None
                    else:
                        # For PostgreSQL, use information_schema
                        result = conn.execute(
                            text(
                                f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}');"
                            )
                        )
                        table_exists = result.scalar()

                    if table_exists:
                        conn.execute(
                            text(
                                f'CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({
                                    ", ".join(columns)});'
                            )
                        )
                        logger.info(f"Added index: {index_name}")
                    else:
                        logger.info(
                            f"Table {table} does not exist, skipping index creation"
                        )
                except Exception as e:
                    logger.warning(f"Index {index_name} may already exist: {e}")

            conn.commit()
            logger.info("Successfully added multi-level indexes")
        except Exception as e:
            logger.error(f"Error adding multi-level indexes: {e}")
            conn.rollback()
            raise


def migrate_postgresql_optimizations():
    """Add PostgreSQL-specific optimizations if available."""
    if not POSTGRESQL_AVAILABLE or "sqlite" in str(engine.url):
        logger.info(
            "Skipping PostgreSQL optimizations (SQLite or PostgreSQL not available)"
        )
        return

    with engine.connect() as conn:
        try:
            logger.info("Adding PostgreSQL-specific optimizations...")

            # Add GIN indexes for JSONB columns for better performance
            jsonb_indexes = [
                ("audit_logs", "context", "ix_audit_logs_context_gin"),
                ("sets_per_year", "set_urls", "ix_sets_per_year_urls_gin"),
                ("sets_per_year", "metrics", "ix_sets_per_year_metrics_gin"),
                ("cards_per_set", "card_urls", "ix_cards_per_set_urls_gin"),
                ("cards_per_set", "metrics", "ix_cards_per_set_metrics_gin"),
                ("totals_rollups", "metrics", "ix_totals_rollups_metrics_gin"),
            ]

            for table, column, index_name in jsonb_indexes:
                try:
                    conn.execute(
                        text(
                            f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} USING GIN ({column});"
                        )
                    )
                    logger.info(f"Added GIN index: {index_name}")
                except Exception as e:
                    logger.warning(f"GIN index {index_name} may already exist: {e}")

            # Add BRIN indexes for timestamp columns (good for time-series data)
            brin_indexes = [
                ("audit_logs", "created_at", "ix_audit_logs_created_at_brin"),
                ("populations", "snapshot_id", "ix_populations_snapshot_brin"),
                (
                    "population_reports",
                    "snapshot_date",
                    "ix_population_reports_date_brin",
                ),
            ]

            for table, column, index_name in brin_indexes:
                try:
                    conn.execute(
                        text(
                            f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} USING BRIN ({column});"
                        )
                    )
                    logger.info(f"Added BRIN index: {index_name}")
                except Exception as e:
                    logger.warning(f"BRIN index {index_name} may already exist: {e}")

            # Add partial indexes for active records
            partial_indexes = [
                ("categories", "ix_categories_active_partial", "is_active = true"),
                ("years", "ix_years_active_partial", "is_active = true"),
                ("sets", "ix_sets_active_partial", "is_active = true"),
                ("cards", "ix_cards_active_partial", "is_active = true"),
            ]

            for table, index_name, condition in partial_indexes:
                try:
                    conn.execute(
                        text(
                            f'CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({
                                index_name.split("_")[1]}) WHERE {condition};'
                        )
                    )
                    logger.info(f"Added partial index: {index_name}")
                except Exception as e:
                    logger.warning(f"Partial index {index_name} may already exist: {e}")

            # Add expression indexes for common queries
            expression_indexes = [
                ("cards", "ix_cards_player_lower", "LOWER(player)"),
                (
                    "cards",
                    "ix_cards_cert_number_clean",
                    "REGEXP_REPLACE(cert_number, '[^0-9]', '', 'g')",
                ),
                ("audit_logs", "ix_audit_logs_level_status", "level, status"),
            ]

            for table, index_name, expression in expression_indexes:
                try:
                    conn.execute(
                        text(
                            f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({expression});"
                        )
                    )
                    logger.info(f"Added expression index: {index_name}")
                except Exception as e:
                    logger.warning(
                        f"Expression index {index_name} may already exist: {e}"
                    )

            conn.commit()
            logger.info("Successfully added PostgreSQL optimizations")

        except Exception as e:
            logger.error(f"Error adding PostgreSQL optimizations: {e}")
            conn.rollback()
            raise


def run_all_migrations():
    """Run all database migrations in the correct order."""
    logger.info("Starting database migrations...")

    try:
        # Core field migrations
        logger.info("Running core field migrations...")
        migrate_add_card_fields()
        migrate_add_updated_at()
        migrate_add_description_fields()
        migrate_add_grade_value()
        migrate_add_snapshot_fields()
        migrate_add_totals_timestamps()

        # Constraint and validation migrations
        logger.info("Running constraint migrations...")
        migrate_add_check_constraints()

        # Active flag migrations
        logger.info("Running active flag migrations...")
        migrate_add_active_flags()

        # Index migrations
        logger.info("Running index migrations...")
        migrate_add_multi_level_indexes()

        # Audit log enhancements
        logger.info("Running audit log enhancements...")
        migrate_enhance_audit_logs()

        # Population reports
        logger.info("Running population report migrations...")
        migrate_create_population_reports()
        migrate_create_population_report_partitions(12)

        # Note about cascade deletes
        migrate_add_cascade_deletes()

        # PostgreSQL-specific optimizations
        migrate_postgresql_optimizations()

        logger.info("All migrations completed successfully!")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


if __name__ == "__main__":
    print("Creating all tables...")
    Base.metadata.create_all(engine)
    print("Done.")

    print("Running comprehensive migrations...")
    run_all_migrations()
    print("All migrations complete.")
