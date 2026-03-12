# 📌 Pinterest Analytics Tool

A dedicated data automation and visualization tool built for **Terradomi Candle Co.** to track Pinterest performance and analyze keyword trends.

---

## 📁 Project Structure

```text
pinterest-analytics/
├── index.html              # Landing Page (Product Introduction)
├── dashboard.html          # Dashboard (Data Analysis)
├── scraper/
│   ├── pinterest_scraper.py    # Scraper Script (Python/Playwright)
│   ├── requirements.txt        # Python Dependencies
│   └── pinterest_session.json  # Pinterest Login Session (LOCAL ONLY - Git Ignored)
├── .github/
│   └── workflows/
│       └── daily-scrape.yml    # GitHub Actions Automation
└── README.md               # Project Documentation
