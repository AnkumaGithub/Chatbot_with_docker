FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install --upgrade setuptools==78.1.1

COPY src_bot/ .

CMD ["python", "main.py"]