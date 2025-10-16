"""
Database Setup Script for TAG Grading Scraper
Run this script to create the basic database structure
"""

from pathlib import Path
import sqlite3


def create_basic_tables() -> None:
    """Create basic database tables for the TAG Grading Scraper."""

    # Get the database path
    db_path = Path(__file__).parent.parent / "data" / "tag_scraper_local.db"
    db_path.parent.mkdir(exist_ok=True)

    print(f"🔧 Setting up database at: {db_path}")

    # Connect to database (creates it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Create basic tables
        print("📋 Creating basic tables...")

        # Categories table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        print("✅ Created categories table")

        # Years table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS years (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                year INTEGER NOT NULL,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        """
        )
        print("✅ Created years table")

        # Sets table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                year_id INTEGER,
                set_name TEXT NOT NULL,
                set_title TEXT,
                num_cards INTEGER,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories (id),
                FOREIGN KEY (year_id) REFERENCES years (id)
            )
        """
        )
        print("✅ Created sets table")

        # Cards table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_uid TEXT UNIQUE,
                category_id INTEGER,
                year_id INTEGER,
                set_id INTEGER,
                card_name TEXT NOT NULL,
                player_name TEXT,
                card_number TEXT,
                cert_number TEXT,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories (id),
                FOREIGN KEY (year_id) REFERENCES years (id),
                FOREIGN KEY (set_id) REFERENCES sets (id)
            )
        """
        )
        print("✅ Created cards table")

        # Grades table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grade_label TEXT NOT NULL UNIQUE,
                grade_value REAL NOT NULL,
                description TEXT,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        print("✅ Created grades table")

        # Audit logs table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                component TEXT,
                operation TEXT,
                status TEXT,
                error_code TEXT,
                error_message TEXT,
                context TEXT,
                message TEXT,
                stack_trace TEXT,
                user_agent TEXT,
                ip_address TEXT,
                execution_time_ms INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        print("✅ Created audit_logs table")

        # Insert some basic data
        print("📝 Inserting basic data...")

        # Insert default categories
        cursor.execute(
            """
            INSERT OR IGNORE INTO categories (name, description) VALUES 
            ('baseball', 'Baseball cards and memorabilia'),
            ('football', 'Football cards and memorabilia'),
            ('basketball', 'Basketball cards and memorabilia'),
            ('hockey', 'Hockey cards and memorabilia'),
            ('soccer', 'Soccer cards and memorabilia')
        """
        )

        # Insert default grades
        cursor.execute(
            """
            INSERT OR IGNORE INTO grades (grade_label, grade_value, description) VALUES 
            ('10.0', 10.0, 'Perfect'),
            ('9.5', 9.5, 'Gem Mint'),
            ('9.0', 9.0, 'Mint'),
            ('8.5', 8.5, 'Near Mint-Mint'),
            ('8.0', 8.0, 'Near Mint'),
            ('7.5', 7.5, 'Near Mint-Mint'),
            ('7.0', 7.0, 'Near Mint')
        """
        )

        print("✅ Inserted basic data")

        # Commit changes
        conn.commit()
        print("\n🎉 Database setup complete!")
        print(f"📊 Database location: {db_path}")
        print("💡 You can now run the schema validation: python src/validate_schema.py")

    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    create_basic_tables()
