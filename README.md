# microverse

**microverse** is a cloud-native microservices recommendation platform built with Django, FastAPI, PostgreSQL, Kafka, Redis, Docker, and Kubernetes-oriented project structure. The project now includes an AI recommendation layer that uses event-driven user signals, Redis-backed feature storage, vector-style item ranking, persistent interaction history, and feedback-based personalization.

The goal is to practice distributed systems architecture while also building toward modern AI product patterns such as personalization, feature stores, embeddings, semantic retrieval, ranking models, and eventually LLM-powered recommendation explanations.

## Current Architecture

```text
Client / Frontend
      |
      v
API Gateway
      |
      +--> User Service - Django + DRF + JWT
      |       |
      |       v
      |   Kafka topic: user-events
      |
      +--> Recommendation AI Service - FastAPI
              |
              +--> Kafka consumer for user lifecycle events
              +--> Redis feature store and recommendation cache
              +--> PostgreSQL interaction and recommendation history
              +--> Hybrid vector ranking engine
```

## What Is Implemented

- **User Service**
  - Django + Django REST Framework service.
  - User registration endpoint at `/api/user/register/`.
  - Login endpoint at `/api/user/login/`.
  - JWT access and refresh token generation using SimpleJWT.
  - Kafka event publishing when a user is created.

- **Recommendation AI Service**
  - FastAPI service running on port `8001`.
  - Kafka consumer listening to the `user-events` topic.
  - Redis-backed user profile storage.
  - Redis-backed recommendation cache with TTL.
  - PostgreSQL persistence for feedback interactions and recommendation snapshots.
  - Hybrid recommendation ranking using:
    - user feature vectors,
    - item vectors,
    - cosine similarity,
    - popularity priors,
    - contextual boosts,
    - lightweight exploration scoring.
  - Feedback endpoint that updates user vectors from interaction events.

- **Infrastructure**
  - Docker Compose for PostgreSQL, Kafka, Zookeeper, Redis, Django, FastAPI, API gateway, and frontend.
  - Dockerfiles for the user and recommendation services.
  - Kubernetes, frontend, gateway, and CI/CD folders are scaffolded for future work.

## AI Layer

The first integrated AI capability is a **hybrid recommendation engine** inside `services/recommendation-service/main.py`.

It currently uses a small in-memory catalog with hand-authored vectors. This keeps the MVP dependency-light while still modeling the architecture used by production recommendation systems:

- **Feature vectors** represent user interests and item attributes.
- **Cosine similarity** performs semantic-style matching.
- **Redis** acts as both a low-latency feature store and inference cache.
- **PostgreSQL** stores durable user auth data, feedback events, and recommendation snapshots.
- **Kafka** streams user lifecycle events into the recommendation service.
- **Online learning loop** updates user profiles from interaction feedback.

### Recommendation Endpoints

```http
GET /health
```

Returns service health.

```http
GET /recommendations/{user_id}
GET /recommendations/{user_id}?context=genai&limit=3
```

Returns ranked personalized recommendations.

```http
POST /events/interaction
Content-Type: application/json

{
  "user_id": 1,
  "item_id": "llm-prompt-engineering",
  "event_type": "like",
  "rating": 5,
  "context": "genai"
}
```

Records a user interaction and updates the profile vector.

## AI Technologies To Integrate Next

These are natural upgrades for the project architecture:

1. **Embedding Models**
   - Use Sentence Transformers, OpenAI embeddings, or Hugging Face models to generate real item and user embeddings.
   - Replace hand-authored vectors with learned semantic vectors.

2. **Vector Database**
   - Add Qdrant, Weaviate, Milvus, Pinecone, or pgvector.
   - Store item embeddings and perform approximate nearest neighbor search.

3. **RAG-Based Recommendation Explanations**
   - Use retrieval augmented generation to explain why an item was recommended.
   - Example: "Recommended because you liked Kafka event streaming and recently explored vector databases."

4. **LLM Personalization Agent**
   - Add an LLM service that rewrites recommendations into natural language.
   - Generate onboarding questions, learning plans, or personalized summaries.

5. **Ranking Model**
   - Train a learning-to-rank model using click, like, completion, and rating events.
   - Candidate technologies: LightGBM LambdaMART, XGBoost ranking, TensorFlow Recommenders, or PyTorch.

6. **Real-Time Feature Store**
   - Expand Redis into an online feature store.
   - Track rolling counters such as recent clicks, preferred categories, session intent, and recency-weighted interests.

7. **MLOps Pipeline**
   - Add MLflow or Weights & Biases for experiment tracking.
   - Add model registry, offline evaluation, A/B testing, and drift monitoring.

8. **Moderation and Safety Layer**
   - Add content filtering for generated explanations.
   - Add policy checks before recommendations are shown.

## Local Development

Start the stack:

```bash
docker compose up --build
```

Service URLs:

- Frontend POC: `http://localhost:3000`
- API Gateway: `http://localhost:8080`
- User Service: `http://localhost:8000/api/user/`
- Django Admin: `http://localhost:8000/admin/`
- Recommendation AI Service: `http://localhost:8001/`
- Recommendation API Docs: `http://localhost:8001/docs`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- Kafka inside Docker: `kafka:9092`
- Kafka from host tools: `localhost:29092`

## Working POC Demo

The fastest demo path is:

1. Start everything with `docker compose up --build`.
2. Open `http://localhost:3000`.
3. Register the prefilled demo user.
4. Wait a moment for the user event to move through Kafka.
5. Review the ranked recommendation cards.
6. Click `View`, `Like`, or `Complete` on an item.
7. Notice the user profile vector and next recommendations update.

The POC proves the main loop:

```text
Frontend -> API Gateway -> Django User Service -> PostgreSQL + Kafka -> FastAPI Recommendation AI Service -> Redis + PostgreSQL -> Frontend
```

## PostgreSQL Persistence

PostgreSQL runs inside Docker, so you do not need to install it locally. The Compose stack creates a persistent Docker volume named `postgres_data`.

The user service stores Django auth tables in PostgreSQL when running through Docker. The recommendation service creates these tables on startup:

- `recommendation_interactions` for feedback events such as `view`, `like`, and `complete`.
- `recommendation_snapshots` for ranked recommendation lists generated by the model.

Reset all local Postgres data only when you intentionally want a clean database:

```bash
docker compose down -v
```

## Local Smoke Tests

The recommendation engine has a lightweight standard-library test suite that does not require Docker:

```bash
python3 -m unittest tests/test_recommendation_service.py
```

It checks catalog metadata, ranking order, feedback-based profile updates, and Redis-cache serialization with a fake in-memory Redis client.

## Example Flow

1. Register a user through the Django user service.
2. The user service publishes a `user_created` event to Kafka.
3. The recommendation service consumes the event.
4. The service creates a Redis-backed user profile vector.
5. The AI ranker generates recommendations and caches them.
6. Frontend or API clients fetch recommendations through `/recommendations/{user_id}`.
7. Interaction events update the profile vector for future personalization.

## Project Structure

```text
microverse/
├── services/
│   ├── user-service/                # Django auth and user event producer
│   └── recommendation-service/      # FastAPI recommendation AI service
│       └── catalog.json             # Seed recommendation catalog
├── kafka/                           # Kafka script placeholders
├── redis/                           # Redis config placeholder
├── frontend/                        # Static POC UI served by Nginx
├── api-gateway/                     # FastAPI gateway for frontend calls
├── kubernetes/                      # Kubernetes manifest placeholders
├── .github/workflows/               # CI/CD scaffold
├── docker-compose.yml
├── microverse_setup_guide.md
└── README.md
```

## Technical Roadmap

- Implement the API gateway with route forwarding to user and recommendation services.
- Build a frontend for login, recommendation display, and feedback capture.
- Add a real vector database for embedding search.
- Replace static vectors with generated embeddings.
- Add offline evaluation metrics such as precision@k, recall@k, NDCG, and MAP.
- Add Kubernetes deployments, services, config maps, and ingress.
- Add CI/CD to run tests, build images, and publish containers.
- Add observability with Prometheus, Grafana, OpenTelemetry, and structured logs.

## License

MIT
