FROM python:3.11-slim-bullseye

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir pyrogram py-tgcalls tgcrypto yt-dlp ffmpeg-python

# Run the bot
CMD ["python", "main.py"]
