from .commands import register_command_handlers
from .callbacks import register_callback_handlers

def register_handlers(bot):
    """Register all handlers to the bot"""
    register_command_handlers(bot)
    register_callback_handlers(bot)
