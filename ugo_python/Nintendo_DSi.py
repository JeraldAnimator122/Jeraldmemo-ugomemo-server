#!/usr/bin/env python3
"""
nintendo_dsi.py
Minimal DSi-compatible Nintendo Authentication Server + Connection test server.
Use with DNS redirection so the DSi hits this server instead of Nintendo.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse as urlparse


class NintendoHandler(BaseHTTPRequestHandler):

    # ---------------------------------------------------------
    # Utility
    # ---------------------------------------------------------

    def _send(self, code=200, ctype="text/plain; charset=utf-8", body=""):
        body_bytes = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body_bytes)))
        self.end_headers()
        if body:
            self.wfile.write(body_bytes)

    def log_message(self, fmt, *args):
        # Cleaner logging
        print(f"[DSi] {fmt % args}")

    # ---------------------------------------------------------
    # GET
    # ---------------------------------------------------------

    def do_GET(self):
        path = self.path.split("?", 1)[0]

        # Extract FSID if present
        fsid = self.headers.get("X-DSi-ID", "UNKNOWN")
        print(f"[INFO] FSID = {fsid}")

        # ---- Connection Test ----
        if path == "/" or "conntest" in path:
            # DSi only checks for HTTP 200
            self._send(200, "text/plain", "OK")
            return

        # ---- NAS GET ----
        if path.startswith("/nas/"):
            self.handle_nas_get(path, fsid)
            return

        self._send(404, "text/plain", "Not Found")

    # ---------------------------------------------------------
    # POST
    # ---------------------------------------------------------

    def do_POST(self):
        path = self.path.split("?", 1)[0]

        fsid = self.headers.get("X-DSi-ID", "UNKNOWN")
        print(f"[INFO] FSID = {fsid}")

        if path.startswith("/nas/"):
            self.handle_nas_post(path, fsid)
            return

        self._send(404, "text/plain", "Not Found")

    # ---------------------------------------------------------
    # NAS Logic
    # ---------------------------------------------------------

    def handle_nas_get(self, path, fsid):
        if path == "/nas/ping":
            self._send(200, "text/plain", "pong")
            return

        if path == "/nas/version":
            self._send(200, "text/plain", "NAS-DSI-1.0")
            return

        self._send(404, "text/plain", "NAS GET Not Found")

    def handle_nas_post(self, path, fsid):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8", errors="ignore")
        params = urlparse.parse_qs(body)

        # ---- NAS LOGIN ----
        if path == "/nas/login":
            print(f"[LOGIN] Params: {params}")

            response = (
                "result=0\n"
                f"fsid={fsid}\n"
                "token=FAKE_TOKEN_1234\n"
                "user_id=0000000000000000\n"
            )
            self._send(200, "text/plain", response)
            return

        # ---- NAS LOGOUT ----
        if path == "/nas/logout":
            self._send(200, "text/plain", "result=0\n")
            return

        self._send(404, "text/plain", "NAS POST Not Found")


# ---------------------------------------------------------
# Server Entry Point
# ---------------------------------------------------------

def run(host="0.0.0.0", port=80):
    print(f"[START] Nintendo NAS + Conntest server on {host}:{port}")
    server = HTTPServer((host, port), NintendoHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[STOP] Server shutting down.")
        server.server_close()


if __name__ == "__main__":
    run()
