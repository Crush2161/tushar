import asyncio
import logging
from bot import MusicBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Initialize and run the music bot
    music_bot = MusicBot()
    
    try:
        logger.info("Starting Music Bot...")
        asyncio.run(music_bot.run())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error occurred: {e}", exc_info=True)
