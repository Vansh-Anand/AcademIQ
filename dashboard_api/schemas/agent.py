from pydantic import BaseModel
from typing import Dict, Any, Optional
from dashboard_api.schemas.pipeline import PipelineRunResponse

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    assistant_message: str
    provider: str
    tool_call: Optional[Dict[str, Any]] = None
    pipeline_result: Optional[PipelineRunResponse] = None
