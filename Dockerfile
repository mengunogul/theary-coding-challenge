# autellect-backend/Dockerfile
FROM python:3.13.3-alpine

WORKDIR /app

# Install uv for faster Python package management
RUN pip install --no-cache-dir uv

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies using uv in a specific location
RUN uv sync --frozen

# Copy the application code
COPY . .

# Copy and set permissions for entrypoint script
COPY src/scripts/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Set PYTHONPATH to include the src directory
ENV PYTHONPATH=/app/src

# Configure uv to use the virtual environment
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Set working directory to where manage.py is located
WORKDIR /app/src

# Create a non-root user for security
RUN adduser -D -s /bin/sh django && \
    chown -R django:django /app

USER django

# Expose the port Django runs on
EXPOSE 8000

# Use entrypoint script that handles migrations
ENTRYPOINT ["/app/entrypoint.sh"]
