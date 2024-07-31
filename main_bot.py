import os
import django
from django_telegram_bot.settings import DATABASES, INSTALLED_APPS
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_telegram_bot.settings')
django.setup()
from asgiref.sync import sync_to_async
import logging
from telegram import (
    Update, 
    InlineKeyboardButton,
    ReplyKeyboardRemove,
    CallbackQuery,
    KeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Updater,
    ContextTypes,
    CommandHandler, 
    CallbackContext, 
    ApplicationBuilder,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from tg_bot_app.views import MnemonicManager, UserManager
from dotenv import load_dotenv

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

mnemonicManager = MnemonicManager()
userManager = UserManager()

MAIN = range(1)
########################################################################
#                        start (Entry Point)                           #
########################################################################
async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    userInfo = update.message.from_user
    user_name = userInfo['username']
    user_id = userInfo['id']
    first_name = userInfo['first_name']
    last_name = userInfo['last_name']
    real_name = "{} {}".format(first_name, last_name)
    is_bot = userInfo['is_bot']
    if is_bot :
        await update.message.reply_text(f"Bot can't join this channel!") #TODO kick off dangerous user
        return

    await sync_to_async(userManager.init)(user_id, user_name, real_name)
    isLock = await sync_to_async(userManager.get_user_lock)(user_id)
    str_lock_status = "ACCOUNT LOCKED! 🔒"
    if not None and not isLock:
        str_lock_status = "ACCOUNT UNLOCKED! 🔓"
    keyboard = [
        [
            KeyboardButton("⬇️ Deposit"),
            KeyboardButton("💳 Balance"),
            KeyboardButton("⬆️ Withdraw"),
        ],
        [
            KeyboardButton("⚙️ Setting"),
            KeyboardButton("🔁 Trade"),
        ],
        [
            KeyboardButton("👤 Admin"),
        ],
    ]
    # reply_inline_markup = InlineKeyboardMarkup(keyboard)
    reply_keyboard_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        f'Welcome *{real_name}*!\n\n{str_lock_status}\n\nChange status 🫴   ⚙️ Setting',
        # parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=reply_keyboard_markup
    )
    return MAIN
########################################################################
#                              +Deposit                                #
########################################################################
async def _func_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    userInfo = update.message.from_user
    user_name = userInfo['username']
    msg = f"{user_name}'s profile"
    keyboard = [
        [
            InlineKeyboardButton("Cancel", callback_data="Cancel"),
        ]
    ]
    await query.message.edit_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

########################################################################
#                        +Message Handler                              #
########################################################################
async def _handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:    
    text = update.message.text
    userInfo = update.message.from_user
    user_id = userInfo['id']
    match text:
        case '⬇️ Deposit':
            eth_wallet, sol_wallet = await sync_to_async(userManager.get_user_wallet)(user_id)
            await update.message.reply_text(
                f"*ETH :*\n👉 `{eth_wallet}`\n*SOL :*\n👉 `{sol_wallet}`",
                parse_mode=ParseMode.MARKDOWN_V2
            )
        case '💳 Balance':
            eth, sol, profit_eth, profit_sol = await sync_to_async(userManager.get_user_balance)(user_id)
            sEth = str(eth).replace('.', '\.')
            sSol = str(sol).replace('.', '\.')
            sProfit_eth = str(profit_eth).replace('.', '\.')
            sProfit_sol = str(profit_sol).replace('.', '\.')
            await update.message.reply_text(
                f"*💵 Balance :*\n ETH : {sEth}\n SOL : {sSol}\n*💸 Profit :*\n ETH : {sProfit_eth}\n SOL : {sProfit_sol}",
                parse_mode=ParseMode.MARKDOWN_V2
            )

########################################################################
#                                 +End                                 #
########################################################################
async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

########################################################################
#                           Main Function                              #
########################################################################
def main() -> None:
    mnemonicManager.init()
    load_dotenv()
    token = os.getenv('BOT_TOKEN')
    application = ApplicationBuilder().token(token).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN: [CallbackQueryHandler(_func_profile, pattern="Profile"),
                   CallbackQueryHandler(start, pattern="Home"),
                   MessageHandler(filters.TEXT, _handle_message)],            
        },
        fallbacks=[CommandHandler("end", end)],
        allow_reentry=True,
    )
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()