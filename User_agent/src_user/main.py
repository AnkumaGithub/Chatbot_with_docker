from fastapi import FastAPI
from pydantic import BaseModel
from diagnostic_graph import DiagnosticGraph
import uvicorn
import os

app = FastAPI()

MEDICAL_AGENT_URL = os.getenv("MEDICAL_AGENT_URL", "http://medical-agent-service:8000")
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://api-service:8000")

diagnostic_graph = DiagnosticGraph(MEDICAL_AGENT_URL, LLM_SERVICE_URL)


class StartRequest(BaseModel):
    user_id: int


class StartResponse(BaseModel):
    session_id: str
    question: str
    status: str


class ContinueRequest(BaseModel):
    session_id: str
    user_id: int
    user_input: str


class ContinueResponse(BaseModel):
    session_id: str
    response: str
    status: str


sessions = {}


@app.post("/diagnose/start")
async def start_diagnosis(request: StartRequest):
    session = diagnostic_graph.start_session(request.user_id)
    sessions[session["session_id"]] = session
    return StartResponse(
        session_id=session["session_id"],
        question="Опишите ваши симптомы:",
        status="in_progress"
    )


@app.post("/diagnose/continue")
async def continue_diagnosis(request: ContinueRequest):
    session = sessions.get(request.session_id)
    if not session:
        return {"error": "Session not found"}

    updated_state = await diagnostic_graph.process_input(session, request.user_input)
    sessions[request.session_id] = updated_state

    if updated_state.get("final_diagnosis"):
        response = updated_state["final_diagnosis"]
        status = "completed"
    else:
        response = updated_state["current_question"]
        status = "in_progress"

    return ContinueResponse(
        session_id=request.session_id,
        response=response,
        status=status
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)