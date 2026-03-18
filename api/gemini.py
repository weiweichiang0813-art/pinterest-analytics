from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import urllib.error
import os

# Gemini API Configuration
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-API-Key')
        self.end_headers()

    def do_POST(self):
        try:
            # Verify API Key
            api_key = self.headers.get('X-API-Key', '')
            expected_key = os.environ.get('API_SECRET_KEY', '')
            
            if api_key != expected_key:
                self.send_error_response(401, "Unauthorized")
                return

            # Get request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_body = json.loads(post_data.decode('utf-8'))
            
            prompt = request_body.get('prompt', '')
            action = request_body.get('action', 'generate')  # generate, analyze
            
            if not prompt:
                self.send_error_response(400, "Missing prompt")
                return

            # Build Gemini request
            if action == 'generate':
                system_prompt = """You are a Pinterest content expert. Generate optimized Pin content that:
- Uses SEO-friendly titles (under 100 characters)
- Writes engaging descriptions (under 500 characters)
- Includes relevant hashtags
- Uses emojis appropriately
- Is designed for high engagement

Respond in JSON format:
{
    "title": "Pin title here",
    "description": "Pin description here",
    "hashtags": ["hashtag1", "hashtag2", "hashtag3", ...]
}"""
            else:  # analyze
                system_prompt = """You are a Pinterest analytics expert. Analyze the performance data and provide:
- Key insights about what's working
- Areas for improvement
- Actionable recommendations
- Trend observations

Keep your response concise and actionable (under 300 words). Use bullet points for clarity."""

            gemini_payload = {
                "contents": [{
                    "parts": [
                        {"text": system_prompt},
                        {"text": prompt}
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 1024
                }
            }

            # Call Gemini API
            req = urllib.request.Request(
                GEMINI_URL,
                data=json.dumps(gemini_payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                # Extract text from Gemini response
                text = result['candidates'][0]['content']['parts'][0]['text']
                
                # Clean up JSON if present
                if action == 'generate':
                    # Try to parse as JSON
                    try:
                        # Remove markdown code blocks if present
                        clean_text = text.strip()
                        if clean_text.startswith('```json'):
                            clean_text = clean_text[7:]
                        if clean_text.startswith('```'):
                            clean_text = clean_text[3:]
                        if clean_text.endswith('```'):
                            clean_text = clean_text[:-3]
                        
                        content = json.loads(clean_text.strip())
                        self.send_json_response({
                            "success": True,
                            "data": content
                        })
                    except json.JSONDecodeError:
                        # Return raw text if not valid JSON
                        self.send_json_response({
                            "success": True,
                            "data": {"raw": text}
                        })
                else:
                    self.send_json_response({
                        "success": True,
                        "data": {"analysis": text}
                    })

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            self.send_error_response(e.code, f"Gemini API error: {error_body}")
        except Exception as e:
            self.send_error_response(500, str(e))

    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def send_error_response(self, code, message):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"success": False, "error": message}).encode('utf-8'))
