FROM mcr.microsoft.com/playwright/python:v1.54.0-jammy

# Install system dependencies including supercronic
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    ca-certificates \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install supercronic (lightweight cron alternative)
RUN curl -fsSLo /usr/local/bin/supercronic \
    https://github.com/aptible/supercronic/releases/download/v0.2.29/supercronic-linux-amd64 \
    && chmod +x /usr/local/bin/supercronic

# Set workdir
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/bin /app/logs /app/data

# Copy the rest of the code
COPY src/ ./src/

# Copy scripts to bin directory
COPY bin/ ./bin/

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Make scripts executable
RUN chmod +x /app/bin/*.sh

# Default command (can be overridden)
CMD ["/app/bin/run.sh"]
