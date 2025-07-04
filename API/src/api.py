from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import os

app = FastAPI()
load_dotenv()
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL")

class GenerationRequest(BaseModel):
    prompt: str

@app.post("/generate")
async def generate_text_api(request: GenerationRequest):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                LLM_SERVICE_URL,
                json={"prompt": request.prompt},
                timeout=180.0
            )
        if response.status_code == 200:
            return response.json()
        return {"error": f"LLM service error: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
async def health_check():
    return {"status": "ok"}