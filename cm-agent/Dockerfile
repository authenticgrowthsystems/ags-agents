FROM python:3.11-slim
WORKDIR /app

# psycopg[binary] ships its own libpq; only curl is needed (healthcheck).
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
RUN mkdir -p /app/logs

EXPOSE 8089
CMD ["python", "-m", "app.worker"]
