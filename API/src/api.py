from fastapi import FastAPI
from pydantic import BaseModel
from LLM_text.src.llm import generate_text
import torch
app = FastAPI()

if torch.cuda.is_available():
    device = torch.device("cuda:0")
elif torch.backends.mps.is_available():
    device = torch.device("mps:0")
else:
    device = torch.device("cpu")

class GenerationRequest(BaseModel):
    prompt: str

@app.post("/generate")
async def generate_text_api(request: GenerationRequest):
    try:
        print(device)
        result = generate_text(request.prompt, device)
        return {"generated_text": result}
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
async def health_check():
    return {"status": "ok", "device": str(device)}