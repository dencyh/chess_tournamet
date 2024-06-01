import asyncio
from datetime import datetime, timezone
from collections.abc import Sequence
import logging as log
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, Bot
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, filters, MessageHandler
from dynaconf import Dynaconf
from chessdotcom import Client
from settings import settings
import json

from chess_tournament import ChessTournament


Client.request_config["headers"]["User-Agent"] = (
   "Python Chesss Bot"
   "Contact me at dencyh@gmail.com"
)

ct = ChessTournament()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ct.waiting_for_names = True
    ct.confirmed = False
    await context.bot.send_message(chat_id=settings.group_id, text="Please enter usernames from chessdotcom \n\nFor example: makecash,dencyh")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    msg: str = update.message.text

    log.info(f'user_id={update.message.chat.id} in message_type={message_type}, chat_id={update.message.chat_id} sent: "{msg}"')

    if ct.waiting_for_names:
        try:
            response = ct.set_challengers(msg)
            await update.message.reply_text(response)
            if (response.startswith('Challengers are:')):
                asyncio.create_task(start_periodic_update(context))
        except Exception as err:
            log.error(err)
            await update.message.reply_text('Error occured, try /start again. Invalida usernames or something...')

async def handle_quick_start(context: ContextTypes.DEFAULT_TYPE):
    if (not ct.started) and settings.quick_start:
        ct.started = True
        asyncio.create_task(start_periodic_update(context.bot))
        tag = "\n\nKickass begins... @gosssky"
        response = f'{ct.get_score()}'
        await context.bot.send_message(text = response, chat_id=settings.group_id)

async def start_periodic_update(context: ContextTypes.DEFAULT_TYPE) -> None:
    log.info("Running score update")
    while not ct.stopped:
        response = ct.update_score()
        if (response != 'No new games'):
            await context.bot.send_message(text=response, chat_id=settings.group_id)
            log.info(f'Response = {response}')
        await asyncio.sleep(settings.score_update_delay)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.info(f'Update {update} caused the error {context.error}')