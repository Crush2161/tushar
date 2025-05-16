import os
import logging
import asyncio
from typing import Optional, Dict, Any
import yt_dlp

from config import Config

logger = logging.getLogger(__name__)

# Configure yt-dlp
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': f'{Config.DOWNLOAD_PATH}%(id)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }]
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

async def extract_info(url: str, download: bool = False) -> Optional[Dict[str, Any]]:
    """
    Extract information from a YouTube URL.
    
    Args:
        url: YouTube URL or search query
        download: Whether to download the audio or just extract info
    
    Returns:
        Dictionary containing song information or None if extraction failed
    """
    try:
        # Run yt-dlp in a separate process to avoid blocking
        loop = asyncio.get_event_loop()
        
        if not url.startswith("http"):
            # If not a URL, treat as a search query
            url = f"ytsearch:{url}"
        
        # Extract info
        info_extraction = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=download)
        )
        
        # For search queries, get the first result
        if 'entries' in info_extraction:
            info = info_extraction['entries'][0]
        else:
            info = info_extraction
            
        # Create a standardized format for song info
        song_info = {
            'id': info['id'],
            'title': info['title'],
            'uploader': info.get('uploader', 'Unknown'),
            'duration': info.get('duration', 0),
            'thumbnail': info.get('thumbnail', None),
            'webpage_url': info.get('webpage_url', None),
            'file_path': f"{Config.DOWNLOAD_PATH}{info['id']}.mp3" if download else None
        }
        
        return song_info
        
    except Exception as e:
        logger.error(f"Error extracting info from YouTube: {e}", exc_info=True)
        return None

async def download_audio(url: str) -> Optional[Dict[str, Any]]:
    """
    Download audio from a YouTube URL.
    
    Args:
        url: YouTube URL or search query
    
    Returns:
        Dictionary containing song information or None if download failed
    """
    try:
        return await extract_info(url, download=True)
    except Exception as e:
        logger.error(f"Error downloading from YouTube: {e}", exc_info=True)
        return None

def cleanup_file(file_path: str) -> bool:
    """
    Remove a downloaded file.
    
    Args:
        file_path: Path to the file to remove
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        logger.error(f"Error cleaning up file {file_path}: {e}", exc_info=True)
        return False
