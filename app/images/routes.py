import os
import uuid
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Header, HTTPException, status, Depends, Request
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.auth.utils import decode_token
from app.core.rate_limit_v2 import check_rate_limit, clear_client_cache
from app.models import User, Image, ImageStatus
from app.images.processor import (
    process_image_sync,
    process_image_background,
    get_upload_directory,
    get_results_directory,
)

router = APIRouter(prefix="/images", tags=["images"])

# Maximum file size in bytes (from config)
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE_MB", 25)) * 1024 * 1024
ALLOWED_FORMATS = os.getenv("ALLOWED_IMAGE_FORMATS", "jpg,jpeg,png,webp").split(",")


def get_current_user_optional(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> Optional[User]:
    """Extract user from Bearer token if present, otherwise return None."""
    if not authorization:
        return None

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
    except ValueError:
        return None

    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        return None

    user_id: str = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    return user


@router.post("/upload", status_code=200)
async def upload_image(
    file: UploadFile = File(...),
    request: Request = None,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Upload and process image.

    - **Anonymous**: No auth required, returns PNG bytes directly
    - **Authenticated**: Saves to history, returns image_id + URL

    Rate limiting:
    - Anonymous: 50 uploads/day per IP
    - Free user: 5 uploads/day
    - Premium user: Unlimited
    """
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ALLOWED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"File format not allowed. Supported: {', '.join(ALLOWED_FORMATS)}"
        )

    # Get user if authenticated
    current_user = get_current_user_optional(authorization, db) if authorization else None
    user_id = current_user.id if current_user else None
    client_ip = request.client.host if request else "unknown"

    # Check rate limit based on client type
    client_id = user_id if user_id else client_ip  # Use user_id if auth, IP if anonymous
    user_tier = current_user.tier if current_user else None  # None for anonymous
    allowed, error_msg = check_rate_limit(client_id, user_tier)

    if not allowed:
        raise HTTPException(status_code=429, detail=error_msg)

    # For now, process synchronously for simplicity
    # Read file into memory
    file_content = await file.read()

    if len(file_content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    # Save input file temporarily
    temp_input = f"/tmp/input_{uuid.uuid4()}.{file_ext}"
    temp_output = f"/tmp/output_{uuid.uuid4()}.png"

    try:
        with open(temp_input, "wb") as f:
            f.write(file_content)

        # Process image
        result = process_image_sync(temp_input, temp_output)

        if result["status"] == "failed":
            raise HTTPException(status_code=500, detail=f"Processing failed: {result.get('error')}")

        # Read processed image
        with open(temp_output, "rb") as f:
            output_data = f.read()

        # If anonymous: return PNG directly
        if not current_user:
            return FileResponse(
                temp_output,
                media_type="image/png",
                headers={"Content-Disposition": "attachment; filename=result.png"}
            )

        # If authenticated: save to database and history
        upload_dir = get_upload_directory(user_id)
        results_dir = get_results_directory(user_id)

        image_id = str(uuid.uuid4())
        original_path = f"{upload_dir}/original_{image_id}.{file_ext}"
        result_path = f"{results_dir}/result_{image_id}.png"

        # Save files
        with open(original_path, "wb") as f:
            f.write(file_content)
        with open(result_path, "wb") as f:
            f.write(output_data)

        # Create database record
        image = Image(
            id=image_id,
            user_id=user_id,
            ip_address=client_ip,
            is_anonymous=0,
            original_path=original_path,
            result_path=result_path,
            status=ImageStatus.DONE,
            processing_time_ms=result.get("processing_time_ms"),
        )
        db.add(image)
        db.commit()

        return JSONResponse({
            "image_id": image_id,
            "status": "done",
            "image_url": f"/images/download/{image_id}",
            "processing_time_ms": result.get("processing_time_ms"),
        })

    finally:
        # Cleanup temp files
        import os as os_module
        for path in [temp_input, temp_output]:
            if os_module.path.exists(path):
                os_module.remove(path)


@router.get("/{image_id}/download")
async def download_image(
    image_id: str,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """Download processed image."""
    current_user = get_current_user_optional(authorization, db) if authorization else None

    image = db.query(Image).filter(Image.id == image_id).first()

    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Check ownership if authenticated
    if current_user and image.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Check if result exists
    if not image.result_path or not os.path.exists(image.result_path):
        raise HTTPException(status_code=404, detail="Result not ready")

    return FileResponse(
        image.result_path,
        media_type="image/png",
        headers={"Content-Disposition": "attachment; filename=result.png"}
    )


@router.get("/list", status_code=200)
async def list_images(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    """List user's processed images (authenticated only)."""
    current_user = get_current_user_optional(authorization, db)

    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    images = db.query(Image).filter(Image.user_id == current_user.id).order_by(Image.created_at.desc()).all()

    return [
        {
            "image_id": img.id,
            "status": img.status.value,
            "created_at": img.created_at.isoformat(),
            "processing_time_ms": img.processing_time_ms,
            "error_message": img.error_message,
        }
        for img in images
    ]
