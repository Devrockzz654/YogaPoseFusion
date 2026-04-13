FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860 \
    MPLCONFIGDIR=/tmp/matplotlib

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements-deploy.txt /tmp/requirements-deploy.txt
RUN pip install --no-cache-dir -r /tmp/requirements-deploy.txt

COPY backend /app/backend

WORKDIR /app/backend

EXPOSE 7860

CMD ["sh", "-c", "uvicorn inference:app --host 0.0.0.0 --port ${PORT:-7860}"]
