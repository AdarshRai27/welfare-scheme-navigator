# Use official lightweight Python image
FROM python:3.11-slim

# Set execution environmental flags
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Set container working directory path
WORKDIR /backend

# Install build dependencies, ffmpeg audio tool, and Tesseract OCR with Hindi packs
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    ffmpeg \
    tesseract-ocr \
    tesseract-ocr-hin \
    && rm -rf /var/lib/apt/lists/*

# Copy package requirements lists and run pip installs
COPY requirements.txt /backend/
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend project directories
COPY . /backend/

# Expose the API server port
EXPOSE 8000

# Run FastAPI app container using Uvicorn webserver bound to public interfaces
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
