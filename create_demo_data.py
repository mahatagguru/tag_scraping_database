#!/usr/bin/env python3
"""
Create demo data for TAG Grading Scraper Reporting Website
This script populates the database with sample data for testing and demonstration
"""

import sys
import os
from datetime import datetime, timezone
import random

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from db import get_db_session_context
from models import (
    Category,
    Year,
    Set,
    Card,
    Grade,
    Snapshot,
    Population,
    AuditLog,
    CategoryTotal,
    YearTotal,
    SetTotal,
)


def create_demo_data():
    """Create comprehensive demo data for testing"""

    with get_db_session_context() as db:
        print("Creating demo data...")

        # Clear existing data (optional - comment out to keep existing data)
        print("Clearing existing data...")
        db.query(Population).delete()
        db.query(Card).delete()
        db.query(Set).delete()
        db.query(Year).delete()
        db.query(Category).delete()
        db.query(Grade).delete()
        db.query(Snapshot).delete()
        db.query(AuditLog).delete()
        db.query(CategoryTotal).delete()
        db.query(YearTotal).delete()
        db.query(SetTotal).delete()
        db.commit()

        # Create categories
        print("Creating categories...")
        categories_data = [
            {"name": "Baseball", "description": "Major League Baseball cards"},
            {"name": "Basketball", "description": "NBA and college basketball cards"},
            {"name": "Football", "description": "NFL and college football cards"},
            {"name": "Hockey", "description": "NHL and college hockey cards"},
        ]

        categories = []
        for cat_data in categories_data:
            category = Category(
                name=cat_data["name"],
                description=cat_data["description"],
                is_active=True,
                updated_at=datetime.now(timezone.utc),
            )
            db.add(category)
            categories.append(category)

        db.commit()

        # Create grades
        print("Creating grades...")
        grades_data = [
            {"label": "10", "value": 10},
            {"label": "9.5", "value": 9.5},
            {"label": "9", "value": 9},
            {"label": "8.5", "value": 8.5},
            {"label": "8", "value": 8},
            {"label": "7.5", "value": 7.5},
            {"label": "7", "value": 7},
            {"label": "6.5", "value": 6.5},
            {"label": "6", "value": 6},
            {"label": "5.5", "value": 5.5},
            {"label": "5", "value": 5},
        ]

        grades = []
        for grade_data in grades_data:
            grade = Grade(
                grade_label=grade_data["label"],
                grade_value=grade_data["value"],
                is_active=True,
            )
            db.add(grade)
            grades.append(grade)

        db.commit()

        # Create years for each category
        print("Creating years...")
        years = []
        for category in categories:
            for year in range(1980, 2024, 2):  # Every other year
                year_obj = Year(
                    category_id=category.id,
                    year=year,
                    is_active=True,
                    updated_at=datetime.now(timezone.utc),
                )
                db.add(year_obj)
                years.append(year_obj)

        db.commit()

        # Create sets for each year
        print("Creating sets...")
        set_names = [
            "Topps",
            "Upper Deck",
            "Fleer",
            "Donruss",
            "Score",
            "Pinnacle",
            "Bowman",
            "Stadium Club",
            "Leaf",
            "Pacific",
            "Skybox",
            "Playoff",
        ]

        sets = []
        for year in years:
            num_sets = random.randint(2, 6)
            selected_sets = random.sample(set_names, num_sets)

            for set_name in selected_sets:
                set_obj = Set(
                    category_id=year.category_id,
                    year_id=year.id,
                    set_name=set_name,
                    set_description=f"{set_name} {year.year} collection",
                    num_sets=random.randint(1, 3),
                    total_items=random.randint(100, 500),
                    is_active=True,
                    updated_at=datetime.now(timezone.utc),
                )
                db.add(set_obj)
                sets.append(set_obj)

        db.commit()

        # Create cards for each set
        print("Creating cards...")
        players = [
            "Michael Jordan",
            "LeBron James",
            "Kobe Bryant",
            "Magic Johnson",
            "Larry Bird",
            "Shaquille O'Neal",
            "Tim Duncan",
            "Kareem Abdul-Jabbar",
            "Wilt Chamberlain",
            "Bill Russell",
            "Kareem Abdul-Jabbar",
            "Oscar Robertson",
            "Jerry West",
            "Elgin Baylor",
            "Bob Cousy",
            "John Havlicek",
            "Tom Brady",
            "Peyton Manning",
            "Joe Montana",
            "Jerry Rice",
            "Barry Sanders",
            "Walter Payton",
            "Emmitt Smith",
            "Jim Brown",
            "Wayne Gretzky",
            "Mario Lemieux",
            "Bobby Orr",
            "Gordie Howe",
            "Sidney Crosby",
            "Alexander Ovechkin",
            "Connor McDavid",
            "Patrick Kane",
            "Babe Ruth",
            "Hank Aaron",
            "Willie Mays",
            "Ted Williams",
            "Mickey Mantle",
            "Lou Gehrig",
            "Ty Cobb",
            "Honus Wagner",
            "Mike Trout",
            "Mookie Betts",
            "Ronald Acuña Jr.",
            "Juan Soto",
            "Fernando Tatis Jr.",
            "Vladimir Guerrero Jr.",
            "Shohei Ohtani",
            "Aaron Judge",
        ]

        cards = []
        for set_obj in sets:
            num_cards = random.randint(20, 100)
            selected_players = random.sample(players, min(num_cards, len(players)))

            for i, player in enumerate(selected_players):
                card = Card(
                    card_uid=f"{set_obj.category.name}_{set_obj.year.year}_{set_obj.set_name}_{i+1}",
                    category_id=set_obj.category_id,
                    year_id=set_obj.year_id,
                    set_id=set_obj.id,
                    card_number=str(i + 1),
                    player=player,
                    detail_url=f"https://example.com/card/{set_obj.category.name}_{set_obj.year.year}_{set_obj.set_name}_{i+1}",
                    image_url=f"https://via.placeholder.com/300x400/cccccc/666666?text={player.replace(' ', '+')}",
                    subset_name=random.choice(
                        [None, "Rookie", "All-Star", "Championship", "Legends"]
                    ),
                    variation=random.choice(
                        [None, "Refractor", "Chrome", "Gold", "Silver"]
                    ),
                    cert_number=f"CERT{random.randint(100000, 999999)}",
                    is_active=True,
                    updated_at=datetime.now(timezone.utc),
                )
                db.add(card)
                cards.append(card)

        db.commit()

        # Create snapshot
        print("Creating snapshot...")
        snapshot = Snapshot(
            captured_at=datetime.now(timezone.utc),
            source="demo_data_script",
            is_complete=True,
        )
        db.add(snapshot)
        db.commit()

        # Create population data
        print("Creating population data...")
        for card in cards:
            # Each card gets population data for 3-7 random grades
            selected_grades = random.sample(grades, random.randint(3, 7))

            for grade in selected_grades:
                population = Population(
                    snapshot_id=snapshot.id,
                    card_uid=card.card_uid,
                    grade_id=grade.id,
                    count=random.randint(1, 100),
                    total_graded=random.randint(50, 500),
                )
                db.add(population)

        db.commit()

        # Create totals
        print("Creating totals...")

        # Category totals
        for category in categories:
            category_cards = [c for c in cards if c.category_id == category.id]
            category_sets = [s for s in sets if s.category_id == category.id]
            category_populations = [
                p
                for p in db.query(Population)
                .join(Card)
                .filter(Card.category_id == category.id)
                .all()
            ]

            category_total = CategoryTotal(
                category_id=category.id,
                num_sets=len(category_sets),
                total_items=sum(
                    card.card_number
                    for card in category_cards
                    if card.card_number and card.card_number.isdigit()
                ),
                total_graded=sum(p.count for p in category_populations),
            )
            db.add(category_total)

        # Year totals
        for year in years:
            year_cards = [c for c in cards if c.year_id == year.id]
            year_sets = [s for s in sets if s.year_id == year.id]
            year_populations = [
                p
                for p in db.query(Population)
                .join(Card)
                .filter(Card.year_id == year.id)
                .all()
            ]

            year_total = YearTotal(
                year_id=year.id,
                num_sets=len(year_sets),
                total_items=sum(
                    int(card.card_number)
                    for card in year_cards
                    if card.card_number and card.card_number.isdigit()
                ),
                total_graded=sum(p.count for p in year_populations),
            )
            db.add(year_total)

        # Set totals
        for set_obj in sets:
            set_cards = [c for c in cards if c.set_id == set_obj.id]
            set_populations = [
                p
                for p in db.query(Population)
                .join(Card)
                .filter(Card.set_id == set_obj.id)
                .all()
            ]

            set_total = SetTotal(
                set_id=set_obj.id,
                num_cards=len(set_cards),
                total_items=sum(
                    int(card.card_number)
                    for card in set_cards
                    if card.card_number and card.card_number.isdigit()
                ),
                total_graded=sum(p.count for p in set_populations),
            )
            db.add(set_total)

        db.commit()

        # Create audit logs
        print("Creating audit logs...")
        audit_messages = [
            "Demo data creation started",
            "Categories created successfully",
            "Years created successfully",
            "Sets created successfully",
            "Cards created successfully",
            "Population data created successfully",
            "Totals calculated successfully",
            "Demo data creation completed",
        ]

        for i, message in enumerate(audit_messages):
            audit_log = AuditLog(
                level="INFO",
                component="demo_data_script",
                operation="CREATE_DEMO_DATA",
                status="SUCCESS",
                message=message,
                execution_time_ms=random.randint(100, 1000),
                created_at=datetime.now(timezone.utc),
            )
            db.add(audit_log)

        db.commit()

        print("Demo data creation completed successfully!")
        print(f"Created:")
        print(f"  - {len(categories)} categories")
        print(f"  - {len(years)} years")
        print(f"  - {len(sets)} sets")
        print(f"  - {len(cards)} cards")
        print(f"  - {len(grades)} grades")
        print(f"  - {len(db.query(Population).all())} population records")
        print(f"  - {len(db.query(AuditLog).all())} audit log entries")


if __name__ == "__main__":
    create_demo_data()
