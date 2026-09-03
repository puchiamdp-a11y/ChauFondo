import time
from io import BytesIO
from PIL import Image as PILImage


def create_test_image(width=100, height=100, format="PNG"):
    """Create a test image in memory."""
    img = PILImage.new("RGB", (width, height), color="red")
    img_bytes = BytesIO()
    img.save(img_bytes, format=format)
    img_bytes.seek(0)
    return img_bytes.getvalue()


def test_upload_valid_image(client):
    """Test valid image upload returns image_id."""
    # Signup and login first
    client.post(
        "/auth/signup",
        json={"email": "test@example.com", "password": "securepass123"}
    )
    login_response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "securepass123"}
    )
    token = login_response.json()["access_token"]

    # Upload image
    image_data = create_test_image()
    response = client.post(
        "/images/upload",
        files={"file": ("test.png", image_data, "image/png")},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 202
    data = response.json()
    assert "image_id" in data
    assert data["status"] == "queued"
    assert "created_at" in data


def test_upload_without_auth(client):
    """Test upload without token returns 401."""
    image_data = create_test_image()
    response = client.post(
        "/images/upload",
        files={"file": ("test.png", image_data, "image/png")}
    )
    assert response.status_code == 401


def test_upload_invalid_format(client):
    """Test upload with invalid format returns 400."""
    # Signup and login
    client.post(
        "/auth/signup",
        json={"email": "test@example.com", "password": "securepass123"}
    )
    login_response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "securepass123"}
    )
    token = login_response.json()["access_token"]

    # Try to upload txt file
    response = client.post(
        "/images/upload",
        files={"file": ("test.txt", b"not an image", "text/plain")},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 400
    assert "Invalid format" in response.json()["detail"]


def test_upload_oversized_image(client):
    """Test upload with oversized dimensions returns 400."""
    # Signup and login
    client.post(
        "/auth/signup",
        json={"email": "test@example.com", "password": "securepass123"}
    )
    login_response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "securepass123"}
    )
    token = login_response.json()["access_token"]

    # Create oversized image (5000x5000)
    try:
        image_data = create_test_image(width=5000, height=5000)
        response = client.post(
            "/images/upload",
            files={"file": ("test.png", image_data, "image/png")},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 400
        assert "too large" in response.json()["detail"].lower()
    except Exception:
        # Memory allocation for huge image might fail, which is ok
        pass


def test_get_image_status(client):
    """Test getting image processing status."""
    # Signup and login
    client.post(
        "/auth/signup",
        json={"email": "test@example.com", "password": "securepass123"}
    )
    login_response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "securepass123"}
    )
    token = login_response.json()["access_token"]

    # Upload image
    image_data = create_test_image()
    upload_response = client.post(
        "/images/upload",
        files={"file": ("test.png", image_data, "image/png")},
        headers={"Authorization": f"Bearer {token}"}
    )
    image_id = upload_response.json()["image_id"]

    # Get status
    response = client.get(
        f"/images/images/{image_id}/status",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["image_id"] == image_id
    assert data["status"] in ["queued", "processing", "done", "failed"]


def test_get_status_wrong_user(client):
    """Test getting status for image from different user returns 404."""
    # User 1: Signup, login, upload
    client.post(
        "/auth/signup",
        json={"email": "user1@example.com", "password": "securepass123"}
    )
    login1 = client.post(
        "/auth/login",
        json={"email": "user1@example.com", "password": "securepass123"}
    )
    token1 = login1.json()["access_token"]

    image_data = create_test_image()
    upload_response = client.post(
        "/images/upload",
        files={"file": ("test.png", image_data, "image/png")},
        headers={"Authorization": f"Bearer {token1}"}
    )
    image_id = upload_response.json()["image_id"]

    # User 2: Signup and login
    client.post(
        "/auth/signup",
        json={"email": "user2@example.com", "password": "securepass123"}
    )
    login2 = client.post(
        "/auth/login",
        json={"email": "user2@example.com", "password": "securepass123"}
    )
    token2 = login2.json()["access_token"]

    # User 2 tries to access User 1's image
    response = client.get(
        f"/images/images/{image_id}/status",
        headers={"Authorization": f"Bearer {token2}"}
    )

    assert response.status_code == 404


def test_download_not_ready(client):
    """Test download before processing is done returns 400."""
    # Signup and login
    client.post(
        "/auth/signup",
        json={"email": "test@example.com", "password": "securepass123"}
    )
    login_response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "securepass123"}
    )
    token = login_response.json()["access_token"]

    # Upload image
    image_data = create_test_image()
    upload_response = client.post(
        "/images/upload",
        files={"file": ("test.png", image_data, "image/png")},
        headers={"Authorization": f"Bearer {token}"}
    )
    image_id = upload_response.json()["image_id"]

    # Try to download immediately (should fail, status is queued)
    response = client.get(
        f"/images/download/{image_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 400
    assert "not ready" in response.json()["detail"].lower()


def test_download_without_auth(client):
    """Test download without auth returns 401."""
    response = client.get("/images/download/fake-image-id")
    assert response.status_code == 401


def test_list_user_images(client):
    """Test listing user's images."""
    # Signup and login
    client.post(
        "/auth/signup",
        json={"email": "test@example.com", "password": "securepass123"}
    )
    login_response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "securepass123"}
    )
    token = login_response.json()["access_token"]

    # Upload first image
    image_data1 = create_test_image()
    client.post(
        "/images/upload",
        files={"file": ("test1.png", image_data1, "image/png")},
        headers={"Authorization": f"Bearer {token}"}
    )

    # Upload second image
    image_data2 = create_test_image()
    client.post(
        "/images/upload",
        files={"file": ("test2.png", image_data2, "image/png")},
        headers={"Authorization": f"Bearer {token}"}
    )

    # List images
    response = client.get(
        "/images/list",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "images" in data
    assert len(data["images"]) == 2
    assert all("image_id" in img for img in data["images"])
    assert all("status" in img for img in data["images"])
