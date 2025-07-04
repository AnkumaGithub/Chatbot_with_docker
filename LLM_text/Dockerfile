FROM --platform=linux/arm64 python:3.10-slim

WORKDIR /app

# Установка зависимостей для PyTorch и MPS
RUN apt-get update && apt-get install -y \
    libopenblas-dev \
    gfortran \
    libomp-dev \
    && rm -rf /var/lib/apt/lists/*

# Установка PyTorch с поддержкой MPS
RUN pip install --no-cache-dir \
    torch \
    torchvision \
    torchaudio \
    --index-url https://download.pytorch.org/whl/nightly/cpu

# Установка остальных зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Проверяем доступность MPS при запуске
CMD ["sh", "-c", "python -c 'import torch; print(\"MPS available:\", torch.backends.mps.is_available())' && uvicorn server:app --host 0.0.0.0 --port 8000"]