# Multi-stage build for BankIQ+ Platform
FROM node:18-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install --only=production
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim AS backend

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./

# Copy frontend build
COPY --from=frontend-build /app/frontend/build ./static

# Create non-root user
RUN useradd -m -u 1000 bankiq
USER bankiq

EXPOSE 8001

# Start Flask with static file serving
CMD ["python", "app.py"]