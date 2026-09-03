from pydantic import BaseModel
from typing import Optional


class ImageUploadResponse(BaseModel):
    image_id: str
    status: str
    created_at: str

    class Config:
        json_schema_extra = {
            "example": {
                "image_id": "uuid-1234",
                "status": "queued",
                "created_at": "2026-09-03T17:00:00Z"
            }
        }


class ImageStatusResponse(BaseModel):
    image_id: str
    status: str
    processing_time_ms: Optional[int] = None
    error_message: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "image_id": "uuid-1234",
                "status": "done",
                "processing_time_ms": 3500,
                "error_message": None
            }
        }


class ImageListResponse(BaseModel):
    images: list

    class Config:
        json_schema_extra = {
            "example": {
                "images": [
                    {
                        "image_id": "uuid-1",
                        "status": "done",
                        "created_at": "2026-09-03T16:00:00Z"
                    },
                    {
                        "image_id": "uuid-2",
                        "status": "processing",
                        "created_at": "2026-09-03T17:00:00Z"
                    }
                ]
            }
        }
