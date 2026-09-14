import logging
import time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.base import get_async_db
from src.dtos.request_dto import TriageRequestDTO, ApproveDraftDTO
from src.dtos.response_dto import TriageResponseDTO
from src.services.triage_service import run_triage, approve_triage_draft
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

@router.post("/triage/{request_id}/approve", status_code=status.HTTP_200_OK)
async def approve_triage(
    request_id: int,
    payload: ApproveDraftDTO,
    db: AsyncSession = Depends(get_async_db),
    triage_repo: TriageRepository = Depends(get_triage_repository)
):
    logger.debug(f"Entering approve_triage route for request #{request_id}")
    try:
        res = await approve_triage_draft(request_id, payload.final_text.strip(), session=db, triage_repo=triage_repo)
        return res
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

