from fastapi import APIRouter, HTTPException

from dashboard_api.schemas.agent import ChatRequest, ChatResponse
from dashboard_api.services.agent_service import AgentService

router = APIRouter()
service = AgentService()

@router.post("/chat", response_model=ChatResponse)
def chat_with_agent(request: ChatRequest):
    try:
        agent_response, pipeline_result = service.process_chat(request.message)
        return ChatResponse(
            assistant_message=agent_response.assistant_message,
            provider=agent_response.provider,
            tool_call=agent_response.tool_call,
            pipeline_result=pipeline_result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
