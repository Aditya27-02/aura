# ─── Stage 1: Build frontend ───────────────────────────────────────────
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --ignore-scripts 2>/dev/null || npm install
COPY frontend/ ./
RUN npm run build

# ─── Stage 2: Python runtime ──────────────────────────────────────────
FROM python:3.12-slim AS runtime
WORKDIR /app

# Install Python dependencies
COPY server/requirements.txt server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt

# Copy engine (read-only)
COPY adaptive/ adaptive/
COPY pyproject.toml ./

# Copy server
COPY server/ server/

# Copy built frontend
COPY --from=frontend-build /app/frontend/dist frontend/dist

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

# Run
ENV PYTHONPATH=/app
CMD ["python", "-m", "uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
