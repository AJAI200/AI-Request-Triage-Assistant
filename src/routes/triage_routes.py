import logging
import time
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.base import get_async_db
from src.dtos.request_dto import TriageRequestDTO
from src.dtos.response_dto import TriageResponseDTO
from src.services.triage_service import run_triage, get_triage_by_id, list_triaged_requests
from src.repositories.triage_repository import TriageRepository, get_triage_repository

logger = logging.getLogger("triage_assistant.triage_routes")

router = APIRouter(tags=["Triage"])

@router.post("/triage", response_model=TriageResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_triage(
    payload: TriageRequestDTO,
    db: AsyncSession = Depends(get_async_db),
    triage_repo: TriageRepository = Depends(get_triage_repository)
):
    logger.debug("Entering create_triage route")
    start_time = time.time()
    if not payload.text or not payload.text.strip():
        logger.warning("Empty request text provided to /triage")
        logger.debug("Exiting create_triage route with HTTP 400")
        raise HTTPException(status_code=400, detail="Request text cannot be empty.")
    
    result = await run_triage(payload.text.strip(), session=db, triage_repo=triage_repo, process_time_ms=None)
    elapsed_ms = round((time.time() - start_time) * 1000, 2)
    result["process_time_ms"] = elapsed_ms
    logger.debug(f"Exiting create_triage route successfully in {elapsed_ms}ms")
    return TriageResponseDTO(**result)

@router.get("/triage/{request_id}", response_model=TriageResponseDTO, status_code=status.HTTP_200_OK)
async def get_triage(
    request_id: int,
    db: AsyncSession = Depends(get_async_db),
    triage_repo: TriageRepository = Depends(get_triage_repository)
):
    logger.debug(f"Entering get_triage route for request_id: {request_id}")
    result = await get_triage_by_id(request_id, session=db, triage_repo=triage_repo)
    if not result:
        logger.warning(f"Triage request #{request_id} not found")
        logger.debug("Exiting get_triage route with HTTP 404")
        raise HTTPException(status_code=404, detail=f"Triage request #{request_id} not found.")
    logger.debug("Exiting get_triage route successfully")
    return TriageResponseDTO(**result)

@router.get("/triage", response_model=List[TriageResponseDTO], status_code=status.HTTP_200_OK)
async def list_triages(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_async_db),
    triage_repo: TriageRepository = Depends(get_triage_repository)
):
    logger.debug(f"Entering list_triages route with limit={limit}")
    results = await list_triaged_requests(limit=limit, session=db, triage_repo=triage_repo)
    logger.debug(f"Exiting list_triages route with {len(results)} items")
    return [TriageResponseDTO(**r) for r in results]
