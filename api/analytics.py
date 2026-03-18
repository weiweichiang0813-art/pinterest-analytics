"""
Pinterest API - Analytics Endpoint (有驗證)
"""

import os
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import urllib.request
import urllib.error
from datetime import datetime, timedelta

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
            parsed_path = urlparse(self.path)
            query_params = parse_qs(parsed_path.query)
            
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            if 'start_date' in query_params:
                start_date = query_params['start_date'][0]
            if 'end_date' in query_params:
                end_date = query_params['end_date'][0]
            
            pins_data = self.get_all_pins_with_stats()
            
            response = {
                'success': True,
                'data': {
                    'pins': pins_data,
                    'date_range': {'start': start_date, 'end': end_date},
                    'summary': self.calculate_summary(pins_data)
                },
                'message': 'Analytics retrieved successfully'
            }
        except Exception as e:
            response = {'success': False, 'error': str(e), 'message': 'Failed to retrieve analytics'}
        
        self.wfile.write(json.dumps(response).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-API-Key')
        self.end_headers()
    
    def get_all_pins_with_stats(self):
        if not PINTEREST_ACCESS_TOKEN:
            raise Exception('Pinterest Access Token not configured')
        
        pins_url = f'{PINTEREST_API_BASE}/pins'
        headers = {'Authorization': f'Bearer {PINTEREST_ACCESS_TOKEN}', 'Content-Type': 'application/json'}
        
        all_pins = []
        bookmark = None
        
        while True:
            url = pins_url
            if bookmark:
                url += f'?bookmark={bookmark}'
            
            req = urllib.request.Request(url, headers=headers)
            
            try:
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode())
                    items = data.get('items', [])
                    all_pins.extend(items)
                    bookmark = data.get('bookmark')
                    if not bookmark:
                        break
            except urllib.error.HTTPError as e:
                raise Exception(f'Pinterest API Error: {e.code} - {e.read().decode()}')
        
        formatted_pins = []
        for pin in all_pins:
            formatted_pins.append({
                'id': pin.get('id', ''),
                'title': pin.get('title', ''),
                'description': pin.get('description', ''),
                'link': pin.get('link', ''),
                'created_at': pin.get('created_at', ''),
                'board_id': pin.get('board_id', ''),
                'media': pin.get('media', {}),
                'metrics': pin.get('pin_metrics', {})
            })
        
        return formatted_pins
    
    def calculate_summary(self, pins):
        return {
            'total_pins': len(pins),
            'last_updated': datetime.now().isoformat()
        }
