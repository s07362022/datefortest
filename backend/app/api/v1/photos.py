from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.photo import PhotoOut
from app.services.photo_service import (
    add_photo,
    delete_photo,
    get_user_photos,
    set_primary_photo,
    validate_and_save_photo,
    _upload_dir,
)

router = APIRouter(prefix="/photos", tags=["Photos"])


@router.post("", response_model=PhotoOut, status_code=status.HTTP_201_CREATED)
async def upload_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a photo. Validates type (JPEG/PNG/WebP), size (≤5 MB), and dimensions (≥400×400)."""
    file_path = await validate_and_save_photo(file)
    photo = add_photo(db, current_user.id, file_path)
    return photo


@router.get("/me", response_model=list[PhotoOut])
def list_my_photos(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return all photos for the current user, ordered by sort_order."""
    return get_user_photos(db, current_user.id)


@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_photo(
    photo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a photo and reorder remaining photos."""
    delete_photo(db, photo_id, current_user.id)


@router.put("/{photo_id}/primary", response_model=PhotoOut)
def make_primary(
    photo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Set a specific photo as the primary (profile) photo."""
    return set_primary_photo(db, photo_id, current_user.id)


@router.get("/file/{filename}")
def serve_photo(filename: str, current_user: User = Depends(get_current_user)):
    """Serve a photo file. Auth required — prevents unauthenticated access."""
    file_path = _upload_dir() / filename
    if not file_path.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail={"code": "FILE_NOT_FOUND", "message": "檔案不存在"})
    return FileResponse(str(file_path))
