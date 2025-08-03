FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY scripts/ /app/scripts/

RUN pip install sentence-transformers qdrant-client pandas chardet

COPY src_med/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]