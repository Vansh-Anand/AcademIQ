from fastapi import APIRouter, HTTPException

from dashboard_api.schemas.evidence import SessionListResponse, SessionDetailResponse, VerifyResponse
from dashboard_api.services.evidence_service import EvidenceService

router = APIRouter()
service = EvidenceService()

@router.get("/sessions", response_model=SessionListResponse)
def list_sessions():
    return service.get_sessions()

@router.get("/session/{session_id}", response_model=SessionDetailResponse)
def get_session_chain(session_id: str):
    detail = service.get_session_chain(session_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Session not found")
    return detail

@router.post("/session/{session_id}/verify", response_model=VerifyResponse)
def verify_session(session_id: str):
    return service.verify_session(session_id)
