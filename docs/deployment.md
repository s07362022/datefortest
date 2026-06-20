# Deployment Guide

## 本機開發

- 後端：uvicorn（localhost:8000）
- 資料庫：Docker PostgreSQL（localhost:5432）

## Staging（Phase 1 完成後部署）

**平台：Railway**

### 步驟

1. 前往 https://railway.app，用 GitHub 登入
2. New Project → Deploy from GitHub repo → 選 `datefortest`
3. 設定 Environment Variables（從 .env 複製，SECRET_KEY 換成強隨機值）
4. Add Plugin → PostgreSQL（Railway 自動提供 DATABASE_URL）
5. 部署完成後取得 staging URL

### 環境變數（Railway 上設定）

```
DATABASE_URL       自動由 Railway PostgreSQL plugin 提供
SECRET_KEY         使用強隨機字串（openssl rand -hex 32）
ALGORITHM          HS256
ACCESS_TOKEN_EXPIRE_MINUTES  60
APP_ENV            staging
UPLOAD_DIR         uploads
```

### 照片儲存（Staging）

Railway 的 volume 重 deploy 可能消失。  
Phase 2 前需決定：
- **選項 A**：Cloudflare R2（免費 10GB，推薦）
- **選項 B**：Railway Volume（$0.25/GB/月）

## Production（M8 之後）

待市場驗證後規劃。
