# Matrica Networks - Cybersecurity Company Website
# Production Docker Image
# 
# This Dockerfile creates a lightweight, secure container for the Matrica
# Networks website using Python 3.10 and alpine Linux for minimal size.

FROM python:3.10-alpine

# Metadata
LABEL maintainer="Matrica Networks <admin@matricanetworks.com>"
LABEL description="Cybersecurity company website with admin portal"
LABEL version="1.0.0"

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MATRICA_ENV=production \
    MATRICA_HOST=0.0.0.0 \
    MATRICA_PORT=8000

# Create non-root user for security
RUN addgroup -g 1001 -S matrica && \
    adduser -u 1001 -S matrica -G matrica

# Set working directory
WORKDIR /app

# Install system dependencies (minimal)
RUN apk add --no-cache \
    sqlite \
    sqlite-dev \
    gcc \
    musl-dev && \
    rm -rf /var/cache/apk/*

# Copy application files
COPY --chown=matrica:matrica . .

# Create necessary directories with proper permissions
RUN mkdir -p \
    backend/logs \
    backend/storage/uploads \
    backend/storage/docs && \
    chown -R matrica:matrica backend/logs backend/storage && \
    chmod 755 backend/logs backend/storage

# Initialize database if not exists
RUN if [ ! -f backend/matrica.db ]; then \
        cd backend && \
        su matrica -c "python db_init.py"; \
    fi

# Create database backup directory
RUN mkdir -p /app/backups && \
    chown matrica:matrica /app/backups

# Health check script
COPY <<EOF /usr/local/bin/healthcheck.sh
#!/bin/sh
# Health check for Matrica Networks application
curl -f http://localhost:8000/ || exit 1
EOF

RUN chmod +x /usr/local/bin/healthcheck.sh

# Security: Switch to non-root user
USER matrica

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /usr/local/bin/healthcheck.sh

# Volume for persistent data
VOLUME ["/app/backend/logs", "/app/backend/storage", "/app/backups"]

# Startup script
COPY <<EOF /app/docker-entrypoint.sh
#!/bin/sh
set -e

echo "🚀 Starting Matrica Networks Application..."
echo "Environment: $MATRICA_ENV"
echo "Host: $MATRICA_HOST"
echo "Port: $MATRICA_PORT"

# Check database exists and is writable
if [ ! -f "backend/matrica.db" ]; then
    echo "📊 Initializing database..."
    cd backend && python db_init.py && cd ..
fi

# Ensure proper permissions
chmod 664 backend/matrica.db 2>/dev/null || true

# Check log directory
if [ ! -d "backend/logs" ]; then
    mkdir -p backend/logs
fi

# Cleanup old sessions on startup
echo "🧹 Cleaning up expired sessions..."
cd backend
python3 -c "
from models import Session
try:
    Session.cleanup_expired()
    print('✓ Expired sessions cleaned')
except Exception as e:
    print(f'⚠ Session cleanup failed: {e}')
"
cd ..

# Start the application
echo "🌐 Starting web server on $MATRICA_HOST:$MATRICA_PORT"
cd backend
exec python server.py
EOF

RUN chmod +x /app/docker-entrypoint.sh

# Default command
CMD ["/app/docker-entrypoint.sh"]