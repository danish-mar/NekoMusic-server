# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install ffmpeg (required by yt-dlp postprocessors)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the application
COPY app /app

# Expose port
ENV PORT=8982
EXPOSE 8982

# Run the server
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 1"]
