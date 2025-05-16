import logging
from pyrogram import filters
from pyrogram.types import CallbackQuery
# Use absolute imports for better compatibility with Heroku
from utils.helpers import create_player_keyboard, get_now_playing_text, get_queue_text, create_queue_keyboard

logger = logging.getLogger(__name__)

def register_callback_handlers(bot):
    """Register callback query handlers to the Pyrogram client"""
    
    @bot.bot.on_callback_query(filters.regex(r"^(pause|resume|skip|stop|refresh)$"))
    async def handle_player_callbacks(_, callback_query: CallbackQuery):
        """Handler for player control callbacks"""
        chat_id = callback_query.message.chat.id
        data = callback_query.data
        
        # Check if there's an active session
        if chat_id not in bot.active_chats or not bot.active_chats[chat_id]["current"]:
            await callback_query.answer("No active music session!", show_alert=True)
            return
        
        try:
            # Handle different player controls
            if data == "pause":
                await bot.call_py.pause_stream(chat_id)
                await callback_query.answer("Paused the music")
                
                # Update keyboard to show resume button instead
                keyboard = create_player_keyboard()
                keyboard.inline_keyboard[0][1].text = "▶️ Resume"
                keyboard.inline_keyboard[0][1].callback_data = "resume"
                await callback_query.message.edit_reply_markup(keyboard)
                
            elif data == "resume":
                await bot.call_py.resume_stream(chat_id)
                await callback_query.answer("Resumed the music")
                
                # Update keyboard to show pause button instead
                keyboard = create_player_keyboard()
                await callback_query.message.edit_reply_markup(keyboard)
                
            elif data == "skip":
                # Skip logic - stop current stream, which will trigger stream end handler
                await bot.call_py.leave_group_call(chat_id)
                await callback_query.answer("Skipped to the next song")
                
                # Process next song - imported function
                from handlers.commands import process_next_song
                await process_next_song(bot, chat_id)
                
            elif data == "stop":
                # Clear queue
                current_song = bot.active_chats[chat_id]["current"]
                
                # Clean up current song file
                if current_song and current_song.get("file_path"):
                    from utils.youtube import cleanup_file
                    cleanup_file(current_song["file_path"])
                
                # Clean up queued song files
                for song in bot.active_chats[chat_id]["queue"]:
                    if song.get("file_path"):
                        from utils.youtube import cleanup_file
                        cleanup_file(song["file_path"])
                
                # Reset chat info
                bot.active_chats[chat_id] = {
                    "queue": [],
                    "current": None,
                    "is_playing": False
                }
                
                # Stop playing
                await bot.call_py.leave_group_call(chat_id)
                await callback_query.answer("Stopped the music")
                
                # Update message
                await callback_query.message.edit_text(
                    "⏹ Music playback stopped and queue cleared.",
                    reply_markup=None
                )
                
            elif data == "refresh":
                # Just refresh the player display
                current_song = bot.active_chats[chat_id]["current"]
                now_playing = get_now_playing_text(current_song)
                
                await callback_query.message.edit_text(
                    now_playing,
                    reply_markup=create_player_keyboard(),
                    disable_web_page_preview=True
                )
                await callback_query.answer("Refreshed player information")
                
        except Exception as e:
            logger.error(f"Error in player callback: {e}", exc_info=True)
            await callback_query.answer(f"Error: {str(e)}", show_alert=True)
    
    @bot.bot.on_callback_query(filters.regex(r"^queue_page:(\d+)$"))
    async def handle_queue_page_callback(_, callback_query: CallbackQuery):
        """Handler for queue pagination callbacks"""
        chat_id = callback_query.message.chat.id
        
        # Extract page number
        page = int(callback_query.data.split(':')[1])
        
        # Check if there's an active session
        if chat_id not in bot.active_chats:
            await callback_query.answer("No active music session!", show_alert=True)
            return
        
        try:
            chat_info = bot.active_chats[chat_id]
            items_per_page = 5
            has_next = len(chat_info["queue"]) > (page + 1) * items_per_page
            
            # Get queue text for the specified page
            queue_text = get_queue_text(
                chat_info["queue"],
                chat_info["current"],
                page=page,
                items_per_page=items_per_page
            )
            
            # Update message with new page
            await callback_query.message.edit_text(
                queue_text,
                reply_markup=create_queue_keyboard(page=page, has_next=has_next),
                disable_web_page_preview=True
            )
            
            await callback_query.answer(f"Page {page + 1}")
            
        except Exception as e:
            logger.error(f"Error in queue pagination: {e}", exc_info=True)
            await callback_query.answer(f"Error: {str(e)}", show_alert=True)
    
    @bot.bot.on_callback_query(filters.regex(r"^queue_back$"))
    async def handle_queue_back_callback(_, callback_query: CallbackQuery):
        """Handler for queue back button callback"""
        chat_id = callback_query.message.chat.id
        
        # Check if there's an active session
        if chat_id not in bot.active_chats or not bot.active_chats[chat_id]["current"]:
            await callback_query.answer("No active music session!", show_alert=True)
            return
        
        try:
            current_song = bot.active_chats[chat_id]["current"]
            now_playing = get_now_playing_text(current_song)
            
            # Update message with player view
            await callback_query.message.edit_text(
                now_playing,
                reply_markup=create_player_keyboard(),
                disable_web_page_preview=True
            )
            
            await callback_query.answer("Back to player")
            
        except Exception as e:
            logger.error(f"Error in queue back callback: {e}", exc_info=True)
            await callback_query.answer(f"Error: {str(e)}", show_alert=True)

    @bot.bot.on_callback_query(filters.regex(r"^previous$"))
    async def handle_previous_callback(_, callback_query: CallbackQuery):
        """Handler for previous song callback - not implemented yet"""
        await callback_query.answer("Previous song function not implemented yet", show_alert=True)
