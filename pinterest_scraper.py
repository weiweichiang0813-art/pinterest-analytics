"""
Pinterest Analytics Scraper
自動抓取 Pinterest Analytics 數據並儲存到 Google Sheets

功能：
- 登入 Pinterest 帳號
- 抓取 Analytics 數據（Impressions, Saves, Clicks 等）
- 自動寫入 Google Sheets
- 支援 GitHub Actions 自動執行
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from playwright.async_api import async_playwright

# Google Sheets
import gspread
from google.oauth2.service_account import Credentials

# ============================================================
# 設定區
# ============================================================

# Google Sheets 設定
GOOGLE_SHEETS_ID = "1A3RLxLbjffrOy7CSqQKJ3nLP-JkuTLp8z6a2GhXAlmg"
SHEET_NAME = "Sheet1"  # 工作表名稱

# Pinterest Session 檔案
SESSION_FILE = "pinterest_session.json"

# Google API 範圍
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


# ============================================================
# Google Sheets 連接
# ============================================================

def get_google_sheets_client():
    """連接 Google Sheets"""
    # 優先使用環境變數（GitHub Actions）
    if os.environ.get('GOOGLE_CREDENTIALS'):
        creds_dict = json.loads(os.environ['GOOGLE_CREDENTIALS'])
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    else:
        # 本地開發使用 JSON 檔案
        creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
    
    client = gspread.authorize(creds)
    return client


def write_to_sheets(data: list):
    """寫入數據到 Google Sheets"""
    try:
        client = get_google_sheets_client()
        sheet = client.open_by_key(GOOGLE_SHEETS_ID).worksheet(SHEET_NAME)
        
        # 取得現有數據行數
        existing_data = sheet.get_all_values()
        next_row = len(existing_data) + 1
        
        # 寫入每筆數據
        for row in data:
            sheet.insert_row(row, next_row)
            next_row += 1
            print(f"  ✅ 寫入: {row}")
        
        print(f"\n📊 成功寫入 {len(data)} 筆數據到 Google Sheets")
        return True
    except Exception as e:
        print(f"❌ Google Sheets 錯誤: {e}")
        return False


# ============================================================
# Pinterest Analytics Scraper
# ============================================================

class PinterestAnalyticsScraper:
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
                # 攔截 Analytics 相關 API
                if any(keyword in url for keyword in [
                    "AnalyticsResource",
                    "analytics",
                    "UserSummaryResource",
                    "PinAnalytics",
                    "AudienceInsights",
                    "PerformanceResource"
                ]):
                    try:
                        data = await response.json()
                        endpoint = url.split("/resource/")[-1].split("/")[0] if "/resource/" in url else "unknown"
                        self._captured_data[endpoint] = data
                        self._all_responses.append({"url": url, "data": data})
                        print(f"  ✅ 攔截: {endpoint}")
                    except:
                        pass
                
                # 攔截所有 resource API（用於 debug）
                elif "/resource/" in url and "get" in url.lower():
                    try:
                        data = await response.json()
                        self._all_responses.append({"url": url, "data": data})
                    except:
                        pass
                        
            except Exception as e:
                pass

        self.page.on("response", on_response)

    async def init_session(self, headless=False):
        """初始化瀏覽器和 Session"""
        self.playwright = await async_playwright().start()
        
        browser_args = ["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=browser_args
        )

        # 檢查是否有現有 Session
        if os.path.exists(SESSION_FILE):
            print("📂 載入現有 Session...")
            with open(SESSION_FILE, "r") as f:
                storage_state = json.load(f)
            self.context = await self.browser.new_context(
                storage_state=storage_state,
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        else:
            print("🔑 需要登入 Pinterest...")
            self.context = await self.browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # 開啟登入頁面
            tmp_page = await self.context.new_page()
            await tmp_page.goto("https://www.pinterest.com/login/", wait_until="domcontentloaded", timeout=30000)
            
            print("\n" + "="*50)
            print("⏳ 請在瀏覽器中登入你的 Pinterest 帳號")
            print("   登入完成後，回到這裡按 Enter 繼續...")
            print("="*50 + "\n")
            
            input("按 Enter 繼續...")
            
            # 儲存 Session
            storage_state = await self.context.storage_state()
            with open(SESSION_FILE, "w") as f:
                json.dump(storage_state, f)
            print("✅ Session 已儲存！下次不需要重新登入。")
            await tmp_page.close()

        self.page = await self.context.new_page()
        self._setup_interceptor()
        print("🚀 初始化完成")
        return True

    async def get_analytics_overview(self):
        """
        抓取 Pinterest Analytics 總覽數據
        """
        self._captured_data.clear()
        self._all_responses.clear()
        
        print("\n📊 正在抓取 Analytics 數據...")
        
        try:
            # 前往 Analytics 頁面
            await self.page.goto(
                "https://analytics.pinterest.com/",
                wait_until="domcontentloaded",
                timeout=60000
            )
            await asyncio.sleep(5)
            
            # 等待頁面載入
            await self.page.wait_for_load_state("networkidle", timeout=30000)
            await asyncio.sleep(3)
            
            # 滾動頁面觸發更多 API
            await self.page.evaluate("window.scrollBy(0, 500)")
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"  ⚠️ 頁面載入錯誤: {e}")
        
        return self._parse_analytics_data()

    def _parse_analytics_data(self):
        """解析攔截到的 Analytics 數據"""
        result = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "impressions": 0,
            "saves": 0,
            "pin_clicks": 0,
            "outbound_clicks": 0,
            "engagement_rate": 0.0,
            "top_pins": []
        }
        
        print(f"\n📊 共攔截到 {len(self._all_responses)} 個 API 回應")
        
        for item in self._all_responses:
            url = item["url"]
            data = item["data"]
            
            # 嘗試從不同 API 回應中提取數據
            try:
                resource_data = data.get("resource_response", {}).get("data", {})
                
                # 提取總覽數據
                if isinstance(resource_data, dict):
                    # Impressions
                    if "impressions" in resource_data:
                        result["impressions"] = resource_data.get("impressions", 0)
                    if "total_impressions" in resource_data:
                        result["impressions"] = resource_data.get("total_impressions", 0)
                    
                    # Saves
                    if "saves" in resource_data:
                        result["saves"] = resource_data.get("saves", 0)
                    if "total_saves" in resource_data:
                        result["saves"] = resource_data.get("total_saves", 0)
                    
                    # Pin Clicks
                    if "pin_clicks" in resource_data:
                        result["pin_clicks"] = resource_data.get("pin_clicks", 0)
                    if "closeups" in resource_data:
                        result["pin_clicks"] = resource_data.get("closeups", 0)
                    
                    # Outbound Clicks
                    if "outbound_clicks" in resource_data:
                        result["outbound_clicks"] = resource_data.get("outbound_clicks", 0)
                    if "link_clicks" in resource_data:
                        result["outbound_clicks"] = resource_data.get("link_clicks", 0)
                    
                    # Engagement Rate
                    if "engagement_rate" in resource_data:
                        result["engagement_rate"] = resource_data.get("engagement_rate", 0)
                    
                    # Top Pins
                    if "pins" in resource_data and isinstance(resource_data["pins"], list):
                        for pin in resource_data["pins"][:10]:
                            if isinstance(pin, dict):
                                result["top_pins"].append({
                                    "id": pin.get("id", ""),
                                    "title": pin.get("title", "")[:100] if pin.get("title") else "",
                                    "impressions": pin.get("impressions", 0),
                                    "saves": pin.get("saves", 0),
                                    "clicks": pin.get("closeups", 0) or pin.get("pin_clicks", 0)
                                })
                
            except Exception as e:
                continue
        
        # 計算 engagement rate
        if result["impressions"] > 0 and result["engagement_rate"] == 0:
            total_engagements = result["saves"] + result["pin_clicks"] + result["outbound_clicks"]
            result["engagement_rate"] = round((total_engagements / result["impressions"]) * 100, 2)
        
        return result

    async def get_pin_stats(self, pin_id: str):
        """取得單一 Pin 的詳細統計"""
        self._captured_data.clear()
        
        try:
            await self.page.goto(
                f"https://www.pinterest.com/pin/{pin_id}/analytics/",
                wait_until="domcontentloaded",
                timeout=30000
            )
            await asyncio.sleep(5)
        except:
            pass
        
        return self._captured_data

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
    print("🔴 Pinterest Analytics Scraper")
    print("="*60)
    
    scraper = PinterestAnalyticsScraper()
    
    # 檢查是否在 GitHub Actions 環境
    is_ci = os.environ.get('CI') == 'true' or os.environ.get('GITHUB_ACTIONS') == 'true'
    
    # 初始化
    ok = await scraper.init_session(headless=is_ci)
    if not ok:
        print("❌ 初始化失敗")
        return
    
    # 抓取 Analytics 數據
    analytics = await scraper.get_analytics_overview()
    
    print("\n" + "="*60)
    print("📊 Analytics 數據")
    print("="*60)
    print(f"  📅 日期: {analytics['date']}")
    print(f"  👁️  Impressions: {analytics['impressions']:,}")
    print(f"  💾 Saves: {analytics['saves']:,}")
    print(f"  🖱️  Pin Clicks: {analytics['pin_clicks']:,}")
    print(f"  🔗 Outbound Clicks: {analytics['outbound_clicks']:,}")
    print(f"  📈 Engagement Rate: {analytics['engagement_rate']}%")
    
    if analytics['top_pins']:
        print(f"\n🏆 Top Pins:")
        for pin in analytics['top_pins'][:5]:
            print(f"    → {pin['title'][:40]}... | Imp: {pin['impressions']:,}")
    
    # 寫入 Google Sheets
    print("\n" + "="*60)
    print("📝 寫入 Google Sheets...")
    print("="*60)
    
    # 準備要寫入的數據
    row_data = [
        analytics['date'],
        analytics['impressions'],
        analytics['saves'],
        analytics['pin_clicks'],
        analytics['outbound_clicks'],
        analytics['engagement_rate'],
        "",  # pin_title (總覽不需要)
        ""   # pin_id (總覽不需要)
    ]
    
    write_to_sheets([row_data])
    
    # 關閉
    await scraper.close()
    
    print("\n✅ 完成！")
    
    # 儲存 debug 資料
    with open("debug_responses.json", "w", encoding="utf-8") as f:
        json.dump(scraper._all_responses, f, indent=2, ensure_ascii=False, default=str)
    print("💾 Debug 資料已儲存到 debug_responses.json")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
