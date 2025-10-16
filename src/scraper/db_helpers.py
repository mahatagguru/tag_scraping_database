import datetime

from sqlalchemy.orm import Session

from models import (
    Card,
    CardGradeRows,
    CardsPerSet,
    Category,
    CategoryTotal,
    PopulationReport,
    Set,
    SetsPerYear,
    SetTotal,
    TotalsRollups,
    Year,
    YearsIndex,
    YearTotal,
)


class DatabaseHelper:
    """Database helper class for managing database operations."""

    def __init__(self):
        self.session = None

    def get_session(self):
        """Get a database session."""
        from db import SessionLocal

        return SessionLocal()

    def close_session(self, session):
        """Close a database session."""
        if session:
            session.close()


def upsert_category(session: Session, name: str, img: str = None):
    """
    Upsert a category by name. Returns the Category instance.
    Usage: cat = upsert_category(session, name, img)
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    cat = session.query(Category).filter_by(name=name).first()
    if not cat:
        cat = Category(name=name, updated_at=now)
        session.add(cat)
        session.flush()  # get id
    else:
        cat.updated_at = now
    # Optionally update image or other fields here if needed
    return cat


def upsert_year(session: Session, category_id: int, year: int):
    """
    Upsert a year by (category_id, year). Returns the Year instance.
    Usage: yr = upsert_year(session, category_id, year)
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    yr = session.query(Year).filter_by(category_id=category_id, year=year).first()
    if not yr:
        yr = Year(category_id=category_id, year=year, updated_at=now)
        session.add(yr)
        session.flush()
    else:
        yr.updated_at = now
    return yr


def upsert_set(
    session: Session,
    category_id: int,
    year_id: int,
    set_name: str,
    num_sets: int = None,
    total_items: int = None,
):
    """
    Upsert a set by (year_id, set_name). Returns the Set instance.
    Usage: s = upsert_set(session, category_id, year_id, set_name, num_sets, total_items)
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    s = session.query(Set).filter_by(year_id=year_id, set_name=set_name).first()
    if not s:
        s = Set(
            category_id=category_id,
            year_id=year_id,
            set_name=set_name,
            num_sets=num_sets,
            total_items=total_items,
            updated_at=now,
        )
        session.add(s)
        session.flush()
    else:
        # Optionally update num_sets/total_items if changed
        if num_sets is not None:
            s.num_sets = num_sets
        if total_items is not None:
            s.total_items = total_items
        s.updated_at = now
    return s


def upsert_category_total(
    session: Session,
    category_id: int,
    num_sets: int = None,
    total_items: int = None,
    total_graded: int = None,
):
    """
    Upsert a category total by category_id. Returns the CategoryTotal instance.
    """
    ct = session.query(CategoryTotal).filter_by(category_id=category_id).first()
    if not ct:
        ct = CategoryTotal(
            category_id=category_id,
            num_sets=num_sets,
            total_items=total_items,
            total_graded=total_graded,
        )
        session.add(ct)
        session.flush()
    else:
        if num_sets is not None:
            ct.num_sets = num_sets
        if total_items is not None:
            ct.total_items = total_items
        if total_graded is not None:
            ct.total_graded = total_graded
    return ct


def upsert_year_total(
    session: Session,
    year_id: int,
    num_sets: int = None,
    total_items: int = None,
    total_graded: int = None,
):
    """
    Upsert a year total by year_id. Returns the YearTotal instance.
    """
    yt = session.query(YearTotal).filter_by(year_id=year_id).first()
    if not yt:
        yt = YearTotal(
            year_id=year_id,
            num_sets=num_sets,
            total_items=total_items,
            total_graded=total_graded,
        )
        session.add(yt)
        session.flush()
    else:
        if num_sets is not None:
            yt.num_sets = num_sets
        if total_items is not None:
            yt.total_items = total_items
        if total_graded is not None:
            yt.total_graded = total_graded
    return yt


def upsert_set_total(
    session: Session,
    set_id: int,
    num_cards: int = None,
    total_items: int = None,
    total_graded: int = None,
):
    """
    Upsert a set total by set_id. Returns the SetTotal instance.
    """
    st = session.query(SetTotal).filter_by(set_id=set_id).first()
    if not st:
        st = SetTotal(
            set_id=set_id,
            num_cards=num_cards,
            total_items=total_items,
            total_graded=total_graded,
        )
        session.add(st)
        session.flush()
    else:
        if num_cards is not None:
            st.num_cards = num_cards
        if total_items is not None:
            st.total_items = total_items
        if total_graded is not None:
            st.total_graded = total_graded
    return st


def upsert_card(
    session: Session,
    card_uid: str,
    category_id: int,
    year_id: int,
    set_id: int,
    card_number: str = None,
    player: str = None,
    detail_url: str = None,
    image_url: str = None,
    subset_name: str = None,
    variation: str = None,
    cert_number: str = None,
):
    now = datetime.datetime.now(datetime.timezone.utc)
    card = session.query(Card).filter_by(card_uid=card_uid).first()
    if not card:
        card = Card(
            card_uid=card_uid,
            category_id=category_id,
            year_id=year_id,
            set_id=set_id,
            card_number=card_number,
            player=player,
            detail_url=detail_url,
            image_url=image_url,
            subset_name=subset_name,
            variation=variation,
            cert_number=cert_number,
            updated_at=now,
        )
        session.add(card)
        session.flush()
    else:
        card.category_id = category_id
        card.year_id = year_id
        card.set_id = set_id
        card.card_number = card_number
        card.player = player
        card.detail_url = detail_url
        card.image_url = image_url
        card.subset_name = subset_name
        card.variation = variation
        card.cert_number = cert_number
        card.updated_at = now
    return card


def upsert_population_report(
    session: Session,
    card_uid: str,
    grade_label: str,
    snapshot_date,
    population_count: int,
    total_graded: int = None,
):
    now = datetime.datetime.now(datetime.timezone.utc)
    pr = (
        session.query(PopulationReport)
        .filter_by(
            card_uid=card_uid, grade_label=grade_label, snapshot_date=snapshot_date
        )
        .first()
    )
    if not pr:
        pr = PopulationReport(
            card_uid=card_uid,
            grade_label=grade_label,
            snapshot_date=snapshot_date,
            population_count=population_count,
            total_graded=total_graded,
            created_at=now,
            updated_at=now,
        )
        session.add(pr)
        session.flush()
    else:
        pr.population_count = population_count
        pr.total_graded = total_graded
        pr.updated_at = now
    return pr


# New helper functions for multi-level scraping system


def upsert_years_index(session: Session, sport: str, year: str, year_url: str):
    """
    Upsert a year index entry by (sport, year). Returns the YearsIndex instance.
    Usage: yi = upsert_years_index(session, sport, year, year_url)
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    yi = session.query(YearsIndex).filter_by(sport=sport, year=year).first()
    if not yi:
        yi = YearsIndex(sport=sport, year=year, year_url=year_url, discovered_at=now)
        session.add(yi)
        session.flush()
    else:
        # Update URL if changed
        if yi.year_url != year_url:
            yi.year_url = year_url
    return yi


def upsert_sets_per_year(
    session: Session,
    sport: str,
    year: str,
    year_url: str,
    set_title: str,
    set_urls: list,
    metrics: dict = None,
):
    """
    Upsert a sets per year entry by (sport, year, set_title). Returns the SetsPerYear instance.
    Usage: spy = upsert_sets_per_year(session, sport, year, year_url, set_title, set_urls, metrics)
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    spy = (
        session.query(SetsPerYear)
        .filter_by(sport=sport, year=year, set_title=set_title)
        .first()
    )
    if not spy:
        spy = SetsPerYear(
            sport=sport,
            year=year,
            year_url=year_url,
            set_title=set_title,
            set_urls=set_urls,
            metrics=metrics,
            discovered_at=now,
        )
        session.add(spy)
        session.flush()
    else:
        # Update fields if changed
        spy.year_url = year_url
        spy.set_urls = set_urls
        spy.metrics = metrics
    return spy


def upsert_totals_rollups(
    session: Session,
    scope: str,
    sport: str,
    year: str = None,
    set_title: str = None,
    card_name: str = None,
    metrics: dict = None,
):
    """
    Upsert a totals rollup entry by (scope, sport, year, set_title, card_name). Returns the TotalsRollups instance.
    Usage: tr = upsert_totals_rollups(session, scope, sport, year, set_title, card_name, metrics)
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    tr = (
        session.query(TotalsRollups)
        .filter_by(
            scope=scope,
            sport=sport,
            year=year,
            set_title=set_title,
            card_name=card_name,
        )
        .first()
    )
    if not tr:
        tr = TotalsRollups(
            scope=scope,
            sport=sport,
            year=year,
            set_title=set_title,
            card_name=card_name,
            metrics=metrics or {},
            computed_at=now,
        )
        session.add(tr)
        session.flush()
    else:
        # Update metrics
        tr.metrics = metrics or {}
        tr.computed_at = now
    return tr


def upsert_cards_per_set(
    session: Session,
    sport: str,
    year: str,
    set_title: str,
    set_url: str,
    card_name: str,
    card_urls: list,
    metrics: dict = None,
):
    """
    Upsert a cards per set entry by (sport, year, set_title, card_name). Returns the CardsPerSet instance.
    Usage: cps = upsert_cards_per_set(session, sport, year, set_title, set_url, card_name, card_urls, metrics)
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    cps = (
        session.query(CardsPerSet)
        .filter_by(sport=sport, year=year, set_title=set_title, card_name=card_name)
        .first()
    )
    if not cps:
        cps = CardsPerSet(
            sport=sport,
            year=year,
            set_title=set_title,
            set_url=set_url,
            card_name=card_name,
            card_urls=card_urls,
            metrics=metrics,
            discovered_at=now,
        )
        session.add(cps)
        session.flush()
    else:
        # Update fields if changed
        cps.set_url = set_url
        cps.card_urls = card_urls
        cps.metrics = metrics
    return cps


def upsert_card_grade_row(
    session: Session,
    sport: str,
    year: str,
    set_title: str,
    card_name: str,
    card_url: str,
    cert_number: str,
    **kwargs,
):
    """
    Upsert a card grade row entry by (sport, year, set_title, card_name, cert_number). Returns the CardGradeRows instance.
    Usage: cgr = upsert_card_grade_row(session, sport, year, set_title, card_name, card_url, cert_number, rank=1, tag_grade="8.5", ...)
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    cgr = (
        session.query(CardGradeRows)
        .filter_by(
            sport=sport,
            year=year,
            set_title=set_title,
            card_name=card_name,
            cert_number=cert_number,
        )
        .first()
    )

    if not cgr:
        cgr = CardGradeRows(
            sport=sport,
            year=year,
            set_title=set_title,
            card_name=card_name,
            card_url=card_url,
            cert_number=cert_number,
            discovered_at=now,
            **kwargs,
        )
        session.add(cgr)
        session.flush()
    else:
        # Update fields if changed
        cgr.card_url = card_url
        for key, value in kwargs.items():
            if hasattr(cgr, key):
                setattr(cgr, key, value)

    return cgr
