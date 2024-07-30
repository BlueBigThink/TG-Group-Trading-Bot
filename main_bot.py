import os
import django
from django_telegram_bot.settings import DATABASES, INSTALLED_APPS
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_telegram_bot.settings')
django.setup()
from asgiref.sync import sync_to_async
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, ApplicationBuilder

from tg_bot_app.views import MnemonicManager, UserManager
from dotenv import load_dotenv

mnemonicManager = MnemonicManager()
userManager = UserManager()

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

    await update.message.reply_text(f'Welcome {user_name}!')

    # try:
    #     user_data = await sync_to_async(User.objects.get)(user_id=user_id)
    #     await update.message.reply_text(f'Welcome back {user_data.first_name}!')
    # except User.DoesNotExist:
    #     new_user = User(
    #         user_id=user_id,
    #         first_name=update.effective_user.first_name,
    #         last_name=update.effective_user.last_name,
    #         username=update.effective_user.username
    #     )
    #     await sync_to_async(new_user.save)()
    #     logging.info(f'New user {new_user.first_name} has been added to the database')
    #     await update.message.reply_text('Welcome to django-telegram-bot!')

def main() -> None:
    mnemonicManager.init()
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger = logging.getLogger(__name__)
    load_dotenv()
    token = os.getenv('BOT_TOKEN')
    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler('start', start))
    application.run_polling()

if __name__ == '__main__':
    main()