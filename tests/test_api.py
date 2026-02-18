import pytest

@pytest.mark.asyncio
async def test_health_unauthorized(client):
    response = await client.get("/health")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_health_authorized(client, auth_headers):
    response = await client.get("/health", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_create_job_no_auth(client):
    response = await client.post("/jobs/", json={"template_name": "report_v1"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_create_job_invalid_template(client, auth_headers):
    response = await client.post(
        "/jobs/", 
        json={"template_name": "invalid_template"}, 
        headers=auth_headers
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_create_job_idempotency(client, auth_headers):
    # This test might fail if DB is not clean, but demonstrates the logic
    payload = {"template_name": "report_v1"}
    headers = {**auth_headers, "Idempotency-Key": "test-key-123"}
    
    # First request
    resp1 = await client.post("/jobs/", json=payload, headers=headers)
    assert resp1.status_code == 201
    job1 = resp1.json()
    
    # Second request with same key
    resp2 = await client.post("/jobs/", json=payload, headers=headers)
    assert resp2.status_code == 201
    job2 = resp2.json()
    
    assert job1["id"] == job2["id"]
