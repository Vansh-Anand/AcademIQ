from fastapi import APIRouter, HTTPException
from dashboard_api.schemas.experiments import ExperimentListResponse, ExperimentNormalized
from dashboard_api.services.experiments_service import ExperimentService

router = APIRouter()

@router.get("", response_model=ExperimentListResponse)
def get_experiments():
    """
    Get a summary of all benchmark experiments.
    """
    experiments = ExperimentService.get_all_experiments()
    return ExperimentListResponse(experiments=experiments)

@router.get("/{experiment_id}", response_model=ExperimentNormalized)
def get_experiment_detail(experiment_id: str):
    """
    Get the fully normalized detail of an experiment, including raw artifacts.
    """
    experiment = ExperimentService.get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return experiment
