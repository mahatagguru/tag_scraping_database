from sqlalchemy import (
    JSON,
    TIMESTAMP,
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from db import Base

# PostgreSQL-specific enhancements
try:
    from sqlalchemy.dialects.postgresql import BIGSERIAL, JSONB
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False

# Use JSONB for PostgreSQL if available, fallback to JSON for SQLite
JSON_TYPE = JSONB if POSTGRESQL_AVAILABLE else JSON
BIGINT_TYPE = BIGSERIAL if POSTGRESQL_AVAILABLE else BigInteger

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    years = relationship('Year', back_populates='category', cascade='all, delete-orphan')
    sets = relationship('Set', back_populates='category', cascade='all, delete-orphan')
    cards = relationship('Card', back_populates='category', cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        Index('ix_categories_name', 'name'),
        Index('ix_categories_active', 'is_active'),
        {'extend_existing': True}
    )

class Year(Base):
    __tablename__ = 'years'
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('categories.id', ondelete='CASCADE'), nullable=False)
    year = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('category_id', 'year', name='uq_category_year'),
        CheckConstraint('year >= 1800 AND year <= 2100', name='chk_year_range'),
        Index('ix_years_category_year', 'category_id', 'year'),
        Index('ix_years_active', 'is_active'),
        {'extend_existing': True}
    )
    
    # Relationships
    category = relationship('Category', back_populates='years')
    sets = relationship('Set', back_populates='year', cascade='all, delete-orphan')
    cards = relationship('Card', back_populates='year', cascade='all, delete-orphan')

class Set(Base):
    __tablename__ = 'sets'
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('categories.id', ondelete='CASCADE'), nullable=False)
    year_id = Column(Integer, ForeignKey('years.id', ondelete='CASCADE'), nullable=False)
    set_name = Column(Text, nullable=False)
    set_description = Column(Text, nullable=True)
    num_sets = Column(Integer, nullable=True)
    total_items = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('year_id', 'set_name', name='uq_year_setname'),
        CheckConstraint('num_sets IS NULL OR num_sets >= 0', name='chk_sets_num_sets'),
        CheckConstraint('total_items IS NULL OR total_items >= 0', name='chk_sets_total_items'),
        Index('ix_sets_year_setname', 'year_id', 'set_name'),
        Index('ix_sets_category_year', 'category_id', 'year_id'),
        Index('ix_sets_active', 'is_active'),
    )
    
    # Relationships
    category = relationship('Category', back_populates='sets')
    year = relationship('Year', back_populates='sets')
    cards = relationship('Card', back_populates='set', cascade='all, delete-orphan')

class Card(Base):
    __tablename__ = 'cards'
    id = Column(Integer, primary_key=True)
    card_uid = Column(Text, unique=True, nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id', ondelete='CASCADE'), nullable=False)
    year_id = Column(Integer, ForeignKey('years.id', ondelete='CASCADE'), nullable=False)
    set_id = Column(Integer, ForeignKey('sets.id', ondelete='CASCADE'), nullable=False)
    card_number = Column(Text, nullable=True)
    player = Column(Text, nullable=True)
    detail_url = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    subset_name = Column(Text, nullable=True)
    variation = Column(Text, nullable=True)
    cert_number = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Constraints
    __table_args__ = (
        Index('ix_cards_category_year_set_player', 'category_id', 'year_id', 'set_id', 'player'),
        Index('ix_cards_card_uid', 'card_uid'),
        Index('ix_cards_active', 'is_active'),
        Index('ix_cards_player', 'player'),
        Index('ix_cards_cert_number', 'cert_number'),
    )
    
    # Relationships
    category = relationship('Category', back_populates='cards')
    year = relationship('Year', back_populates='cards')
    set = relationship('Set', back_populates='cards')
    populations = relationship('Population', back_populates='card', cascade='all, delete-orphan')

class Grade(Base):
    __tablename__ = 'grades'
    id = Column(Integer, primary_key=True)
    grade_label = Column(Text, unique=True, nullable=False)
    grade_value = Column(SmallInteger, nullable=True)  # Numeric value for sorting
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Constraints
    __table_args__ = (
        Index('ix_grades_label', 'grade_label'),
        Index('ix_grades_value', 'grade_value'),
        Index('ix_grades_active', 'is_active'),
    )
    
    # Relationships
    populations = relationship('Population', back_populates='grade')

class Snapshot(Base):
    __tablename__ = 'snapshots'
    id = Column(Integer, primary_key=True)
    captured_at = Column(TIMESTAMP(timezone=True), unique=True, nullable=False)
    source = Column(Text, nullable=True)  # Source of the snapshot
    is_complete = Column(Boolean, default=False, nullable=False)
    
    # Constraints
    __table_args__ = (
        Index('ix_snapshots_captured_at', 'captured_at'),
        Index('ix_snapshots_source', 'source'),
        Index('ix_snapshots_complete', 'is_complete'),
    )
    
    # Relationships
    populations = relationship('Population', back_populates='snapshot')

class Population(Base):
    __tablename__ = 'populations'
    snapshot_id = Column(Integer, ForeignKey('snapshots.id', ondelete='CASCADE'), primary_key=True)
    card_uid = Column(Text, ForeignKey('cards.card_uid', ondelete='CASCADE'), primary_key=True)
    grade_id = Column(Integer, ForeignKey('grades.id', ondelete='CASCADE'), primary_key=True)
    count = Column(Integer, nullable=False)
    total_graded = Column(Integer, nullable=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('count >= 0', name='chk_populations_count'),
        CheckConstraint('total_graded IS NULL OR total_graded >= count', name='chk_populations_total_graded'),
        Index('ix_populations_carduid_snapshot', 'card_uid', 'snapshot_id'),
        Index('ix_populations_grade', 'grade_id'),
        Index('ix_populations_count', 'count'),
    )
    
    # Relationships
    snapshot = relationship('Snapshot', back_populates='populations')
    card = relationship('Card', back_populates='populations')
    grade = relationship('Grade', back_populates='populations')

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(BIGINT_TYPE, primary_key=True)
    level = Column(Text, nullable=False)  # INFO, WARNING, ERROR, DEBUG
    component = Column(Text, nullable=True)  # Which component generated the log
    operation = Column(Text, nullable=True)  # Operation being performed
    status = Column(Text, nullable=True)  # SUCCESS, FAILURE, PARTIAL
    error_code = Column(Text, nullable=True)  # Specific error code if applicable
    error_message = Column(Text, nullable=True)  # Detailed error message
    context = Column(JSON_TYPE, nullable=True)  # Additional context data
    message = Column(Text, nullable=False)  # Main log message
    stack_trace = Column(Text, nullable=True)  # Stack trace for errors
    user_agent = Column(Text, nullable=True)  # User agent if applicable
    ip_address = Column(Text, nullable=True)  # IP address if applicable
    execution_time_ms = Column(Integer, nullable=True)  # Execution time in milliseconds
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    
    # Constraints
    __table_args__ = (
        CheckConstraint("level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')", name='chk_audit_level'),
        CheckConstraint("status IS NULL OR status IN ('SUCCESS', 'FAILURE', 'PARTIAL')", name='chk_audit_status'),
        CheckConstraint('execution_time_ms IS NULL OR execution_time_ms >= 0', name='chk_audit_execution_time'),
        Index('ix_audit_logs_created_at_desc', 'created_at'),
        Index('ix_audit_logs_level', 'level'),
        Index('ix_audit_logs_component', 'component'),
        Index('ix_audit_logs_status', 'status'),
        Index('ix_audit_logs_error_code', 'error_code'),
        Index('ix_audit_logs_operation', 'operation'),
    )

class CategoryTotal(Base):
    __tablename__ = 'category_totals'
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('categories.id', ondelete='CASCADE'), unique=True, nullable=False)
    num_sets = Column(Integer, nullable=True)
    total_items = Column(Integer, nullable=True)
    total_graded = Column(Integer, nullable=True)
    last_updated = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('num_sets IS NULL OR num_sets >= 0', name='chk_category_totals_num_sets'),
        CheckConstraint('total_items IS NULL OR total_items >= 0', name='chk_category_totals_total_items'),
        CheckConstraint('total_graded IS NULL OR total_graded >= 0', name='chk_category_totals_total_graded'),
        Index('ix_category_totals_category', 'category_id'),
    )
    
    # Relationships
    category = relationship('Category', backref='category_total', uselist=False)

class YearTotal(Base):
    __tablename__ = 'year_totals'
    id = Column(Integer, primary_key=True)
    year_id = Column(Integer, ForeignKey('years.id', ondelete='CASCADE'), unique=True, nullable=False)
    num_sets = Column(Integer, nullable=True)
    total_items = Column(Integer, nullable=True)
    total_graded = Column(Integer, nullable=True)
    last_updated = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('num_sets IS NULL OR num_sets >= 0', name='chk_year_totals_num_sets'),
        CheckConstraint('total_items IS NULL OR total_items >= 0', name='chk_year_totals_total_items'),
        CheckConstraint('total_graded IS NULL OR total_graded >= 0', name='chk_year_totals_total_graded'),
        Index('ix_year_totals_year', 'year_id'),
    )
    
    # Relationships
    year = relationship('Year', backref='year_total', uselist=False)

class SetTotal(Base):
    __tablename__ = 'set_totals'
    id = Column(Integer, primary_key=True)
    set_id = Column(Integer, ForeignKey('sets.id', ondelete='CASCADE'), unique=True, nullable=False)
    num_cards = Column(Integer, nullable=True)
    total_items = Column(Integer, nullable=True)
    total_graded = Column(Integer, nullable=True)
    last_updated = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('num_cards IS NULL OR num_cards >= 0', name='chk_set_totals_num_cards'),
        CheckConstraint('total_items IS NULL OR total_items >= 0', name='chk_set_totals_total_items'),
        CheckConstraint('total_graded IS NULL OR total_graded >= 0', name='chk_set_totals_total_graded'),
        Index('ix_set_totals_set', 'set_id'),
    )
    
    # Relationships
    set = relationship('Set', backref='set_total', uselist=False)

class PopulationReport(Base):
    __tablename__ = 'population_reports'
    id = Column(BIGINT_TYPE, primary_key=True)
    card_uid = Column(Text, nullable=False)
    grade_label = Column(Text, nullable=False)
    snapshot_date = Column(TIMESTAMP(timezone=True), nullable=False)
    population_count = Column(Integer, nullable=False)
    total_graded = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('population_count >= 0', name='chk_population_reports_count'),
        CheckConstraint('total_graded IS NULL OR total_graded >= population_count', name='chk_population_reports_total_graded'),
        Index('ix_pop_card_grade_date', 'card_uid', 'grade_label', 'snapshot_date'),
    )

# Multi-level scraping system models with improved relationships

class YearsIndex(Base):
    """Years discovered for a sport"""
    __tablename__ = 'years_index'
    id = Column(Integer, primary_key=True)
    sport = Column(Text, nullable=False)
    year = Column(Text, nullable=False)
    year_url = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    discovered_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('sport', 'year', name='uq_sport_year'),
        Index('ix_years_index_sport_year', 'sport', 'year'),
        Index('ix_years_index_active', 'is_active'),
        Index('ix_years_index_discovered', 'discovered_at'),
    )
    
    # Relationships
    sets = relationship('SetsPerYear', back_populates='year_index', cascade='all, delete-orphan')

class SetsPerYear(Base):
    """Sets discovered per (sport, year)"""
    __tablename__ = 'sets_per_year'
    id = Column(Integer, primary_key=True)
    year_index_id = Column(Integer, ForeignKey('years_index.id', ondelete='CASCADE'), nullable=True)
    sport = Column(Text, nullable=False)
    year = Column(Text, nullable=False)
    year_url = Column(Text, nullable=False)
    set_title = Column(Text, nullable=False)
    set_urls = Column(JSON_TYPE, nullable=False)  # array of strings
    metrics = Column(JSON_TYPE, nullable=True)   # optional numeric map
    is_active = Column(Boolean, default=True, nullable=False)
    discovered_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('sport', 'year', 'set_title', name='uq_sport_year_set'),
        Index('ix_sets_per_year_year_index', 'year_index_id'),
        Index('ix_sets_per_year_sport_year', 'sport', 'year'),
        Index('ix_sets_per_year_set_title', 'set_title'),
        Index('ix_sets_per_year_active', 'is_active'),
        Index('ix_sets_per_year_discovered', 'discovered_at'),
    )
    
    # Relationships
    year_index = relationship('YearsIndex', back_populates='sets')
    cards = relationship('CardsPerSet', back_populates='set_per_year', cascade='all, delete-orphan')

class CardsPerSet(Base):
    """Cards discovered per (sport, year, set)"""
    __tablename__ = 'cards_per_set'
    id = Column(Integer, primary_key=True)
    set_per_year_id = Column(Integer, ForeignKey('sets_per_year.id', ondelete='CASCADE'), nullable=True)
    sport = Column(Text, nullable=False)
    year = Column(Text, nullable=False)
    set_title = Column(Text, nullable=False)
    set_url = Column(Text, nullable=False)
    card_name = Column(Text, nullable=False)
    card_urls = Column(JSON_TYPE, nullable=False)  # array of strings
    metrics = Column(JSON_TYPE, nullable=True)   # optional numeric map
    is_active = Column(Boolean, default=True, nullable=False)
    discovered_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('sport', 'year', 'set_title', 'card_name', name='uq_sport_year_set_card'),
        Index('ix_cards_per_set_set_per_year', 'set_per_year_id'),
        Index('ix_cards_per_set_sport_year_set', 'sport', 'year', 'set_title'),
        Index('ix_cards_per_set_card_name', 'card_name'),
        Index('ix_cards_per_set_active', 'is_active'),
        Index('ix_cards_per_set_discovered', 'discovered_at'),
    )
    
    # Relationships
    set_per_year = relationship('SetsPerYear', back_populates='cards')
    grade_rows = relationship('CardGradeRows', back_populates='card_per_set', cascade='all, delete-orphan')

class CardGradeRows(Base):
    """Individual grade rows for each card"""
    __tablename__ = 'card_grade_rows'
    id = Column(Integer, primary_key=True)
    card_per_set_id = Column(Integer, ForeignKey('cards_per_set.id', ondelete='CASCADE'), nullable=True)
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
    is_active = Column(Boolean, default=True, nullable=False)
    discovered_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('sport', 'year', 'set_title', 'card_name', 'cert_number', name='uq_sport_year_set_card_cert'),
        Index('ix_card_grade_rows_card_per_set', 'card_per_set_id'),
        Index('ix_card_grade_rows_sport_year_set_card', 'sport', 'year', 'set_title', 'card_name'),
        Index('ix_card_grade_rows_cert_number', 'cert_number'),
        Index('ix_card_grade_rows_tag_grade', 'tag_grade'),
        Index('ix_card_grade_rows_active', 'is_active'),
        Index('ix_card_grade_rows_discovered', 'discovered_at'),
    )
    
    # Relationships
    card_per_set = relationship('CardsPerSet', back_populates='grade_rows')

class TotalsRollups(Base):
    """Separate rollups for TOTALS"""
    __tablename__ = 'totals_rollups'
    id = Column(Integer, primary_key=True)
    scope = Column(Text, nullable=False)  # 'sport', 'year', 'set', or 'card'
    sport = Column(Text, nullable=False)
    year = Column(Text, nullable=True)      # null for sport-scope
    set_title = Column(Text, nullable=True) # null for sport/year scopes
    card_name = Column(Text, nullable=True) # null for sport/year/set scopes
    metrics = Column(JSON_TYPE, nullable=False)
    computed_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('scope', 'sport', 'year', 'set_title', 'card_name', name='uq_scope_sport_year_set_card'),
        CheckConstraint("scope IN ('sport', 'year', 'set', 'card')", name='chk_totals_rollups_scope'),
        Index('ix_totals_rollups_scope_sport', 'scope', 'sport'),
        Index('ix_totals_rollups_computed', 'computed_at'),
    )
