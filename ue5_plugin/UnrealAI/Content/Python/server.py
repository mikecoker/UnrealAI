"""
HTTP server that runs inside UE5's editor process.
Requests arrive on a background thread; unreal.* calls are dispatched
on the game thread via a tick callback queue.
"""
import json
import queue
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self._send({"ok": True, "service": "unreal-ai"})
        else:
            self._send({"ok": False, "error": f"Unknown route: {self.path}"}, 404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        resp_q = queue.Queue()
        self.server.request_queue.put((self.path, body, resp_q))
        try:
            result = resp_q.get(timeout=30)
        except queue.Empty:
            result = {"ok": False, "error": "Request timed out (30s)"}

        self._send(result)

    def _send(self, data, status=200):
        payload = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        pass  # suppress default HTTP logs


class UnrealAIServer:
    def __init__(self, port=7777):
        self.port = port
        self._httpd = HTTPServer(("localhost", port), _Handler)
        self._httpd.request_queue = queue.Queue()
        self._thread = None

    def start(self):
        """Start serving in a background thread. Register tick callback for game thread dispatch."""
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()

        try:
            import unreal
            self._tick_handle = unreal.register_slate_post_tick_callback(self._tick)
            unreal.log(f"[UnrealAI] Server running on localhost:{self.port}")
        except ImportError:
            pass  # running outside UE5 (tests)

    def serve_once(self):
        """Used in tests — handle one request then return."""
        self._httpd.handle_request()

    def shutdown(self):
        if self._thread is not None and self._thread.is_alive():
            self._httpd.shutdown()
        else:
            self._httpd.server_close()

    def _tick(self, _delta):
        """Called on the game thread each frame. Drains the request queue."""
        import importlib, sys

        # Auto-reload handler modules so file changes take effect without restart
        for key in [k for k in list(sys.modules) if k.startswith("handlers") or k == "routes"]:
            try:
                importlib.reload(sys.modules[key])
            except Exception:
                del sys.modules[key]

        from routes import dispatch
        while True:
            try:
                path, body, resp_q = self._httpd.request_queue.get_nowait()
            except queue.Empty:
                break
            try:
                result = dispatch(path, body)
            except Exception as exc:
                result = {"ok": False, "error": str(exc)}
            resp_q.put(result)
