FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY database.py .
COPY rss.py .
COPY scraper.py .
COPY notifier.py .
COPY scheduler.py .
COPY config.json .

# Create directories for data and logs
RUN mkdir -p data logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CHECK_INTERVAL_HOURS=6
ENV DATABASE_PATH=data/news_monitor.db
ENV LOG_FILE=logs/news_monitor.log
ENV LOG_LEVEL=INFO

# Volume for persistent data
VOLUME ["/app/data", "/app/logs"]

# Run the application
CMD ["python", "app.py"]
