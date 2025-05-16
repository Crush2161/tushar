FROM python:3.11-slim-bullseye

WORKDIR /app

# Install Node.js (using latest LTS version 18.x)
RUN apt-get update && \
    apt-get install -y curl gnupg && \
    curl -sL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g npm@latest

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Verify Node.js installation
RUN node --version && npm --version

# Copy project files
COPY . .

# Create downloads directory
RUN mkdir -p downloads

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install pyrogram tgcrypto yt-dlp
RUN pip install --no-cache-dir --pre py-tgcalls

# Set environment variable
ENV IS_HEROKU=true

# Run the bot
CMD ["python", "main.py"]
