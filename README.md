
# 🌐 microverse — Microservices Based Recommendation Platform

microverse is a complete microservices-based project built with Django, FastAPI, Redis, Kafka, Docker, Kubernetes, and a modern UI. It is designed for learning and hands-on experience in distributed system architecture and cloud-native application development.

---

## 🚀 Features

- 🧑‍💼 User Service — Django + DRF + JWT authentication
- 🎯 Recommendation Service — FastAPI + Redis + Kafka
- 📡 Kafka Messaging between services
- 🧠 Redis for caching recommendations
- 🌍 API Gateway to route traffic
- 🧪 Dockerized for local development
- ☸️ Kubernetes deployment ready
- 🔁 GitHub Actions for CI/CD
- 💻 Frontend for interaction and testing

---

## 🏗️ Project Structure

```
microverse/
├── services/
│   ├── user-service/               # Django app for auth & users
│   └── recommendation-service/    # FastAPI app for recs
├── kafka/                         # Kafka producers/consumers
├── redis/                         # Redis setup
├── frontend/                      # Web UI (HTML/React)
├── api-gateway/                   # NGINX or FastAPI as gateway
├── kubernetes/                    # YAML configs for K8s
├── .github/workflows/             # GitHub Actions for CI/CD
├── docker-compose.yml             # All-in-one orchestration
├── .gitignore
├── README.md
```

---

## ⚙️ Tech Stack

- Django & Django REST Framework
- FastAPI
- Kafka (via docker-compose)
- Redis
- Docker
- Kubernetes (Minikube/Kind)
- GitHub Actions
- React (or basic HTML/CSS for MVP)

---

## 📦 Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/microverse.git
cd microverse
```

2. Set up environment variables:

```bash
cp .env.example .env
```

3. Start all services using Docker:

```bash
docker-compose up --build
```

4. Open your browser:

- API Gateway: http://localhost:8080/
- Django Admin: http://localhost:8000/admin/
- Kafka UI (optional): http://localhost:9000

---

## ☸️ Kubernetes Deployment

1. Start Minikube:

```bash
minikube start
```

2. Apply manifests:

```bash
kubectl apply -f kubernetes/
```

3. Use port forwarding or Ingress to expose services.

---

## 🔁 CI/CD with GitHub Actions

A sample CI/CD pipeline is configured in:

```
.github/workflows/ci-cd.yaml
```

It includes:

- Linting and testing
- Docker build and push
- (Optional) Kubernetes deployment

---

## 🧪 Testing

- Django: `pytest` or `unittest`
- FastAPI: `pytest`, `requests`
- Kafka: Publish/consume message test
- Redis: Cache hit/miss test
- Postman for API testing

---

## 👥 Contributors

- AG
- HA
- SC
- SS
- ST

---

## 📃 License

This project is licensed under the MIT License.
