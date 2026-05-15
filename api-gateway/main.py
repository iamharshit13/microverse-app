import os
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware


USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8000")
RECOMMENDATION_SERVICE_URL = os.getenv("RECOMMENDATION_SERVICE_URL", "http://localhost:8001")

app = FastAPI(
    title="Microverse API Gateway",
    description="Thin gateway for the Microverse POC frontend.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def forward_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> Any:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.request(method, url, json=payload, params=params)
    except httpx.RequestError as error:
        raise HTTPException(status_code=502, detail=f"Upstream unavailable: {error}") from error

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    return response.json()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "api-gateway"}


@app.post("/api/user/register/")
async def register(request: Request) -> Any:
    payload = await request.json()
    return await forward_json("POST", f"{USER_SERVICE_URL}/api/user/register/", payload)


@app.post("/api/user/login/")
async def login(request: Request) -> Any:
    payload = await request.json()
    return await forward_json("POST", f"{USER_SERVICE_URL}/api/user/login/", payload)


@app.get("/api/recommendations/{user_id}")
async def recommendations(user_id: int, context: str | None = None, limit: int = 5) -> Any:
    params: dict[str, Any] = {"limit": limit}
    if context:
        params["context"] = context
    return await forward_json("GET", f"{RECOMMENDATION_SERVICE_URL}/recommendations/{user_id}", params=params)


@app.post("/api/events/interaction")
async def interaction(request: Request) -> Any:
    payload = await request.json()
    return await forward_json("POST", f"{RECOMMENDATION_SERVICE_URL}/events/interaction", payload)
