import logging, configparser, traceback
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode

import datetime
import pytz
import os

# Config
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

domain = ""

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.

def error_callback(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


# Auto-kickout
def kickout(update, context):
    try:
        for new_user in update.effective_message.new_chat_members:
            update.effective_chat.kick_member(user_id=new_user.id)
        for new_user in update.effective_message.new_chat_members:
            update.effective_chat.unban_member(user_id=new_user.id)
        update.effective_message.delete()
    except Exception as e:
        logger.error(e)
        logger.debug(traceback.format_exc())

def remove_kickout_msg(update, context):
    try:
        update.effective_message.delete()
    except Exception as e:
        logger.error(e)
        logger.debug(traceback.format_exc())

# birthday
def happyBirthday(update, context):
    timezone = pytz.timezone(config['ENVIRON']['TZ'])
    cur_time = datetime.datetime.now(timezone)
    if cur_time.month == int(config['BIRTHDAY']['month']) and cur_time.day == int(config['BIRTHDAY']['day']):
        update.message.reply_text(config['BIRTHDAY']['reply'], reply_to_message_id=update.effective_message.message_id)
    else:
        update.message.reply_text(config['BIRTHDAY']['wrong_reply'], reply_to_message_id=update.effective_message.message_id)


# context.args: chat_id, text, reply_id(optional)
def send(update, context):
    if authorize(update.message.from_user.id):
        if 2 == len(context.args):
            context.bot.send_message(context.args[0], context.args[1], parse_mode = ParseMode.HTML)
        elif 3 == len(context.args):
            context.bot.send_message(context.args[0], context.args[1], reply_to_message_id = context.args[2], parse_mode = ParseMode.HTML)
        else:
            update.message.reply_text("usage: /send <chat_id> <text> <reply_id>(optional)")

def tryURI(update, context):
    if authorize(update.message.from_user.id):
        uri = context.args[0]
        result = os.popen('curl -o /dev/null -s -w %%{http_code} %s%s/' % (domain, uri), mode='r').readlines()
        update.message.reply_text(result[0], reply_to_message_id=update.effective_message.message_id)

def setDomain(update, context):
    if authorize(update.message.from_user.id):
        domain = context.args[0]
        update.message.reply_text("Domain has been set to be " + domain, reply_to_message_id=update.effective_message.message_id)

def authorize(user_id):
    try:
        return config['AUTHORITY'][str(user_id)]
    except Exception as e:
        return False

def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(config['BOT']['TOKEN'], request_kwargs={'proxy_url': config['PROXY']['proxy_url']}, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    dp.add_error_handler(error_callback)


    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, kickout))
    dp.add_handler(MessageHandler(Filters.status_update.left_chat_member, remove_kickout_msg))

    dp.add_handler(CommandHandler("send", send, pass_args = True))
    dp.add_handler(CommandHandler("try", tryURI, pass_args = True))
    dp.add_handler(CommandHandler("setDomain", setDomain, pass_args = True))

    dp.add_handler(MessageHandler(Filters.regex(config['BIRTHDAY']['command']), happyBirthday))

    # Start the Bot
    updater.start_polling()

    # Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()