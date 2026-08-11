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
COPY bot.py .
COPY database.py .
COPY rss.py .
COPY scraper.py .
COPY scheduler.py .
COPY notifier.py .

# Create directories for data and logs
RUN mkdir -p data logs

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Volume for persistent data
VOLUME ["/app/data", "/app/logs"]

# Run the application
CMD ["python", "bot.py"]
