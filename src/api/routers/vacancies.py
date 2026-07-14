from json import loads, JSONDecodeError
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from src.storage.db import get_db
from src.storage.models import RawVacancy, FilteredVacancy
from src.api.schemas import VacancyResponse, FilteredVacancyResponse

router = APIRouter(prefix="/vacancies", tags=["vacancies"])


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
def get_raw_vacancies(
        limit: int = Query(50, ge=1, le=200),
        db: Session = Depends(get_db)
):
    """Get raw (unfiltered) vacancies"""
    query = db.query(RawVacancy)
    return query.order_by(RawVacancy.fetched_at.desc()).limit(limit).all()


@router.get("/unrejected", response_model=list[FilteredVacancyResponse])
def get_filtered_unrejected(
        limit: int = Query(50, ge=1, le=200),
        db: Session = Depends(get_db)
):
    """Get LLM-filtered unrejected vacancies with raw data (title, company, url)"""

    query = db.query(
        FilteredVacancy, RawVacancy).join(
        RawVacancy, FilteredVacancy.source_id == RawVacancy.source_id
    )

    query = query.filter(FilteredVacancy.decision != "reject")
    results = query.order_by(FilteredVacancy.processed_at.desc()).limit(limit).all()

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
def get_filtered_rejected(
        limit: int = Query(50, ge=1, le=200),
        db: Session = Depends(get_db)
):
    """Get LLM-filtered rejected vacancies with raw data (title, company, url)"""

    query = db.query(FilteredVacancy, RawVacancy).join(
        RawVacancy, FilteredVacancy.source_id == RawVacancy.source_id
    )

    query = query.filter(FilteredVacancy.decision == "reject")
    results = query.order_by(FilteredVacancy.processed_at.desc()).limit(limit).all()

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
