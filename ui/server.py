"""Tiny local web server that shows the Jarvis screen and shares live state with it."""
import json
import queue
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

WEB_DIR = Path(__file__).parent / "web"


class UIState:
    """Shared state between the assistant (main thread) and the browser (server threads)."""

    def __init__(self, model_label=""):
        self._lock = threading.Lock()
        self._inbox = queue.Queue()
        self._confirm_event = threading.Event()
        self._confirm_answer = False
        self.data = {
            "status": "idle",  # idle | listening | thinking | speaking
            "messages": [],
            "msg_id": 0,
            "confirm": "",
            "browser_speech": False,
            "model": model_label,
        }

    def set(self, **kwargs):
        with self._lock:
            self.data.update(kwargs)

    def add(self, role, text):
        with self._lock:
            self.data["msg_id"] += 1
            self.data["messages"].append({"id": self.data["msg_id"], "role": role, "text": text})
            self.data["messages"] = self.data["messages"][-12:]

    def snapshot(self):
        with self._lock:
            return json.loads(json.dumps(self.data))

    # typed commands coming from the browser
    def submit(self, text):
        self.add("user", text)
        self._inbox.put(text)

    def has_input(self):
        return not self._inbox.empty()

    def pop_input(self, timeout=None):
        try:
            return self._inbox.get_nowait() if timeout is None else self._inbox.get(timeout=timeout)
        except queue.Empty:
            return None

    # yes/no confirmation shown as a popup in the browser
    def ask(self, question, timeout=45):
        self._confirm_event.clear()
        self._confirm_answer = False
        self.set(confirm=question)
        got = self._confirm_event.wait(timeout)
        self.set(confirm="")
        return bool(got and self._confirm_answer)

    def answer(self, yes):
        self._confirm_answer = bool(yes)
        self._confirm_event.set()


def _make_handler(state, token, allowed_hosts):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # keep the terminal clean
            pass

        def _send(self, code, body, ctype="application/json"):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _host_ok(self):
            # blocks DNS-rebinding tricks from other websites
            return self.headers.get("Host", "") in allowed_hosts

        def do_GET(self):
            if not self._host_ok():
                return self._send(403, b"{}")
            if self.path in ("/", "/index.html"):
                html = (WEB_DIR / "index.html").read_text(encoding="utf-8").replace("__TOKEN__", token)
                self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
            elif self.path.startswith("/state"):
                self._send(200, json.dumps(state.snapshot()).encode("utf-8"))
            else:
                self._send(404, b"{}")

        def do_POST(self):
            # only our own page (which knows the secret token) may send commands
            if not self._host_ok() or self.headers.get("X-Jarvis-Token") != token:
                return self._send(403, b"{}")
            length = int(self.headers.get("Content-Length", 0) or 0)
            try:
                payload = json.loads(self.rfile.read(length) or b"{}")
            except ValueError:
                payload = {}
            if self.path == "/say":
                text = str(payload.get("text", "")).strip()[:500]
                if text:
                    state.submit(text)
            elif self.path == "/confirm":
                state.answer(payload.get("answer"))
            self._send(200, b"{}")

    return Handler


def start_server(state, start_port=8765):
    """Start the server in a background thread. Returns the URL to open."""
    token = secrets.token_urlsafe(16)
    for port in range(start_port, start_port + 20):
        hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), _make_handler(state, token, hosts))
        except OSError:
            continue  # port busy, try the next one
        server.daemon_threads = True
        threading.Thread(target=server.serve_forever, daemon=True).start()
        return f"http://127.0.0.1:{port}/"
    raise RuntimeError("Could not find a free port for the Jarvis screen.")