"""
Pinterest Analytics Scraper v4
進入每一則 Pin 抓取詳細統計數據

流程：
1. 開啟 Pinterest 讓用戶手動切換帳號
2. 前往 Created tab 
3. 逐一進入每個 Pin 的統計頁面
4. 抓取數據並寫入 Google Sheets
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
SHEET_NAME = "Pinterest Analytics Data"
SESSION_FILE = "pinterest_session.json"

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


# ============================================================
# Google Sheets 連接
# ============================================================

def get_google_sheets_client():
    """連接 Google Sheets"""
    if os.environ.get('GOOGLE_CREDENTIALS'):
        creds_dict = json.loads(os.environ['GOOGLE_CREDENTIALS'])
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
    
    client = gspread.authorize(creds)
    return client


def write_to_sheets(data: list):
    """寫入數據到 Google Sheets"""
    try:
        client = get_google_sheets_client()
        sheet = client.open_by_key(GOOGLE_SHEETS_ID).worksheet(SHEET_NAME)
        
        existing_data = sheet.get_all_values()
        next_row = len(existing_data) + 1
        
        for row in data:
            sheet.insert_row(row, next_row)
            next_row += 1
            print(f"  ✅ 寫入: {row[0]} - {row[6][:30] if row[6] else 'N/A'}...")
        
        print(f"\n📊 成功寫入 {len(data)} 筆數據到 Google Sheets")
        return True
    except Exception as e:
        print(f"❌ Google Sheets 錯誤: {e}")
        return False


# ============================================================
# Pinterest Pin Stats Scraper
# ============================================================

class PinterestPinScraper:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self._captured_stats = {}
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
                        
                        # 嘗試提取 Pin 統計數據
                        self._extract_pin_stats(url, data)
                        
                    except:
                        pass
            except:
                pass

        self.page.on("response", on_response)

    def _extract_pin_stats(self, url, data):
        """從 API 回應中提取 Pin 統計數據"""
        try:
            # GraphQL 格式
            if "graphql" in url.lower():
                gql_data = data.get("data", {})
                
                # 嘗試各種可能的 key
                for key in gql_data:
                    if "pin" in key.lower() or "analytics" in key.lower():
                        inner = gql_data[key]
                        if isinstance(inner, dict):
                            self._parse_stats_from_dict(inner)
            
            # REST API 格式
            resource_data = data.get("resource_response", {}).get("data", {})
            if resource_data:
                self._parse_stats_from_dict(resource_data)
                
        except Exception as e:
            pass

    def _parse_stats_from_dict(self, d):
        """從字典中解析統計數據"""
        if not isinstance(d, dict):
            return
        
        # 常見的統計欄位名稱
        stat_keys = {
            "impressions": ["impressions", "impression", "impressionCount", "total_impressions"],
            "saves": ["saves", "save", "saveCount", "total_saves", "repin_count"],
            "pin_clicks": ["pin_clicks", "pinClick", "closeups", "closeup_count", "clicks"],
            "outbound_clicks": ["outbound_clicks", "outboundClick", "link_clicks", "click_count"],
            "engagement_rate": ["engagement_rate", "engagementRate"],
        }
        
        for stat_name, possible_keys in stat_keys.items():
            for key in possible_keys:
                if key in d and d[key] is not None:
                    value = d[key]
                    if isinstance(value, (int, float)):
                        self._captured_stats[stat_name] = value
                        break

    async def init_session(self):
        """初始化瀏覽器和 Session"""
        self.playwright = await async_playwright().start()
        
        self.browser = await self.playwright.chromium.launch(
            headless=False,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )

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
            
            tmp_page = await self.context.new_page()
            await tmp_page.goto("https://www.pinterest.com/login/", wait_until="domcontentloaded", timeout=30000)
            
            print("\n" + "="*50)
            print("⏳ 請在瀏覽器中登入你的 Pinterest 帳號")
            print("   登入完成後，回到這裡按 Enter 繼續...")
            print("="*50 + "\n")
            
            input("按 Enter 繼續...")
            
            storage_state = await self.context.storage_state()
            with open(SESSION_FILE, "w") as f:
                json.dump(storage_state, f)
            print("✅ Session 已儲存！")
            await tmp_page.close()

        self.page = await self.context.new_page()
        self._setup_interceptor()
        print("🚀 初始化完成")
        return True

    async def let_user_navigate_to_created_page(self):
        """
        讓用戶手動導航到 Created 頁面
        """
        print("\n" + "="*60)
        print("📌 開啟 Pinterest...")
        print("="*60)
        
        await self.page.goto("https://www.pinterest.com/", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)
        
        print("\n" + "="*60)
        print("👆 請在瀏覽器中操作：")
        print("="*60)
        print("")
        print("   1. 如果需要切換帳號，點擊右上角頭像 → 切換帳號")
        print("   2. 點擊你的頭像進入個人頁面")
        print("   3. 點擊 'Created' 分頁")
        print("   4. 確認看到你發布的所有 Pins")
        print("")
        print("="*60)
        
        input("\n✅ 準備好後，按 Enter 開始爬蟲...")
        
        return True

    async def scrape_all_pins(self, max_pins: int = 20):
        """
        爬取頁面上所有 Pins 的統計數據
        """
        all_pin_stats = []
        
        print(f"\n📊 開始爬取 Pins 數據（最多 {max_pins} 則）...")
        
        # 先滾動頁面載入更多 Pins
        print("  📜 載入更多 Pins...")
        try:
            for _ in range(3):
                await self.page.evaluate("window.scrollBy(0, 800)")
                await asyncio.sleep(1)
            
            # 回到頂部
            await self.page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(1)
        except Exception as e:
            print(f"  ⚠️ 滾動頁面時發生錯誤，繼續執行...")
        
        # 找到所有 Pin 連結
        print("  🔍 尋找 Pin 連結...")
        
        # 取得頁面上所有 /pin/ 連結
        try:
            links = await self.page.query_selector_all('a[href*="/pin/"]')
        except Exception as e:
            print(f"  ⚠️ 無法取得連結: {e}")
            return []
        
        pin_ids = []
        for link in links:
            try:
                href = await link.get_attribute('href')
                if href and '/pin/' in href:
                    # 提取 Pin ID
                    match = re.search(r'/pin/(\d+)', href)
                    if match:
                        pin_id = match.group(1)
                        if pin_id not in pin_ids:
                            pin_ids.append(pin_id)
            except:
                continue
        
        print(f"  ✅ 找到 {len(pin_ids)} 個 Pins")
        
        if not pin_ids:
            print("  ⚠️ 找不到 Pins，請確認你在 Created 頁面")
            return []
        
        # 限制數量
        pin_ids = pin_ids[:max_pins]
        
        # 逐一進入每個 Pin 的統計頁面
        for i, pin_id in enumerate(pin_ids):
            print(f"\n  [{i+1}/{len(pin_ids)}] 抓取 Pin: {pin_id}")
            
            self._captured_stats.clear()
            self._all_responses.clear()
            
            try:
                # 進入 Pin 統計頁面
                stats_url = f"https://www.pinterest.com/pin/{pin_id}/analytics/"
                await self.page.goto(stats_url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(4)
                
                # 滾動觸發更多 API（加入錯誤處理）
                try:
                    await self.page.evaluate("window.scrollBy(0, 300)")
                    await asyncio.sleep(2)
                except:
                    pass
                
                # 嘗試從頁面提取數據
                page_stats = await self._extract_stats_from_page()
                
                # 合併 API 攔截的數據和頁面提取的數據
                stats = {**self._captured_stats, **page_stats}
                
                # 嘗試獲取 Pin 標題
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
                
                print(f"      👁️ Impressions: {pin_data['impressions']:,}")
                print(f"      💾 Saves: {pin_data['saves']}")
                print(f"      🖱️ Clicks: {pin_data['pin_clicks']}")
                
            except Exception as e:
                print(f"      ⚠️ 錯誤: {e}")
                continue
        
        return all_pin_stats

    async def _extract_stats_from_page(self):
        """從頁面元素中提取統計數據"""
        stats = {}
        
        try:
            # 等待頁面穩定
            await asyncio.sleep(1)
            
            # 取得頁面文字
            try:
                all_text = await self.page.inner_text('body')
            except:
                return stats
            
            # 找 "XXX Impressions" 格式
            imp_match = re.search(r'([\d,]+)\s*[Ii]mpressions?', all_text)
            if imp_match:
                stats['impressions'] = int(imp_match.group(1).replace(',', ''))
            
            # 找 "XXX Saves" 格式
            save_match = re.search(r'([\d,]+)\s*[Ss]aves?', all_text)
            if save_match:
                stats['saves'] = int(save_match.group(1).replace(',', ''))
            
            # 找 "XXX Clicks" 或 "XXX Pin clicks" 格式
            click_match = re.search(r'([\d,]+)\s*(?:[Pp]in\s*)?[Cc]licks?', all_text)
            if click_match:
                stats['pin_clicks'] = int(click_match.group(1).replace(',', ''))
            
            # 找 "XXX Link clicks" 或 "XXX Outbound clicks" 格式
            link_match = re.search(r'([\d,]+)\s*(?:[Ll]ink|[Oo]utbound)\s*[Cc]licks?', all_text)
            if link_match:
                stats['outbound_clicks'] = int(link_match.group(1).replace(',', ''))
                
        except Exception as e:
            pass
        
        return stats

    async def _get_pin_title(self):
        """獲取 Pin 標題"""
        try:
            # 嘗試各種 selector
            for selector in ['h1', '[data-test-id="pin-title"]', '.pinTitle']:
                el = await self.page.query_selector(selector)
                if el:
                    text = await el.inner_text()
                    if text and len(text) > 2 and 'analytics' not in text.lower():
                        return text.strip()[:100]
        except:
            pass
        return ""

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
    print("🔴 Pinterest Pin Analytics Scraper v4")
    print("="*60)
    
    scraper = PinterestPinScraper()
    
    ok = await scraper.init_session()
    if not ok:
        print("❌ 初始化失敗")
        return
    
    # 讓用戶導航到 Created 頁面
    await scraper.let_user_navigate_to_created_page()
    
    # 詢問要爬取多少 Pins
    try:
        max_pins = int(input("\n📌 要爬取多少則 Pins？(預設 10): ").strip() or "10")
    except:
        max_pins = 10
    
    # 爬取所有 Pins
    all_stats = await scraper.scrape_all_pins(max_pins=max_pins)
    
    # 顯示結果
    print("\n" + "="*60)
    print(f"📊 爬取結果：共 {len(all_stats)} 則 Pins")
    print("="*60)
    
    total_impressions = sum(p['impressions'] for p in all_stats)
    total_saves = sum(p['saves'] for p in all_stats)
    total_clicks = sum(p['pin_clicks'] for p in all_stats)
    
    print(f"  👁️ 總 Impressions: {total_impressions:,}")
    print(f"  💾 總 Saves: {total_saves:,}")
    print(f"  🖱️ 總 Clicks: {total_clicks:,}")
    
    if all_stats:
        # 詢問是否寫入 Google Sheets
        print("\n" + "="*60)
        save_choice = input("💾 要將數據寫入 Google Sheets 嗎？(y/n): ").strip().lower()
        
        if save_choice == 'y':
            print("\n📝 寫入 Google Sheets...")
            
            rows_to_write = []
            for pin in all_stats:
                row = [
                    pin["date"],
                    pin["impressions"],
                    pin["saves"],
                    pin["pin_clicks"],
                    pin["outbound_clicks"],
                    pin["engagement_rate"],
                    pin["pin_title"],
                    pin["pin_id"]
                ]
                rows_to_write.append(row)
            
            write_to_sheets(rows_to_write)
        else:
            print("  ⏭️ 跳過寫入 Google Sheets")
    
    # 關閉
    await scraper.close()
    
    print("\n✅ 完成！")
    
    # 儲存結果到本地 JSON
    with open("pin_stats_result.json", "w", encoding="utf-8") as f:
        json.dump(all_stats, f, indent=2, ensure_ascii=False)
    print("💾 結果已儲存到 pin_stats_result.json")


if __name__ == "__main__":
    asyncio.run(main())
