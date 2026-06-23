# Android Dating App MVP Plan

建立日期：2026-06-20
最後更新：2026-06-24
目標平台：Android first
主要語言：Python

## 進度總覽（最後更新：2026-06-24）

| 里程碑 | 目標日期 | 實際完成 | 狀態 |
|--------|---------|---------|------|
| M1 專案骨架 | 2026-06-22 | 2026-06-21 | ✅ 完成 |
| M2 帳號+個人檔案 | 2026-06-29 | 2026-06-21 | ✅ 完成 |
| M3 照片+推薦 | 2026-07-06 | 2026-06-21 | ✅ 完成 |
| M4 配對 | 2026-07-13 | 2026-06-21 | ✅ 完成 |
| M5 聊天 | 2026-07-20 | — | ⏳ 進行中 |
| M5.5 升 JDK 17 | 2026-07-27 | — | ⬜ 待開始 |
| M6 Android 原型 | 2026-08-10 | — | ⬜ 待開始 |
| M7 安全+管理後台 | 2026-08-17 | — | ⬜ 待開始 |
| M8 內測 | 2026-08-31 | — | ⬜ 待開始 |

pytest：55/55 PASSED｜Git commits：7｜DB 資料表：9｜API 端點：20｜版本：v0.3.0
目前本機狀態：Python 3.10.11 可用，Git 可用，Docker 未安裝，Java 未安裝
Canonical project path：F:\cursor_coding\project01\dating-app

## 1. 專案目標

本專案的第一階段目標不是一次做出完整大型交友平台，而是先做出一個可以驗證市場的 Android MVP。

MVP 完成時應該具備：

- 使用者可以註冊與登入
- 使用者可以建立個人檔案
- 使用者可以上傳照片
- 使用者可以設定基本配對偏好
- 使用者可以看到推薦對象
- 使用者可以喜歡或略過對象
- 雙方互相喜歡後可以配對
- 配對雙方可以文字聊天
- 使用者可以封鎖與檢舉
- 管理者可以查看使用者、照片與檢舉資料

成功標準：

- 本機可以啟動後端 API
- 本機可以跑資料庫與測試資料
- 手機或 Android 模擬器可以登入並使用核心流程
- 至少 10 位測試使用者可以完成註冊、配對、聊天流程
- 沒有重大隱私、安全或資料遺失問題

## 2. 建議技術路線

考量你希望用 Python 環境開始，建議採用分階段策略：

第一階段先做 Python 後端，因為這台電腦已經有 Python 與 Git，可以今天開始。

推薦架構：

- 後端 API：FastAPI
- 資料庫：PostgreSQL，開發初期可先用 SQLite
- 地理距離：初期用簡化經緯度計算，後期升級 PostgreSQL + PostGIS
- 登入：JWT token
- 圖片：本機儲存起步，後期改 S3 或 Cloudflare R2
- 聊天：初期 REST API，後期升級 WebSocket
- Android App：先用 Kivy/KivyMD 做 Python 版 MVP，後期評估 Flutter 或 Kotlin
- 管理後台：先做簡單 FastAPI admin 頁面

重要判斷：

Python 可以做 Android App，但不是交友 app 的長期最佳前端技術。最務實的做法是：

1. Python FastAPI 後端先做好
2. Kivy 做 Android MVP 或桌面互動原型
3. 若市場驗證成功，再把 App 前端升級為 Flutter 或 Kotlin

## 3. 本機第一步驟

今天從這台電腦可以開始的第一步，是建立後端專案骨架。

原因：

- Python 已經安裝完成
- Git 已經安裝完成
- 後端是整個產品的核心
- Android 打包需要 Java、Android SDK、Gradle 等環境，現在尚未安裝
- 先做後端可以避免一開始卡在手機打包環境

第一步完成定義：

- 建立專案資料夾
- 建立 Python 虛擬環境
- 建立 FastAPI app
- 建立健康檢查 API
- 建立初版資料模型
- 可以在本機瀏覽器看到 API 文件
- 建立 Git 版本控管

建議第一步資料夾：

```text
F:\cursor_coding\project01\dating-app
```

專案路徑規則：

- 所有原始碼、測試、文件與本機開發檔案都以 F:\cursor_coding\project01\dating-app 作為唯一 canonical path
- 非 canonical path 不再使用
- 規劃文件集中放在 F:\cursor_coding\project01\dating-app-md

建議初始結構：

```text
dating-app/
  backend/
    app/
      main.py
      core/
      models/
      schemas/
      api/
      services/
      db/
    tests/
    requirements.txt
    .env.example
  docs/
    product-spec.md
    api-spec.md
    data-model.md
  mobile/
    README.md
```

第一批需要安裝的 Python 套件：

```text
fastapi
uvicorn
sqlalchemy
pydantic
python-dotenv
passlib
python-jose
pytest
httpx
```

## 4. MVP 功能範圍

### 4.1 帳號系統

第一版功能：

- Email 註冊
- Email 登入
- 密碼雜湊
- JWT token
- 取得目前登入使用者
- 登出由前端清除 token

JWT MVP 規格：

- 第一版使用 access token
- access token 有效時間：60 分鐘
- refresh token 暫不做，等內測穩定後再補
- token 內至少包含 user_id、is_admin、issued_at、expires_at
- 使用者停權後，API 每次驗證 token 時都要檢查 users.is_active，停權帳號即使 token 未過期也不可繼續使用

暫不做：

- Google 登入
- Apple 登入
- 手機簡訊驗證
- 忘記密碼信件

後期再加入這些，避免第一版被外部服務設定拖慢。

### 4.2 個人檔案

欄位：

- 顯示名稱
- 生日
- 年齡
- 性別
- 想認識的性別
- 城市
- 經緯度
- 自我介紹
- 身高，可選
- 興趣標籤
- 建立時間
- 最後活躍時間

規則：

- 年齡必須 18 歲以上
- 自我介紹限制長度
- 城市與距離資訊不得顯示太精準
- 檔案未完成前不能進入推薦頁

檔案完成條件：

- display_name 必填
- birthday 必填，且年齡必須 18 歲以上
- gender 必填
- interested_in 必填
- city 必填
- bio 至少 20 個中文字或 40 個英文字元
- 至少 1 張 approved 或 pending 照片
- 至少 3 個興趣標籤

profile_complete_score MVP 公式：

```text
profile_complete_score =
  display_name 10
  + birthday 10
  + gender 10
  + interested_in 10
  + city 10
  + bio_min_length 20
  + has_photo 20
  + has_3_tags 10
```

滿分 100。推薦排序可使用此分數，但未達檔案完成條件者不得進入 discover。

距離與位置隱私：

- 使用者自己的 latitude、longitude 只存在後端
- API 不回傳其他使用者的精確經緯度
- discover 與 profile detail 只回傳距離區間
- MVP 距離區間：< 1km、1-5km、5-10km、10-25km、25-50km、50km+

### 4.3 照片

第一版功能：

- 每位使用者最多 6 張照片
- 第一張為主照片
- 可刪除照片
- 可調整主照片
- 檔案大小限制
- 圖片格式限制

照片 MVP 規格：

- 單檔大小上限：5 MB
- 允許格式：JPEG、PNG、WebP
- 最小尺寸：400 x 400
- 每位使用者最多 6 張照片
- moderation_status 允許值：pending、approved、rejected
- pending 照片可在內測階段先顯示；正式公開前改為 approved 才可出現在 discover

安全需求：

- 不接受可執行檔
- 不直接信任使用者上傳的檔名
- 儲存前重新命名
- 管理後台可以標記照片不合格

### 4.4 探索與推薦

第一版推薦邏輯：

- 排除自己
- 排除已封鎖使用者
- 排除已經喜歡或略過的人
- 符合年齡偏好
- 符合性別偏好
- 符合距離範圍
- 優先顯示最近活躍者
- 優先顯示檔案完整者

第一版推薦分數：

```text
score =
  profile_complete_score
  + recent_active_score
  + distance_score
  + shared_interest_score
```

同分排序：

```text
score DESC, last_active_at DESC, created_at DESC, user_id ASC
```

shared_interest_score 依共同興趣標籤數計算，MVP 可先使用：

```text
shared_interest_score = min(shared_tag_count * 5, 20)
```

### 4.5 喜歡與配對

資料行為：

- A 喜歡 B，建立 like
- B 也喜歡 A，建立 match
- 已配對雙方可以聊天
- 略過也要記錄，避免短時間重複出現

限制：

- 免費使用者每日喜歡數可先設定為 50
- 測試階段可關閉限制
- 每日 like 額度以 Asia/Taipei 時區 00:00 重置
- like limit 做成 feature flag，內測可調整或關閉

### 4.6 聊天

第一版功能：

- 只有配對後可以聊天
- 傳送文字訊息
- 查看聊天紀錄
- 訊息時間戳
- 簡單已讀狀態可後期再做

第一版可以先用一般 API：

- App 每 3-5 秒拉一次新訊息
- 拉取新訊息使用 since_message_id，避免每次全量載入
- 後期改 WebSocket 即時聊天

### 4.7 安全、封鎖與檢舉

必做功能：

- 封鎖使用者
- 檢舉使用者
- 檢舉原因
- 管理者查看檢舉
- 管理者停權帳號

封鎖行為：

- A 封鎖 B 後，A 和 B 互相不再出現在 discover
- A 封鎖 B 後，B 不能查看 A 的 profile detail
- 若 A 和 B 已配對，封鎖後該 match 標記為 blocked，不再允許互傳新訊息
- 舊聊天紀錄 MVP 預設保留給封鎖者 A 查看，被封鎖者 B 不可再開啟該對話
- A 解除封鎖 B 後，不自動恢復 match；若要恢復，需要重新配對

停權行為：

- is_active = false 的使用者不可登入
- 已登入 token 也會在下一次 API 驗證時失效
- 停權使用者從 discover 排除
- 停權使用者不可傳訊息、按讚、更新照片或檔案
- 管理後台操作停權必須留下 admin_actions audit log

檢舉原因：

- 假帳號
- 騷擾
- 詐騙
- 不當照片
- 仇恨或威脅內容
- 其他

### 4.9 MVP 枚舉值

gender：

- woman
- man
- non_binary
- other
- prefer_not_to_say

interested_in / preferred_genders：

- women
- men
- non_binary
- everyone

photo.moderation_status：

- pending
- approved
- rejected

report.status：

- open
- reviewing
- resolved
- dismissed

report.reason：

- fake_account
- harassment
- scam
- inappropriate_photo
- hate_or_threat
- other

like.action：

- like
- pass

### 4.8 管理後台

第一版後台功能：

- 使用者列表
- 使用者詳情
- 照片列表
- 檢舉列表
- 封鎖或停權使用者
- 查看基本統計

基本統計：

- 註冊人數
- 完成檔案人數
- 今日活躍人數
- 喜歡數
- 配對數
- 訊息數
- 檢舉數

## 5. 初版資料表

### users

- id
- email
- password_hash
- is_active
- is_admin
- created_at
- updated_at

### profiles

- id
- user_id
- display_name
- birthday
- gender
- interested_in
- bio
- city
- latitude
- longitude
- height_cm
- last_active_at
- created_at
- updated_at

### tags

- id
- name
- created_at

### profile_tags

- profile_id
- tag_id
- created_at

### photos

- id
- user_id
- file_path
- sort_order
- is_primary
- moderation_status
- created_at

### preferences

- id
- user_id
- min_age
- max_age
- max_distance_km
- preferred_genders
- created_at
- updated_at

### likes

- id
- from_user_id
- to_user_id
- action
- created_at

action 可為：

- like
- pass

### matches

- id
- user_a_id
- user_b_id
- created_at
- unmatched_at

### messages

- id
- match_id
- sender_id
- body
- created_at
- read_at

### blocks

- id
- blocker_id
- blocked_id
- created_at

### reports

- id
- reporter_id
- reported_user_id
- reason
- description
- status
- created_at
- reviewed_at

### admin_actions

- id
- admin_user_id
- action_type
- target_type
- target_id
- note
- created_at

## 5.1 資料約束與索引

users：

- email UNIQUE
- is_active 預設 true
- is_admin 預設 false

profiles：

- user_id UNIQUE
- birthday 建議建立索引，供年齡篩選使用
- city 建議建立索引
- last_active_at 建議建立索引

tags：

- name UNIQUE

profile_tags：

- UNIQUE(profile_id, tag_id)

photos：

- 使用者最多 6 張照片，先由 service layer 檢查
- UNIQUE(user_id, sort_order)
- 同一 user_id 只能有一張 is_primary = true，SQLite 階段由 service layer 保證，PostgreSQL 階段改 partial unique index

likes：

- UNIQUE(from_user_id, to_user_id)
- from_user_id、to_user_id 建立索引

matches：

- 使用 user_low_id、user_high_id 儲存正規化配對，避免 A-B 與 B-A 重複
- UNIQUE(user_low_id, user_high_id)
- user_low_id = min(user_a_id, user_b_id)
- user_high_id = max(user_a_id, user_b_id)

blocks：

- UNIQUE(blocker_id, blocked_id)
- blocker_id、blocked_id 建立索引

messages：

- match_id + created_at 建立索引
- match_id + id 建立索引，支援 since_message_id polling

reports：

- status 建立索引
- reported_user_id 建立索引

admin_actions：

- admin_user_id 建立索引
- target_type + target_id 建立索引
- created_at 建立索引

## 6. API 規劃

### Auth

- POST /auth/register
- POST /auth/login
- GET /auth/me

### Profile

- GET /profiles/me
- PUT /profiles/me
- GET /profiles/{user_id}

### Photos

- POST /photos
- GET /photos/me
- DELETE /photos/{photo_id}
- PUT /photos/{photo_id}/primary

### Preferences

- GET /preferences/me
- PUT /preferences/me

### Discover

- GET /discover?limit=20&cursor={cursor}

### Likes and Matches

- POST /likes
- GET /matches
- DELETE /matches/{match_id}

### Messages

- GET /matches/{match_id}/messages?limit=50&since_message_id={id}
- POST /matches/{match_id}/messages

### Safety

- POST /blocks
- GET /blocks
- DELETE /blocks/{user_id}
- POST /reports

### Admin

- GET /admin/users?limit=50&cursor={cursor}
- GET /admin/reports?limit=50&cursor={cursor}&status={status}
- PUT /admin/reports/{report_id}
- PUT /admin/users/{user_id}/suspend
- GET /admin/photos?limit=50&cursor={cursor}&status={moderation_status}
- PUT /admin/photos/{photo_id}
- GET /admin/actions?limit=50&cursor={cursor}

Admin 認證：

- MVP 使用同一套 JWT
- users.is_admin = true 才可進入 /admin/*
- 所有停權、照片審核、檢舉處理都寫入 admin_actions

分頁規則：

- discover、messages、admin list 必須支援 limit
- limit 預設 20，最大 100
- cursor 可先使用 base64 encoded id 或 created_at
- messages 支援 since_message_id，供聊天 polling 使用

錯誤格式：

```json
{
  "error": {
    "code": "PROFILE_INCOMPLETE",
    "message": "Profile must be completed before using discover."
  }
}
```

## 7. 里程碑與日期

以 2026-06-20 作為起點，建議規劃如下。

| 里程碑 | 日期 | 完成標準 |
|---|---:|---|
| M1 專案骨架完成 | 2026-06-22 | FastAPI 本機可啟動，Git 初始化完成 |
| M2 帳號與個人檔案完成 | 2026-06-29 | 可以註冊、登入、建立檔案 |
| M3 照片與推薦 API 完成 | 2026-07-06 | 可以上傳照片並取得推薦列表 |
| M4 喜歡與配對完成 | 2026-07-13 | 雙向喜歡可以產生配對 |
| M5 聊天功能完成 | 2026-07-20 | 配對雙方可以傳送與讀取訊息 |
| M6 Android 原型完成 | 2026-08-03 | 手機或模擬器可跑核心流程 |
| M7 安全與管理後台完成 | 2026-08-17 | 可封鎖、檢舉、管理者審核 |
| M8 內測版本完成 | 2026-08-31 | staging 可連線，10 位測試者可完整使用 |

## 8. 工作階段拆解

### Phase 0：本機環境與專案骨架，1 至 2 天

任務：

- 建立專案資料夾
- 建立 Git repo
- 建立 Python 虛擬環境
- 建立 FastAPI 專案
- 建立 requirements.txt
- 建立 .env.example
- 建立 README
- 建立 docs 資料夾

完成標準：

- 本機可啟動 API
- /health 回傳 ok
- /docs 可看到 API 文件
- Git 有第一個 commit

### Phase 1：帳號與個人檔案，1 週

任務：

- users 資料模型
- profiles 資料模型
- tags 與 profile_tags 資料模型
- 註冊 API
- 登入 API
- 密碼雜湊
- JWT 驗證
- 取得目前使用者
- 建立與更新個人檔案
- 建立 GET/PUT /preferences/me
- 決定 staging 內測平台：Railway、Render 或 VPS 三選一
- 基本測試

完成標準：

- 可以建立帳號
- 可以登入取得 token
- 可以用 token 更新個人檔案
- 18 歲以下不能建立有效檔案
- 檔案完成條件有測試覆蓋
- staging 平台與部署方式已決策並寫入 docs/deployment.md

### Phase 2：照片與推薦，1 週

任務：

- photos 資料模型
- 本機圖片儲存
- 上傳照片 API
- 刪除照片 API
- 主照片 API
- preferences 資料模型
- 推薦查詢 API
- 假資料產生器
- tags 與 shared_interest_score 實作

完成標準：

- 使用者可以上傳最多 6 張照片
- 可以設定偏好
- 可以取得推薦使用者列表
- 已略過或喜歡的人不重複出現
- discover 不回傳其他使用者精確經緯度，只回傳距離區間

### Phase 3：喜歡、略過與配對，1 週

任務：

- likes 資料模型
- matches 資料模型
- 喜歡 API
- 略過 API
- 雙向喜歡自動建立 match
- 配對列表 API
- 解除配對 API
- likes、matches、blocks 的唯一性約束

完成標準：

- A 喜歡 B 不會馬上配對
- B 也喜歡 A 會產生配對
- 配對列表可以查到對方

### Phase 4：聊天，1 週

任務：

- messages 資料模型
- 傳送訊息 API
- 讀取聊天紀錄 API
- since_message_id polling
- 確認只有配對雙方能聊天
- 訊息排序
- 聊天測試

完成標準：

- 未配對不能聊天
- 配對後可以互傳訊息
- 聊天紀錄依時間正確顯示
- App 端可用 3-5 秒 polling 取得新訊息

### Phase 5：Android 原型，2 週

任務：

- 安裝 Java
- 安裝 Android Studio 或 Android SDK
- 評估 Kivy/KivyMD 打包方式
- 建立 App 專案
- 登入畫面
- 個人檔案畫面
- 探索卡片畫面
- 配對列表畫面
- 聊天畫面
- 串接後端 API
- Android 內測版本可切換 local API 與 staging API

完成標準：

- Android 手機或模擬器可登入
- 可以看到推薦
- 可以喜歡、配對、聊天

### Phase 6：安全與管理，2 週

任務：

- blocks 資料模型
- reports 資料模型
- admin_actions 資料模型
- 封鎖 API
- 檢舉 API
- 封鎖列表與解除封鎖 API
- 後台使用者列表
- 後台檢舉列表
- 後台照片審核
- 停權功能
- 管理者登入保護
- admin_actions audit log

完成標準：

- 使用者可以封鎖與檢舉
- 被封鎖者不再出現在推薦中
- 管理者可以處理檢舉
- 停權、照片審核、檢舉處理都有 audit log

### Phase 7：內測準備，2 週

任務：

- 補齊錯誤處理
- 補齊日誌
- 補齊測試
- 至少 1 條 E2E 測試：註冊 -> 完成檔案 -> 互相喜歡 -> 配對 -> 聊天
- 建立測試帳號
- 整理隱私政策草稿
- 整理服務條款草稿
- 測試資料備份策略
- 內測問卷
- staging 部署與測試者連線方式

完成標準：

- 10 位測試者可用
- 測試者不是連 localhost，而是連 staging API
- 核心流程沒有重大錯誤
- 有基本安全與客服處理流程

## 9. 本機環境補齊清單

目前已具備：

- Python 3.10.11
- Git 2.53.0

需要補齊：

- Java JDK
- Android Studio 或 Android SDK
- Docker Desktop，可稍後
- PostgreSQL，可稍後
- Firebase 專案，可稍後

安裝順序建議：

1. 先不用安裝 Docker 和 Java，直接開始 FastAPI 後端
2. 後端核心完成後再安裝 Java 與 Android Studio
3. Android 原型開始前再處理 Kivy 打包
4. 要部署或多人測試時再補 Docker、PostgreSQL、雲端儲存

## 10. 今日可執行清單

今天只做這些，避免範圍太大：

1. 建立 F:\cursor_coding\project01\dating-app 專案資料夾
2. 建立 backend、docs、mobile 三個資料夾
3. 建立 Python 虛擬環境
4. 安裝 FastAPI 基本套件
5. 建立 /health API
6. 建立 README
7. 建立 product-spec.md
8. 初始化 Git
9. 確認本機可以打開 API 文件

今日完成後，下一步才開始寫帳號系統。

## 11. 風險與處理方式

| 風險 | 影響 | 機率 | 處理方式 |
|---|---|---|---|
| Python Android 打包不穩 | 高 | 中 | 先做後端與桌面原型，必要時前端改 Flutter |
| 一開始功能做太多 | 高 | 高 | 嚴格限制 MVP，只做註冊、檔案、推薦、配對、聊天 |
| 交友平台安全問題 | 高 | 高 | 第一版就做封鎖、檢舉、18 歲限制 |
| 圖片與個資外洩 | 高 | 中 | 上傳重新命名、權限控管、後期改私有儲存 |
| 推薦品質不好 | 中 | 高 | 第一版用規則型，收集資料後再優化 |
| Google Play 上架政策變動 | 中 | 中 | 上架前重新確認最新政策 |
| 開發者環境卡關 | 中 | 中 | 後端優先，Android 打包延後到核心 API 完成 |
| 內測部署太晚決定 | 高 | 中 | Phase 1 就決定 staging 平台，M8 前不使用 localhost 內測 |

## 12. 決策紀錄

目前已決策：

- 先做 Android
- 優先使用 Python 環境
- 後端採 FastAPI
- MVP 不做 iOS
- MVP 不做影片、直播、複雜 AI 推薦
- 第一個實作目標是後端 API
- canonical project path 為 F:\cursor_coding\project01\dating-app
- 規劃文件集中放在 F:\cursor_coding\project01\dating-app-md
- MVP 預設台灣市場
- MVP 預設嚴肅交友
- MVP 使用城市 + 粗略距離，不對其他使用者回傳精確 GPS
- MVP 免費使用者每日 50 likes，以 Asia/Taipei 時區 00:00 重置

尚未決策：

- App 名稱
- 品牌定位
- 是否一開始就需要付費功能
- 是否需要手機驗證
- staging 平台使用 Railway、Render 或 VPS
- Android MVP 最終使用 Kivy/KivyMD 或改 Flutter

## 13. 下一步建議

下一個實際動作應該是建立專案骨架。

建議我接下來執行：

- 建立 F:\cursor_coding\project01\dating-app
- 建立 backend FastAPI
- 建立 /health API
- 建立初始 README
- 建立 Git repo

完成後，你會得到一個可以在這台電腦跑起來的交友 app 後端起點。
