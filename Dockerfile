FROM python:3.11-slim

LABEL org.opencontainers.image.title="ClawBoard Pro — Deep Agents + OpenClaw"
LABEL org.opencontainers.image.source="https://github.com/Get-Second-Step/clawboard-agent"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps
RUN apt-get update -qq && \
    apt-get install -y -qq --no-install-recommends \
        curl git chromium && \
    rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Python dependencies
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt -q

# Copy source
COPY . .

# Reports directory
RUN mkdir -p reports config

EXPOSE 3000

HEALTHCHECK --interval=20s --timeout=5s --start-period=15s \
    CMD curl -sf http://localhost:3000/health || exit 1

CMD ["python3", "server.py"]
