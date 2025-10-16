#!/usr/bin/env python3
"""
TAG Grading Scraper - Reporting Website Backend API
FastAPI-based REST API for comprehensive data reporting and analysis
"""

from fastapi import FastAPI, HTTPException, Depends, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

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
    PopulationReport,
    YearsIndex,
    SetsPerYear,
    CardsPerSet,
    CardGradeRows,
    TotalsRollups,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TAG Grading Scraper API",
    description="Comprehensive API for TAG grading data analysis and reporting",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API responses
from pydantic import BaseModel
from typing import Optional as Opt


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Opt[str] = None
    is_active: bool
    updated_at: datetime
    num_sets: Opt[int] = None
    total_items: Opt[int] = None
    total_graded: Opt[int] = None


class YearResponse(BaseModel):
    id: int
    category_id: int
    year: int
    is_active: bool
    updated_at: datetime
    category_name: str
    num_sets: Opt[int] = None
    total_items: Opt[int] = None
    total_graded: Opt[int] = None


class SetResponse(BaseModel):
    id: int
    category_id: int
    year_id: int
    set_name: str
    set_description: Opt[str] = None
    num_sets: Opt[int] = None
    total_items: Opt[int] = None
    is_active: bool
    updated_at: datetime
    category_name: str
    year: int
    num_cards: Opt[int] = None
    total_graded: Opt[int] = None


class CardResponse(BaseModel):
    id: int
    card_uid: str
    category_id: int
    year_id: int
    set_id: int
    card_number: Opt[str] = None
    player: Opt[str] = None
    detail_url: Opt[str] = None
    image_url: Opt[str] = None
    subset_name: Opt[str] = None
    variation: Opt[str] = None
    cert_number: Opt[str] = None
    is_active: bool
    updated_at: datetime
    category_name: str
    year: int
    set_name: str


class GradeResponse(BaseModel):
    id: int
    grade_label: str
    grade_value: Opt[int] = None
    is_active: bool


class PopulationResponse(BaseModel):
    card_uid: str
    grade_label: str
    count: int
    total_graded: Opt[int] = None
    snapshot_date: datetime
    player: str
    set_name: str
    year: int
    category_name: str


class DashboardStats(BaseModel):
    total_categories: int
    total_years: int
    total_sets: int
    total_cards: int
    total_grades: int
    total_populations: int
    latest_snapshot: Opt[datetime] = None
    recent_activity: List[Dict[str, Any]]


class SearchResult(BaseModel):
    type: str  # 'card', 'set', 'year', 'category'
    id: int
    name: str
    description: Opt[str] = None
    category: Opt[str] = None
    year: Opt[int] = None
    set_name: Opt[str] = None


# API Routes


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "TAG Grading Scraper API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "status": "operational",
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        with get_db_session_context() as db:
            # Test database connection
            db.execute("SELECT 1")
            return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503, content={"status": "unhealthy", "error": str(e)}
        )


@app.get("/api/dashboard", response_model=DashboardStats)
async def get_dashboard_stats():
    """Get comprehensive dashboard statistics"""
    try:
        with get_db_session_context() as db:
            # Basic counts
            total_categories = db.query(Category).count()
            total_years = db.query(Year).count()
            total_sets = db.query(Set).count()
            total_cards = db.query(Card).count()
            total_grades = db.query(Grade).count()
            total_populations = db.query(Population).count()

            # Latest snapshot
            latest_snapshot = (
                db.query(Snapshot).order_by(desc(Snapshot.captured_at)).first()
            )
            latest_snapshot_date = (
                latest_snapshot.captured_at if latest_snapshot else None
            )

            # Recent activity (last 10 audit logs)
            recent_activity = (
                db.query(AuditLog).order_by(desc(AuditLog.created_at)).limit(10).all()
            )
            activity_list = []
            for log in recent_activity:
                activity_list.append(
                    {
                        "timestamp": log.created_at,
                        "level": log.level,
                        "component": log.component,
                        "operation": log.operation,
                        "message": log.message,
                        "status": log.status,
                    }
                )

            return DashboardStats(
                total_categories=total_categories,
                total_years=total_years,
                total_sets=total_sets,
                total_cards=total_cards,
                total_grades=total_grades,
                total_populations=total_populations,
                latest_snapshot=latest_snapshot_date,
                recent_activity=activity_list,
            )
    except Exception as e:
        logger.error(f"Dashboard stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/categories", response_model=List[CategoryResponse])
async def get_categories(
    active_only: bool = Query(True, description="Only return active categories"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of categories to return"
    ),
    offset: int = Query(0, ge=0, description="Number of categories to skip"),
):
    """Get all categories with optional filtering"""
    try:
        with get_db_session_context() as db:
            query = db.query(Category)

            if active_only:
                query = query.filter(Category.is_active == True)

            categories = query.offset(offset).limit(limit).all()

            result = []
            for cat in categories:
                # Get totals if available
                totals = (
                    db.query(CategoryTotal)
                    .filter(CategoryTotal.category_id == cat.id)
                    .first()
                )

                result.append(
                    CategoryResponse(
                        id=cat.id,
                        name=cat.name,
                        description=cat.description,
                        is_active=cat.is_active,
                        updated_at=cat.updated_at,
                        num_sets=totals.num_sets if totals else None,
                        total_items=totals.total_items if totals else None,
                        total_graded=totals.total_graded if totals else None,
                    )
                )

            return result
    except Exception as e:
        logger.error(f"Categories error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/categories/{category_id}/years", response_model=List[YearResponse])
async def get_years_by_category(
    category_id: int = Path(..., description="Category ID"),
    active_only: bool = Query(True, description="Only return active years"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of years to return"
    ),
    offset: int = Query(0, ge=0, description="Number of years to skip"),
):
    """Get years for a specific category"""
    try:
        with get_db_session_context() as db:
            query = (
                db.query(Year).join(Category).filter(Year.category_id == category_id)
            )

            if active_only:
                query = query.filter(Year.is_active == True)

            years = query.offset(offset).limit(limit).all()

            result = []
            for year in years:
                # Get totals if available
                totals = (
                    db.query(YearTotal).filter(YearTotal.year_id == year.id).first()
                )

                result.append(
                    YearResponse(
                        id=year.id,
                        category_id=year.category_id,
                        year=year.year,
                        is_active=year.is_active,
                        updated_at=year.updated_at,
                        category_name=year.category.name,
                        num_sets=totals.num_sets if totals else None,
                        total_items=totals.total_items if totals else None,
                        total_graded=totals.total_graded if totals else None,
                    )
                )

            return result
    except Exception as e:
        logger.error(f"Years error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/years/{year_id}/sets", response_model=List[SetResponse])
async def get_sets_by_year(
    year_id: int = Path(..., description="Year ID"),
    active_only: bool = Query(True, description="Only return active sets"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of sets to return"
    ),
    offset: int = Query(0, ge=0, description="Number of sets to skip"),
):
    """Get sets for a specific year"""
    try:
        with get_db_session_context() as db:
            query = (
                db.query(Set).join(Year).join(Category).filter(Set.year_id == year_id)
            )

            if active_only:
                query = query.filter(Set.is_active == True)

            sets = query.offset(offset).limit(limit).all()

            result = []
            for s in sets:
                # Get totals if available
                totals = db.query(SetTotal).filter(SetTotal.set_id == s.id).first()

                result.append(
                    SetResponse(
                        id=s.id,
                        category_id=s.category_id,
                        year_id=s.year_id,
                        set_name=s.set_name,
                        set_description=s.set_description,
                        num_sets=s.num_sets,
                        total_items=s.total_items,
                        is_active=s.is_active,
                        updated_at=s.updated_at,
                        category_name=s.category.name,
                        year=s.year.year,
                        num_cards=totals.num_cards if totals else None,
                        total_graded=totals.total_graded if totals else None,
                    )
                )

            return result
    except Exception as e:
        logger.error(f"Sets error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sets/{set_id}/cards", response_model=List[CardResponse])
async def get_cards_by_set(
    set_id: int = Path(..., description="Set ID"),
    active_only: bool = Query(True, description="Only return active cards"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of cards to return"
    ),
    offset: int = Query(0, ge=0, description="Number of cards to skip"),
    search: Opt[str] = Query(None, description="Search by player name"),
):
    """Get cards for a specific set"""
    try:
        with get_db_session_context() as db:
            query = (
                db.query(Card)
                .join(Set)
                .join(Year)
                .join(Category)
                .filter(Card.set_id == set_id)
            )

            if active_only:
                query = query.filter(Card.is_active == True)

            if search:
                query = query.filter(Card.player.ilike(f"%{search}%"))

            cards = query.offset(offset).limit(limit).all()

            result = []
            for card in cards:
                result.append(
                    CardResponse(
                        id=card.id,
                        card_uid=card.card_uid,
                        category_id=card.category_id,
                        year_id=card.year_id,
                        set_id=card.set_id,
                        card_number=card.card_number,
                        player=card.player,
                        detail_url=card.detail_url,
                        image_url=card.image_url,
                        subset_name=card.subset_name,
                        variation=card.variation,
                        cert_number=card.cert_number,
                        is_active=card.is_active,
                        updated_at=card.updated_at,
                        category_name=card.category.name,
                        year=card.year.year,
                        set_name=card.set.set_name,
                    )
                )

            return result
    except Exception as e:
        logger.error(f"Cards error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cards/{card_uid}/populations", response_model=List[PopulationResponse])
async def get_card_populations(
    card_uid: str = Path(..., description="Card UID"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of populations to return"
    ),
    offset: int = Query(0, ge=0, description="Number of populations to skip"),
):
    """Get population data for a specific card"""
    try:
        with get_db_session_context() as db:
            query = (
                db.query(Population)
                .join(Card)
                .join(Grade)
                .join(Snapshot)
                .filter(Population.card_uid == card_uid)
            )

            populations = query.offset(offset).limit(limit).all()

            result = []
            for pop in populations:
                result.append(
                    PopulationResponse(
                        card_uid=pop.card_uid,
                        grade_label=pop.grade.grade_label,
                        count=pop.count,
                        total_graded=pop.total_graded,
                        snapshot_date=pop.snapshot.captured_at,
                        player=pop.card.player,
                        set_name=pop.card.set.set_name,
                        year=pop.card.year.year,
                        category_name=pop.card.category.name,
                    )
                )

            return result
    except Exception as e:
        logger.error(f"Populations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/grades", response_model=List[GradeResponse])
async def get_grades(
    active_only: bool = Query(True, description="Only return active grades"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of grades to return"
    ),
):
    """Get all grades"""
    try:
        with get_db_session_context() as db:
            query = db.query(Grade)

            if active_only:
                query = query.filter(Grade.is_active == True)

            grades = query.limit(limit).all()

            result = []
            for grade in grades:
                result.append(
                    GradeResponse(
                        id=grade.id,
                        grade_label=grade.grade_label,
                        grade_value=grade.grade_value,
                        is_active=grade.is_active,
                    )
                )

            return result
    except Exception as e:
        logger.error(f"Grades error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search", response_model=List[SearchResult])
async def search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(
        50, ge=1, le=200, description="Maximum number of results to return"
    ),
):
    """Search across all entities"""
    try:
        with get_db_session_context() as db:
            results = []

            # Search cards
            cards = (
                db.query(Card)
                .join(Set)
                .join(Year)
                .join(Category)
                .filter(
                    or_(
                        Card.player.ilike(f"%{q}%"),
                        Card.card_number.ilike(f"%{q}%"),
                        Card.cert_number.ilike(f"%{q}%"),
                    )
                )
                .limit(limit // 4)
                .all()
            )

            for card in cards:
                results.append(
                    SearchResult(
                        type="card",
                        id=card.id,
                        name=f"{card.player} - {card.card_number}"
                        if card.player and card.card_number
                        else card.player or card.card_number or "Unknown",
                        description=f"{card.category.name} {card.year.year} {card.set.set_name}",
                        category=card.category.name,
                        year=card.year.year,
                        set_name=card.set.set_name,
                    )
                )

            # Search sets
            sets = (
                db.query(Set)
                .join(Year)
                .join(Category)
                .filter(Set.set_name.ilike(f"%{q}%"))
                .limit(limit // 4)
                .all()
            )

            for s in sets:
                results.append(
                    SearchResult(
                        type="set",
                        id=s.id,
                        name=s.set_name,
                        description=f"{s.category.name} {s.year.year}",
                        category=s.category.name,
                        year=s.year.year,
                    )
                )

            # Search years
            years = (
                db.query(Year)
                .join(Category)
                .filter(Year.year == int(q) if q.isdigit() else False)
                .limit(limit // 4)
                .all()
            )

            for year in years:
                results.append(
                    SearchResult(
                        type="year",
                        id=year.id,
                        name=str(year.year),
                        description=f"{year.category.name}",
                        category=year.category.name,
                        year=year.year,
                    )
                )

            # Search categories
            categories = (
                db.query(Category)
                .filter(Category.name.ilike(f"%{q}%"))
                .limit(limit // 4)
                .all()
            )

            for cat in categories:
                results.append(
                    SearchResult(
                        type="category",
                        id=cat.id,
                        name=cat.name,
                        description=cat.description,
                    )
                )

            return results[:limit]
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/population-trends")
async def get_population_trends(
    card_uid: Opt[str] = Query(None, description="Filter by specific card UID"),
    grade_label: Opt[str] = Query(None, description="Filter by specific grade"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
):
    """Get population trends over time"""
    try:
        with get_db_session_context() as db:
            # This would require population_reports table with historical data
            # For now, return current snapshot data
            query = db.query(Population).join(Card).join(Grade).join(Snapshot)

            if card_uid:
                query = query.filter(Population.card_uid == card_uid)

            if grade_label:
                query = query.filter(Grade.grade_label == grade_label)

            populations = query.all()

            # Group by grade and sum counts
            grade_totals = {}
            for pop in populations:
                grade = pop.grade.grade_label
                if grade not in grade_totals:
                    grade_totals[grade] = 0
                grade_totals[grade] += pop.count

            return {
                "trends": grade_totals,
                "total_cards": len(set(p.card_uid for p in populations)),
                "date_range": {
                    "start": (datetime.now() - timedelta(days=days)).isoformat(),
                    "end": datetime.now().isoformat(),
                },
            }
    except Exception as e:
        logger.error(f"Population trends error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
