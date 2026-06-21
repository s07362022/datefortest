import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.photo import ModerationStatusEnum, Photo

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE_BYTES = settings.max_photo_size_mb * 1024 * 1024  # 5 MB
MIN_DIMENSION = 400


def _upload_dir() -> Path:
    """Return absolute path to the uploads directory, creating it if needed."""
    path = Path(settings.upload_dir)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[2] / settings.upload_dir
    path.mkdir(parents=True, exist_ok=True)
    return path


async def validate_and_save_photo(file: UploadFile) -> str:
    """Validate file type, size, dimensions; save with a new UUID filename.

    Returns the relative file path stored in the DB.
    Raises HTTPException on any violation.
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_FILE_TYPE", "message": "只接受 JPEG、PNG 或 WebP 圖片"},
        )

    contents = await file.read()

    if len(contents) > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=422,
            detail={"code": "FILE_TOO_LARGE", "message": f"圖片大小不得超過 {settings.max_photo_size_mb} MB"},
        )

    # Validate image dimensions using Pillow
    try:
        from io import BytesIO
        img = Image.open(BytesIO(contents))
        w, h = img.size
        if w < MIN_DIMENSION or h < MIN_DIMENSION:
            raise HTTPException(
                status_code=422,
                detail={"code": "IMAGE_TOO_SMALL", "message": f"圖片最小尺寸為 {MIN_DIMENSION}×{MIN_DIMENSION} px"},
            )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_IMAGE", "message": "無法讀取圖片檔案"},
        )

    # Save with UUID filename to prevent path traversal / filename collisions
    ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[file.content_type]
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = _upload_dir() / filename
    dest.write_bytes(contents)

    return filename


def get_user_photos(db: Session, user_id: int) -> list[Photo]:
    """Return all photos for a user ordered by sort_order."""
    return (
        db.query(Photo)
        .filter(Photo.user_id == user_id)
        .order_by(Photo.sort_order)
        .all()
    )


def add_photo(db: Session, user_id: int, file_path: str) -> Photo:
    """Add a new photo record; assign sort_order and set as primary if first."""
    existing = get_user_photos(db, user_id)
    if len(existing) >= settings.max_photos_per_user:
        raise HTTPException(
            status_code=422,
            detail={"code": "MAX_PHOTOS_REACHED", "message": f"每位使用者最多上傳 {settings.max_photos_per_user} 張照片"},
        )
    sort_order = len(existing)
    is_primary = sort_order == 0

    photo = Photo(
        user_id=user_id,
        file_path=file_path,
        sort_order=sort_order,
        is_primary=is_primary,
        moderation_status=ModerationStatusEnum.pending,
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo


def delete_photo(db: Session, photo_id: int, user_id: int) -> None:
    """Delete a photo and reorder remaining photos."""
    photo = db.get(Photo, photo_id)
    if not photo or photo.user_id != user_id:
        raise HTTPException(status_code=404, detail={"code": "PHOTO_NOT_FOUND", "message": "照片不存在"})

    was_primary = photo.is_primary
    db.delete(photo)
    db.flush()

    # Delete physical file
    try:
        file_path = _upload_dir() / photo.file_path
        if file_path.exists():
            os.remove(file_path)
    except OSError:
        pass

    # Reorder remaining photos
    remaining = get_user_photos(db, user_id)
    for i, p in enumerate(remaining):
        p.sort_order = i
        if was_primary and i == 0:
            p.is_primary = True

    db.commit()


def set_primary_photo(db: Session, photo_id: int, user_id: int) -> Photo:
    """Set a photo as primary, unset all others."""
    photo = db.get(Photo, photo_id)
    if not photo or photo.user_id != user_id:
        raise HTTPException(status_code=404, detail={"code": "PHOTO_NOT_FOUND", "message": "照片不存在"})

    db.query(Photo).filter(Photo.user_id == user_id).update({"is_primary": False})
    photo.is_primary = True
    db.commit()
    db.refresh(photo)
    return photo
