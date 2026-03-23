# =============================================================================
# KISWARM6.0 Multi-Stage Dockerfile
# =============================================================================
# Production-ready Docker image for KISWARM6.0
#
# Stages:
#   1. base       - Common base with system dependencies
#   2. backend    - Python/Flask backend
#   3. frontend   - Node.js/Vite frontend build
#   4. bridge     - tRPC bridge service
#   5. production - Final production image
#
# Author: Baron Marco Paolo Ialongo
# Version: 6.0.0
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Base Image
# -----------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS base

# Labels
LABEL maintainer="Baron Marco Paolo Ialongo"
LABEL version="6.0.0"
LABEL description="KISWARM6.0 - KI-natives Finanzprotokoll"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    nodejs \
    npm \
    mariadb-client \
    libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

# Install pnpm
RUN npm install -g pnpm

# Create app user
RUN groupadd -r kiswarm && useradd -r -g kiswarm kiswarm

# Set work directory
WORKDIR /app

# -----------------------------------------------------------------------------
# Stage 2: Backend Builder
# -----------------------------------------------------------------------------
FROM base AS backend-builder

# Copy backend requirements first for better caching
COPY backend/requirements.txt /app/backend/

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r /app/backend/requirements.txt

# Copy backend source
COPY backend/ /app/backend/

# Run basic checks
RUN python -m py_compile /app/backend/run.py

# -----------------------------------------------------------------------------
# Stage 3: Frontend Builder
# -----------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder

# Set environment variables
ENV NODE_ENV=production \
    PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"

# Enable corepack for pnpm
RUN corepack enable

# Set work directory
WORKDIR /app

# Copy frontend package files
COPY frontend/package.json frontend/pnpm-lock.yaml /app/

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy frontend source
COPY frontend/ /app/

# Build frontend
RUN pnpm build

# -----------------------------------------------------------------------------
# Stage 4: Bridge Builder
# -----------------------------------------------------------------------------
FROM node:20-alpine AS bridge-builder

# Set environment variables
ENV NODE_ENV=production \
    PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"

# Enable corepack for pnpm
RUN corepack enable

# Set work directory
WORKDIR /app

# Copy bridge package files
COPY bridge/package.json /app/

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy bridge source
COPY bridge/ /app/

# Build bridge (if needed)
RUN pnpm build || true

# -----------------------------------------------------------------------------
# Stage 5: Production Backend
# -----------------------------------------------------------------------------
FROM base AS backend-production

# Copy Python dependencies from builder
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy backend source
COPY --from=backend-builder /app/backend /app/backend

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/tmp \
    && chown -R kiswarm:kiswarm /app

# Set environment variables
ENV FLASK_APP=run.py \
    FLASK_ENV=production \
    PYTHONPATH=/app/backend

# Expose backend port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/api/v6/status || exit 1

# Switch to non-root user
USER kiswarm

# Set work directory
WORKDIR /app/backend

# Start command
CMD ["gunicorn", "--config", "gunicorn.conf.py", "run:create_kiswarm6_app()"]

# -----------------------------------------------------------------------------
# Stage 6: Production Frontend
# -----------------------------------------------------------------------------
FROM node:20-alpine AS frontend-production

# Set environment variables
ENV NODE_ENV=production \
    PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"

# Enable corepack for pnpm
RUN corepack enable

# Install serve for static file serving
RUN pnpm add -g serve

# Set work directory
WORKDIR /app

# Copy built frontend from builder
COPY --from=frontend-builder /app/dist /app/dist

# Create necessary directories
RUN mkdir -p /app/logs /app/tmp

# Expose frontend port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# Start command
CMD ["serve", "-s", "dist/client", "-l", "3000"]

# -----------------------------------------------------------------------------
# Stage 7: Development Image (All-in-one)
# -----------------------------------------------------------------------------
FROM base AS development

# Copy Python dependencies
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy all source
COPY --from=backend-builder /app/backend /app/backend
COPY --from=frontend-builder /app /app/frontend
COPY --from=bridge-builder /app /app/bridge

# Create virtual environment symlink
RUN ln -s /usr/local/lib/python3.11/site-packages /app/.venv

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/tmp /app/.venv \
    && chown -R kiswarm:kiswarm /app

# Set environment variables
ENV FLASK_APP=run.py \
    FLASK_ENV=development \
    NODE_ENV=development \
    PYTHONPATH=/app/backend

# Expose ports
EXPOSE 5001 3000 5173

# Default command (can be overridden)
CMD ["python", "/app/backend/run.py"]

# -----------------------------------------------------------------------------
# Stage 8: Production All-in-one
# -----------------------------------------------------------------------------
FROM base AS production

# Copy Python dependencies
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy backend
COPY --from=backend-builder /app/backend /app/backend

# Copy frontend dist
COPY --from=frontend-builder /app/dist /app/frontend/dist

# Copy bridge
COPY --from=bridge-builder /app /app/bridge

# Copy scripts
COPY scripts/ /app/scripts/

# Make scripts executable
RUN chmod +x /app/scripts/*.sh

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/tmp \
    && chown -R kiswarm:kiswarm /app

# Set environment variables
ENV FLASK_APP=run.py \
    FLASK_ENV=production \
    NODE_ENV=production \
    PYTHONPATH=/app/backend

# Expose ports
EXPOSE 5001 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/api/v6/status || exit 1

# Switch to non-root user
USER kiswarm

# Set work directory
WORKDIR /app/backend

# Start command
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "4", "run:create_kiswarm6_app()"]
