import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_endpoint(client: AsyncClient):
    """Tests /api/v1/health API endpoint."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["api_version"] == "v1"


@pytest.mark.asyncio
async def test_deep_health_check_endpoint(client: AsyncClient):
    """Tests /api/v1/health/deep API endpoint."""
    response = await client.get("/api/v1/health/deep")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["database"] == "healthy"
    assert "embedding_backend" in data
    assert "metrics" in data
