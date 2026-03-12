# Pinterest Analytics Tool - Setup Guide

## 📁 Project Structure

```
pinterest-analytics/
├── index.html              # Landing Page (Product Introduction)
├── dashboard.html          # Dashboard（Data Analysis）
├── scraper/
│   ├── pinterest_scraper.py    # Scraper Script
│   ├── requirements.txt        # Python Dependencies
│   └── pinterest_session.json  # Pinterest login Session
├── .github/
│   └── workflows/
│       └── daily-scrape.yml    # GitHub Actions Automation
└── README.md
```

---

## 🚀 Quick Start

### Step 1: Local Testing

```bash
# Install dependencies
cd scraper
pip install -r requirements.txt
playwright install chromium

# Add Google Credentials
# Rename your JSON key file to credentials.json and place it in the scraper/ folder

# Run scraper (Initial login to Pinterest required for the first time)
python pinterest_scraper.py
```

### Step 2: Configure GitHub Secrets

Set the following Secrets in your GitHub Repository:

1. **GOOGLE_CREDENTIALS**
   - Paste the entire content of the JSON key file

2. **PINTEREST_SESSION**
   - After running the scraper once, paste the content of pinterest_session.json here

#### How to set up GitHub Secrets:
1. Go to Repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Enter Name and Content

### Step 3: Enable GitHub Actions

1. Go to Repository → Actions
2. If prompted to enable workflows, click to enable
3. To perform a manual test: Click "Pinterest Analytics Daily Scraper" → "Run workflow"

---

## ⏰ Automation Schedule

- **Daily at 9:00 AM EST (10:00 PM Taiwan Time)
- Can also be triggered manually

---

## 🔐 Password Configuration

The password for the Landing Page is set in index.html:

```javascript
const ACCESS_PASSWORD = 'pinterest2026';  // Change this to your desired password
```

---

## 📊 Google Sheets Format

| Field | Description |
|------|------|
| date | Date (YYYY-MM-DD) |
| impressions | Impressions |
| saves | Saves |
| pin_clicks | Pin Click |
| outbound_clicks | Outbound Link Clicks |
| engagement_rate | Engagement Rate (%) |
| pin_title | Pin Title (for individual Pin tracking) |
| pin_id | Pin ID (for individual Pin tracking) |

---

## ❓ FAQ

### Q: Scraper execution failed?
- Check if the Pinterest Session has expired
- Re-run the local scraper to log in and update the PINTEREST_SESSION secret

### Q: Data not writing to Google Sheets?
- Confirm that the Google Sheet is shared with the Service Account email
- Check if the GOOGLE_CREDENTIALS secret is correct

### Q: Want to track specific Pins?
- Modify the get_pin_stats() function in pinterest_scraper.py

---

## 🛠️ Developer Information

**Built by:** Wei Wei Chiang  
**GitHub:** [weiweichiang0813-art](https://github.com/weiweichiang0813-art)  
**Portfolio:** [weiweichiang0813-art.github.io/profolio](https://weiweichiang0813-art.github.io/profolio/)
