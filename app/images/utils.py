import os
import time
from pathlib import Path
from io import BytesIO
from PIL import Image as PILImage
from rembg import remove
from app.core.config import settings


UPLOAD_DIR = Path("uploads")
RESULT_DIR = Path("results")


def ensure_directories():
    """Create upload and result directories if they don't exist."""
    UPLOAD_DIR.mkdir(exist_ok=True)
    RESULT_DIR.mkdir(exist_ok=True)


def validate_image_file(file_bytes: bytes, filename: str) -> tuple[bool, str]:
    """
    Validate image file format, size, and dimensions.

    Returns: (is_valid, error_message)
    """
    # Check file size (max 25MB)
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_size:
        return False, f"File too large. Max: {settings.MAX_UPLOAD_SIZE_MB}MB"

    # Check file format
    allowed_formats = settings.ALLOWED_IMAGE_FORMATS.split(",")
    file_ext = Path(filename).suffix.lower().lstrip(".")
    if file_ext not in allowed_formats:
        return False, f"Invalid format. Allowed: {', '.join(allowed_formats)}"

    # Check image dimensions
    try:
        img = PILImage.open(BytesIO(file_bytes))
        width, height = img.size
        if width > 4000 or height > 4000:
            return False, "Image too large. Max dimensions: 4000x4000px"
    except Exception as e:
        return False, f"Invalid image file: {str(e)}"

    return True, ""


def save_original_image(file_bytes: bytes, user_id: str, image_id: str) -> str:
    """Save original image to disk. Returns file path."""
    ensure_directories()

    user_dir = UPLOAD_DIR / user_id
    user_dir.mkdir(exist_ok=True)

    file_path = user_dir / f"{image_id}_original.png"
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    return str(file_path)


def process_image_with_rembg(input_path: str, output_path: str) -> tuple[bool, int, str]:
    """
    Process image with rembg to remove background.

    Returns: (success, processing_time_ms, error_message)
    """
    start_time = time.time()

    try:
        # Load original image
        with open(input_path, "rb") as f:
            input_data = f.read()

        # Process with timeout
        input_img = PILImage.open(BytesIO(input_data))
        output_img = remove(input_img)

        # Save result as PNG with transparency
        output_img.save(output_path, "PNG")

        elapsed_ms = int((time.time() - start_time) * 1000)
        return True, elapsed_ms, None

    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        error_msg = str(e)[:500]  # Truncate error message
        return False, elapsed_ms, error_msg


def get_result_image_bytes(image_id: str, user_id: str) -> bytes:
    """Get processed image bytes from disk."""
    result_path = RESULT_DIR / user_id / f"{image_id}_result.png"

    if not result_path.exists():
        return None

    with open(result_path, "rb") as f:
        return f.read()


def cleanup_image_files(user_id: str, image_id: str):
    """Delete original and result image files."""
    original_path = UPLOAD_DIR / user_id / f"{image_id}_original.png"
    result_path = RESULT_DIR / user_id / f"{image_id}_result.png"

    try:
        if original_path.exists():
            original_path.unlink()
        if result_path.exists():
            result_path.unlink()
    except Exception:
        pass  # Ignore cleanup errors
