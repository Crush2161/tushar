import math
import logging
from typing import Dict, List, Union, Any, Optional
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

def format_duration(seconds: int) -> str:
    """Format seconds into MM:SS format."""
    minutes = math.floor(seconds / 60)
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"

def create_player_keyboard() -> InlineKeyboardMarkup:
    """
    Create the player control keyboard.
    
    Returns:
        InlineKeyboardMarkup with player controls
    """
    keyboard = [
        [
            InlineKeyboardButton("⏪ Previous", callback_data="previous"),
            InlineKeyboardButton("⏸ Pause", callback_data="pause"),
            InlineKeyboardButton("⏭ Skip", callback_data="skip"),
        ],
        [
            InlineKeyboardButton("⏹ Stop", callback_data="stop"),
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_queue_keyboard(page: int = 0, has_next: bool = False) -> InlineKeyboardMarkup:
    """
    Create the queue navigation keyboard.
    
    Args:
        page: Current page number
        has_next: Whether there's a next page
    
    Returns:
        InlineKeyboardMarkup with navigation controls
    """
    keyboard = []
    
    # Add navigation buttons if needed
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"queue_page:{page-1}"))
    if has_next:
        nav_buttons.append(InlineKeyboardButton("➡️ Next", callback_data=f"queue_page:{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="queue_back")])
    
    return InlineKeyboardMarkup(keyboard)

def get_queue_text(queue: List[Dict[str, Any]], current: Optional[Dict[str, Any]], page: int = 0, 
                   items_per_page: int = 5) -> str:
    """
    Format the queue as text.
    
    Args:
        queue: List of songs in queue
        current: Currently playing song
        page: Page number to display
        items_per_page: Number of items per page
    
    Returns:
        Formatted queue text
    """
    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(queue))
    
    text = "🎵 **Music Queue**\n\n"
    
    # Add currently playing song
    if current:
        text += f"**Now Playing:**\n"
        text += f"🎧 **{current['title']}**\n"
        text += f"⏱ Duration: {format_duration(current['duration'])}\n\n"
    else:
        text += "**Not playing anything currently**\n\n"
    
    # Add queue items
    if queue:
        text += f"**Queue:** {len(queue)} song(s)\n"
        for i, song in enumerate(queue[start_idx:end_idx], start=start_idx + 1):
            text += f"{i}. {song['title']} ({format_duration(song['duration'])})\n"
    else:
        text += "**Queue is empty**\n"
    
    # Show page info if necessary
    if len(queue) > items_per_page:
        total_pages = math.ceil(len(queue) / items_per_page)
        text += f"\nPage {page + 1}/{total_pages}"
    
    return text

def get_now_playing_text(song: Dict[str, Any]) -> str:
    """
    Format the currently playing song info as text.
    
    Args:
        song: Song information
    
    Returns:
        Formatted now playing text
    """
    text = "🎵 **Now Playing**\n\n"
    text += f"🎧 **{song['title']}**\n"
    text += f"👤 Uploader: {song['uploader']}\n"
    text += f"⏱ Duration: {format_duration(song['duration'])}\n"
    if song.get('webpage_url'):
        text += f"🔗 [Link to Video]({song['webpage_url']})\n"
    
    return text
