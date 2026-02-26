# Docker Setup Guide

This guide will help you containerize and deploy the AI Virtual Interviewer platform using Docker.

## Prerequisites

- Docker installed ([https://www.docker.com/get-started](https://www.docker.com/get-started))
- Docker Compose installed (comes with Docker Desktop)
- Gemini API key
- MongoDB connection string or local MongoDB

## Project Structure

```
AI_INTERVIEWER/
├── backend/
│   ├── app/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   └── ...
├── frontend/
│   ├── src/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.js
│   └── ...
├── docker-compose.yml
└── .env
```

## Create Dockerfiles

### Backend Dockerfile

Create `backend/Dockerfile`:

```dockerfile
# Build stage
FROM python:3.10-slim as builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.10-slim

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Set environment to use installed packages
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create uploads directory
RUN mkdir -p uploads

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"

# Run application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile

Create `frontend/Dockerfile`:

```dockerfile
# Build stage
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Build application
RUN npm run build

# Runtime stage
FROM node:18-alpine

WORKDIR /app

# Install serve to run the app
RUN npm install -g serve

# Copy built application from builder
COPY --from=builder /app/dist ./dist

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})"

# Run application
CMD ["serve", "-s", "dist", "-l", "3000"]
```

## Docker Compose

Create `docker-compose.yml` in the project root:

```yaml
version: '3.8'

services:
  # MongoDB Database
  mongodb:
    image: mongo:6.0
    container_name: ai_interviewer_mongodb
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password123
      MONGO_INITDB_DB: ai_interviewer
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
      - mongodb_config:/data/configdb
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/test --quiet
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - ai_interviewer_network

  # Backend API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: ai_interviewer_backend
    environment:
      MONGODB_URL: mongodb://admin:password123@mongodb:27017/ai_interviewer
      MONGODB_DB: ai_interviewer
      GEMINI_API_KEY: ${GEMINI_API_KEY}
      SECRET_KEY: ${SECRET_KEY:-change-me-in-production}
      DEBUG: ${DEBUG:-False}
      CORS_ORIGINS: http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000
      ALGORITHM: HS256
      ACCESS_TOKEN_EXPIRE_MINUTES: 30
    ports:
      - "8000:8000"
    volumes:
      - ./backend/uploads:/app/uploads
    depends_on:
      mongodb:
        condition: service_healthy
    networks:
      - ai_interviewer_network
    restart: unless-stopped

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: ai_interviewer_frontend
    environment:
      VITE_API_URL: http://backend:8000
    ports:
      - "3000:3000"
    depends_on:
      - backend
    networks:
      - ai_interviewer_network
    restart: unless-stopped

volumes:
  mongodb_data:
  mongodb_config:

networks:
  ai_interviewer_network:
    driver: bridge
```

## Environment Setup

### Create `.env` file

Create `.env` in project root:

```env
# Backend Environment
GEMINI_API_KEY=your-gemini-api-key-here
SECRET_KEY=your-super-secret-key-change-in-production
DEBUG=False

# MongoDB
MONGODB_ROOT_USER=admin
MONGODB_ROOT_PASSWORD=password123

# Frontend
VITE_API_URL=http://localhost:8000
```

### Update Backend `.env.example`

Ensure `backend/.env.example` has all needed variables:

```env
# Database
MONGODB_URL=mongodb://admin:password123@mongodb:27017/ai_interviewer
MONGODB_DB=ai_interviewer

# JWT
SECRET_KEY=change-me-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Keys
GEMINI_API_KEY=${GEMINI_API_KEY}

# Server
DEBUG=False
APP_NAME=AI Virtual Interviewer

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000

# File Upload
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE=10485760
```

## Building and Running

### Build Images

```bash
# Build all images
docker-compose build

# Build specific service
docker-compose build backend
docker-compose build frontend
```

### Run Containers

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mongodb
```

### Stop Containers

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Accessing the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **MongoDB**: localhost:27017 (username: admin, password: password123)

## Database Access

### Using mongosh CLI

```bash
# Connect to MongoDB container
docker-compose exec mongodb mongosh -u admin -p password123 --authenticationDatabase admin

# Switch to database
use ai_interviewer

# View collections
show collections

# Query users
db.users.find()

# Query resumes
db.resumes.find()

# Query interviews
db.interviews.find()
```

### Using MongoDB Compass

1. Download MongoDB Compass
2. Connect to: `mongodb://admin:password123@localhost:27017`
3. Browse collections visually

## Health Checks

All services have health checks configured:

```bash
# Check container health
docker-compose ps

# Check specific container
docker inspect ai_interviewer_backend --format='{{.State.Health.Status}}'
```

## Production Deployment

### Multi-stage Builds

Both Dockerfiles use multi-stage builds to:
- Reduce final image size
- Improve build performance
- Keep production images lean

### Image Sizes

- Backend: ~200MB (Python + dependencies)
- Frontend: ~5MB (static files only)
- MongoDB: ~500MB

### Optimization Tips

1. **Use .dockerignore:**

```
# backend/.dockerignore
__pycache__
*.pyc
*.pyo
.env
.pytest_cache
tests
.git

# frontend/.dockerignore
node_modules
dist
.git
.gitignore
README.md
```

2. **Use specific image versions:**

```dockerfile
FROM python:3.10-slim
FROM node:18-alpine
FROM mongo:6.0
```

3. **Regular cleanup:**

```bash
# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Remove unused networks
docker network prune
```

## Troubleshooting

### MongoDB Connection Issues

```bash
# Check MongoDB logs
docker-compose logs mongodb

# Verify network connectivity
docker network inspect ai_interviewer_network
```

### Backend Connection Issues

```bash
# Check backend logs
docker-compose logs backend

# Test API connectivity
curl http://localhost:8000/health
```

### Frontend Build Issues

```bash
# Rebuild frontend
docker-compose build --no-cache frontend

# Clear volumes and rebuild
docker-compose down -v
docker-compose up -d
```

### Common Issues & Solutions

**Issue: "MongoDB could not connect"**
```bash
# Solution: Ensure MongoDB service is healthy
docker-compose ps
# or wait longer for MongoDB to start
```

**Issue: "Backend cannot reach MongoDB"**
```bash
# Solution: Check MONGODB_URL environment variable
docker-compose exec backend env | grep MONGODB_URL
```

**Issue: "Port 8000 already in use"**
```bash
# Solution: Use different port in docker-compose.yml
# Change ports: "8001:8000" instead of "8000:8000"
```

**Issue: "Files not persisting after container restart"**
```bash
# Solution: Ensure volumes are properly configured
# Check: docker-compose exec backend ls -la uploads/
```

## Deployment to Cloud

### AWS ECS

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name ai-interviewer

# Push images to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com

docker tag ai_interviewer_backend <account-id>.dkr.ecr.<region>.amazonaws.com/ai-interviewer-backend:latest
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/ai-interviewer-backend:latest
```

### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/<project>/ai-interviewer-backend

# Deploy
gcloud run deploy ai-interviewer-backend --image gcr.io/<project>/ai-interviewer-backend
```

### Azure Container Instances

```bash
# Login to ACR
az acr login --name <registry-name>

# Build and push
az acr build --registry <registry-name> --image ai-interviewer-backend:latest .

# Deploy
az container create --resource-group <group> --name ai-interviewer --image <registry>.azurecr.io/ai-interviewer-backend:latest
```

## Docker Compose Best Practices

1. **Use explicit image versions** - Not `latest`
2. **Set resource limits:**

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

3. **Use restart policies:**

```yaml
services:
  backend:
    restart: unless-stopped
```

4. **Implement logging:**

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Monitoring & Logging

### Docker Stats

```bash
# Monitor container resource usage
docker stats

# Monitor specific container
docker stats ai_interviewer_backend
```

### Log Aggregation

```bash
# Save logs to file
docker-compose logs > logs.txt

# Follow logs in real-time
docker-compose logs -t -f
```

## Backup & Restore

### Backup MongoDB

```bash
# Create backup
docker-compose exec mongodb mongodump --out /data/backup

# Or
docker exec ai_interviewer_mongodb mongodump -u admin -p password123 --authenticationDatabase admin --out /backup
```

### Restore MongoDB

```bash
docker-compose exec mongodb mongorestore /data/backup

# Or copy backup and restore
docker cp backup ai_interviewer_mongodb:/
docker exec ai_interviewer_mongodb mongorestore /backup
```

## Cleaning Up

```bash
# Remove all containers
docker-compose down

# Remove all volumes (careful!)
docker-compose down -v

# Remove all images
docker-compose down --rmi all
```

---

Happy containerizing! 🐳
