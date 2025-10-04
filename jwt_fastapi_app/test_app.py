
import pytest
from httpx import AsyncClient
from fastapi import status
from app import app

@pytest.mark.asyncio
async def test_full_flow():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/register", params={"username":"alice","password":"s3cr3t"})
        assert r.status_code == 200
        r = await ac.post("/login", data={"username":"alice","password":"s3cr3t"})
        assert r.status_code == 200
        token = r.json()["access_token"]
        r = await ac.get("/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["username"] == "alice"

@pytest.mark.asyncio
async def test_me_unauthorized():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/me")
        assert r.status_code == status.HTTP_401_UNAUTHORIZED
