import logging as log
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from chess_tournament import ChessTournament
from settings import settings
from bot import handle_quick_start, start, handle_message
import asyncio

def main():
    log.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=log.INFO
    )

    log.info('Starting the bot')
    app = ApplicationBuilder().token(settings.token).build()

    # Commands
    app.add_handler(CommandHandler('start', start))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    app.job_queue.run_once(callback=handle_quick_start, when=5, chat_id=settings.group_id)
    # Start polling
    app.run_polling(poll_interval=settings.message_read_delay)

if __name__ == '__main__':
    main()