from sous_vide import Cooker

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from urllib.parse import parse_qs

class WebServer(HTTPServer):
    def __init__(self, port=9901, server_address=('', 9901), cooker=None):
        self.cooker = cooker or Cooker()
        super().__init__(server_address, RequestHandler)

class RequestHandler (BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_state_json()

    def do_POST(self):
        cooker = self.server.cooker
        state = cooker.get_state()

        content_len = int(self.headers.get('content-length', 0))
        new_data = self.rfile.read(content_len)
        for (k,[v]) in parse_qs(new_data).items():
            state[str(k, "utf-8")] = float(v)

        cooker.set_state(state)
        self.send_state_json()

    def send_state_json(self):
        state = self.server.cooker.get_state()
        response = bytes(json.dumps(state), "utf-8")
        self.send_response(200, "ok")
        self.send_header("Content-Length", len(response))
        self.end_headers()
        self.wfile.write(response)

    def bad_request(self):
        self.send_response(400, "Bad Request")
        self.end_headers()

if __name__ == "__main__":
    print("hello")
    server = WebServer()
    try:
        server.cooker.heater.run()
        print("data:")
        print(server.cooker.get_state())
        print("starting server...")
        server.serve_forever()
    finally:
        server.cooker.close()
