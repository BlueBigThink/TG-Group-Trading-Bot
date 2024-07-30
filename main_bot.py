import os
import django
from django_telegram_bot.settings import DATABASES, INSTALLED_APPS
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_telegram_bot.settings')
django.setup()
from asgiref.sync import sync_to_async
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, ApplicationBuilder

from tg_bot_app.models import UserModel
from tg_bot_app.views import MnemonicManager, UserManager
from dotenv import load_dotenv

mnemonicManager = MnemonicManager()

async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user_name=update.effective_user.username
    first_name=update.effective_user.first_name,
    last_name=update.effective_user.last_name,
    real_name=f"{first_name} {last_name}"

    await update.message.reply_text(f'Welcome {user_data.first_name}!')

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