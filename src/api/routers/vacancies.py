from json import loads, JSONDecodeError
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from src.api.rate_limiter import limiter
from src.storage.db import get_db
from src.storage.models import RawVacancy, FilteredVacancy
from src.api.schemas import VacancyResponse, FilteredVacancyResponse
from src.api.security import get_current_user, User


router = APIRouter(prefix="/vacancies", tags=["vacancies"])


def pagination_parameters(skip: int = 0, limit: int = 100):
    return {"skip": skip, "limit": limit}

def _parse_tags(tags_json: str | None) -> list[str]:
    """Convert JSON-string of tags into the list"""
    if not tags_json:
        return []
    try:
        result = loads(tags_json)
        return result if isinstance(result, list) else []
    except (JSONDecodeError, TypeError):
        return []

def _extract_decision(decision_obj) -> str:
    """Get a string value from ENUM"""
    if hasattr(decision_obj, 'value'):
        return decision_obj.value
    return str(decision_obj)


@router.get("/raw", response_model=list[VacancyResponse])
@limiter.limit("60/minute")
def get_raw_vacancies(
        request: Request,
        pagination: dict = Depends(pagination_parameters),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get raw (unfiltered) vacancies"""

    skip, limit = pagination["skip"], pagination["limit"]

    query = db.query(RawVacancy)
    return query.order_by(RawVacancy.fetched_at.desc()).limit(limit).offset(skip).all()


@router.get("/unrejected", response_model=list[FilteredVacancyResponse])
@limiter.limit("60/minute")
def get_filtered_unrejected(
        request: Request,
        pagination: dict = Depends(pagination_parameters),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get LLM-filtered unrejected vacancies with raw data (title, company, url)"""

    skip, limit = pagination["skip"], pagination["limit"]

    results = (
        db.query(FilteredVacancy, RawVacancy)
        .join(RawVacancy, FilteredVacancy.source_id == RawVacancy.source_id)
        .filter(FilteredVacancy.decision != "reject")
        .order_by(FilteredVacancy.processed_at.desc())
        .limit(limit)
        .offset(skip)
        .all()
    )

    return [
        FilteredVacancyResponse(
            id=filtered.id,
            title=raw.title,
            company=raw.company,
            description=raw.description,
            url=raw.url,
            decision=_extract_decision(filtered.decision),
            confidence=filtered.confidence,
            reason=filtered.reason or "",
            tags=_parse_tags(filtered.tags),
            processed_at=filtered.processed_at
        )
        for filtered, raw in results
    ]


@router.get("/rejected", response_model=list[FilteredVacancyResponse])
@limiter.limit("60/minute")
def get_filtered_rejected(
        request: Request,
        pagination: dict = Depends(pagination_parameters),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get LLM-filtered rejected vacancies with raw data (title, company, url)"""

    skip, limit = pagination["skip"], pagination["limit"]

    results = (
        db.query(FilteredVacancy, RawVacancy)
        .join(RawVacancy, FilteredVacancy.source_id == RawVacancy.source_id)
        .filter(FilteredVacancy.decision == "reject")
        .order_by(FilteredVacancy.processed_at.desc())
        .limit(limit)
        .offset(skip)
        .all()
    )

    return [
        FilteredVacancyResponse(
            id=filtered.id,
            title=raw.title,
            company=raw.company,
            description=raw.description,
            url=raw.url,
            decision=_extract_decision(filtered.decision),
            confidence=filtered.confidence,
            reason=filtered.reason or "",
            tags=_parse_tags(filtered.tags),
            processed_at=filtered.processed_at
        )
        for filtered, raw in results
    ]
