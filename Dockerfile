# Use Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy ONLY backend files (not frontend)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Create directory for SQLite database
RUN mkdir -p /data

# Expose port
EXPOSE 8000

# Start command - point to your app.py
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]