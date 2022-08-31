# TO DO
# test on multiple devices

# future:
# link to other bots
# create chat for logging purposes visible to me
# work with databases instead of redis (?)
# make money
# get bitches
# use decode maybe instead of all the replaces

# can maybe use dictionary functions instead of all the replaces


import logging
import urllib

import redis
import requests
from telegram import *
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    CallbackQueryHandler,
    ContextTypes,
    PreCheckoutQueryHandler
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

r = redis.Redis()
PAYMENT_TOKEN = '284685063:TEST:NmYwYmQyN2VlYmMw'
apiKey = ***REMOVED***


# links to api and shortens the url
async def URLShorten(update: Update, context: CallbackContext) -> None:
    userID = update.effective_user.id
    userKey = f'shortener:{userID}'
    numUses = r.zscore('urlShortenerBot', userID)
    numUses = 0 if numUses is None else int(numUses)

    # checks the user can access the bot
    if numUses > 7 and not r.sismember('premium', userID):
        await update.message.reply_text('Sorry you have reached the free trial limit!\n\nPlease upgrade to premium to '
                                        'continue')

        # sends inline message for user to upgrade
        inlineKeyboard = [[InlineKeyboardButton('Upgrade to Premium', callback_data='upgrade')]]
        reply_markup = InlineKeyboardMarkup(inlineKeyboard)

        await update.message.reply_text('Click:', reply_markup=reply_markup)
        return

    # shortens the url
    chatID = update.message.chat_id
    message = await context.bot.send_message(text='_fetching url..._', chat_id=chatID, parse_mode='Markdown')

    toShorten = urllib.parse.quote(update.message.text)

    # calls the api as saves as 'data'
    data = requests.get('http://cutt.ly/api/api.php?key={}&short={}'.format(apiKey,
                                                                            toShorten)).text.replace('"', '').replace(
        '\\', '').replace('}', '').replace('{', '').replace('url:status:7,', '')

    # adds the data to database
    r.sadd(userKey, data)
    # increments uses
    r.zincrby('urlShortenerBot', 1, userID)
    # cuts the shortened url from all the data
    shortURL: str = data.rsplit(',')[2].replace('shortLink:', "")

    await context.bot.edit_message_text(message_id=message["message_id"], chat_id=chatID, text='Here is your '
                                                                                               'shortened URL:')
    await update.message.reply_text(shortURL)


# handles the inline keyboard
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    await query.answer()

    if query.data == 'upgrade':
        await query.edit_message_text(text="Thank you for choosing to upgrade!\nPay below:")
        await upgrade(update, context)

    else:
        await query.edit_message_text(text='Invalid option')


# start function
async def start(update: Update, context: CallbackContext) -> None:
    # gets user info
    userName = update.effective_user.first_name
    userID = update.effective_user.id
    numUses = r.zscore('urlShortenerBot', userID)
    numUses = 0 if numUses is None else int(numUses)

    if numUses == 0:
        await update.message.reply_text(f'Hello {userName}, welcome to URL Clipper Bot.\nIf you need any help, feel '
                                        f'free to contact me through support.\n\nTo use this bot, simply send a URL, '
                                        f'and it will be shortened automatically!')

    if not r.sismember('premium', userID):
        await update.message.reply_text(f'You have {8 - numUses} uses remaining on your free trial.\nOr upgrade to '
                                        f'Premium for unlimited use across a number of different bots!')
        keyboard = [
            [KeyboardButton("My URLs", callback_data="1")],
            [
                KeyboardButton("Premium", callback_data="2"),
                KeyboardButton("Support!", callback_data="3"),
            ],
        ]

    else:
        await update.message.reply_text(f'Welcome back {userName}\n\nYou have already chosen to upgrade to premium.'
                                        f'\nUnlimited use!')
        keyboard = [
            [KeyboardButton("My URLs", callback_data="1")],
            [KeyboardButton("Support!", callback_data="3")],
        ]

    # different keyboards if premium or not - to also be added to premium function
    menu_markup = ReplyKeyboardMarkup(keyboard)
    await update.message.reply_text('Send a URL to get started, or select an option below:', reply_markup=menu_markup)


# help function
async def helpInfo(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Hello,\n\nTo begin, simply send a link / URL, and the shortened version will be '
                                    'sent to you automatically.\n\nView previously shortened URL\'s by clicking the '
                                    '\"My URLs\" button.\n\nOr upgrade to premium for limitless use!\n\nFeel free to '
                                    'contact me @JacobJEdwards')


# upgrade to premium
async def upgrade(update: Update, context: CallbackContext) -> None:
    # checks user is not already premium
    if r.sismember('premium', update.effective_user.id):
        keyboard = [
            [KeyboardButton("My URLs", callback_data="1")],
            [KeyboardButton("Support!", callback_data="3")],
        ]

        menu_markup = ReplyKeyboardMarkup(keyboard)
        await update.message.reply_text('You are premium!', reply_markup=menu_markup)

    # generates and sends an invoice to user
    else:
        chat_id = update.effective_message.chat_id
        title = "Premium Upgrade -Limitless Use!"
        description = 'Get unlimited uses, and full access to a range of bots now, and upcoming bots!\n\nContact ' \
                      '@JacobJEdwards for details '
        payload = 'URL Shortener Bot Premium'
        currency = "USD"
        price = 15
        prices = [LabeledPrice('Upgrade', price * 10)]
        await context.bot.send_invoice(
            chat_id, title, description, payload, PAYMENT_TOKEN, currency, prices
        )


# final check before payment is accepted
async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.pre_checkout_query
    # check the payload, is this from your bot?
    if query.invoice_payload != "URL Shortener Bot Premium":
        # answer False pre_checkout_query
        await query.answer(ok=False, error_message="Something went wrong...")
    else:
        await query.answer(ok=True)


# unknown command function
async def unknownCommand(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Unknown command\n\nPlease use /help for help, or send a URL to shorten!')


# my urls function
async def myURLs(update: Update, context: CallbackContext) -> None:
    # gets user info
    userID = update.effective_user.id
    userKey = f'shortener:{userID}'
    uses = r.scard(userKey)

    if uses == 0:
        await update.message.reply_text('You have not shortened any URLs yet!')
    else:
        # sends a list of their urls to user
        urlData = str(r.smembers(userKey)).split(',')
        await update.message.reply_text('---------')

        for i in range(0, len(urlData), 4):
            shortened = urlData[i + 2].replace('shortLink:', '')
            title = urlData[i + 3].replace("title:", '').replace("'", "").replace('}', '')

            await update.message.reply_text(title)
            await update.message.reply_text(shortened)
            await update.message.reply_text('---------')


# called when payment has been made - adds user to premium key
async def upgradeSuccessful(update: Update, context: CallbackContext) -> None:
    r.sadd('premium', update.effective_user.id)

    keyboard = [
        [KeyboardButton("My URLs", callback_data="1")],
        [KeyboardButton("Support!", callback_data="3")],
    ]
    menu_markup = ReplyKeyboardMarkup(keyboard)
    await update.message.reply_text('Upgrade successful! Welcome to premium.', reply_markup=menu_markup)


# generates the bot and handlers
def main() -> None:
    # creates application and passes the api token
    application = Application.builder().token(***REMOVED***).build()

    # basic command handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', helpInfo))

    # inline keyboard handler
    application.add_handler(CallbackQueryHandler(button))

    # handles the pre-made keyboard
    application.add_handler(MessageHandler(filters.Regex('Support!'), helpInfo))
    application.add_handler(MessageHandler(filters.Regex('My URLs'), myURLs))
    application.add_handler(MessageHandler(filters.Regex('Premium'), upgrade))

    # Pre-checkout handler to final check
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))

    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, upgradeSuccessful))

    # handles urls
    application.add_handler(MessageHandler(filters.ALL &
                                           (filters.Entity(MessageEntity.URL) | filters.Entity(
                                               MessageEntity.TEXT_LINK)),
                                           URLShorten))
    # filters.ALL means any text can be passed, but ~filters.COMMAND means commands cannot be passed

    # handles unknown commands
    application.add_handler(MessageHandler(filters.ALL, unknownCommand))

    # runs the application
    application.run_polling()


# runs the program
if __name__ == '__main__':
    main()
