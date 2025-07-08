FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y librdkafka-dev build-essential

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install --upgrade setuptools==78.1.1

COPY src_api/ .

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]