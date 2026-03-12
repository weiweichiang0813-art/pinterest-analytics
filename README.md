# PinTrend Analytics - Open Platform by wwclab.

PinTrend Analytics is a professional analytics platform designed for Pinterest creators. It combines automated web scraping, cloud storage via Google Sheets, and an intuitive dashboard to transform data into growth insights.

---

## 📂 Project Structure

- **index.html**: Landing Page (wwclab. branded product entry)
- **dashboard.html**: Analytics Dashboard (Trend visualization)
- **privacy.html**: Privacy Policy (Compliant with Pinterest API standards)
- **logo.png**: wwclab. Circular Brand Logo
- **scraper/**: Automated scraper and Python dependencies

---

## 🚀 Quick Start Guide

## 1. Local Setup

```bash
cd scraper
pip install -r requirements.txt
playwright install chromium
Note: Place your credentials.json inside the scraper/ folder.
```

## 2. GitHub Secrets Configuration


- Go to Settings > Secrets and variables > Actions and add:

- GOOGLE_CREDENTIALS: Full content of credentials.json

- PINTEREST_SESSION: Content of pinterest_session.json


## 3. Automation


- Schedule: Daily at 9:00 AM EST.

- Manual: Go to Actions tab and click "Run workflow".


## 📊 Core Features


- wwclab. Visual Identity: Deep-blue professional theme with circular logo.

- Smart Data Cleaning: Automatically removes "Untitled Pin" or "Pinterest" entries.

- Performance Trends: Interactive charts for Impressions, Clicks, and Saves.

- OAuth 2.0 Ready: Pre-configured for official Pinterest API integration.


## 🛠️ Data Schema (Google Sheets)


- date: Sync Date (YYYY-MM-DD)

- impressions: Cumulative views

- saves: Total times saved

- pin_clicks: Total closeup clicks

- outbound_clicks: Clicks to external website (Terradomi)

- engagement_rate: (Clicks + Saves) / Impressions * 100

- pin_title: Validated title (Filtered for accuracy)


## 👨‍💻 Developer Information

Built by: Wei Wei Chiang

Brand: wwclab.

GitHub: weiweichiang0813-art

Portfolio: View My Work


## 📝 Note for API Reviewers
The authorized Redirect URI for the Pinterest App (ID: 1552254) is:
https://www.google.com/search?q=https://weiweichiang0813-art.github.io/pinterest-analytics/dashboard.html
