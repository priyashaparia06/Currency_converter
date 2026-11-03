# Use an official lightweight Python runtime
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first for Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY converter.py server.py ./

# Create a non-root system user for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose Gunicorn application port
EXPOSE 5000

# Run with Gunicorn using 2 worker processes and 2 threads
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "2", "--timeout", "30", "server:app"]