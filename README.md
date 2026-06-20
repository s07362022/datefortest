# Dating App MVP

Android-first dating app built with Python (FastAPI) backend.

## 專案路徑

```
F:\cursor_coding\project01\dating-app     ← canonical project root
F:\cursor_coding\project01\dating-app-md  ← 規劃文件與 logs
```

## 技術架構

| 層級 | 技術 |
|------|------|
| 後端 API | FastAPI + Python 3.10 |
| 資料庫 | PostgreSQL 16（Docker） |
| ORM / Migration | SQLAlchemy 2 + Alembic |
| 認證 | JWT（python-jose） |
| 照片 | 本機儲存（後期改 Cloudflare R2） |
| 聊天 | REST polling（後期升 WebSocket） |
| Android App | Kivy/KivyMD（後期評估 Flutter） |

## 本機開發快速開始

### 1. 啟動 PostgreSQL

```powershell
docker-compose up -d
```

### 2. 建立虛擬環境（第一次）

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 設定環境變數

```powershell
copy .env.example .env
# 編輯 .env，修改 SECRET_KEY 與 POSTGRES_PASSWORD
```

### 4. 啟動 API

```powershell
cd backend
.\.venv\Scripts\activate
uvicorn app.main:app --reload
```

開啟瀏覽器：
- API 文件：http://localhost:8000/docs
- Health check：http://localhost:8000/health

## 查看資料庫（DBeaver）

連線設定：

| 項目 | 值 |
|------|-----|
| Host | localhost |
| Port | 5432 |
| Database | datingapp |
| Username | postgres |
| Password | devpassword123（見 .env） |

## 里程碑

| 里程碑 | 日期 | 內容 |
|--------|------|------|
| M1 | 2026-06-22 | 專案骨架 ✅ |
| M2 | 2026-06-29 | 帳號與個人檔案 |
| M3 | 2026-07-06 | 照片與推薦 |
| M4 | 2026-07-13 | 配對 |
| M5 | 2026-07-20 | 聊天 |
| M6 | 2026-08-10 | Android 原型 |
| M7 | 2026-08-17 | 安全與管理後台 |
| M8 | 2026-08-31 | 內測 |

## 目錄結構

```
dating-app/
  backend/
    app/
      main.py          ← FastAPI 進入點
      core/
        config.py      ← 設定（從 .env 讀取）
      models/          ← SQLAlchemy 資料模型
      schemas/         ← Pydantic 請求/回應結構
      api/             ← 路由
      services/        ← 業務邏輯
      db/
        session.py     ← 資料庫連線
    tests/
    logs/
    requirements.txt
    .env.example
  docs/
  mobile/
  docker-compose.yml
```
