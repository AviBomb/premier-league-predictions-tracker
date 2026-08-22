"""
Local Development Web Server for Premier League Predictions Dashboard & Admin Portal
- Supports CORS for file:/// and http:// origins
- Provides real-time REST API endpoints:
  * POST /api/save-approvals -> Saves decisions to data/admin_approvals.json and triggers live scoring recalculation
  * POST /api/save-config    -> Saves config to config/gameweek_config.json and triggers pipeline
  * POST /api/recalculate    -> Runs main pipeline on-demand
"""
import http.server
import socketserver
import webbrowser
import os
import json
from typing import Dict, Any

CANDIDATE_PORTS = [3000, 5000, 5500, 8888, 9000, 9090, 10000, 0]
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_body = self.rfile.read(content_length)

        if self.path == "/api/save-approvals":
            try:
                data = json.loads(post_body.decode('utf-8'))
                approvals_path = os.path.join(DIRECTORY, "data", "admin_approvals.json")
                os.makedirs(os.path.dirname(approvals_path), exist_ok=True)
                with open(approvals_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                # Trigger pipeline recalculation
                from main import run_pipeline
                run_pipeline(use_live_api=True)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "message": "Approvals saved and scores recalculated!"}).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
                return

        elif self.path == "/api/save-config":
            try:
                data = json.loads(post_body.decode('utf-8'))
                config_path = os.path.join(DIRECTORY, "config", "gameweek_config.json")
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                from main import run_pipeline
                run_pipeline(use_live_api=True)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "message": "Configuration saved and pipeline executed!"}).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
                return

        elif self.path == "/api/recalculate":
            try:
                from main import run_pipeline
                run_pipeline(use_live_api=False)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "message": "Scoring pipeline recalculated!"}).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
                return

        super().do_GET()


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def find_and_start_server():
    os.chdir(DIRECTORY)
    
    server = None
    active_port = None

    for port in CANDIDATE_PORTS:
        try:
            server = ReusableTCPServer(("127.0.0.1", port), CustomHandler)
            active_port = server.server_address[1]
            break
        except Exception:
            continue

    if not server:
        print("[!] Error: Could not find an available open port.")
        return

    url = f"http://127.0.0.1:{active_port}/dashboard.html"
    admin_url = f"http://127.0.0.1:{active_port}/admin.html"

    print("=" * 80)
    print(f"  PREMIER LEAGUE DASHBOARD LOCAL SERVER RUNNING")
    print("=" * 80)
    print(f"[*] Public Live Dashboard : {url}")
    print(f"[*] Admin Control Portal  : {admin_url}")
    print(f"[*] Local Host / Origin   : http://127.0.0.1:{active_port}")
    print("=" * 80)
    print("Press Ctrl+C in terminal to stop the server.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Server stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    find_and_start_server()
