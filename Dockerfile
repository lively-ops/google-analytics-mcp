FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app


RUN pip install --no-cache-dir -e . \
    && pip install --no-cache-dir "mcp[server]" uvicorn

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD bash -lc '</dev/tcp/127.0.0.1/8080 || exit 1'

CMD ["uvicorn", "serve:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers", "--forwarded-allow-ips", "*"]


