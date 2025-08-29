from dotenv import load_dotenv
load_dotenv()

from db import engine, Base  # ensures engine and Base are loaded
import models  # ensures all models are registered
from sqlalchemy import text
import datetime

def migrate_add_card_fields():
    with engine.connect() as conn:
        # Add columns if they do not exist
        conn.execute(text('ALTER TABLE cards ADD COLUMN IF NOT EXISTS image_url TEXT;'))
        conn.execute(text('ALTER TABLE cards ADD COLUMN IF NOT EXISTS subset_name TEXT;'))
        conn.execute(text('ALTER TABLE cards ADD COLUMN IF NOT EXISTS variation TEXT;'))
        conn.execute(text('ALTER TABLE cards ADD COLUMN IF NOT EXISTS cert_number TEXT;'))
        conn.commit()

def migrate_add_updated_at():
    with engine.connect() as conn:
        for table in ['categories', 'years', 'sets', 'cards']:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT now();"))
        conn.commit()

def migrate_create_population_reports():
    with engine.connect() as conn:
        # Create the partitioned table if it doesn't exist
        conn.execute(text('''
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
        '''))
        # Create a default partition for the current month if it doesn't exist
        now = datetime.datetime.now(datetime.timezone.utc)
        first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = (first_of_month + datetime.timedelta(days=32)).replace(day=1)
        partition_name = f"population_reports_{first_of_month.strftime('%Y_%m')}"
        conn.execute(text(f'''
        CREATE TABLE IF NOT EXISTS {partition_name} PARTITION OF population_reports
        FOR VALUES FROM ('{first_of_month.isoformat()}') TO ('{next_month.isoformat()}');
        '''))
        conn.commit()

def migrate_create_population_report_partitions(months_ahead=12):
    with engine.connect() as conn:
        now = datetime.datetime.now(datetime.timezone.utc)
        for i in range(months_ahead):
            first_of_month = (now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=32*i)).replace(day=1)
            next_month = (first_of_month + datetime.timedelta(days=32)).replace(day=1)
            partition_name = f"population_reports_{first_of_month.strftime('%Y_%m')}"
            conn.execute(text(f'''
            CREATE TABLE IF NOT EXISTS {partition_name} PARTITION OF population_reports
            FOR VALUES FROM ('{first_of_month.isoformat()}') TO ('{next_month.isoformat()}');
            '''))
        conn.commit()

if __name__ == "__main__":
    print("Creating all tables...")
    Base.metadata.create_all(engine)
    print("Done.")
    print("Running migration for new card fields...")
    migrate_add_card_fields()
    print("Migration for card fields complete.")
    print("Running migration for updated_at columns...")
    migrate_add_updated_at()
    print("Migration for updated_at columns complete.")
    print("Running migration for population_reports table...")
    migrate_create_population_reports()
    print("Migration for population_reports table complete.")
    print("Creating partitions for the next 12 months...")
    migrate_create_population_report_partitions(12)
    print("Population report partitions created.")
