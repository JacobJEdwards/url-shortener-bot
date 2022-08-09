# TO DO
# redis doesnt work with heroku - use a database ! (learn how to use sql with python)
# Complete my urls function
# Add payment
# test on multiple devices

# future:
# link to other bots
# create chat for logging purposes visible to me
# premium on one bot, premium on every bot (?)
# work with databases instead of redis
# look into hosting if heroku doesn't pan out - eventually hope to host on a raspberry pi
# make money
# get bitches


import logging
import urllib

import redis
import requests
from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )

from telegram import *

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    CallbackQueryHandler,
    ContextTypes,
    PreCheckoutQueryHandler,
    PicklePersistence,
    ShippingQueryHandler
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

r = redis.Redis()

PAYMENT_TOKEN = 'pk_test_51LQZq4K5tAPUABZW9u9rUKSxSpMvuWRGAhByInPoXw97xKOKSdUCEEaJbqz7hE2aFbixiVPLFRbrR1FMnFmUlfMh00MMPtRlat'


# links to api
async def URLShorten(update: Update, context: CallbackContext) -> None:
    if r.scard(str(update.effective_user.id)) < 2 or r.sismember('premium', update.effective_user.id):
        chatID = update.message.chat_id
        messageID = await context.bot.send_message(text='fetching url...', chat_id=chatID)
        key = ***REMOVED***
        toShorten = urllib.parse.quote(update.message.text)
        data = requests.get('http://cutt.ly/api/api.php?key={}&short={}'.format(key, toShorten)).text
        r.sadd(str(update.effective_user.id), data)
        shortURL: str = data.rsplit('"')[15].replace('\\', "")

        await context.bot.edit_message_text(message_id=messageID["message_id"], chat_id=chatID, text='Here is your '
                                                                                                     'shortened URL:')
        await update.message.reply_text(shortURL)
        # to finish
    else:
        await update.message.reply_text('Sorry you have reached the free trial limit!\nPlease upgrade to premium to '
                                        'continue')
        inlineKeyboard = [[InlineKeyboardButton('Upgrade to Premium', callback_data='1')]]
        reply_markup = InlineKeyboardMarkup(inlineKeyboard)

        await update.message.reply_text('Click:', reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()

    await query.edit_message_text(text='Premium')


# start function
async def start(update: Update, context: CallbackContext) -> None:
    userName = update.effective_user.first_name
    userID = update.effective_user.id

    try:
        numUses = r.scard(str(userID))
    except:
        numUses = 0

    if numUses == 0:
        await update.message.reply_text(f'Hello {userName}, welcome to URL Clipper Bot! \nIf you need any help, feel '
                                        f'free to contact me through support!')
    elif numUses < 6:
        if r.sismember('premium', userID) == 1:
            await update.message.reply_text(f'Welcome back {userName}')
        else:
            await update.message.reply_text(f'Welcome back {userName}\nYou have {5 - numUses} uses remaining!')
    else:
        await update.message.reply_text(f'Welcome back {userName}')

    if r.sismember('premium', update.effective_user.id):
        keyboard = [
            [KeyboardButton("My URLs", callback_data="1")],
            [KeyboardButton("Support!", callback_data="3")],
        ]
    else:
        keyboard = [
            [KeyboardButton("My URLs", callback_data="1")],
            [
                KeyboardButton("Premium", callback_data="2"),
                KeyboardButton("Support!", callback_data="3"),
            ],
        ]

    menu_markup = ReplyKeyboardMarkup(keyboard)
    await update.message.reply_text('Please select an option: ', reply_markup=menu_markup)


# async def button(update: Update, context: CallbackContext) -> None:
#     query = update.callback_query
#
#     await query.answer()
#     await query.edit_message_text(text=f"Selected option: {query.data}")


# help function - to expand
async def helpInfo(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Help!')


# upgrade to premium - to include payment
async def upgrade(update: Update, context: CallbackContext) -> None:
    if r.sismember('premium', update.effective_user.id):
        await update.message.reply_text('You are premium')
    else:
        r.sadd('premium', update.effective_user.id)


# unknown command function
async def unknownCommand(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Unknown command')


# my urls function - to complete
async def myURLs(update: Update, context: CallbackContext) -> None:
    uses = r.scard(update.effective_user.id)
    if uses == 0:
        await update.message.reply_text('You have not shortened any URLs yet!')
    else:
        urlData = str(r.smembers(update.effective_user.id)).split(',')
        print(urlData)


# async def getUserInfo(update: Update, context: CallbackContext) -> None:
#     global userID
#     global userName
#     global premium
#     global numUses
#
#     userID = update.effective_user.id
#     userName = update.effective_user.first_name
#
#     if r.sismember('premium', userID) == 1:
#         premium = True
#     else:
#         premium = False
#
#     try:
#         numUses = r.scard(str(userID))
#     except:
#         numUses = 0


def main() -> None:
    # creates application and passes the api token
    application = Application.builder().token("5524215935:AAFnV8SarFii_QaPzw7InyqniROsbVmmrPs").build()

    # basic command handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', helpInfo))

    application.add_handler(CallbackQueryHandler(button))

    # handles the pre-made keyboard
    application.add_handler(MessageHandler(filters.Regex('Support!'), helpInfo))
    application.add_handler(MessageHandler(filters.Regex('My URLs'), myURLs))
    application.add_handler(MessageHandler(filters.Regex('Premium'), upgrade))

    # message handler - URL check
    application.add_handler(MessageHandler(filters.ALL &
                                           (filters.Entity(MessageEntity.URL) | filters.Entity(
                                               MessageEntity.TEXT_LINK)),
                                           URLShorten))
    # filters.ALL means any text can be passed, but ~filters.COMMAND means commands cannot be passed

    # handles unknown commands
    application.add_handler(MessageHandler(filters.ALL, unknownCommand))

    # runs the application
    application.run_polling()


if __name__ == '__main__':
    main()
