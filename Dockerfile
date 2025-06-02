FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y gcc libpq-dev tini procps && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app and scripts
COPY app ./app
COPY scripts ./scripts

# Expose ports:
# 8000 - FastAPI
# 8089 - Locust Web UI
# 5557 - Locust Master (RPC)
# 5558 - Locust Worker (RPC)
EXPOSE 8000 8089 5557 5558 9080-9090

COPY start.sh /start.sh
RUN chmod +x /start.sh

ENV DATABASE_URL=postgresql://proot:proot@host.docker.internal:5432/hopper

ENTRYPOINT ["/start.sh"]