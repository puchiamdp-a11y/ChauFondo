import os
import threading
import tempfile
from pathlib import Path
from datetime import datetime
from app.core.config import settings


def process_image_sync(input_path: str, output_path: str) -> dict:
    """
    Process image and remove background synchronously.

    Returns: {"status": "done", "processing_time_ms": int} or {"status": "failed", "error": str}
    """
    try:
        from rembg import remove
        from PIL import Image as PILImage

        start_time = datetime.utcnow()

        with open(input_path, 'rb') as i:
            input_data = i.read()

        output_data = remove(input_data)

        with open(output_path, 'wb') as o:
            o.write(output_data)

        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        return {
            "status": "done",
            "processing_time_ms": processing_time,
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
        }


def process_image_background(image_id: str, input_path: str, output_path: str, db_session=None, user_id=None):
    """
    Process image in background thread.

    Updates database with processing status and result.
    """
    from app.models import Image, ImageStatus
    from app.core.database import SessionLocal

    db = db_session or SessionLocal()

    try:
        from rembg import remove

        with open(input_path, 'rb') as i:
            input_data = i.read()

        output_data = remove(input_data)

        with open(output_path, 'wb') as o:
            o.write(output_data)

        # Update database
        image = db.query(Image).filter(Image.id == image_id).first()
        if image:
            image.status = ImageStatus.DONE
            image.result_path = output_path
            db.commit()

    except Exception as e:
        image = db.query(Image).filter(Image.id == image_id).first()
        if image:
            image.status = ImageStatus.FAILED
            image.error_message = str(e)
            db.commit()
    finally:
        if not db_session:
            db.close()


def get_upload_directory(user_id: str = None) -> str:
    """Get upload directory path, creating if needed."""
    if user_id:
        upload_dir = f"uploads/{user_id}"
    else:
        upload_dir = "uploads/anonymous"

    Path(upload_dir).mkdir(parents=True, exist_ok=True)
    return upload_dir


def get_results_directory(user_id: str = None) -> str:
    """Get results directory path, creating if needed."""
    if user_id:
        results_dir = f"results/{user_id}"
    else:
        results_dir = "results/anonymous"

    Path(results_dir).mkdir(parents=True, exist_ok=True)
    return results_dir
