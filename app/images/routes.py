import uuid
import threading
from datetime import datetime
from pathlib import Path
from fastapi import (
    APIRouter, File, UploadFile, Depends, HTTPException, status, Header
)
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import User, Image, ImageStatus
from app.images.schemas import ImageUploadResponse, ImageStatusResponse
from app.images.utils import (
    validate_image_file,
    save_original_image,
    process_image_with_rembg,
    get_result_image_bytes,
    RESULT_DIR,
)
from app.auth.routes import get_current_user_from_header

router = APIRouter(prefix="/images", tags=["images"])


def process_image_background(image_id: str, user_id: str, input_path: str, db_session):
    """Background job to process image with rembg."""
    try:
        # Ensure result directory exists
        user_result_dir = RESULT_DIR / user_id
        user_result_dir.mkdir(parents=True, exist_ok=True)

        output_path = user_result_dir / f"{image_id}_result.png"

        # Process image
        success, processing_time_ms, error_msg = process_image_with_rembg(
            input_path, str(output_path)
        )

        # Update database
        image = db_session.query(Image).filter(Image.id == image_id).first()
        if image:
            if success:
                image.status = ImageStatus.DONE
                image.result_path = str(output_path)
                image.processing_time_ms = processing_time_ms
                image.error_message = None
            else:
                image.status = ImageStatus.FAILED
                image.error_message = error_msg
                image.processing_time_ms = processing_time_ms

            db_session.commit()

    except Exception as e:
        # Update image as failed
        image = db_session.query(Image).filter(Image.id == image_id).first()
        if image:
            image.status = ImageStatus.FAILED
            image.error_message = str(e)[:500]
            db_session.commit()
    finally:
        db_session.close()


@router.post("/upload", response_model=ImageUploadResponse, status_code=202)
async def upload_image(
    file: UploadFile = File(...),
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    """
    Upload image for background removal.

    - **file**: Image file (JPG, PNG, WEBP, max 25MB)

    Returns: image_id and status = "queued"
    """
    # Get current user
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    from app.auth.utils import decode_token

    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    user_id: str = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    # Read file
    file_bytes = await file.read()

    # Validate file
    is_valid, error_msg = validate_image_file(file_bytes, file.filename)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # Create image record
    image_id = str(uuid.uuid4())
    original_path = save_original_image(file_bytes, user_id, image_id)

    image = Image(
        id=image_id,
        user_id=user_id,
        original_path=original_path,
        status=ImageStatus.QUEUED,
    )
    db.add(image)
    db.commit()

    # Start background processing
    from app.core.database import SessionLocal

    db_session = SessionLocal()
    thread = threading.Thread(
        target=process_image_background,
        args=(image_id, user_id, original_path, db_session),
        daemon=True,
    )
    thread.start()

    return {
        "image_id": image_id,
        "status": "queued",
        "created_at": image.created_at.isoformat() + "Z"
    }


@router.get("/images/{image_id}/status", response_model=ImageStatusResponse)
def get_image_status(
    image_id: str,
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    """
    Get processing status of image.

    - **image_id**: Image ID

    Returns: status (queued, processing, done, failed), processing_time_ms
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    from app.auth.utils import decode_token

    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    user_id: str = payload.get("sub")

    image = db.query(Image).filter(
        Image.id == image_id,
        Image.user_id == user_id
    ).first()

    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )

    return {
        "image_id": image.id,
        "status": image.status.value,
        "processing_time_ms": image.processing_time_ms,
        "error_message": image.error_message,
    }


@router.get("/download/{image_id}")
def download_image(
    image_id: str,
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    """
    Download processed image (PNG with transparent background).

    - **image_id**: Image ID

    Returns: PNG file bytes
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    from app.auth.utils import decode_token

    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    user_id: str = payload.get("sub")

    image = db.query(Image).filter(
        Image.id == image_id,
        Image.user_id == user_id
    ).first()

    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )

    if image.status != ImageStatus.DONE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image not ready. Status: {image.status.value}"
        )

    # Get file bytes
    image_bytes = get_result_image_bytes(image_id, user_id)
    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Result file not found"
        )

    from fastapi.responses import Response

    return Response(
        content=image_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename={image_id}.png"}
    )


@router.get("/list")
def list_user_images(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    """
    List all images for current user.

    - **Authorization**: Bearer <access_token>

    Returns: list of images with id, status, created_at
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    from app.auth.utils import decode_token

    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    user_id: str = payload.get("sub")

    images = db.query(Image).filter(Image.user_id == user_id).order_by(
        Image.created_at.desc()
    ).all()

    return {
        "images": [
            {
                "image_id": img.id,
                "status": img.status.value,
                "created_at": img.created_at.isoformat() + "Z"
            }
            for img in images
        ]
    }
