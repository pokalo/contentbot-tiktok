#!/usr/bin/env python3
"""
TikTok OAuth Authorization with PKCE
Авторизация через localhost callback или ручной ввод code
"""

import os
import json
import requests
import webbrowser
import base64
import hashlib
import secrets
import threading
import time
import http.server
import socketserver
from urllib.parse import urlencode, urlparse, parse_qs
from tiktok_config import TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET, SCOPES, TOKEN_FILE

# ============ PKCE ============
def generate_pkce():
    """Генерация PKCE code_verifier и code_challenge"""
    code_verifier = secrets.token_urlsafe(64)[:128]
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip('=')
    return code_verifier, code_challenge


# ============ CALLBACK SERVER ============
class CallbackHandler(http.server.SimpleHTTPRequestHandler):
    code = None
    
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        
        if 'code' in query:
            CallbackHandler.code = query['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = """
            <html>
            <head><title>TikTok Auth</title></head>
            <body style="font-family:Arial;text-align:center;padding:50px;background:#000;color:#fff">
                <h1>✅ Success!</h1>
                <p>You can close this window.</p>
                <script>setTimeout(window.close, 2000)</script>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = """
            <html><body style="font-family:Arial;text-align:center;padding:50px;background:#000;color:#fff">
                <h1>❌ Error</h1>
                <p>No authorization code received.</p>
            </body></html>
            """
            self.wfile.write(html.encode())
    
    def log_message(self, format, *args):
        pass  # Suppress logging


def start_callback_server(port=8080, timeout=120):
    """Запуск сервера для приёма callback"""
    CallbackHandler.code = None
    
    class TCPServer(socketserver.TCPServer):
        allow_reuse_address = True
    
    server = TCPServer(("", port), CallbackHandler)
    server.timeout = timeout
    
    thread = threading.Thread(target=server.handle_request)
    thread.daemon = True
    thread.start()
    
    return server, thread


# ============ MAIN ============
def main():
    print("=" * 50)
    print("TikTok Authorization (PKCE)")
    print("=" * 50)
    
    # Генерируем PKCE
    code_verifier, code_challenge = generate_pkce()
    
    # Сохраняем verifier для обмена
    with open("code_verifier.txt", "w") as f:
        f.write(code_verifier)
    
    print(f"\n[*] PKCE generated")
    print(f"   code_verifier: {code_verifier[:20]}...")
    print(f"   code_challenge: {code_challenge[:20]}...")
    
    # Выбор режима
    print("\n[*] Choose authorization method:")
    print("   1. Localhost callback (automatic)")
    print("   2. Manual code entry")
    
    choice = input("\nChoice [1]: ").strip() or "1"
    
    # Redirect URI (из Cloudflare туннеля или зарегистрированный в Developer Portal)
    redirect_uri = input("\nEnter redirect_uri (e.g., https://your-tunnel.trycloudflare.com/callback): ").strip()
    if not redirect_uri:
        print("❌ Redirect URI required")
        return

    if choice == "1":
        # Localhost callback - НЕ ИСПОЛЬЗУЕТСЯ, ждём код на указанный redirect_uri
        port = 8080
        
        print(f"\n🌐 Starting callback server on port {port}...")
        server, thread = start_callback_server(port)
        
        # Строим URL
        params = {
            "client_key": TIKTOK_CLIENT_KEY,
            "scope": ",".join(SCOPES),
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }
        
        auth_url = "https://www.tiktok.com/v2/auth/authorize/?" + urlencode(params)
        
        print(f"\n📱 Opening browser...")
        print(f"   URL: {auth_url[:80]}...")
        
        webbrowser.open(auth_url)
        
        print(f"\n⏳ Waiting for callback (up to 2 minutes)...")
        
        # Ждём код
        start_time = time.time()
        while not CallbackHandler.code and time.time() - start_time < 120:
            time.sleep(0.5)
        
        server.server_close()
        
        if not CallbackHandler.code:
            print("\n❌ Timeout! No code received.")
            print("Try manual mode instead.")
            return
        
        code = CallbackHandler.code
        print(f"\n✅ Code received: {code[:30]}...")
        
    else:
        # Manual mode
        redirect_uri = input("\nEnter redirect_uri from Developer Portal: ").strip()
        if not redirect_uri:
            print("❌ Redirect URI required")
            return
        
        params = {
            "client_key": TIKTOK_CLIENT_KEY,
            "scope": ",".join(SCOPES),
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }
        
        auth_url = "https://www.tiktok.com/v2/auth/authorize/?" + urlencode(params)
        
        print(f"\n🔗 QUICKLY copy and open this URL (code expires fast!):\n")
        print(f"{auth_url}\n")
        
        code = input("Paste 'code' from redirect URL: ").strip()
        
        if not code:
            print("❌ No code provided")
            return
    
    # Обмениваем code на token
    print("\n🔄 Exchanging code for token...")
    
    with open("code_verifier.txt", "r") as f:
        code_verifier = f.read().strip()
    
    data = {
        "client_key": TIKTOK_CLIENT_KEY,
        "client_secret": TIKTOK_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier
    }
    
    r = requests.post("https://open.tiktokapis.com/v2/oauth/token/", data=data)
    
    if r.status_code == 200:
        token = r.json()
        token["expires_at"] = time.time() + token.get("expires_in", 86400)
        
        with open(TOKEN_FILE, "w") as f:
            json.dump(token, f, indent=2)
        
        print("\n" + "=" * 50)
        print("✅ SUCCESS! Token saved.")
        print("=" * 50)
        print(f"\n   Access Token:  {token.get('access_token', 'N/A')[:25]}...")
        print(f"   Refresh Token: {token.get('refresh_token', 'N/A')[:25]}...")
        print(f"   Open ID:       {token.get('open_id', 'N/A')[:25]}...")
        print(f"   Expires in:    {token.get('expires_in', 'N/A')} seconds (24h)")
        print(f"   Scopes:        {token.get('scope', 'N/A')}")
        
        # Cleanup
        if os.path.exists("code_verifier.txt"):
            os.remove("code_verifier.txt")
        
        print("\n🎉 You can now use publish_video()")
    else:
        print(f"\n❌ Token exchange failed: {r.status_code}")
        print(f"   Response: {r.text}")
        
        # Сохраняем verifier для ручного повтора
        print(f"\n💡 code_verifier saved to code_verifier.txt")
        print("   You can retry exchange manually.")


if __name__ == "__main__":
    main()