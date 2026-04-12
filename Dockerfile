FROM python:3.11-slim

WORKDIR /app

RUN mkdir -p /app/data /app/templates

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py scraper.py init_db.py scheduler.py ./
COPY templates/ templates/

# Seed the database at build time so the app has data on first start.
# The scraper will overwrite statuses with live data on its first run.
ENV DATABASE_PATH=/app/data/trails.db
RUN python init_db.py

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

CMD ["python", "app.py"]
