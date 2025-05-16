FROM python:3.11-slim-bullseye

WORKDIR /app

# Install Node.js and npm (compatible versions)
RUN apt-get update && \
    apt-get install -y curl gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_16.x | bash - && \
    apt-get install -y nodejs && \
    # Don't upgrade npm to avoid compatibility issues
    npm --version

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Verify Node.js installation
RUN node --version && npm --version

# Create downloads directory
RUN mkdir -p downloads

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install pyrogram tgcrypto yt-dlp ffmpeg-python && \
    pip install --pre py-tgcalls

# Copy project files
COPY . .

# Set environment variable
ENV IS_HEROKU=true

# Run the bot
CMD ["python", "main.py"]
