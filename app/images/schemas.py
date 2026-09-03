from pydantic import BaseModel
from typing import Optional


class UploadResponse(BaseModel):
    """Response for anonymous upload (direct PNG)."""
    image_data: bytes


class AuthenticatedUploadResponse(BaseModel):
    """Response for authenticated upload (saved to history)."""
    image_id: str
    status: str
    image_url: str


class ImageInfo(BaseModel):
    """Image info from user history."""
    image_id: str
    status: str
    created_at: str
    processing_time_ms: Optional[int] = None
    error_message: Optional[str] = None
