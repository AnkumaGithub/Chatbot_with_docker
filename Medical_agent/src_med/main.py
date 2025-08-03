from typing import List
from fastapi import FastAPI
from pydantic import BaseModel
from agent import MedicalAgent
import uvicorn

app = FastAPI()
medical_agent = MedicalAgent()

class SearchRequest(BaseModel):
    symptoms: List[str]

class SearchResponse(BaseModel):
    diseases: List[dict]

class QuestionRequest(BaseModel):
    top_disease: dict
    confirmed_symptoms: List[str]

class QuestionResponse(BaseModel):
    question: str

class DiagnosisRequest(BaseModel):
    top_disease: dict
    confirmed_symptoms: List[str]

class DiagnosisResponse(BaseModel):
    diagnosis: str

@app.post("/search_diseases")
async def search_diseases(request: SearchRequest):
    diseases = medical_agent.search_diseases(request.symptoms)
    return SearchResponse(diseases=diseases)

@app.post("/generate_question")
async def generate_question(request: QuestionRequest):
    question = medical_agent.generate_question(
        request.top_disease,
        request.confirmed_symptoms
    )
    return QuestionResponse(question=question)

@app.post("/make_diagnosis")
async def make_diagnosis(request: DiagnosisRequest):
    diagnosis = medical_agent.make_diagnosis(
        request.top_disease,
        request.confirmed_symptoms
    )
    return DiagnosisResponse(diagnosis=diagnosis)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)