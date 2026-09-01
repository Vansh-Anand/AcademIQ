from fastapi import APIRouter
from dashboard_api.schemas.status import SystemStatusResponse
from dashboard_api.services.status_service import StatusService

router = APIRouter()

@router.get("", response_model=SystemStatusResponse)
def get_system_status():
    """
    Get a comprehensive, truthful architectural status of the AcademIQ system.
    Dynamically checks database health and explicitly distinguishes between native, 
    simulated, and benchmark capabilities.
    """
    return StatusService.get_system_status()
