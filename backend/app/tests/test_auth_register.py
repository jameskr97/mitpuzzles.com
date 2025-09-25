import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from app.modules.auth.models import User


class TestUserRegistration:
    @pytest.mark.asyncio
    async def test_register_success(self, client, db: AsyncSession, mock_send_verification_email):
        user = {"username": "user", "email": "test@example.com", "password": "password123"}
        response = client.post("/api/auth/register", json=user)

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "user"
        assert data["email"] == "test@example.com"
        assert "id" in data

        # Verify email sending was called
        mock_send_verification_email.assert_called_once()

    def test_register_duplicate_username(self, client, db: AsyncSession):
        user1 = {"username": "dupe", "email": "u1@example.com", "password": "password123"}
        user2 = {"username": "dupe", "email": "u2@example.com", "password": "password123"}

        client.post("/api/auth/register", json=user1)
        res = client.post("/api/auth/register", json=user2)

        assert res.status_code == 400
        assert "Username already registered" in res.json()["detail"]

    def test_register_duplicate_email(self, client, db: AsyncSession):
        user1 = {"username": "user1", "email": "dupe@example.com", "password": "password123"}
        user2 = {"username": "user2", "email": "dupe@example.com", "password": "password123"}

        client.post("/api/auth/register", json=user1)
        res = client.post("/api/auth/register", json=user2)

        assert res.status_code == 400
        assert "Email already registered" in res.json()["detail"]

    def test_register_invalid_email(self, client, db: AsyncSession):
        user = {"username": "user", "email": "invalid-email", "password": "password123"}
        res = client.post("/api/auth/register", json=user)

        assert res.status_code == 422

    def test_register_missing_fields(self, client, db: AsyncSession):
        # missing password
        user = {"username": "user", "email": "invalid-email"}
        response = client.post("/api/auth/register", json=user)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_password_is_hashed(self, client, db: AsyncSession):
        user_data = {"username": "user", "email": "example@example.com", "password": "password123"}
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 201

        # Verify password is not stored in plain text
        result = await db.execute(select(User).where(User.username == "user"))
        user = result.scalar_one_or_none()
        assert user.hashed_password != "password123"
        assert user.hashed_password.startswith("$argon2id$")

    # def test_verification_token_created(self, client, db: AsyncSession):
    #     response = client.post(
    #         "/auth/register",
    #         json={
    #             "username": "tokentest",
    #             "email": "token@example.com",
    #             "password": "password123"
    #         }
    #     )
    #
    #     assert response.status_code == 201
    #     user_id = response.json()["id"]
    #
    #     # Check that verification token was created
    #     token = db.query(EmailVerificationToken).filter(
    #         EmailVerificationToken.user_id == user_id
    #     ).first()
    #     assert token is not None
    #     assert token.used == False
    #     assert token.expires_at > token.date_created
