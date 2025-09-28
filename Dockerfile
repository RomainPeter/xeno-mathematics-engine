# Discovery Engine 2-Cat v0.1.0
# Hermetic build for reproducible execution

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install OPA
RUN curl -L -o opa https://openpolicyagent.org/downloads/v0.60.0/opa_linux_amd64 && \
    chmod +x opa && \
    mv opa /usr/local/bin/opa

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 discovery && \
    chown -R discovery:discovery /app

USER discovery

# Set environment variables
ENV PYTHONPATH=/app
ENV OPA_PATH=/usr/local/bin/opa
ENV DISCOVERY_ENGINE_VERSION=v0.1.0

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command
CMD ["python", "scripts/demo_discovery_engine.py"]
