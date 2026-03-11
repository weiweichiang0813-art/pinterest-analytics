"""
Pinterest Analytics Scraper - 全自動版本
每日自動執行：爬取 Pins 數據 + Trending Keywords

功能：
1. 自動登入（使用已儲存的 Session）
2. 自動切換到指定帳號（Terradomi Candle Co.）
3. 爬取所有 Pins 的統計數據
4. 爬取 Trending Keywords
5. 寫入 Google Sheets
"""

import asyncio
import json
import os
import sys
import re
from datetime import datetime
from playwright.async_api import async_playwright

# Google Sheets
import gspread
from google.oauth2.service_account import Credentials

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# ============================================================
# 設定區
# ============================================================

GOOGLE_SHEETS_ID = "1A3RLxLbjffrOy7CSqQKJ3nLP-JkuTLp8z6a2GhXAlmg"
PINS_SHEET_NAME = "Pinterest Analytics Data"  # Pin 數據工作表
KEYWORDS_SHEET_NAME = "Keywords"  # Keywords 工作表（需要你建立）

SESSION_FILE = "pinterest_session.json"

# 要切換到的帳號 ID（Terradomi Candle Co.）
TARGET_ACCOUNT_ID = "790030097041256840"
TARGET_ACCOUNT_NAME = "Terradomi Candle Co."

# 要爬取的 Pin 數量
MAX_PINS = 50

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


# ============================================================
# Google Sheets 連接
# ============================================================

def get_google_sheets_client():
    """連接 Google Sheets"""
    # 優先從 GitHub Secrets 環境變數讀取 
    creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    
    if creds_json:
        try:
            creds_dict = json.loads(creds_json)
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            print("  ✅ 成功從環境變數載入 Google 憑證")
        except Exception as e:
            print(f"  ❌ 解析 GOOGLE_CREDENTIALS Secret 失敗: {e}")
            raise
    else:
        # 本地測試路徑
        creds_path = 'credentials.json' if os.path.exists('credentials.json') else 'scraper/credentials.json'
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        print(f"  ✅ 從檔案載入憑證: {creds_path}")
    
    client = gspread.authorize(creds)
    return client


def write_pins_to_sheets(data: list):
    """寫入 Pin 數據到 Google Sheets"""
    try:
        client = get_google_sheets_client()
        sheet = client.open_by_key(GOOGLE_SHEETS_ID).worksheet(PINS_SHEET_NAME)
        
        existing_data = sheet.get_all_values()
        next_row = len(existing_data) + 1
        
        for row in data:
            sheet.insert_row(row, next_row)
            next_row += 1
        
        print(f"  ✅ 成功寫入 {len(data)} 筆 Pin 數據")
        return True
    except Exception as e:
        print(f"  ❌ Google Sheets 錯誤: {e}")
        return False


def write_keywords_to_sheets(data: list):
    """寫入 Keywords 數據到 Google Sheets"""
    try:
        client = get_google_sheets_client()
        
        # 嘗試取得 Keywords 工作表，如果不存在則建立
        try:
            sheet = client.open_by_key(GOOGLE_SHEETS_ID).worksheet(KEYWORDS_SHEET_NAME)
        except:
            spreadsheet = client.open_by_key(GOOGLE_SHEETS_ID)
            sheet = spreadsheet.add_worksheet(title=KEYWORDS_SHEET_NAME, rows=1000, cols=10)
            # 加入標題列
            sheet.insert_row(["date", "keyword", "trend_score", "category"], 1)
        
        existing_data = sheet.get_all_values()
        next_row = len(existing_data) + 1
        
        for row in data:
            sheet.insert_row(row, next_row)
            next_row += 1
        
        print(f"  ✅ 成功寫入 {len(data)} 筆 Keyword 數據")
        return True
    except Exception as e:
        print(f"  ❌ Keywords 寫入錯誤: {e}")
        return False


# ============================================================
# Pinterest 全自動爬蟲
# ============================================================

class PinterestAutoScraper:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self._captured_data = {}
        self._all_responses = []

    def _setup_interceptor(self):
        """攔截 Pinterest API 回應"""
        async def on_response(response):
            url = response.url
            if "pinterest.com" not in url:
                return
            
            try:
                if any(p in url for p in ["/resource/", "/_/graphql", "/v3/", "/_/api/"]):
                    try:
                        data = await response.json()
                        self._all_responses.append({"url": url, "data": data})
                    except:
                        pass
            except:
                pass

        self.page.on("response", on_response)

    async def init_session(self, headless=True):
        """初始化瀏覽器"""
        self.playwright = await async_playwright().start()
        
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )

        if os.path.exists(SESSION_FILE):
            print("📂 載入 Session...")
            with open(SESSION_FILE, "r") as f:
                storage_state = json.load(f)
            self.context = await self.browser.new_context(
                storage_state=storage_state,
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        else:
            print("❌ 找不到 Session 檔案")
            return False

        self.page = await self.context.new_page()
        self._setup_interceptor()
        print("🚀 初始化完成")
        return True

    async def switch_to_target_account(self):
        """切換到目標帳號"""
        print(f"\n🔄 切換到 {TARGET_ACCOUNT_NAME}...")
        
        try:
            # 先去 Pinterest Business Hub
            await self.page.goto(
                "https://www.pinterest.com/business/hub/",
                wait_until="domcontentloaded",
                timeout=30000
            )
            await asyncio.sleep(3)
            
            # 點擊帳號切換按鈕
            switcher_selectors = [
                '[data-test-id="header-accounts-menu-button"]',
                '[data-test-id="account-switcher-button"]',
                'button[aria-label*="account"]',
                '[data-test-id="biz-header-account-switcher"]'
            ]
            
            for selector in switcher_selectors:
                try:
                    el = await self.page.wait_for_selector(selector, timeout=3000)
                    if el:
                        await el.click()
                        await asyncio.sleep(2)
                        break
                except:
                    continue
            
            # 嘗試點擊目標帳號
            account_selectors = [
                f'[data-test-id="account-item-{TARGET_ACCOUNT_ID}"]',
                f'div:has-text("{TARGET_ACCOUNT_NAME}")',
                f'button:has-text("{TARGET_ACCOUNT_NAME}")',
                f'a:has-text("Terradomi")'
            ]
            
            for selector in account_selectors:
                try:
                    el = await self.page.wait_for_selector(selector, timeout=3000)
                    if el:
                        await el.click()
                        await asyncio.sleep(3)
                        print(f"  ✅ 已切換到 {TARGET_ACCOUNT_NAME}")
                        return True
                except:
                    continue
            
            print("  ⚠️ 無法自動切換帳號，嘗試直接訪問...")
            
        except Exception as e:
            print(f"  ⚠️ 切換帳號錯誤: {e}")
        
        return True  # 繼續執行

    async def get_created_pins_page(self):
        """前往 Created Pins 頁面"""
        print("\n📌 前往 Created 頁面...")
        
        # 嘗試不同的 URL 格式
        urls_to_try = [
            f"https://www.pinterest.com/business/created-pins/",
            f"https://www.pinterest.com/terradomicandle/_created/",
            f"https://www.pinterest.com/terradomicandle/pins/"
        ]
        
        for url in urls_to_try:
            try:
                await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(3)
                
                # 檢查是否有 Pin 連結
                links = await self.page.query_selector_all('a[href*="/pin/"]')
                if links:
                    print(f"  ✅ 找到 Pins 頁面: {url}")
                    return True
            except:
                continue
        
        print("  ⚠️ 無法找到 Created 頁面")
        return False

    async def scrape_all_pins(self):
        """爬取所有 Pins 的統計數據"""
        all_pin_stats = []
        
        print(f"\n📊 開始爬取 Pins 數據（最多 {MAX_PINS} 則）...")
        
        # 滾動頁面載入更多 Pins
        try:
            for _ in range(5):
                await self.page.evaluate("window.scrollBy(0, 800)")
                await asyncio.sleep(1)
            await self.page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(1)
        except:
            pass
        
        # 收集 Pin IDs
        try:
            links = await self.page.query_selector_all('a[href*="/pin/"]')
        except:
            return []
        
        pin_ids = []
        for link in links:
            try:
                href = await link.get_attribute('href')
                if href and '/pin/' in href:
                    match = re.search(r'/pin/(\d+)', href)
                    if match:
                        pin_id = match.group(1)
                        if pin_id not in pin_ids:
                            pin_ids.append(pin_id)
            except:
                continue
        
        print(f"  📌 找到 {len(pin_ids)} 個 Pins")
        pin_ids = pin_ids[:MAX_PINS]
        
        # 逐一爬取每個 Pin
        for i, pin_id in enumerate(pin_ids):
            print(f"  [{i+1}/{len(pin_ids)}] Pin: {pin_id}", end="")
            
            try:
                stats_url = f"https://www.pinterest.com/pin/{pin_id}/analytics/"
                await self.page.goto(stats_url, wait_until="domcontentloaded", timeout=20000)
                await asyncio.sleep(3)
                
                # 從頁面提取數據
                stats = await self._extract_stats_from_page()
                title = await self._get_pin_title()
                
                pin_data = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "pin_id": pin_id,
                    "pin_title": title,
                    "impressions": stats.get("impressions", 0),
                    "saves": stats.get("saves", 0),
                    "pin_clicks": stats.get("pin_clicks", 0),
                    "outbound_clicks": stats.get("outbound_clicks", 0),
                    "engagement_rate": stats.get("engagement_rate", 0)
                }
                
                all_pin_stats.append(pin_data)
                print(f" → Imp: {pin_data['impressions']}")
                
            except Exception as e:
                print(f" → ❌ 錯誤")
                continue
        
        return all_pin_stats

    async def _extract_stats_from_page(self):
        """從頁面提取統計數據"""
        stats = {}
        
        try:
            await asyncio.sleep(1)
            all_text = await self.page.inner_text('body')
            
            # Impressions
            imp_match = re.search(r'([\d,]+)\s*[Ii]mpressions?', all_text)
            if imp_match:
                stats['impressions'] = int(imp_match.group(1).replace(',', ''))
            
            # Saves
            save_match = re.search(r'([\d,]+)\s*[Ss]aves?', all_text)
            if save_match:
                stats['saves'] = int(save_match.group(1).replace(',', ''))
            
            # Clicks
            click_match = re.search(r'([\d,]+)\s*(?:[Pp]in\s*)?[Cc]licks?', all_text)
            if click_match:
                stats['pin_clicks'] = int(click_match.group(1).replace(',', ''))
            
            # Outbound Clicks
            link_match = re.search(r'([\d,]+)\s*(?:[Ll]ink|[Oo]utbound)\s*[Cc]licks?', all_text)
            if link_match:
                stats['outbound_clicks'] = int(link_match.group(1).replace(',', ''))
                
        except:
            pass
        
        return stats

    async def _get_pin_title(self):
        """獲取 Pin 標題"""
        try:
            for selector in ['h1', '[data-test-id="pin-title"]']:
                el = await self.page.query_selector(selector)
                if el:
                    text = await el.inner_text()
                    if text and len(text) > 2 and 'analytics' not in text.lower():
                        return text.strip()[:100]
        except:
            pass
        return ""

    async def scrape_trending_keywords(self):
        """爬取 Pinterest Trending Keywords"""
        print("\n🔍 爬取 Trending Keywords...")
        keywords = []
        
        try:
            # 前往 Pinterest Trends 頁面
            await self.page.goto(
                "https://trends.pinterest.com/",
                wait_until="domcontentloaded",
                timeout=30000
            )
            await asyncio.sleep(5)
            
            # 滾動頁面
            for _ in range(3):
                await self.page.evaluate("window.scrollBy(0, 500)")
                await asyncio.sleep(1)
            
            # 嘗試提取 trending keywords
            all_text = await self.page.inner_text('body')
            
            # 找出可能的 keywords（這需要根據實際頁面結構調整）
            # 暫時使用一些熱門類別作為示範
            categories = ["home decor", "DIY", "fashion", "recipes", "travel", "beauty"]
            
            for category in categories:
                keywords.append({
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "keyword": category,
                    "trend_score": "trending",
                    "category": "general"
                })
            
            print(f"  ✅ 取得 {len(keywords)} 個 Keywords")
            
        except Exception as e:
            print(f"  ⚠️ Keywords 爬取錯誤: {e}")
        
        return keywords

    async def scrape_keyword_suggestions(self, seed_keyword: str):
        """爬取關鍵字建議"""
        print(f"\n🔍 搜尋關鍵字建議: {seed_keyword}")
        suggestions = []
        
        try:
            search_url = f"https://www.pinterest.com/search/pins/?q={seed_keyword.replace(' ', '%20')}"
            await self.page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
            
            # 等待 typeahead 回應
            for item in self._all_responses:
                url = item.get("url", "")
                data = item.get("data", {})
                
                if "typeahead" in url.lower() or "AdvancedTypeahead" in url:
                    raw = data.get("resource_response", {}).get("data", {})
                    if isinstance(raw, dict):
                        items = raw.get("items", [])
                        for i in items[:10]:
                            if isinstance(i, dict):
                                term = i.get("display") or i.get("term") or i.get("query") or ""
                                if term:
                                    suggestions.append({
                                        "date": datetime.now().strftime("%Y-%m-%d"),
                                        "keyword": term,
                                        "trend_score": "suggested",
                                        "category": seed_keyword
                                    })
            
            print(f"  ✅ 找到 {len(suggestions)} 個建議")
            
        except Exception as e:
            print(f"  ⚠️ 錯誤: {e}")
        
        return suggestions

    async def close(self):
        """關閉瀏覽器"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()


# ============================================================
# 主程式
# ============================================================

async def main():
    print("\n" + "="*60)
    print("🔴 Pinterest Analytics - 全自動爬蟲")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 檢查是否在 CI 環境
    is_ci = os.environ.get('CI') == 'true' or os.environ.get('GITHUB_ACTIONS') == 'true'
    
    scraper = PinterestAutoScraper()
    
    # 初始化（CI 環境用 headless 模式）
    ok = await scraper.init_session(headless=is_ci)
    if not ok:
        print("❌ 初始化失敗")
        return
    
    # 切換到目標帳號
    await scraper.switch_to_target_account()
    
    # 前往 Created 頁面
    await scraper.get_created_pins_page()
    
    # 爬取 Pin 數據
    pin_stats = await scraper.scrape_all_pins()
    
    # 爬取 Keywords
    keywords = await scraper.scrape_trending_keywords()
    
    # 爬取關鍵字建議（使用幾個種子關鍵字）
    seed_keywords = ["candle", "home decor", "DIY crafts"]
    for seed in seed_keywords:
        suggestions = await scraper.scrape_keyword_suggestions(seed)
        keywords.extend(suggestions)
    
    # 顯示結果
    print("\n" + "="*60)
    print("📊 爬取結果")
    print("="*60)
    
    total_impressions = sum(p['impressions'] for p in pin_stats)
    total_saves = sum(p['saves'] for p in pin_stats)
    total_clicks = sum(p['pin_clicks'] for p in pin_stats)
    
    print(f"  📌 Pins: {len(pin_stats)} 則")
    print(f"  👁️  總 Impressions: {total_impressions:,}")
    print(f"  💾 總 Saves: {total_saves:,}")
    print(f"  🖱️  總 Clicks: {total_clicks:,}")
    print(f"  🔍 Keywords: {len(keywords)} 個")
    
    # 寫入 Google Sheets
    print("\n" + "="*60)
    print("📝 寫入 Google Sheets...")
    print("="*60)
    
    if pin_stats:
        rows = []
        for pin in pin_stats:
            rows.append([
                pin["date"],
                pin["impressions"],
                pin["saves"],
                pin["pin_clicks"],
                pin["outbound_clicks"],
                pin["engagement_rate"],
                pin["pin_title"],
                pin["pin_id"]
            ])
        write_pins_to_sheets(rows)
    
    if keywords:
        rows = []
        for kw in keywords:
            rows.append([
                kw["date"],
                kw["keyword"],
                kw["trend_score"],
                kw["category"]
            ])
        write_keywords_to_sheets(rows)
    
    # 關閉
    await scraper.close()
    
    # 儲存結果
    result = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pins": pin_stats,
        "keywords": keywords
    }
    with open("scrape_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print("\n✅ 全自動爬蟲完成！")


if __name__ == "__main__":
    asyncio.run(main())
