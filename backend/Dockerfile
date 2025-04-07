# Use a slim Python base image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Install system dependencies required for psycopg2 build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    python3-dev \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt

# Create a non-root user and switch to it
RUN addgroup --system app && adduser --system --group app
USER app

# Copy the application code
COPY . .

# Expose the port Gunicorn will run on
EXPOSE 8000

# Run the application using Gunicorn
# Adjust the number of workers (-w) as needed based on your server resources
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "core.wsgi:application"]