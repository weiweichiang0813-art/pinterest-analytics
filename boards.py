"""
Pinterest API - Boards Endpoint (有驗證)
"""

import os
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import urllib.request
import urllib.error

PINTEREST_ACCESS_TOKEN = os.environ.get('PINTEREST_ACCESS_TOKEN', '')
PINTEREST_API_BASE = 'https://api.pinterest.com/v5'
API_SECRET_KEY = os.environ.get('API_SECRET_KEY', '')


class handler(BaseHTTPRequestHandler):
    
    def verify_api_key(self):
        auth_header = self.headers.get('X-API-Key', '')
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        query_key = query_params.get('api_key', [''])[0]
        provided_key = auth_header or query_key
        
        if not API_SECRET_KEY:
            return True
        return provided_key == API_SECRET_KEY
    
    def send_unauthorized(self):
        self.send_response(401)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        response = {'success': False, 'error': 'Unauthorized', 'message': 'Invalid or missing API key'}
        self.wfile.write(json.dumps(response).encode())
    
    def do_GET(self):
        if not self.verify_api_key():
            self.send_unauthorized()
            return
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-API-Key')
        self.end_headers()
        
        try:
            boards_data = self.get_user_boards()
            response = {'success': True, 'data': boards_data, 'message': 'Boards retrieved successfully'}
        except Exception as e:
            response = {'success': False, 'error': str(e), 'message': 'Failed to retrieve boards'}
        
        self.wfile.write(json.dumps(response).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-API-Key')
        self.end_headers()
    
    def get_user_boards(self):
        if not PINTEREST_ACCESS_TOKEN:
            raise Exception('Pinterest Access Token not configured')
        
        url = f'{PINTEREST_API_BASE}/boards'
        headers = {'Authorization': f'Bearer {PINTEREST_ACCESS_TOKEN}', 'Content-Type': 'application/json'}
        req = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            raise Exception(f'Pinterest API Error: {e.code} - {e.read().decode()}')
