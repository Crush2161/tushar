import logging
import os
import asyncio
from typing import Dict, Any
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import BadRequest, Forbidden, UserNotParticipant
from pytgcalls.exceptions import NoActiveGroupCall
from pytgcalls.types.input_stream import InputAudioStream
from pytgcalls.types import Update
from pytgcalls.types.stream import StreamAudioEnded

from config import Config
from utils.youtube import download_audio, cleanup_file
from utils.helpers import create_player_keyboard, get_now_playing_text, get_queue_text

logger = logging.getLogger(__name__)

async def ensure_assistant_in_chat(bot, chat_id):
    """
    Ensure that the assistant user is in the chat.
    
    Args:
        bot: The MusicBot instance
        chat_id: Chat ID to check
        
    Returns:
        True if assistant is in chat or joined successfully, False otherwise
    """
    if not bot.assistant:
        return False
        
    try:
        # Check if assistant is already in the chat
        await bot.assistant.get_chat_member(chat_id, bot.assistant_id)
        return True
    except UserNotParticipant:
        # Assistant is not in the chat, inform user to add it
        chat = await bot.bot.get_chat(chat_id)
        chat_title = chat.title
        
        await bot.bot.send_message(
            chat_id,
            f"❗ My assistant account (@{bot.assistant_name}) needs to be in this chat to play music.\n\n"
            f"Please add @{bot.assistant_name} to the group '{chat_title}' and try again."
        )
        return False
    except Exception as e:
        logger.error(f"Error checking assistant in chat: {e}", exc_info=True)
        return False

async def play_audio(bot, chat_id, audio_info):
    """
    Play audio in a voice chat.
    
    Args:
        bot: The MusicBot instance
        chat_id: Chat ID to play in
        audio_info: Audio information dictionary
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if not audio_info or not audio_info.get('file_path'):
            return False
        
        if not os.path.exists(audio_info['file_path']):
            return False
            
        # Check if assistant is in the chat
        if not await ensure_assistant_in_chat(bot, chat_id):
            return False
        
        # Create InputAudioStream
        audio_stream = InputAudioStream(
            audio_info['file_path'],
        )
        
        # Join and play
        await bot.call_py.join_group_call(
            chat_id,
            audio_stream,
            stream_type=0  # For audio streams
        )
        
        # Update active chat info
        bot.active_chats[chat_id]["is_playing"] = True
        bot.active_chats[chat_id]["current"] = audio_info
        
        return True
    except NoActiveGroupCall:
        await bot.bot.send_message(
            chat_id,
            "❌ No active voice chat found. Please start a voice chat first!"
        )
        return False
    except Exception as e:
        logger.error(f"Error playing audio: {e}", exc_info=True)
        await bot.bot.send_message(
            chat_id,
            f"❌ Error playing audio: {str(e)}"
        )
        return False

async def process_next_song(bot, chat_id):
    """
    Process the next song in the queue.
    
    Args:
        bot: The MusicBot instance
        chat_id: Chat ID to play in
    """
    try:
        # Get chat info
        chat_info = bot.active_chats.get(chat_id, {
            "queue": [],
            "current": None,
            "is_playing": False
        })
        
        # If queue is empty, reset
        if not chat_info["queue"]:
            chat_info["is_playing"] = False
            chat_info["current"] = None
            bot.active_chats[chat_id] = chat_info
            
            # Leave the voice chat
            await bot.call_py.leave_group_call(chat_id)
            await bot.bot.send_message(
                chat_id,
                "✅ Queue finished. Left the voice chat."
            )
            return
        
        # Get next song from queue
        next_song = chat_info["queue"].pop(0)
        bot.active_chats[chat_id] = chat_info
        
        # Download if not already downloaded
        if not next_song.get('file_path') or not os.path.exists(next_song.get('file_path')):
            await bot.bot.send_message(
                chat_id,
                f"🔄 Downloading: {next_song['title']}"
            )
            next_song = await download_audio(next_song['webpage_url'])
            
            if not next_song:
                await bot.bot.send_message(
                    chat_id,
                    "❌ Failed to download the song. Skipping..."
                )
                # Process next song
                await process_next_song(bot, chat_id)
                return
        
        # Play the song
        success = await play_audio(bot, chat_id, next_song)
        
        if success:
            # Send now playing message
            await bot.bot.send_message(
                chat_id,
                get_now_playing_text(next_song),
                reply_markup=create_player_keyboard(),
                disable_web_page_preview=True
            )
            
            # Clean up previous file if exists
            if chat_info["current"] and chat_info["current"].get("file_path"):
                cleanup_file(chat_info["current"]["file_path"])
        else:
            # Failed to play, try next song
            await process_next_song(bot, chat_id)
            
    except Exception as e:
        logger.error(f"Error processing next song: {e}", exc_info=True)
        try:
            await bot.bot.send_message(
                chat_id,
                f"❌ Error processing next song: {str(e)}"
            )
        except:
            pass

def register_command_handlers(bot):
    """Register command handlers to the Pyrogram client"""
    
    # Stream audio ended handler
    @bot.call_py.on_stream_end()
    async def on_stream_end(_, update: Update):
        if isinstance(update, StreamAudioEnded):
            chat_id = update.chat_id
            # Play next song
            await process_next_song(bot, chat_id)
    
    @bot.bot.on_message(filters.command("start", prefixes=Config.PREFIX) & filters.group)
    async def start_command(_, message: Message):
        """Handler for the start command"""
        await message.reply_text(
            "👋 **Hello! I'm a Music Bot for Telegram voice chats.**\n\n"
            f"Use `{Config.PREFIX}help` to see available commands."
        )
    
    @bot.bot.on_message(filters.command("help", prefixes=Config.PREFIX) & filters.group)
    async def help_command(_, message: Message):
        """Handler for the help command"""
        help_text = (
            "📋 **Available Commands:**\n\n"
            f"`{Config.PREFIX}play [song name/YouTube URL]` - Play a song in voice chat\n"
            f"`{Config.PREFIX}pause` - Pause the current song\n"
            f"`{Config.PREFIX}resume` - Resume the paused song\n"
            f"`{Config.PREFIX}skip` - Skip to the next song\n"
            f"`{Config.PREFIX}stop` - Stop playing and clear queue\n"
            f"`{Config.PREFIX}queue` - Show the current song queue\n"
            f"`{Config.PREFIX}now` - Show currently playing song\n"
            f"`{Config.PREFIX}help` - Show this help message\n"
        )
        
        # Add info about assistant
        if bot.assistant_name:
            help_text += f"\n**Note**: Make sure to add my assistant (@{bot.assistant_name}) to the group to enable voice chat features."
            
        await message.reply_text(help_text)
    
    @bot.bot.on_message(filters.command("play", prefixes=Config.PREFIX) & filters.group)
    async def play_command(_, message: Message):
        """Handler for the play command"""
        chat_id = message.chat.id
        
        # Check if assistant is configured
        if not bot.assistant:
            await message.reply_text(
                "❌ Voice chat functionality is not available because no assistant account is configured.\n\n"
                "Please ask the bot owner to configure an assistant account."
            )
            return
            
        # Initialize chat info if not exists
        if chat_id not in bot.active_chats:
            bot.active_chats[chat_id] = {
                "queue": [],
                "current": None,
                "is_playing": False
            }
        
        # Check if query is provided
        if len(message.command) < 2:
            await message.reply_text(
                f"❌ Please provide a song name or YouTube URL.\n"
                f"Example: `{Config.PREFIX}play despacito`"
            )
            return
            
        # Check if assistant is in the chat
        if not await ensure_assistant_in_chat(bot, chat_id):
            return
        
        # Get query
        query = message.text.split(None, 1)[1]
        
        # Send processing message
        status_message = await message.reply_text("🔍 Searching...")
        
        try:
            # Download and extract info
            song_info = await download_audio(query)
            
            if not song_info:
                await status_message.edit(
                    "❌ Failed to download the song. Please try another one."
                )
                return
            
            # Check if currently playing
            if bot.active_chats[chat_id]["is_playing"]:
                # Add to queue
                if len(bot.active_chats[chat_id]["queue"]) >= Config.MAX_PLAYLIST_SIZE:
                    await status_message.edit(
                        f"❌ Maximum queue size ({Config.MAX_PLAYLIST_SIZE}) reached."
                    )
                    # Clean up downloaded file if not used
                    cleanup_file(song_info['file_path'])
                    return
                
                # Add to queue
                bot.active_chats[chat_id]["queue"].append(song_info)
                
                # Update status message
                queue_position = len(bot.active_chats[chat_id]["queue"])
                await status_message.edit(
                    f"✅ **{song_info['title']}** added to queue at position {queue_position}."
                )
            else:
                # Play immediately
                await status_message.edit(
                    f"🔄 Processing **{song_info['title']}**..."
                )
                
                # Play the song
                success = await play_audio(bot, chat_id, song_info)
                
                if success:
                    # Update status message
                    await status_message.edit(
                        get_now_playing_text(song_info),
                        reply_markup=create_player_keyboard(),
                        disable_web_page_preview=True
                    )
                else:
                    await status_message.edit(
                        "❌ Failed to play the song."
                    )
                    # Clean up downloaded file
                    cleanup_file(song_info['file_path'])
        except Exception as e:
            logger.error(f"Error in play command: {e}", exc_info=True)
            await status_message.edit(
                f"❌ Error: {str(e)}"
            )
    
    @bot.bot.on_message(filters.command("pause", prefixes=Config.PREFIX) & filters.group)
    async def pause_command(_, message: Message):
        """Handler for the pause command"""
        chat_id = message.chat.id
        
        if chat_id not in bot.active_chats or not bot.active_chats[chat_id]["is_playing"]:
            await message.reply_text("❌ Nothing is playing to pause.")
            return
        
        try:
            await bot.call_py.pause_stream(chat_id)
            await message.reply_text("⏸ Paused the current song.")
        except Exception as e:
            logger.error(f"Error pausing stream: {e}", exc_info=True)
            await message.reply_text(f"❌ Error: {str(e)}")
    
    @bot.bot.on_message(filters.command("resume", prefixes=Config.PREFIX) & filters.group)
    async def resume_command(_, message: Message):
        """Handler for the resume command"""
        chat_id = message.chat.id
        
        if chat_id not in bot.active_chats or not bot.active_chats[chat_id]["is_playing"]:
            await message.reply_text("❌ Nothing is paused to resume.")
            return
        
        try:
            await bot.call_py.resume_stream(chat_id)
            await message.reply_text("▶️ Resumed the current song.")
        except Exception as e:
            logger.error(f"Error resuming stream: {e}", exc_info=True)
            await message.reply_text(f"❌ Error: {str(e)}")
    
    @bot.bot.on_message(filters.command("skip", prefixes=Config.PREFIX) & filters.group)
    async def skip_command(_, message: Message):
        """Handler for the skip command"""
        chat_id = message.chat.id
        
        if chat_id not in bot.active_chats or not bot.active_chats[chat_id]["is_playing"]:
            await message.reply_text("❌ Nothing is playing to skip.")
            return
        
        # Skip logic - stop current stream, which will trigger stream end handler
        try:
            await bot.call_py.leave_group_call(chat_id)
            await message.reply_text("⏭ Skipped the current song.")
            
            # Process next song
            await process_next_song(bot, chat_id)
            
        except Exception as e:
            logger.error(f"Error skipping song: {e}", exc_info=True)
            await message.reply_text(f"❌ Error: {str(e)}")
    
    @bot.bot.on_message(filters.command("stop", prefixes=Config.PREFIX) & filters.group)
    async def stop_command(_, message: Message):
        """Handler for the stop command"""
        chat_id = message.chat.id
        
        if chat_id not in bot.active_chats or not bot.active_chats[chat_id]["is_playing"]:
            await message.reply_text("❌ Nothing is playing to stop.")
            return
        
        try:
            # Clear queue
            current_song = bot.active_chats[chat_id]["current"]
            bot.active_chats[chat_id] = {
                "queue": [],
                "current": None,
                "is_playing": False
            }
            
            # Stop playing
            await bot.call_py.leave_group_call(chat_id)
            
            # Clean up current song file
            if current_song and current_song.get("file_path"):
                cleanup_file(current_song["file_path"])
            
            # Clean up queued song files
            for song in bot.active_chats[chat_id]["queue"]:
                if song.get("file_path"):
                    cleanup_file(song["file_path"])
            
            await message.reply_text("⏹ Stopped playing and cleared the queue.")
            
        except Exception as e:
            logger.error(f"Error stopping: {e}", exc_info=True)
            await message.reply_text(f"❌ Error: {str(e)}")
    
    @bot.bot.on_message(filters.command("queue", prefixes=Config.PREFIX) & filters.group)
    async def queue_command(_, message: Message):
        """Handler for the queue command"""
        chat_id = message.chat.id
        
        if chat_id not in bot.active_chats:
            await message.reply_text("❌ No active music session found.")
            return
        
        chat_info = bot.active_chats[chat_id]
        queue_text = get_queue_text(
            chat_info["queue"],
            chat_info["current"]
        )
        
        await message.reply_text(queue_text)
    
    @bot.bot.on_message(filters.command("now", prefixes=Config.PREFIX) & filters.group)
    async def now_command(_, message: Message):
        """Handler for the now playing command"""
        chat_id = message.chat.id
        
        if chat_id not in bot.active_chats or not bot.active_chats[chat_id]["current"]:
            await message.reply_text("❌ Nothing is playing right now.")
            return
        
        current_song = bot.active_chats[chat_id]["current"]
        now_playing = get_now_playing_text(current_song)
        
        await message.reply_text(
            now_playing,
            reply_markup=create_player_keyboard(),
            disable_web_page_preview=True
        )
