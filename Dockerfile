FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Create data directory inside container
RUN mkdir -p /app/data

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY scraper.py .
COPY init_db.py .
COPY init_container_db.py .

# Initialize database on build
RUN python init_container_db.py

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run the application
CMD ["python", "app.py"]
