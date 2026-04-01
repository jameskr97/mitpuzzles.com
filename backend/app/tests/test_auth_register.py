"""tests for authentication — registration, login, and user management."""

import pytest
from sqlalchemy import select

from app.modules.authentication import User


class TestRegistration:
    @pytest.mark.asyncio
    async def test_register_success(self, seeded_client):
        client, db = seeded_client
        response = await client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, seeded_client):
        client, db = seeded_client
        await client.post("/api/auth/register", json={
            "username": "user1", "email": "dupe@example.com", "password": "password123",
        })
        response = await client.post("/api/auth/register", json={
            "username": "user2", "email": "dupe@example.com", "password": "password123",
        })
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, seeded_client):
        client, db = seeded_client
        await client.post("/api/auth/register", json={
            "username": "dupe", "email": "u1@example.com", "password": "password123",
        })
        response = await client.post("/api/auth/register", json={
            "username": "dupe", "email": "u2@example.com", "password": "password123",
        })
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, seeded_client):
        client, _ = seeded_client
        response = await client.post("/api/auth/register", json={
            "username": "user", "email": "not-an-email", "password": "password123",
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_password(self, seeded_client):
        client, _ = seeded_client
        response = await client.post("/api/auth/register", json={
            "username": "user", "email": "test@example.com",
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_password_is_hashed(self, seeded_client):
        client, db = seeded_client
        await client.post("/api/auth/register", json={
            "username": "hashtest", "email": "hash@example.com", "password": "password123",
        })
        result = await db.execute(select(User).where(User.username == "hashtest"))
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.hashed_password != "password123"


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, seeded_client):
        client, db = seeded_client
        await client.post("/api/auth/register", json={
            "username": "loginuser", "email": "login@example.com", "password": "password123",
        })
        result = await db.execute(select(User).where(User.username == "loginuser"))
        user = result.scalar_one()
        user.is_verified = True
        await db.commit()

        response = await client.post("/api/auth/login", data={
            "username": "login@example.com", "password": "password123",
        })
        assert response.status_code in (200, 204)

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, seeded_client):
        client, db = seeded_client
        await client.post("/api/auth/register", json={
            "username": "wrongpw", "email": "wrongpw@example.com", "password": "password123",
        })
        result = await db.execute(select(User).where(User.username == "wrongpw"))
        user = result.scalar_one()
        user.is_verified = True
        await db.commit()

        response = await client.post("/api/auth/login", data={
            "username": "wrongpw@example.com", "password": "wrongpassword",
        })
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, seeded_client):
        client, _ = seeded_client
        response = await client.post("/api/auth/login", data={
            "username": "nobody@example.com", "password": "password123",
        })
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_me_after_login(self, seeded_client):
        client, db = seeded_client
        await client.post("/api/auth/register", json={
            "username": "metest", "email": "me@example.com", "password": "password123",
        })
        result = await db.execute(select(User).where(User.username == "metest"))
        user = result.scalar_one()
        user.is_verified = True
        await db.commit()

        await client.post("/api/auth/login", data={
            "username": "me@example.com", "password": "password123",
        })
        response = await client.get("/api/users/me")
        assert response.status_code == 200
        assert response.json()["username"] == "metest"

    @pytest.mark.asyncio
    async def test_me_unauthenticated(self, seeded_client):
        client, _ = seeded_client
        response = await client.get("/api/users/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_logout(self, seeded_client):
        client, db = seeded_client
        await client.post("/api/auth/register", json={
            "username": "logoutuser", "email": "logout@example.com", "password": "password123",
        })
        result = await db.execute(select(User).where(User.username == "logoutuser"))
        user = result.scalar_one()
        user.is_verified = True
        await db.commit()

        await client.post("/api/auth/login", data={
            "username": "logout@example.com", "password": "password123",
        })
        me = await client.get("/api/users/me")
        assert me.status_code == 200

        await client.post("/api/auth/logout")
        me = await client.get("/api/users/me")
        assert me.status_code == 401
