from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.tag import Tag
from app.models.user import User
from app.schemas.profile import TagOut

router = APIRouter(prefix="/tags", tags=["Tags"])

DEFAULT_TAGS = [
    "旅遊", "攝影", "音樂", "電影", "閱讀", "美食", "健身", "瑜伽",
    "登山", "跑步", "游泳", "單車", "寵物", "烹飪", "咖啡", "茶道",
    "繪畫", "設計", "遊戲", "動漫", "科技", "創業", "投資", "語言學習",
    "舞蹈", "唱歌", "戲劇", "志工", "冥想", "手作",
]


@router.get("", response_model=list[TagOut])
def list_tags(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return all available interest tags."""
    return db.query(Tag).order_by(Tag.name).all()


def seed_tags(db: Session) -> None:
    """Insert default tags if not already present."""
    for name in DEFAULT_TAGS:
        if not db.query(Tag).filter(Tag.name == name).first():
            db.add(Tag(name=name))
    db.commit()
