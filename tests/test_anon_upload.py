import io
import pytest
from PIL import Image as PILImage
from app.models import Image, ImageStatus


@pytest.fixture
def sample_image():
    """Create a sample image file."""
    img = PILImage.new('RGB', (100, 100), color='red')
    img_io = io.BytesIO()
    img.save(img_io, format='PNG')
    img_io.seek(0)
    return img_io


def test_anonymous_upload_returns_png(client, sample_image):
    """Test anonymous upload returns PNG bytes directly."""
    response = client.post(
        "/images/upload",
        files={"file": ("test.png", sample_image, "image/png")}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 0


def test_authenticated_upload_saves_to_db(client, db):
    """Test authenticated upload saves to database."""
    # Signup and login
    client.post(
        "/auth/signup",
        json={"email": "auth@example.com", "password": "secure123"}
    )
    login_resp = client.post(
        "/auth/login",
        json={"email": "auth@example.com", "password": "secure123"}
    )
    token = login_resp.json()["access_token"]

    # Create test image
    img = PILImage.new('RGB', (100, 100), color='blue')
    img_io = io.BytesIO()
    img.save(img_io, format='PNG')
    img_io.seek(0)

    # Upload
    response = client.post(
        "/images/upload",
        files={"file": ("test.png", img_io, "image/png")},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "image_id" in data
    assert data["status"] == "done"
    assert "image_url" in data


def test_anon_upload_rate_limit_50_per_day(client, db):
    """Test anonymous users get 50 uploads/day limit."""
    # Create 50 test images and upload
    for i in range(50):
        img = PILImage.new('RGB', (50, 50), color='red')
        img_io = io.BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)

        response = client.post(
            "/images/upload",
            files={"file": (f"test{i}.png", img_io, "image/png")}
        )
        assert response.status_code == 200

    # 51st upload should fail
    img = PILImage.new('RGB', (50, 50), color='red')
    img_io = io.BytesIO()
    img.save(img_io, format='PNG')
    img_io.seek(0)

    response = client.post(
        "/images/upload",
        files={"file": ("test51.png", img_io, "image/png")}
    )
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]


def test_free_user_upload_rate_limit_5_per_day(client, db):
    """Test free users get 5 uploads/day limit."""
    # Signup and login
    client.post(
        "/auth/signup",
        json={"email": "free@example.com", "password": "secure123"}
    )
    login_resp = client.post(
        "/auth/login",
        json={"email": "free@example.com", "password": "secure123"}
    )
    token = login_resp.json()["access_token"]

    # Upload 5 images
    for i in range(5):
        img = PILImage.new('RGB', (50, 50), color='blue')
        img_io = io.BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)

        response = client.post(
            "/images/upload",
            files={"file": (f"test{i}.png", img_io, "image/png")},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

    # 6th upload should fail
    img = PILImage.new('RGB', (50, 50), color='blue')
    img_io = io.BytesIO()
    img.save(img_io, format='PNG')
    img_io.seek(0)

    response = client.post(
        "/images/upload",
        files={"file": ("test6.png", img_io, "image/png")},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 429
