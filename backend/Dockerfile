# ==============================================================================
# CivicVision AI — Backend Containerfile
# Python 3.11 Debian Slim base for full native PyTorch / Ultralytics support
# ==============================================================================
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install essential system dependencies for OpenCV and system builds
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt /app/requirements.txt

# Install official Linux CPU wheels for PyTorch, torchvision, and Ultralytics
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        torch==2.2.2 \
        torchvision==0.17.2 \
        --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir \
        ultralytics==8.1.42 && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy application source code
COPY backend /app/backend

# Ensure upload and weights directories exist with appropriate permissions
RUN mkdir -p /app/backend/uploads/original /app/backend/uploads/annotated

WORKDIR /app/backend

EXPOSE 8000

# Default command: launch uvicorn bound to 0.0.0.0
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
