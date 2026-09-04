# ── Build stage ───────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build
COPY pyproject.toml README.md ./
COPY src/ src/

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -e .

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="SimuCity AI"
LABEL org.opencontainers.image.description="Autonomous Multi-Agent Simulation Research Platform"
LABEL org.opencontainers.image.version="0.1.0"

WORKDIR /app

# Copy installed packages and project from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /build /app

# Copy frontend dashboard
COPY frontend/ frontend/

# SQLite DB will be created at /data/simucity.db
RUN mkdir -p /data

EXPOSE 8000

# Allow API key env vars to be passed at runtime
ENV ANTHROPIC_API_KEY=""
ENV GEMINI_API_KEY=""

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"

CMD ["python", "-m", "uvicorn", "simucity.api.main:app", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "1"]
