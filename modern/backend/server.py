#!/usr/bin/env python3
"""
Minimal JSON HTTP server for the LifeRPG modern scaffold.
This intentionally uses only the Python stdlib so it's runnable without installing dependencies.
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class Handler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path == "/health":
            self._send_json({"status": "ok"})
            return
        if self.path == "/api/v1/hello":
            self._send_json({"message": "Hello from LifeRPG modern backend"})
            return
        self._send_json({"error": "not_found"}, status=404)

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8000), Handler)
    print("LifeRPG backend listening on http://0.0.0.0:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
    
