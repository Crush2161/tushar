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

# Install Python dependencies with specific versions
RUN pip install --no-cache-dir pyrogram==2.0.106 tgcrypto==1.2.5 yt-dlp==2025.4.30
# Install py-tgcalls separately with --pre flag to get pre-release versions if needed
RUN pip install --no-cache-dir --pre py-tgcalls==0.9.7

# Run the bot
CMD ["python", "main.py"]
