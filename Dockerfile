FROM python:3.10-slim

WORKDIR /app

# Set default environment variables
ENV PORT=5000
ENV DEBUG=False
ENV DATABRICKS_TOKEN=""
ENV DATABRICKS_BASE_URL=""
ENV AVAILABLE_MODELS=""

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Run as non-root user for security
RUN useradd -m appuser
USER appuser

# Expose the port the app runs on
EXPOSE ${PORT}

# Use gunicorn as production server
CMD gunicorn --bind 0.0.0.0:${PORT} app:app