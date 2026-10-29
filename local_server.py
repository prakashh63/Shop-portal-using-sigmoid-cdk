"""Run the shop portal on your machine: http://localhost:8000  (no AWS account needed).

It imitates what the cloud does:
  CloudFront   -> routes '/', '/assets/*' to static files and '/api/*' to the API
  API Gateway  -> turns an HTTP request into an 'event' dict and calls the Lambda
  Lambda       -> your real handler code in src/<name>/index.py

What it does NOT imitate: HTTPS, caching, IAM permissions, throttling, real S3 and SNS.
(BUCKET_INVOICES is not set locally, so orders/reports skip S3.)
"""

import importlib.util
import json
import mimetypes
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

HERE = Path(__file__).parent
SITE = HERE / "site"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

# Same table as api_gateway.routes in app.py: path prefix -> (folder, function name)
ROUTES = {
    "/api/users": ("users", "shop-users"),
    "/api/orders": ("orders", "shop-orders-api"),
    "/api/reports": ("reports", "shop-reports"),
}

_handlers = {}


def load_handler(folder):
    if folder not in _handlers:
        path = HERE / "src" / folder / "index.py"
        spec = importlib.util.spec_from_file_location(f"{folder}_index", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _handlers[folder] = module.handler
    return _handlers[folder]


def find_route(path):
    for prefix, target in ROUTES.items():
        if path == prefix or path.startswith(prefix + "/"):
            return target
    return None


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _static(self, path):
        name = "index.html" if path == "/" else path.lstrip("/")
        file = (SITE / name).resolve()
        if SITE.resolve() not in file.parents or not file.is_file():
            return self._send(404, b"Not found", "text/plain")
        kind = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
        self._send(200, file.read_bytes(), kind)

    def _api(self, method, parsed, folder, function_name):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length).decode("utf-8") if length else None
        # This is the shape API Gateway gives a Lambda (REST API, proxy integration)
        event = {
            "httpMethod": method,
            "path": parsed.path,
            "headers": dict(self.headers),
            "queryStringParameters": {k: v[0] for k, v in parse_qs(parsed.query).items()} or None,
            "body": body,
            "isBase64Encoded": False,
        }
        context = SimpleNamespace(function_name=function_name, aws_request_id=str(uuid4()))
        try:
            result = load_handler(folder)(event, context)
        except Exception as error:  # a crash in the Lambda becomes a 502 in API Gateway
            print(f"  Lambda {function_name} raised: {error!r}")
            return self._send(502, b'{"message": "Internal server error"}', "application/json")
        headers = result.get("headers") or {}
        self._send(
            result.get("statusCode", 200),
            (result.get("body") or "").encode("utf-8"),
            headers.get("Content-Type", "application/json"),
        )

    def _dispatch(self, method):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            target = find_route(parsed.path)
            if target is None:  # API Gateway answers 403 for an unknown route
                return self._send(403, b'{"message": "Missing Authentication Token"}', "application/json")
            return self._api(method, parsed, *target)
        if method == "GET":
            return self._static(parsed.path)
        self._send(405, b"Method not allowed", "text/plain")

    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")

    def do_PUT(self):
        self._dispatch("PUT")

    def do_DELETE(self):
        self._dispatch("DELETE")

    def log_message(self, fmt, *args):
        print(f"{self.command:<6} {self.path}  ->  {args[1]}")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Shop portal running at http://localhost:{PORT}   (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()