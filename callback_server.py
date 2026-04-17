#!/usr/bin/env python3
"""Callback server для TikTok OAuth"""

import http.server
import socketserver
import urllib.parse
import json
import os

PORT = 8080
CODE = None

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global CODE
        query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        
        if 'code' in query:
            CODE = query['code'][0]
            print(f"\n[OK] Code received: {CODE[:30]}...")
            
            # Сохраняем в файл
            with open("auth_code.txt", "w") as f:
                f.write(CODE)
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = """
            <html><body style="font-family:Arial;text-align:center;padding:50px;background:#000;color:#fff">
                <h1>Success! You can close this window.</h1>
            </body></html>
            """
            self.wfile.write(html.encode())
        else:
            self.send_response(400)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

print(f"Starting callback server on port {PORT}...")
print(f"Waiting for redirect to http://localhost:{PORT}/callback")
print("\nOpen this URL in browser:")
print(f"https://www.tiktok.com/v2/auth/authorize/?client_key=sbawjmiia75sublu3y&scope=user.info.basic,video.upload&response_type=code&redirect_uri=https://knowledgestorm-seat-dedicated-school.trycloudflare.com/callback")
print("\nWaiting for callback...")

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.timeout = 120
    httpd.handle_request()

if CODE:
    print(f"\nCode saved to auth_code.txt")
    print("Now run: python exchange_code.py")
else:
    print("\nNo code received")