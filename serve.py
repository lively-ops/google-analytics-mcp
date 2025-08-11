# serve.py
import os, json, base64, tempfile
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from analytics_mcp.server import mcp

def _ensure_adc_from_env():
    adc_json = os.getenv("GOOGLE_ADC_JSON")
    adc_b64 = os.getenv("GOOGLE_ADC_JSON_B64")
    if adc_b64 and not adc_json:
        adc_json = base64.b64decode(adc_b64).decode("utf-8")
    if not adc_json:
        return
    data = json.loads(adc_json)
    fd = tempfile.NamedTemporaryFile("w", delete=False, suffix=".json")
    fd.write(json.dumps(data)); fd.flush(); fd.close()
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = fd.name

class TokenAuth(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        tok = os.getenv("MCP_AUTH_TOKEN")
        if tok and request.headers.get("authorization", "") != f"Bearer {tok}":
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return await call_next(request)

async def healthz(_):
    return JSONResponse({"ok": True})

_ensure_adc_from_env()
try:
    mcp.settings.mount_path = "/unused"
except Exception:
    pass

app = Starlette(
    routes=[
        Mount("/sse/", app=mcp.sse_app()),
        Mount("/", app=mcp.streamable_http_app()),
        Route("/healthz", healthz),
    ],
)
app.add_middleware(TokenAuth)
