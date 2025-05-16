import os
import logging
import asyncio
from pyrogram.client import Client
from pyrogram.sync import idle
from pytgcalls import PyTgCalls
from pyrogram.errors import ApiIdInvalid, ApiIdPublishedFlood, AccessTokenInvalid, AuthKeyUnregistered, PhoneCodeInvalid
from pyrogram.enums import ParseMode

from config import Config
from handlers import register_handlers

logger = logging.getLogger(__name__)

class MusicBot:
    def __init__(self):
        """Initialize the Music Bot with Pyrogram and PyTgCalls clients"""
        # Initialize Bot client
        self.bot = Client(
            "MusicBot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Initialize Assistant client (for voice chats)
        self.assistant = None
        if Config.SESSION_STRING:
            self.assistant = Client(
                "MusicAssistant",
                api_id=Config.API_ID,
                api_hash=Config.API_HASH,
                session_string=Config.SESSION_STRING
            )
        elif Config.PHONE_NUMBER:
            self.assistant = Client(
                "MusicAssistant",
                api_id=Config.API_ID,
                api_hash=Config.API_HASH,
                phone_number=Config.PHONE_NUMBER
            )
        
        # Initialize PyTgCalls client on the assistant
        self.call_py = PyTgCalls(self.assistant)
        
        # Dictionary to store active voice chats and queues
        # Structure: {chat_id: {"queue": [], "current": None, "is_playing": False}}
        self.active_chats = {}
        
        # Store assistant info
        self.assistant_id = None
        self.assistant_name = None
    
    async def run(self):
        """Start the bot and PyTgCalls client"""
        try:
            # Start the Bot client
            await self.bot.start()
            logger.info("Bot client started")
            
            # Start the Assistant client
            if self.assistant:
                await self.assistant.start()
                
                # Get assistant info
                me = await self.assistant.get_me()
                self.assistant_id = me.id
                self.assistant_name = me.first_name
                logger.info(f"Assistant started - ID: {self.assistant_id}, Name: {self.assistant_name}")
                
                # Start the PyTgCalls client
                await self.call_py.start()
                logger.info("PyTgCalls client started")
            else:
                logger.error("No assistant account configured - voice chat functionality will not work!")
            
            # Register command handlers
            register_handlers(self)
            logger.info("Command handlers registered")
            
            # Keep the bot running
            await idle()
            
        except (ApiIdInvalid, ApiIdPublishedFlood):
            logger.error("Invalid API ID or API ID is published/flood")
            raise
        except AccessTokenInvalid:
            logger.error("Invalid Bot Token")
            raise
        except AuthKeyUnregistered:
            logger.error("Authentication key is unregistered (invalid session string)")
            raise
        except PhoneCodeInvalid:
            logger.error("Invalid phone code provided during authentication")
            raise
        except Exception as e:
            logger.error(f"Error starting bot: {e}", exc_info=True)
            raise
        finally:
            # Ensure proper shutdown
            await self.shutdown()
    
    async def shutdown(self):
        """Properly shut down the bot and PyTgCalls client"""
        try:
            if hasattr(self, 'call_py') and self.call_py.is_connected:
                await self.call_py.stop()
            
            if hasattr(self, 'assistant') and self.assistant.is_connected:
                await self.assistant.stop()
                
            if hasattr(self, 'bot') and self.bot.is_connected:
                await self.bot.stop()
                
            logger.info("Bot shut down gracefully")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)
