# serve.py
import os, json, base64, tempfile, contextlib
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


from google_analytics_mcp.server import mcp

def _ensure_adc_from_env():
    adc_json = os.getenv("GOOGLE_ADC_JSON")
    adc_b64 = os.getenv("GOOGLE_ADC_JSON_B64")
    if not (adc_json or adc_b64):
        return
    if adc_b64 and not adc_json:
        adc_json = base64.b64decode(adc_b64).decode("utf-8")
    # validate & write to a temp file, then point ADC to it
    data = json.loads(adc_json)
    fd = tempfile.NamedTemporaryFile("w", delete=False, suffix=".json")
    fd.write(json.dumps(data))
    fd.flush(); fd.close()
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = fd.name


class TokenAuth(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        token = os.getenv("MCP_AUTH_TOKEN")
        if not token:
            return await call_next(request)
        auth = request.headers.get("authorization", "")
        if auth != f"Bearer {token}":
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return await call_next(request)


_ensure_adc_from_env()
# default mount paths from the SDK are /sse and /mcp; we’ll be explicit:
mcp.settings.mount_path = "/unused"
app = Starlette(
    routes=[
        Mount("/sse", app=mcp.sse_app()),
        Mount("/mcp", app=mcp.streamable_http_app()),
    ],
)
app.add_middleware(TokenAuth)
