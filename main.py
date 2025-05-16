import os
import asyncio
import logging
from bot import MusicBot

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

async def main():
    retry_delay = 1
    max_retries = 5

    for attempt in range(max_retries):
        try:
            music_bot = MusicBot()
            await music_bot.run()
            break
        except Exception as e:
            if "FLOOD_WAIT" in str(e):
                wait_time = int(str(e).split()[8])  # Extract wait time from error
                logging.warning(f"Hit rate limit, waiting {wait_time} seconds")
                await asyncio.sleep(wait_time)
            else:
                logging.error(f"Error occurred: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise

if __name__ == "__main__":
    asyncio.run(main())
