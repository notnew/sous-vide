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
        allowed_files = ["style.css", "cooker.html"]
        if self.path == "/":
            self.send_page("cooker.html")
        elif self.path == "/state":
            self.send_state_json()
        elif self.path[1:] in allowed_files:
            self.send_page(self.path[1:])
        else:
            self.not_found()

    def do_POST(self):
        cooker = self.server.cooker
        with cooker._state_lock as l:
            state = cooker.get_state()

            content_len = int(self.headers.get('content-length', 0))
            new_data = self.rfile.read(content_len)
            print("posted data:", new_data)
            for (k,[v]) in parse_qs(new_data).items():
                state[str(k, "utf-8")] = float(v)

            cooker.set_state(state)
            self.send_state_json()

    def send_page(self, page="cooker.html"):
        with open("site/" + page, "r") as doc:
            content = bytes(doc.read(), "utf-8")
            self.send_response(200, "ok")
            self.send_header("Content-Length", len(content))
            self.end_headers()
            self.wfile.write(content)

    def send_state_json(self):
        state = self.server.cooker.get_state()
        response = bytes(json.dumps(state, indent=2), "utf-8")
        self.send_response(200, "ok")
        self.send_header("Content-Length", len(response))
        self.end_headers()
        self.wfile.write(response)

    def not_found(self):
        self.send_response(404, "Not Found")
        self.end_headers()

    def bad_request(self):
        self.send_response(400, "Bad Request")
        self.end_headers()

if __name__ == "__main__":
    print("hello")
    server = WebServer()
    try:
        server.cooker.heater.run()
        server.cooker.start_sampling()
        print("data:")
        print(server.cooker.get_state())
        print("starting server...")
        server.serve_forever()
    finally:
        server.cooker.close()
