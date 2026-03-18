# 📌 PinTrend Analytics Pro

<div align="center">

![PinTrend Analytics](https://img.shields.io/badge/PinTrend-Analytics%20Pro-BD081C?style=for-the-badge&logo=pinterest&logoColor=white)
![Powered by](https://img.shields.io/badge/Powered%20by-Google%20Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)
![Vercel](https://img.shields.io/badge/Deployed%20on-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)

**A professional Pinterest analytics platform with AI-powered insights**

[Live Demo](https://pinterest-analytics-gamma.vercel.app) • [Portfolio](https://weiweichiang0813-art.github.io/portfolio/)

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📊 **Performance Dashboard** | Real-time analytics with impressions, clicks, saves, and engagement rates |
| 🤖 **AI-Powered Insights** | Smart performance analysis powered by Google Gemini AI |
| ✍️ **Content Creator** | AI-generated Pinterest Pin titles, descriptions, and hashtags |
| 👥 **Audience Analytics** | Demographics, interests, and best posting times |
| 🔍 **Keyword Research** | Trending keywords and SEO optimization suggestions |
| 🔄 **Automated Data Sync** | Daily scraping with GitHub Actions + Google Sheets storage |

---

## 🖥️ Pages Overview

```
├── index.html          # Home - Performance Summary
├── analytics.html      # Detailed Analytics + AI Insights
├── audience.html       # Audience Demographics & Interests
├── keywords.html       # Keyword Research & Trends
├── creator.html        # AI Content Generator
├── privacy.html        # Privacy Policy
└── api/
    ├── gemini.py       # Google Gemini AI Integration
    ├── user.py         # Pinterest User API
    ├── pins.py         # Pinterest Pins API
    ├── boards.py       # Pinterest Boards API
    └── analytics.py    # Pinterest Analytics API
```

---

## 🚀 Tech Stack

| Category | Technologies |
|----------|--------------|
| **Frontend** | HTML5, CSS3, JavaScript, Chart.js |
| **Backend** | Python, Vercel Serverless Functions |
| **AI** | Google Gemini 1.5 Flash |
| **APIs** | Pinterest API, Google Sheets API |
| **Deployment** | Vercel, GitHub Pages |
| **Automation** | GitHub Actions (Daily Scraper) |
| **Design** | Instrument Serif, Manrope, JetBrains Mono |

---

## 📦 Installation

### Prerequisites

- Python 3.9+
- Pinterest Developer Account
- Google Cloud Console Account (for Gemini API)
- Vercel Account

### 1. Clone the Repository

```bash
git clone https://github.com/weiweichiang0813-art/pinterest-analytics.git
cd pinterest-analytics
```

### 2. Install Dependencies

```bash
cd scraper
pip install -r requirements.txt
playwright install chromium
```

### 3. Configure Environment Variables (Vercel)

Go to **Vercel Dashboard** → **Settings** → **Environment Variables** and add:

| Variable | Description |
|----------|-------------|
| `PINTEREST_APP_ID` | Your Pinterest App ID |
| `PINTEREST_APP_SECRET` | Your Pinterest App Secret |
| `PINTEREST_ACCESS_TOKEN` | Your Pinterest Access Token |
| `GEMINI_API_KEY` | Your Google Gemini API Key |
| `API_SECRET_KEY` | Custom secret key for API authentication |

### 4. Configure GitHub Secrets (for Scraper)

Go to **Settings** → **Secrets and variables** → **Actions** and add:

| Secret | Description |
|--------|-------------|
| `GOOGLE_CREDENTIALS` | Full content of `credentials.json` |
| `PINTEREST_SESSION` | Content of `pinterest_session.json` |

---

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/user` | GET | Get Pinterest user profile |
| `/api/pins` | GET | Get user's pins |
| `/api/boards` | GET | Get user's boards |
| `/api/analytics` | GET | Get analytics data |
| `/api/gemini` | POST | AI content generation |

### Authentication

All API endpoints require authentication via header or query parameter:

```bash
# Header
X-API-Key: your_api_secret_key

# Query Parameter
?api_key=your_api_secret_key
```

---

## 📊 Data Schema (Google Sheets)

| Column | Type | Description |
|--------|------|-------------|
| `date` | Date | Sync date (YYYY-MM-DD) |
| `impressions` | Integer | Total views |
| `saves` | Integer | Total saves |
| `pin_clicks` | Integer | Closeup clicks |
| `outbound_clicks` | Integer | External link clicks |
| `engagement_rate` | Float | (Clicks + Saves) / Impressions × 100 |
| `pin_title` | String | Pin title (filtered) |

---

## 🤖 AI Features

### Content Creator
Generate optimized Pinterest content with customizable:
- **Tone**: Friendly, Professional, Playful, Luxurious, Minimalist
- **Output**: SEO-optimized titles, engaging descriptions, relevant hashtags

### Performance Insights
AI analyzes your data and provides:
- What's working well
- Areas for improvement
- Content strategy recommendations
- Trend observations

---

## 📅 Automation

The scraper runs automatically via GitHub Actions:

- **Schedule**: Daily at 9:00 AM EST
- **Manual**: Go to Actions tab → "Run workflow"

---

## 🎨 Design System

| Element | Value |
|---------|-------|
| **Primary Color** | Pinterest Red `#BD081C` |
| **Background** | Light Gray `#F8FAFC` |
| **Text** | Navy `#1E3A5F` |
| **Fonts** | Instrument Serif (Display), Manrope (Body), JetBrains Mono (Code) |

---

## 👨‍💻 Developer

<div align="center">

**Wei Wei Chiang**

[![GitHub](https://img.shields.io/badge/GitHub-weiweichiang0813--art-181717?style=flat-square&logo=github)](https://github.com/weiweichiang0813-art)
[![Portfolio](https://img.shields.io/badge/Portfolio-View%20My%20Work-BD081C?style=flat-square)](https://weiweichiang0813-art.github.io/portfolio/)

**Brand**: wwclab.

</div>

---

## 📝 License

This project is for personal and educational use.

---

## 🔗 Links

- **Live Site**: [pinterest-analytics-gamma.vercel.app](https://pinterest-analytics-gamma.vercel.app)
- **GitHub Pages**: [weiweichiang0813-art.github.io/pinterest-analytics](https://weiweichiang0813-art.github.io/pinterest-analytics/)
- **Portfolio**: [weiweichiang0813-art.github.io/portfolio](https://weiweichiang0813-art.github.io/portfolio/)

---

<div align="center">

Made with ❤️ by Wei Wei Chiang • Powered by Pinterest API & Google Gemini AI

</div>
