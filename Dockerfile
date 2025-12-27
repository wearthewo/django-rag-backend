# Use a slim Python 3.14 image for smaller size
FROM python:3.14-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies for PostgreSQL, Redis, and Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt /app/

# Upgrade pip and install Python dependencies without caching to reduce image size
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir psycopg2-binary django-redis

# Copy project files
COPY . /app/

# Expose port for Uvicorn / Django
EXPOSE 8000

# Run Django with Uvicorn (ASGI)
CMD ["uvicorn", "backend.config.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--reload"]
