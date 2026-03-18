"""
Pinterest API Backend for Vercel
有 API Key 驗證，保護你的 API
"""

import os
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import urllib.request
import urllib.error

# 從環境變數取得憑證
PINTEREST_ACCESS_TOKEN = os.environ.get('PINTEREST_ACCESS_TOKEN', '')
PINTEREST_API_BASE = 'https://api.pinterest.com/v5'

# 🔐 API 驗證密鑰（從環境變數取得）
API_SECRET_KEY = os.environ.get('API_SECRET_KEY', '')


class handler(BaseHTTPRequestHandler):
    
    def verify_api_key(self):
        """驗證 API Key"""
        # 從 Header 取得 API Key
        auth_header = self.headers.get('X-API-Key', '')
        
        # 從 Query 參數取得 API Key（備用）
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        query_key = query_params.get('api_key', [''])[0]
        
        # 檢查是否匹配
        provided_key = auth_header or query_key
        
        if not API_SECRET_KEY:
            # 如果沒設定 API_SECRET_KEY，允許所有請求（開發模式）
            return True
        
        return provided_key == API_SECRET_KEY
    
    def send_unauthorized(self):
        """回傳未授權錯誤"""
        self.send_response(401)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            'success': False,
            'error': 'Unauthorized',
            'message': 'Invalid or missing API key'
        }
        self.wfile.write(json.dumps(response).encode())
    
    def do_GET(self):
        """處理 GET 請求"""
        
        # 🔐 驗證 API Key
        if not self.verify_api_key():
            self.send_unauthorized()
            return
        
        # 設定 CORS headers
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-API-Key')
        self.end_headers()
        
        try:
            pins_data = self.get_user_pins()
            
            response = {
                'success': True,
                'data': pins_data,
                'message': 'Pins retrieved successfully'
            }
            
        except Exception as e:
            response = {
                'success': False,
                'error': str(e),
                'message': 'Failed to retrieve pins'
            }
        
        self.wfile.write(json.dumps(response).encode())
    
    def do_OPTIONS(self):
        """處理 CORS preflight 請求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-API-Key')
        self.end_headers()
    
    def get_user_pins(self):
        """從 Pinterest API 取得用戶的 Pins"""
        
        if not PINTEREST_ACCESS_TOKEN:
            raise Exception('Pinterest Access Token not configured')
        
        url = f'{PINTEREST_API_BASE}/pins'
        
        headers = {
            'Authorization': f'Bearer {PINTEREST_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        req = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                return data
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            raise Exception(f'Pinterest API Error: {e.code} - {error_body}')
