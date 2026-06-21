"""Seed the database with test users, profiles, tags, and preferences.

Usage (from backend/):
    .venv/Scripts/python scripts/seed_data.py
    .venv/Scripts/python scripts/seed_data.py --clear   # wipe and re-seed
"""

import argparse
import random
import sys
from datetime import date, datetime, timezone
from pathlib import Path

# Ensure backend root is in path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.photo import ModerationStatusEnum, Photo
from app.models.preference import Preference
from app.models.profile import GenderEnum, InterestedInEnum, Profile
from app.models.tag import ProfileTag, Tag
from app.models.user import User
from app.api.v1.tags import DEFAULT_TAGS, seed_tags

# ── Seed data ─────────────────────────────────────────────────────────────────

SEED_USERS = [
    {"email": "alice@test.com",   "name": "Alice",   "birthday": date(1995, 3, 15), "gender": "woman",  "interested_in": "men",     "city": "台北", "lat": 25.033, "lon": 121.565, "bio": "喜歡週末去爬山和發現隱藏版咖啡廳，工作是平面設計師，對生活充滿好奇心。"},
    {"email": "bob@test.com",     "name": "Bob",     "birthday": date(1993, 7, 22), "gender": "man",    "interested_in": "women",   "city": "台北", "lat": 25.047, "lon": 121.517, "bio": "軟體工程師，熱愛旅遊和攝影，曾去過二十個國家，下一個目標是冰島。"},
    {"email": "carol@test.com",   "name": "Carol",   "birthday": date(1997, 11, 5), "gender": "woman",  "interested_in": "everyone","city": "新北", "lat": 25.012, "lon": 121.466, "bio": "瑜伽老師，也是業餘烹飪愛好者，相信食物是連結人心最好的橋樑。"},
    {"email": "david@test.com",   "name": "David",   "birthday": date(1991, 4, 18), "gender": "man",    "interested_in": "women",   "city": "台北", "lat": 25.040, "lon": 121.543, "bio": "創業者，喜歡閱讀商業書籍和思考新創點子，週末會去跑馬拉松放鬆。"},
    {"email": "emma@test.com",    "name": "Emma",    "birthday": date(1998, 8, 30), "gender": "woman",  "interested_in": "men",     "city": "桃園", "lat": 24.993, "lon": 121.301, "bio": "音樂系畢業，目前在音樂公司工作，會彈鋼琴和吉他，最喜歡爵士樂。"},
    {"email": "frank@test.com",   "name": "Frank",   "birthday": date(1994, 1, 10), "gender": "man",    "interested_in": "everyone","city": "台中", "lat": 24.148, "lon": 120.673, "bio": "攝影師，熱衷記錄生活中的每個美好瞬間，也喜歡獨自一人在山中露營。"},
    {"email": "grace@test.com",   "name": "Grace",   "birthday": date(1996, 6, 25), "gender": "woman",  "interested_in": "men",     "city": "台北", "lat": 25.038, "lon": 121.532, "bio": "醫護人員，工作很忙但下班後喜歡看電影和逛書店，喜歡任何形式的藝術。"},
    {"email": "henry@test.com",   "name": "Henry",   "birthday": date(1992, 9, 14), "gender": "man",    "interested_in": "women",   "city": "高雄", "lat": 22.627, "lon": 120.301, "bio": "廚師，熱愛探索各種料理文化，曾在法國和日本受訓，回台灣開了自己的餐廳。"},
    {"email": "ivy@test.com",     "name": "Ivy",     "birthday": date(1999, 2, 7),  "gender": "woman",  "interested_in": "women",   "city": "台北", "lat": 25.055, "lon": 121.510, "bio": "插畫家和內容創作者，IG 有三萬粉絲，喜歡分享生活中的小確幸和手繪作品。"},
    {"email": "jack@test.com",    "name": "Jack",    "birthday": date(1990, 12, 3), "gender": "man",    "interested_in": "men",     "city": "台北", "lat": 25.029, "lon": 121.558, "bio": "建築師，對空間設計充滿熱情，週末喜歡騎自行車環島，也熱衷戶外冒險。"},
]

TAG_ASSIGNMENTS = {
    "alice@test.com":  ["旅遊", "咖啡", "設計"],
    "bob@test.com":    ["旅遊", "攝影", "科技"],
    "carol@test.com":  ["瑜伽", "烹飪", "健身"],
    "david@test.com":  ["閱讀", "跑步", "創業"],
    "emma@test.com":   ["音樂", "電影", "咖啡"],
    "frank@test.com":  ["攝影", "登山", "旅遊"],
    "grace@test.com":  ["電影", "閱讀", "音樂"],
    "henry@test.com":  ["烹飪", "旅遊", "美食"],
    "ivy@test.com":    ["繪畫", "設計", "手作"],
    "jack@test.com":   ["單車", "登山", "設計"],
}


def clear_seed_data(db: Session) -> None:
    print("  清除現有測試資料...")
    for email in [u["email"] for u in SEED_USERS]:
        user = db.query(User).filter(User.email == email).first()
        if user:
            db.delete(user)
    db.commit()
    print("  ✅ 清除完成")


def run_seed(db: Session) -> None:
    print("▶ 寫入 Tags...")
    seed_tags(db)
    tag_map = {t.name: t for t in db.query(Tag).all()}
    print(f"  ✅ {len(tag_map)} 個 tags 就緒")

    created = 0
    skipped = 0
    for u_data in SEED_USERS:
        if db.query(User).filter(User.email == u_data["email"]).first():
            skipped += 1
            continue

        user = User(email=u_data["email"], password_hash=hash_password("Seed1234!"), is_active=True)
        db.add(user)
        db.flush()

        profile = Profile(
            user_id=user.id,
            display_name=u_data["name"],
            birthday=u_data["birthday"],
            gender=GenderEnum(u_data["gender"]),
            interested_in=InterestedInEnum(u_data["interested_in"]),
            bio=u_data["bio"],
            city=u_data["city"],
            latitude=u_data["lat"],
            longitude=u_data["lon"],
            height_cm=random.randint(155, 185),
            last_active_at=datetime.now(timezone.utc),
        )
        db.add(profile)
        db.flush()

        for tag_name in TAG_ASSIGNMENTS.get(u_data["email"], []):
            if tag_name in tag_map:
                db.add(ProfileTag(profile_id=profile.id, tag_id=tag_map[tag_name].id))

        pref = Preference(user_id=user.id, min_age=20, max_age=40, max_distance_km=50, preferred_genders="everyone")
        db.add(pref)

        # Placeholder primary photo (a 1x1 pixel placeholder path)
        db.add(Photo(user_id=user.id, file_path="placeholder.jpg", sort_order=0,
                     is_primary=True, moderation_status=ModerationStatusEnum.approved))

        created += 1

    db.commit()
    print(f"  ✅ 建立 {created} 位測試用戶，跳過 {skipped} 位（已存在）")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed test data into the database")
    parser.add_argument("--clear", action="store_true", help="Clear existing seed users before seeding")
    args = parser.parse_args()

    db: Session = SessionLocal()
    try:
        if args.clear:
            clear_seed_data(db)
        print("▶ 開始寫入測試資料...")
        run_seed(db)
        print("✅ Seed 完成！")
        print("   測試帳號密碼一律為：Seed1234!")
    finally:
        db.close()
