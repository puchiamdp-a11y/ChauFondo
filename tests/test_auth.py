import pytest
from app.auth.utils import hash_password, verify_password


def test_signup_valid(client, db):
    """Test valid signup creates user with free tier."""
    response = client.post(
        "/auth/signup",
        json={
            "email": "test@example.com",
            "password": "securepass123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["tier"] == "free"
    assert "id" in data
    assert "created_at" in data


def test_signup_duplicate_email(client, db):
    """Test signup with existing email returns 400."""
    # First signup
    client.post(
        "/auth/signup",
        json={
            "email": "test@example.com",
            "password": "securepass123"
        }
    )

    # Second signup with same email
    response = client.post(
        "/auth/signup",
        json={
            "email": "test@example.com",
            "password": "anotherpass456"
        }
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_signup_invalid_email(client):
    """Test signup with invalid email format."""
    response = client.post(
        "/auth/signup",
        json={
            "email": "not-an-email",
            "password": "securepass123"
        }
    )
    assert response.status_code == 422


def test_signup_short_password(client):
    """Test signup with password < 8 characters."""
    response = client.post(
        "/auth/signup",
        json={
            "email": "test@example.com",
            "password": "short"
        }
    )
    assert response.status_code == 422


def test_login_valid(client):
    """Test valid login returns access_token."""
    # Signup first
    client.post(
        "/auth/signup",
        json={
            "email": "test@example.com",
            "password": "securepass123"
        }
    )

    # Login
    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "securepass123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


def test_login_wrong_password(client):
    """Test login with wrong password returns 401."""
    # Signup first
    client.post(
        "/auth/signup",
        json={
            "email": "test@example.com",
            "password": "securepass123"
        }
    )

    # Login with wrong password
    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_login_nonexistent_user(client):
    """Test login with non-existent user returns 401."""
    response = client.post(
        "/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "anypassword"
        }
    )
    assert response.status_code == 401


def test_get_current_user_with_token(client):
    """Test /me endpoint with valid token."""
    # Signup and login
    client.post(
        "/auth/signup",
        json={
            "email": "test@example.com",
            "password": "securepass123"
        }
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "securepass123"
        }
    )
    token = login_response.json()["access_token"]

    # Get current user
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["tier"] == "free"


def test_get_current_user_without_token(client):
    """Test /me endpoint without token returns 401."""
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_get_current_user_with_invalid_token(client):
    """Test /me endpoint with invalid token returns 401."""
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid_token_xyz"}
    )
    assert response.status_code == 401


def test_refresh_token_valid(client):
    """Test refresh token endpoint with valid refresh token."""
    # Signup and login
    client.post(
        "/auth/signup",
        json={
            "email": "test@example.com",
            "password": "securepass123"
        }
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "securepass123"
        }
    )
    refresh_token = login_response.json()["refresh_token"]

    # Refresh token
    response = client.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {refresh_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_refresh_token_with_access_token(client):
    """Test refresh endpoint with access token (should fail)."""
    # Signup and login
    client.post(
        "/auth/signup",
        json={
            "email": "test@example.com",
            "password": "securepass123"
        }
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "securepass123"
        }
    )
    access_token = login_response.json()["access_token"]

    # Try to refresh with access token
    response = client.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401


def test_password_hashing():
    """Test password hashing and verification."""
    password = "mysecurepassword123"
    hashed = hash_password(password)

    # Verify correct password
    assert verify_password(password, hashed) is True

    # Verify wrong password
    assert verify_password("wrongpassword", hashed) is False
