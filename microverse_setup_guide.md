
# 🧠 Project Setup Instructions: microverse

This guide will help you build a complete microservices-based recommendation system using Django, FastAPI, Kafka, Redis, Docker, and Kubernetes.

---

## 📋 Prerequisites

Make sure you have the following installed:

- Python 3.10+
- Node.js + npm
- Docker Desktop (with WSL2 on Windows)
- Minikube or Kind (for Kubernetes)
- Git
- VS Code (optional)

---

## 🏗 Project Structure

```
microverse/
├── services/
│   ├── user-service/
│   └── recommendation-service/
├── kafka/
├── redis/
├── frontend/
├── api-gateway/
├── kubernetes/
├── .github/workflows/
├── .env.example
├── docker-compose.yml
├── .gitignore
├── README.md
```

---

## 👤 Step 1: User Service (Django + DRF)

```bash
cd microverse/services/user-service
python -m venv env
source env/bin/activate
pip install django djangorestframework
django-admin startproject user_app .
python manage.py startapp users
```

- Add models for user profile
- Add JWT authentication
- Expose login/register APIs

**Dockerfile**:

```Dockerfile
FROM python:3.10
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

---

## 🤖 Step 2: Recommendation Service (FastAPI)

```bash
cd ../recommendation-service
python -m venv env
source env/bin/activate
pip install fastapi uvicorn redis kafka-python
```

- Create a FastAPI app
- Listen to Kafka events
- Query Redis and generate recommendations

---

## 📡 Step 3: Kafka

Use Docker Compose for Kafka + Zookeeper setup:

```yaml
services:
  zookeeper:
    image: confluentinc/cp-zookeeper
  kafka:
    image: confluentinc/cp-kafka
```

- Django → sends events to Kafka
- FastAPI → consumes events from Kafka

---

## ⚡ Step 4: Redis

- Runs as a separate container
- FastAPI stores & reads cached recommendations
- Add Redis connection logic

---

## 💻 Step 5: Frontend

- Create login form
- Display recommendations after login
- Use HTML/React + Bootstrap

---

## 🌐 Step 6: API Gateway

- Use FastAPI or NGINX
- Forward routes:
  - /api/user/ → user-service
  - /api/recommend/ → recommendation-service

---

## 🐳 Step 7: Docker Compose

```bash
docker-compose up --build
```

- Include all services in one file
- Set up environment variables using `.env`

---

## ☸️ Step 8: Kubernetes Deployment

```bash
kubectl apply -f kubernetes/
```

- Create Deployment & Service files for:
  - Django
  - FastAPI
  - Kafka, Redis
  - Gateway
- Use Ingress Controller for external access

---

## 🔁 Step 9: CI/CD (GitHub Actions)

`.github/workflows/ci-cd.yaml`:

```yaml
name: CI/CD
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: docker build -t user-service ./services/user-service
```

---

## ✅ Step 10: Testing

- Use `pytest` for Django and FastAPI
- Test Kafka event publishing/consumption
- Use Postman for manual API testing

---

## 📖 Documentation

- Complete README.md with:
  - Setup instructions
  - Architecture diagram
  - Contributors
  - Tech stack

---

## 🎁 Bonus

- Add Prometheus + Grafana for monitoring
- Use Horizontal Pod Autoscaler in Kubernetes

---

Built with ❤️ by Team AG, HA, SC, SS, ST
