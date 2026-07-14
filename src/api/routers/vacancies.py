from json import loads, JSONDecodeError
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from src.storage.db import get_db
from src.storage.models import RawVacancy, FilteredVacancy
from src.api.schemas import VacancyResponse, FilteredVacancyResponse

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
def get_raw_vacancies(
        pagination: dict = Depends(pagination_parameters),
        db: Session = Depends(get_db)
):
    """Get raw (unfiltered) vacancies"""

    skip, limit = pagination["skip"], pagination["limit"]
    offset = skip * limit
    query = db.query(RawVacancy)
    return query.order_by(RawVacancy.fetched_at.desc()).limit(limit).offset(offset).all()


@router.get("/unrejected", response_model=list[FilteredVacancyResponse])
def get_filtered_unrejected(
        pagination: dict = Depends(pagination_parameters),
        db: Session = Depends(get_db)
):
    """Get LLM-filtered unrejected vacancies with raw data (title, company, url)"""

    skip, limit = pagination["skip"], pagination["limit"]
    offset = skip * limit
    query = db.query(
        FilteredVacancy, RawVacancy).join(
        RawVacancy, FilteredVacancy.source_id == RawVacancy.source_id
    )

    query = query.filter(FilteredVacancy.decision != "reject")
    results = query.order_by(FilteredVacancy.processed_at.desc()).limit(limit).offset(offset).all()

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
        pagination: dict = Depends(pagination_parameters),
        db: Session = Depends(get_db)
):
    """Get LLM-filtered rejected vacancies with raw data (title, company, url)"""

    skip, limit = pagination["skip"], pagination["limit"]
    offset = skip * limit
    query = db.query(FilteredVacancy, RawVacancy).join(
        RawVacancy, FilteredVacancy.source_id == RawVacancy.source_id
    )

    query = query.filter(FilteredVacancy.decision == "reject")
    results = query.order_by(FilteredVacancy.processed_at.desc()).limit(limit).offset(offset).all()

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
