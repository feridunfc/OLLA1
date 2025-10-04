
import pytest
from httpx import AsyncClient
from fastapi import status
from app.main import app

@pytest.mark.asyncio
async def test_register_login_me_happy_path():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/register", json={"username":"alice","password":"secret123"})
        assert r.status_code in (201, 200)
        r = await ac.post("/login", json={"username":"alice","password":"secret123"})
        assert r.status_code == 200
        token = r.json()["access_token"]
        r = await ac.get("/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["username"] == "alice"

@pytest.mark.asyncio
async def test_login_fail_and_me_unauthorized():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/login", json={"username":"bob","password":"x"})
        assert r.status_code == status.HTTP_401_UNAUTHORIZED
        r = await ac.get("/me")
        assert r.status_code == status.HTTP_401_UNAUTHORIZED
