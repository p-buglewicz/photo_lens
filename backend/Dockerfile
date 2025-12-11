FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Copy application code early so setuptools can find packages
COPY . .

# Build dependencies into /opt/venv
RUN uv sync \
    --frozen \
    --no-dev


FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy venv from builder
COPY --from=builder /app/.venv /app/.venv

# Set PATH to use venv
ENV PATH="/app/.venv/bin:$PATH"

# Expose FastAPI port
EXPOSE 8000

# Run migrations and start the server
CMD ["sh", "-c", "alembic upgrade head && uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"]
