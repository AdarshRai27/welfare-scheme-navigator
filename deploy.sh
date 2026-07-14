#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

echo "============================================================"
echo "🚀 STARTING AGENTIC SCHEME NAVIGATOR DEPLOYMENT PIPELINE"
echo "============================================================"

# 1. Verify that the production environment configuration exists
if [ ! -f "backend/.env" ]; then
    echo "❌ Error: backend/.env file not found!"
    echo "Please copy backend/.env.example to backend/.env and populate it with your Meta/Bhashini keys."
    exit 1
fi

# 2. Source configuration parameters
export $(grep -v '^#' backend/.env | xargs)

# 3. Build and spawn container services in detached mode
echo "🐳 Building and starting Docker services..."
docker compose -f infra/docker-compose.yml up --build -d

# 4. Display service statuses
echo "⏳ Service containers deployed. Status check:"
docker compose -f infra/docker-compose.yml ps

echo "============================================================"
echo "✅ DEPLOYMENT PIPELINE RUN COMPLETED"
echo "FastAPI API endpoint: http://localhost:8000"
echo "WhatsApp webhook trigger path: http://<your-public-ip>:8000/webhook/whatsapp"
echo "============================================================"
