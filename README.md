# Pinterest Analytics Tool - 設定指南

## 📁 專案結構

```
pinterest-analytics/
├── index.html              # Landing Page（產品介紹）
├── dashboard.html          # Dashboard（數據分析）
├── scraper/
│   ├── pinterest_scraper.py    # 爬蟲程式
│   ├── requirements.txt        # Python 依賴
│   └── pinterest_session.json  # Pinterest 登入 Session（不要上傳！）
├── .github/
│   └── workflows/
│       └── daily-scrape.yml    # GitHub Actions 自動化
└── README.md
```

---

## 🚀 快速開始

### Step 1：本地測試

```bash
# 安裝依賴
cd scraper
pip install -r requirements.txt
playwright install chromium

# 放入 Google 憑證
# 把你的 JSON 金鑰檔案重新命名為 credentials.json 放在 scraper/ 資料夾

# 執行爬蟲（第一次會需要登入 Pinterest）
python pinterest_scraper.py
```

### Step 2：設定 GitHub Secrets

在你的 GitHub Repository 設定以下 Secrets：

1. **GOOGLE_CREDENTIALS**
   - 把整個 JSON 金鑰檔案的內容貼上去

2. **PINTEREST_SESSION**
   - 執行過一次爬蟲後，把 `pinterest_session.json` 的內容貼上去

#### 如何設定 GitHub Secrets：
1. 進入 Repository → Settings → Secrets and variables → Actions
2. 點擊 "New repository secret"
3. 輸入名稱和內容

### Step 3：啟用 GitHub Actions

1. 進入 Repository → Actions
2. 如果看到提示要啟用 workflows，點擊啟用
3. 可以手動執行一次測試：點擊 "Pinterest Analytics Daily Scraper" → "Run workflow"

---

## ⏰ 自動執行時間

- **每天早上 9:00 AM EST**（台灣時間晚上 10:00）
- 也可以手動觸發執行

---

## 🔐 密碼設定

Landing Page 的密碼在 `index.html` 中設定：

```javascript
const ACCESS_PASSWORD = 'pinterest2026';  // 改成你想要的密碼
```

---

## 📊 Google Sheets 格式

| 欄位 | 說明 |
|------|------|
| date | 日期 (YYYY-MM-DD) |
| impressions | 曝光數 |
| saves | 儲存數 |
| pin_clicks | Pin 點擊數 |
| outbound_clicks | 外部連結點擊數 |
| engagement_rate | 互動率 (%) |
| pin_title | Pin 標題（單一 Pin 追蹤時用） |
| pin_id | Pin ID（單一 Pin 追蹤時用） |

---

## ❓ 常見問題

### Q: 爬蟲執行失敗？
- 檢查 Pinterest Session 是否過期
- 重新執行一次本地爬蟲登入，更新 PINTEREST_SESSION secret

### Q: 數據沒有寫入 Google Sheets？
- 確認 Google Sheets 有分享給 Service Account email
- 檢查 GOOGLE_CREDENTIALS secret 是否正確

### Q: 想要追蹤特定 Pin？
- 修改 `pinterest_scraper.py` 中的 `get_pin_stats()` 函數

---

## 🛠️ 開發者資訊

**Built by:** Wei Wei Chiang  
**GitHub:** [weiweichiang0813-art](https://github.com/weiweichiang0813-art)  
**Portfolio:** [weiweichiang0813-art.github.io/profolio](https://weiweichiang0813-art.github.io/profolio/)
