from fastapi import FastAPI
from pydantic import BaseModel
from llm import generate_text
import torch

app = FastAPI()
device = torch.device("cpu")
print(f"Using device: {device}")

class GenerationRequest(BaseModel):
    prompt: str

@app.post("/generate")
async def generate_endpoint(request: GenerationRequest):
    try:
        result = generate_text(request.prompt, device)
        return {"generated_text": result}
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
async def health_check():
    return {"status": "ok", "device": str(device)}