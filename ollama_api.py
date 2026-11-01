#!/usr/bin/env python3
"""Proxy OpenAI-compatible: BACKEND=ollama (ค่าเริ่มต้น) หรือ openrouter"""
import json, os, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOKEN = os.environ["API_TOKEN"]
BACKEND = os.environ.get("BACKEND", "ollama")
OLLAMA = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
OR_BASE = "https://openrouter.ai/api"
OR_KEY = ""
if BACKEND == "openrouter":
    OR_KEY = os.environ.get("OPENROUTER_API_KEY") or open("/root/.openrouter_key").read().strip()
# GitHub Models (OpenAI-compatible) ใช้ GitHub Personal Access Token ที่มีสิทธิ์ models
GH_BASE = "https://models.github.ai/inference"
GH_KEY = ""
if BACKEND == "github":
    GH_KEY = os.environ.get("GITHUB_TOKEN") or open("/root/.github_token").read().strip()
ORIGIN = os.environ.get("ALLOWED_ORIGIN", "*")
PORT = int(os.environ.get("PORT", "8080"))
MAX_BODY = 256 * 1024
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "meta-llama/llama-3.3-70b-instruct" if BACKEND != "github" else "openai/gpt-4o-mini")
MAX_OUT = int(os.environ.get("MAX_OUTPUT_TOKENS", "1024"))
THAI_SYSTEM = "คุณเป็นผู้ช่วย AI ตอบเป็นภาษาไทยเสมอ เว้นแต่ผู้ใช้ขอให้ใช้ภาษาอื่น"


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", ORIGIN)
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")

    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authed(self):
        if self.headers.get("Authorization") != f"Bearer {TOKEN}":
            self._send(401, {"error": {"message": "invalid api key", "type": "auth"}})
            return False
        return True

    def _forward(self, method, upstream_path, body=None):
        if BACKEND == "openrouter":
            base, headers = OR_BASE, {"Authorization": f"Bearer {OR_KEY}",
                                      "HTTP-Referer": "https://codingfleet.com",
                                      "X-Title": "CodingFleet"}
        elif BACKEND == "github":
            base, headers = GH_BASE, {"Authorization": f"Bearer {GH_KEY}",
                                      "Accept": "application/vnd.github+json",
                                      "X-GitHub-Api-Version": "2022-11-28"}
            # GitHub: chat อยู่ที่ /inference/chat/completions และรายการโมเดลอยู่ที่ /catalog/models
            if upstream_path == "/v1/models":
                base = "https://models.github.ai"
                upstream_path = "/catalog/models"
            else:
                upstream_path = upstream_path.replace("/v1/", "/", 1)
        else:
            base, headers = OLLAMA, {}
        headers["Content-Type"] = "application/json"
        req = urllib.request.Request(f"{base}{upstream_path}", data=body,
                                     method=method, headers=headers)
        try:
            resp = urllib.request.urlopen(req, timeout=600)
        except urllib.error.HTTPError as e:
            resp = e
        except urllib.error.URLError as e:
            return self._send(502, {"error": {"message": f"upstream unavailable: {e}"}})
        self.send_response(resp.status)
        self._cors()
        self.send_header("Content-Type", resp.headers.get("Content-Type", "application/json"))
        self.send_header("Connection", "close")
        self.end_headers()
        while True:  # ส่งต่อทีละ chunk (รองรับ stream)
            chunk = resp.read(1024)
            if not chunk:
                break
            self.wfile.write(chunk)
            self.wfile.flush()

    def _adapt_openrouter(self, raw):
        """แมปชื่อโมเดลเก่า (เช่น qwen2.5:0.5b) ไปเป็นโมเดลบน OpenRouter และบังคับให้ตอบภาษาไทย"""
        try:
            req = json.loads(raw)
        except json.JSONDecodeError:
            return raw
        model = str(req.get("model", ""))
        if "/" not in model:  # ชื่อแบบ Ollama ไม่ใช่ slug ของ OpenRouter
            req["model"] = DEFAULT_MODEL
        msgs = req.get("messages", [])
        if not any(m.get("role") == "system" and "ไทย" in str(m.get("content", "")) for m in msgs):
            msgs.insert(0, {"role": "system", "content": THAI_SYSTEM})
        req["messages"] = msgs
        # จำกัด max_tokens ไม่ให้เกินเครดิตที่มี (ค่าที่ส่งมาเช่น 32768 ทำให้ 402)
        try:
            req["max_tokens"] = min(int(req.get("max_tokens") or MAX_OUT), MAX_OUT)
        except (TypeError, ValueError):
            req["max_tokens"] = MAX_OUT
        return json.dumps(req, ensure_ascii=False).encode()

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Connection", "close")
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            return self._send(200, {"ok": True, "backend": BACKEND})
        if self.path in ("/v1/models", "/models"):
            if not self._authed():
                return
            return self._forward("GET", "/v1/models")
        self._send(404, {"error": {"message": "not found"}})

    def do_POST(self):
        if not self._authed():
            return
        length = int(self.headers.get("Content-Length", 0))
        if length > MAX_BODY:
            return self._send(413, {"error": {"message": "body too large"}})
        raw = self.rfile.read(length)

        if self.path in ("/v1/chat/completions", "/chat/completions"):
            if BACKEND in ("openrouter", "github"):
                raw = self._adapt_openrouter(raw)
            return self._forward("POST", "/v1/chat/completions", raw)

        if self.path == "/api/chat":  # รูปแบบเดิม (Ollama เท่านั้น)
            if BACKEND != "ollama":
                return self._send(400, {"error": "use /v1/chat/completions"})
            try:
                req = json.loads(raw)
            except json.JSONDecodeError:
                return self._send(400, {"error": "invalid JSON"})
            messages = req.get("messages")
            if not messages and req.get("message"):
                messages = [{"role": "user", "content": str(req["message"])}]
            if not messages:
                return self._send(400, {"error": "missing message"})
            payload = {"model": req.get("model", "qwen2.5:0.5b"),
                       "messages": messages[-20:], "stream": False}
            return self._forward("POST", "/api/chat", json.dumps(payload).encode())

        self._send(404, {"error": {"message": "not found"}})

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print(f"listening on :{PORT} backend={BACKEND}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
