"""Local branch preview. Deterministic product tools need no cloud credentials.

Run: python scripts/serve_local.py --port 8765
Bill/voice OCR stays on the deployed service; the Delhi sample uses the existing sunlight fixture.
"""
import argparse
import json
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from surya import handler, pipeline
from surya.solar import solar_yield

fixture = ROOT / "tests/fixtures/delhi_sources.json"
pipeline._yields["v2:28.6:77.2"] = solar_yield(json.loads(fixture.read_text(encoding="utf-8")))


class Preview(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "web"), **kwargs)

    def send_head(self):
        # Development assets should reflect the working tree after a browser reload.
        if "If-Modified-Since" in self.headers:
            del self.headers["If-Modified-Since"]
        return super().send_head()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        if self.path.startswith("/api/"):
            self.api("GET")
        else:
            super().do_GET()

    def do_POST(self):
        self.api("POST")

    def do_DELETE(self):
        self.api("DELETE")

    def api(self, method):
        url = urlsplit(self.path)
        path = url.path.removeprefix("/api")
        size = int(self.headers.get("Content-Length", 0))
        if size > 6000000:
            self.send_error(413)
            return
        raw = self.rfile.read(size).decode("utf-8") if size else None
        if path in ("/bill", "/quote", "/ask"):
            result = {"statusCode": 503, "body": json.dumps({"error": "This local preview does not call cloud AI. Use the sample comparison or enter your quote terms below; bill/photo/voice AI remains available on the deployed site."})}
        else:
            try:
                result = handler.lambda_handler({"requestContext": {"http": {"method": method}}, "rawPath": path,
                    "queryStringParameters": {k:v[-1] for k,v in parse_qs(url.query).items()}, "body": raw}, None)
            except Exception:
                result = {"statusCode": 500, "body": json.dumps({"error": "Preview request failed; check the local console."})}
                import traceback
                traceback.print_exc()
        body = result["body"].encode("utf-8")
        self.send_response(result["statusCode"])
        self.send_header("Content-Type", result.get("headers", {}).get("content-type", "application/json; charset=utf-8"))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    print(f"Surya Saathi branch preview: http://127.0.0.1:{args.port} (local tools + captured Delhi sample sunlight)", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port), Preview).serve_forever()
