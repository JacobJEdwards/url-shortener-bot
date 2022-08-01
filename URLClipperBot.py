import logging
import urllib
import redis

import requests
import validators

from telegram import __version__ as TG_VER

# response_API = requests.get('https://cutt.ly')
# print(response_API.status_code)

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
    CallbackQueryHandler
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


r = redis.Redis()


# links to api
def URLShorten(url):
    key = '27c6fb4f18e8f88b30baf342df13ef98d0aae'
    toShorten = urllib.parse.quote(url)
    data = requests.get('http://cutt.ly/api/api.php?key={}&short={}'.format(key, toShorten)).text
    r.sadd(str(userID), data)
    shortURL: str = data.rsplit('"')[15].replace('\\', "")
    return shortURL


# start function
async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user.first_name
    userID = update.effective_user.id
    uses = r.scard(str(userID))
    if uses == 0:
        await update.message.reply_text(f'Hello {user}, welcome to URL Clipper Bot! \nIf you need any help, feel '
                                        f'free to contact me through support!')
    elif uses < 10:
        await update.message.reply_text(f'Welcome back {user}\nYou have {10 - uses} uses remaining!')
    else:
        await update.message.reply_text(f'Welcome back {user}')

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


# help function
async def helpInfo(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Help!')


async def upgrade(update: Update, context: CallbackContext) -> None:
    if r.sismember('premium', update.effective_user.id) == 1:
        await update.message.reply_text('You are premium')
    else:
        r.sadd('premium', update.effective_user.id)


# unknown command function
async def unknownCommand(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Unknown command')


# my urls function
async def myURLs(update: Update, context: CallbackContext) -> None:
    global userID
    userID = update.effective_user.id
    urlData = str(r.smembers(userID)).split(',')
    print(urlData)


async def checkURL(update: Update, context: CallbackContext) -> None:
    # checks text is valid url
    global userID
    userID = update.effective_user.id

    user_message = update.message.text
    if validators.url(user_message):
        await update.message.reply_text('Valid URL')
        shortURL = URLShorten(user_message)
        await update.message.reply_text(shortURL)
    else:
        await update.message.reply_text('Invalid URL')


def main() -> None:
    # creates application and passes the api token
    application = Application.builder().token("5524215935:AAFnV8SarFii_QaPzw7InyqniROsbVmmrPs").build()

    # basic command handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', helpInfo))

    # handles unknown commands
    application.add_handler(MessageHandler(filters.COMMAND, unknownCommand))
    # handles the pre-made keyboard
    application.add_handler(MessageHandler(filters.Regex('Support!'), helpInfo))
    application.add_handler(MessageHandler(filters.Regex('My URLs'), myURLs))
    application.add_handler(MessageHandler(filters.Regex('Premium'), upgrade))

    # message handler - URL check
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, checkURL))
    # filters.ALL means any text can be passed, but ~filters.COMMAND means commands cannot be passed

    # runs the application
    application.run_polling()


if __name__ == '__main__':
    main()
