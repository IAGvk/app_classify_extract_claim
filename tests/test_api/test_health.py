"""Tests for GET /health."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from httpx import AsyncClient


async def test_health_returns_200(async_client: AsyncClient) -> None:
    """Health probe should return HTTP 200."""
    response = await async_client.get("/health")
    assert response.status_code == 200


async def test_health_body_has_status_ok(async_client: AsyncClient) -> None:
    """Health probe response body must include ``status: ok``."""
    response = await async_client.get("/health")
    body = response.json()
    assert body["status"] == "ok"


async def test_health_body_has_version(async_client: AsyncClient) -> None:
    """Health probe response body must include a non-empty version string."""
    response = await async_client.get("/health")
    body = response.json()
    assert body.get("version"), "Expected non-empty version in /health response"
