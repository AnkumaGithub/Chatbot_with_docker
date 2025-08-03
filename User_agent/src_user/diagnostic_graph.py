from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Optional
import httpx
import uuid
import json
import re


class DiagnosticState(TypedDict):
    session_id: str
    user_id: int
    symptoms: List[str]
    confirmed_symptoms: List[str]
    possible_diseases: List[Dict]
    current_question: Optional[str]
    final_diagnosis: Optional[str]


class DiagnosticGraph:
    def __init__(self, medical_agent_url: str, llm_service_url: str):
        self.medical_agent_url = medical_agent_url
        self.llm_service_url = llm_service_url
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        workflow = StateGraph(DiagnosticState)

        workflow.add_node("extract_symptoms", self.extract_symptoms)
        workflow.add_node("search_diseases", self.search_diseases)
        workflow.add_node("generate_question", self.generate_question)
        workflow.add_node("make_diagnosis", self.make_diagnosis)

        workflow.set_entry_point("extract_symptoms")
        workflow.add_edge("extract_symptoms", "search_diseases")
        workflow.add_conditional_edges(
            "search_diseases",
            self.should_continue,
            {
                "question": "generate_question",
                "diagnose": "make_diagnosis",
                "end": END
            }
        )
        workflow.add_edge("generate_question", END)
        workflow.add_edge("make_diagnosis", END)

        return workflow.compile()

    async def extract_symptoms(self, state: DiagnosticState):
        user_input = state["symptoms"][-1]

        prompt = (
            "Ты медицинский ассистент. Извлеки симптомы из текста пациента.\n"
            "Верни ТОЛЬКО JSON в формате: {\"symptoms\": [\"симптом1\", \"симптом2\"]}\n"
            "Не добавляй пояснений, только чистый JSON.\n"
            f"Текст пациента: {user_input}"
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.llm_service_url}/generate",
                json={"prompt": prompt},
                timeout=30.0
            )

        if response.status_code != 200:
            return {"confirmed_symptoms": state["confirmed_symptoms"]}

        try:
            data = response.json()
            result = json.loads(data["generated_text"])
            return {"confirmed_symptoms": list(set(state["confirmed_symptoms"] + result["symptoms"]))}
        except json.JSONDecodeError:
            try:
                json_str = re.search(r'\{.*\}', data["generated_text"], re.DOTALL)
                if json_str:
                    result = json.loads(json_str.group())
                    return {"confirmed_symptoms": list(set(state["confirmed_symptoms"] + result["symptoms"]))}
            except:
                pass

        try:
            symptoms_text = data["generated_text"].split('[')[1].split(']')[0]
            symptoms = [s.strip().strip('"') for s in symptoms_text.split(",")]
            return {"confirmed_symptoms": list(set(state["confirmed_symptoms"] + symptoms))}
        except:
            return {"confirmed_symptoms": state["confirmed_symptoms"]}

    async def search_diseases(self, state: DiagnosticState):
        if not state["confirmed_symptoms"]:
            return {"possible_diseases": []}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.medical_agent_url}/search_diseases",
                json={"symptoms": state["confirmed_symptoms"]}
            )
            if response.status_code == 200:
                data = response.json()
                return {"possible_diseases": data["diseases"]}
            else:
                return {"possible_diseases": []}

    async def generate_question(self, state: DiagnosticState):
        top_disease = state["possible_diseases"][0] if state["possible_diseases"] else None

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.medical_agent_url}/generate_question",
                json={
                    "top_disease": top_disease,
                    "confirmed_symptoms": state["confirmed_symptoms"]
                }
            )
            if response.status_code == 200:
                data = response.json()
                return {"current_question": data["question"]}
            else:
                return {"current_question": "Опишите ваши симптомы подробнее?"}

    async def make_diagnosis(self, state: DiagnosticState):
        top_disease = state["possible_diseases"][0] if state["possible_diseases"] else None

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.medical_agent_url}/make_diagnosis",
                json={
                    "top_disease": top_disease,
                    "confirmed_symptoms": state["confirmed_symptoms"]
                }
            )
            if response.status_code == 200:
                data = response.json()
                return {"final_diagnosis": data["diagnosis"]}
            else:
                return {"final_diagnosis": "Не удалось сформулировать диагноз"}

    def should_continue(self, state: DiagnosticState):
        if state.get("final_diagnosis") is not None:
            return "end"

        if len(state.get("confirmed_symptoms", [])) >= 5 or not state["possible_diseases"]:
            return "diagnose"

        return "question"

    def start_session(self, user_id: int):
        session_id = str(uuid.uuid4())
        initial_state = DiagnosticState(
            session_id=session_id,
            user_id=user_id,
            symptoms=[],
            confirmed_symptoms=[],
            possible_diseases=[],
            current_question=None,
            final_diagnosis=None
        )
        return initial_state

    async def process_input(self, state: DiagnosticState, user_input: str):
        state["symptoms"].append(user_input)
        return await self.workflow.ainvoke(state)