from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, UniqueConstraint, Index, TIMESTAMP, JSON, BigInteger, func
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from db import Base

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True, nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    years = relationship('Year', back_populates='category')
    sets = relationship('Set', back_populates='category')
    cards = relationship('Card', back_populates='category')

class Year(Base):
    __tablename__ = 'years'
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    year = Column(Integer, nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    __table_args__ = (UniqueConstraint('category_id', 'year', name='uq_category_year'),)
    category = relationship('Category', back_populates='years')
    sets = relationship('Set', back_populates='year')
    cards = relationship('Card', back_populates='year')

class Set(Base):
    __tablename__ = 'sets'
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    year_id = Column(Integer, ForeignKey('years.id'), nullable=False)
    set_name = Column(Text, nullable=False)
    num_sets = Column(Integer, nullable=True)
    total_items = Column(Integer, nullable=True)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    __table_args__ = (UniqueConstraint('year_id', 'set_name', name='uq_year_setname'),)
    category = relationship('Category', back_populates='sets')
    year = relationship('Year', back_populates='sets')
    cards = relationship('Card', back_populates='set')

class Card(Base):
    __tablename__ = 'cards'
    id = Column(Integer, primary_key=True)
    card_uid = Column(Text, unique=True, nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    year_id = Column(Integer, ForeignKey('years.id'), nullable=False)
    set_id = Column(Integer, ForeignKey('sets.id'), nullable=False)
    card_number = Column(Text, nullable=True)
    player = Column(Text, nullable=True)
    detail_url = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    subset_name = Column(Text, nullable=True)
    variation = Column(Text, nullable=True)
    cert_number = Column(Text, nullable=True)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    __table_args__ = (
        Index('ix_cards_category_year_set_player', 'category_id', 'year_id', 'set_id', 'player'),
    )
    category = relationship('Category', back_populates='cards')
    year = relationship('Year', back_populates='cards')
    set = relationship('Set', back_populates='cards')
    populations = relationship('Population', back_populates='card')

class Grade(Base):
    __tablename__ = 'grades'
    id = Column(Integer, primary_key=True)
    grade_label = Column(Text, unique=True, nullable=False)
    populations = relationship('Population', back_populates='grade')

class Snapshot(Base):
    __tablename__ = 'snapshots'
    id = Column(Integer, primary_key=True)
    captured_at = Column(TIMESTAMP(timezone=True), unique=True, nullable=False)
    populations = relationship('Population', back_populates='snapshot')

class Population(Base):
    __tablename__ = 'populations'
    snapshot_id = Column(Integer, ForeignKey('snapshots.id'), primary_key=True)
    card_uid = Column(Text, ForeignKey('cards.card_uid'), primary_key=True)
    grade_id = Column(Integer, ForeignKey('grades.id'), primary_key=True)
    count = Column(Integer, nullable=False)
    total_graded = Column(Integer, nullable=True)
    __table_args__ = (
        Index('ix_populations_carduid_snapshot', 'card_uid', 'snapshot_id'),
    )
    snapshot = relationship('Snapshot', back_populates='populations')
    card = relationship('Card', back_populates='populations')
    grade = relationship('Grade', back_populates='populations')

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(BigInteger, primary_key=True)
    level = Column(Text, nullable=False)
    context = Column(JSONB, nullable=True)
    message = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default='now()')

# Add descending index for created_at after class definition
Index('ix_audit_logs_created_at_desc', AuditLog.created_at.desc())

class CategoryTotal(Base):
    __tablename__ = 'category_totals'
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('categories.id'), unique=True, nullable=False)
    num_sets = Column(Integer, nullable=True)
    total_items = Column(Integer, nullable=True)
    total_graded = Column(Integer, nullable=True)
    category = relationship('Category', backref='category_total', uselist=False)

class YearTotal(Base):
    __tablename__ = 'year_totals'
    id = Column(Integer, primary_key=True)
    year_id = Column(Integer, ForeignKey('years.id'), unique=True, nullable=False)
    num_sets = Column(Integer, nullable=True)
    total_items = Column(Integer, nullable=True)
    total_graded = Column(Integer, nullable=True)
    year = relationship('Year', backref='year_total', uselist=False)

class SetTotal(Base):
    __tablename__ = 'set_totals'
    id = Column(Integer, primary_key=True)
    set_id = Column(Integer, ForeignKey('sets.id'), unique=True, nullable=False)
    num_cards = Column(Integer, nullable=True)
    total_items = Column(Integer, nullable=True)
    total_graded = Column(Integer, nullable=True)
    set = relationship('Set', backref='set_total', uselist=False)

class PopulationReport(Base):
    __tablename__ = 'population_reports'
    id = Column(BigInteger)
    card_uid = Column(Text, primary_key=True)
    grade_label = Column(Text, primary_key=True)
    snapshot_date = Column(TIMESTAMP(timezone=True), primary_key=True)
    population_count = Column(Integer, nullable=False)
    total_graded = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    __table_args__ = (
        Index('ix_pop_card_grade_date', 'card_uid', 'grade_label', 'snapshot_date'),
        {'postgresql_partition_by': 'RANGE (snapshot_date)'}
    )

# New models for multi-level scraping system

class YearsIndex(Base):
    """Years discovered for a sport"""
    __tablename__ = 'years_index'
    id = Column(Integer, primary_key=True)
    sport = Column(Text, nullable=False)
    year = Column(Text, nullable=False)
    year_url = Column(Text, nullable=False)
    discovered_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    __table_args__ = (UniqueConstraint('sport', 'year', name='uq_sport_year'),)

class SetsPerYear(Base):
    """Sets discovered per (sport, year)"""
    __tablename__ = 'sets_per_year'
    id = Column(Integer, primary_key=True)
    sport = Column(Text, nullable=False)
    year = Column(Text, nullable=False)
    year_url = Column(Text, nullable=False)
    set_title = Column(Text, nullable=False)
    set_urls = Column(JSONB, nullable=False)  # array of strings
    metrics = Column(JSONB, nullable=True)   # optional numeric map
    discovered_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    __table_args__ = (UniqueConstraint('sport', 'year', 'set_title', name='uq_sport_year_set'),)

class TotalsRollups(Base):
    """Separate rollups for TOTALS"""
    __tablename__ = 'totals_rollups'
    id = Column(Integer, primary_key=True)
    scope = Column(Text, nullable=False)  # 'sport', 'year', 'set', or 'card'
    sport = Column(Text, nullable=False)
    year = Column(Text, nullable=True)      # null for sport-scope
    set_title = Column(Text, nullable=True) # null for sport/year scopes
    card_name = Column(Text, nullable=True) # null for sport/year/set scopes
    metrics = Column(JSONB, nullable=False)
    computed_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    __table_args__ = (
        UniqueConstraint('scope', 'sport', 'year', 'set_title', 'card_name', name='uq_scope_sport_year_set_card'),
        # Add check constraint for scope values
    )

class CardsPerSet(Base):
    """Cards discovered per (sport, year, set)"""
    __tablename__ = 'cards_per_set'
    id = Column(Integer, primary_key=True)
    sport = Column(Text, nullable=False)
    year = Column(Text, nullable=False)
    set_title = Column(Text, nullable=False)
    set_url = Column(Text, nullable=False)
    card_name = Column(Text, nullable=False)
    card_urls = Column(JSONB, nullable=False)  # array of strings
    metrics = Column(JSONB, nullable=True)   # optional numeric map
    discovered_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    __table_args__ = (UniqueConstraint('sport', 'year', 'set_title', 'card_name', name='uq_sport_year_set_card'),)

class CardGradeRows(Base):
    """Individual grade rows for each card"""
    __tablename__ = 'card_grade_rows'
    id = Column(Integer, primary_key=True)
    sport = Column(Text, nullable=False)
    year = Column(Text, nullable=False)
    set_title = Column(Text, nullable=False)
    card_name = Column(Text, nullable=False)
    card_url = Column(Text, nullable=False)
    rank = Column(Text, nullable=True)
    tag_grade = Column(Text, nullable=True)
    report_url = Column(Text, nullable=True)
    rank_by_grade = Column(Text, nullable=True)
    chronology = Column(Text, nullable=True)
    chron_by_grade = Column(Text, nullable=True)
    completed_date_raw = Column(Text, nullable=True)
    completed_date_iso = Column(TIMESTAMP(timezone=True), nullable=True)
    cert_number = Column(Text, nullable=False)
    discovered_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    __table_args__ = (UniqueConstraint('sport', 'year', 'set_title', 'card_name', 'cert_number', name='uq_sport_year_set_card_cert'),)
