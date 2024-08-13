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

from tg_bot_app.views import MnemonicManager, UserManager, TimeScheduler
from tg_bot_app.utils import ( 
    is_valid_ethereum_address,
    is_valid_ethereum_token_address,
    is_valid_solana_address,
    is_valid_solana_token_address,
    get_name_marketcap_liqudity_price,
    get_token_amount_out_from_eth,
    get_eth_amount_out_from_token
)
from dotenv import load_dotenv
# import time
import threading
import asyncio

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def format_float(value, decimals):
    formatted_value = f"{value:.{decimals}f}".rstrip('0').rstrip('.')
    return formatted_value
def format_string(s):
    return s[:20].ljust(20)
mnemonicManager = MnemonicManager()
userManager = UserManager()

MAIN, INVEST, WITHDRAW, TRADE = range(4)
g_UserStatus = {}

# async def callback_auto(context):
#     await sync_to_async(mnemonicManager.update_index_key)(99)
#     print('callback_auto')
# def start_auto(update, context):
#     chat_id = update.message.chat_id
#     context.job_queue.run_repeating(callback_auto, 10)
#     #context.job_queue.run_once(callback_auto, 3600, context=chat_id)
#     #context.job_queue.run_daily(callback_auto, time=datetime.time(hour=9, minute=22), days=(0, 1, 2, 3, 4, 5, 6), context=chat_id)
# def stop_notify(update, context):
#     chat_id = update.message.chat_id
#     context.bot.send_message(chat_id=chat_id, text='Stopping aut!')
#     job = context.job_queue.get_jobs_by_name(str(chat_id))
#     job[0].schedule_removal()
########################################################################
#                        start (Entry Point)                           #
########################################################################
async def start(update: Update, context: CallbackContext) -> None:
    # chat_type = update.message.chat.type
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
    global g_UserStatus
    g_UserStatus[user_id] = {
        "withdraw_request": False,
        "withdraw_token": "",
        "withdraw_amount": 0,
        "invest_request": False,
        "invest_token": "",
        "token_address_request" : False,
        "token_chain_type" : "",
        "token_info" : '',
        "token_input" : False,
        "token_input_type" : '',
        "token_input_addr" : '',
        "slippage_request" : False,      
        "slippage_meta" : '',      
    }

    str_lock_status = "ACCOUNT LOCKED! 🔒"
    if not None and not isLock:
        str_lock_status = "ACCOUNT OPENED! 🔓"
    await update.message.reply_text(
        f'🏠 Home\n\nWelcome {real_name}!\n\n{str_lock_status}',
        parse_mode=ParseMode.HTML,
    )
    return MAIN
########################################################################
#                                 +Lock                                #
########################################################################
async def user_lock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    userInfo = update.message.from_user
    user_id = userInfo['id']
    first_name = userInfo['first_name']
    last_name = userInfo['last_name']
    real_name = "{} {}".format(first_name, last_name)
    user_id = userInfo['id']

    await sync_to_async(userManager.user_lock)(user_id)

    str_message = f"*\-\-\-\-\-\-\-\- {real_name} \-\-\-\-\-\-\-\-\-*\n⚙️ Setting\nACCOUNT LOCK\! 🔒"
    await update.message.reply_text(
        str_message,
        parse_mode=ParseMode.MARKDOWN_V2
    )
########################################################################
#                                 +Unlock                              #
########################################################################
async def user_unlock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    userInfo = update.message.from_user
    user_id = userInfo['id']
    first_name = userInfo['first_name']
    last_name = userInfo['last_name']
    real_name = "{} {}".format(first_name, last_name)
    user_id = userInfo['id']

    await sync_to_async(userManager.user_unlock)(user_id)

    str_message = f"*\-\-\-\-\-\-\-\- {real_name} \-\-\-\-\-\-\-\-\-*\n⚙️ Setting\nACCOUNT OPEN\! 🔒"
    await update.message.reply_text(
        str_message,
        parse_mode=ParseMode.MARKDOWN_V2
      )
########################################################################
#                                 +Deposit                             #
########################################################################
async def user_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    userInfo = update.message.from_user
    user_id = userInfo['id']
    first_name = userInfo['first_name']
    last_name = userInfo['last_name']
    real_name = "{} {}".format(first_name, last_name)
    user_id = userInfo['id']

    eth_wallet, sol_wallet = await sync_to_async(userManager.get_user_wallet)(user_id)
    await update.message.reply_text(
        f"*\-\-\-\-\-\-\-\- {real_name} \-\-\-\-\-\-\-\-\-*\n⬇️ Deposit\n*ETH :*\n👉 `{eth_wallet}`\n*SOL :*\n👉 `{sol_wallet}`",
        parse_mode=ParseMode.MARKDOWN_V2
    )
########################################################################
#                              +Balance                                #
########################################################################
async def user_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    userInfo = update.message.from_user
    user_id = userInfo['id']
    first_name = userInfo['first_name']
    last_name = userInfo['last_name']
    real_name = "{} {}".format(first_name, last_name)
    user_id = userInfo['id']

    eth, sol, profit_eth, profit_sol = await sync_to_async(userManager.get_user_balance)(user_id)
    await update.message.reply_text(
        f"<b>-------- {real_name} ---------\n💳 Balance\n"+
        f"Token      Deposit      Profit\n"+
        f"---------      ----------      ----------\n"+
        f" ETH          {eth:.3f}          {profit_eth:.3f}\n"+
        f" SOL          {sol:.3f}          {profit_sol:.3f}</b>",
        parse_mode=ParseMode.HTML
    )
########################################################################
#                              +Users                                  #
########################################################################
async def user_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    userInfo = update.message.from_user
    first_name = userInfo['first_name']
    last_name = userInfo['last_name']
    real_name = "{} {}".format(first_name, last_name)

    users = await sync_to_async(userManager.get_all_user_status)()
    str_users = ""
    for user in users:
        str_user = f"{format_string(user['name'])}"
        if user['status']:
            str_user += "      Lock 🔒\n"
        else :
            str_user += "      Open 🔓\n"
        str_users += str_user
    await update.message.reply_text(
        f"<b>-------- {real_name} ---------\n👥 Users\n{str_users}</b>",
        parse_mode=ParseMode.HTML
    )
########################################################################
#                              +Withdraw                               #
########################################################################
async def user_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    userInfo = update.message.from_user
    user_id = userInfo['id']
    first_name = userInfo['first_name']
    last_name = userInfo['last_name']
    real_name = "{} {}".format(first_name, last_name)

    eth, sol, profit_eth, profit_sol = await sync_to_async(userManager.get_user_balance)(user_id)
    keyboard = [
        [
            InlineKeyboardButton("ETH", callback_data="Withdraw:ETH"),
            InlineKeyboardButton("SOL", callback_data="Withdraw:SOL"),
        ]
    ]
    await update.message.reply_text(
        f"<b>-------- {real_name} ---------\n⬆️ Withdraw\n"+
        f"Token      Deposit      Profit\n"+
        f"---------      ----------      ----------\n"+
        f" ETH          {eth:.3f}          {profit_eth:.3f}\n"+
        f" SOL          {sol:.3f}          {profit_sol:.3f}\n"+
        f"👇 Please select token to withdraw</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return WITHDRAW

async def _user_withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    params = query.data.split(":")
    token_type = params[1]
    userInfo = query.from_user
    user_id = userInfo['id']
    first_name = userInfo['first_name']
    last_name = userInfo['last_name']
    real_name = "{} {}".format(first_name, last_name)
    eth, sol, profit_eth, profit_sol = await sync_to_async(userManager.get_user_balance)(user_id)
    global g_UserStatus
    g_UserStatus[user_id]['withdraw_request'] = True
    g_UserStatus[user_id]['withdraw_token'] = token_type

    await query.message.edit_text(
        f"<b>-------- {real_name} ---------\n⬆️ Withdraw\n"+
        f"Token      Deposit      Profit\n"+
        f"---------      ----------      ----------\n"+
        f" ETH          {eth:.3f}          {profit_eth:.3f}\n"+
        f" SOL          {sol:.3f}          {profit_sol:.3f}\n\n"+
        f"Please input {token_type} amount to withdraw</b>",
        parse_mode=ParseMode.HTML,
    )
    return WITHDRAW

async def _withdraw_handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: 
    text = update.message.text
    userInfo = update.message.from_user
    user_id = userInfo['id']
    print("======================",text)
    global g_UserStatus
    if g_UserStatus[user_id]['withdraw_request'] and g_UserStatus[user_id]['withdraw_amount'] == 0:
        amount = 0
        try :
            amount = float(text)
        except Exception as e:
            print(f"-- _withdraw_handle_message : Error : {e} --")
        if amount == 0:
            await update.message.reply_text(
                "❌ Input correct number!",
            )
            return WITHDRAW
        eth, sol, profit_eth, profit_sol = await sync_to_async(userManager.get_user_balance)(user_id)    
        balance = 0
        token_type = g_UserStatus[user_id]['withdraw_token']
        if token_type == 'ETH':
            balance = eth + profit_eth
        elif token_type == 'SOL':
            balance = sol + profit_sol
        if amount > balance :
            await update.message.reply_text(
                f"❌ Input correct number!\n{token_type} : {format_float(balance, 3)}",
            )
            return WITHDRAW
        g_UserStatus[user_id]['withdraw_amount'] = amount
        await update.message.reply_text(
            f"Input withdraw {token_type} address",
        )
        return WITHDRAW
    if g_UserStatus[user_id]['withdraw_request'] and g_UserStatus[user_id]['withdraw_amount'] > 0:
        valid = False
        token_type = g_UserStatus[user_id]['withdraw_token']
        if token_type == 'ETH':
            valid = is_valid_ethereum_address(text)
        elif token_type == 'SOL':
            valid = is_valid_solana_address(text)

        if not valid:
            await update.message.reply_text(
                f"❌ It's not valid {token_type} address\n{text}\nInput correct address",
            )
            return WITHDRAW
        token_amount = g_UserStatus[user_id]['withdraw_amount']
        receiver = text
        first_name = userInfo['first_name']
        last_name = userInfo['last_name']
        real_name = "{} {}".format(first_name, last_name)

        g_UserStatus[user_id]['withdraw_request'] = False
        g_UserStatus[user_id]['withdraw_token'] = ""
        g_UserStatus[user_id]['withdraw_amount'] = 0
        await update.message.reply_text(
            f"<b>Name : {real_name}\nToken : {token_type}\nAmount : {token_amount}\nWallet : {receiver}\nPlease wait...⏰\nThis might take a few mins</b>",
            parse_mode=ParseMode.HTML
        )
        await sync_to_async(userManager.user_withdraw_balance)(user_id, token_type, token_amount, receiver)
        return MAIN
########################################################################
#                               +Invest                                #
########################################################################
async def user_invest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    userInfo = update.message.from_user
    user_id = userInfo['id']
    first_name = userInfo['first_name']
    last_name = userInfo['last_name']
    real_name = "{} {}".format(first_name, last_name)

    eth, sol, profit_eth, profit_sol = await sync_to_async(userManager.get_user_balance)(user_id)
    keyboard = [
        [
            InlineKeyboardButton("ETH", callback_data="Invest:ETH"),
            InlineKeyboardButton("SOL", callback_data="Invest:SOL"),
        ]
    ]
    await update.message.reply_text(
        f"<b>-------- {real_name} ---------\n💵 Invest\n"+
        f"Token      Deposit      Profit\n"+
        f"---------      ----------      ----------\n"+
        f" ETH          {eth:.3f}          {profit_eth:.3f}\n"+
        f" SOL          {sol:.3f}          {profit_sol:.3f}\n"+
        f"👇 Please select token to invest</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return INVEST
async def _user_invest_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    params = query.data.split(":")
    token_type = params[1]
    userInfo = query.from_user
    user_id = userInfo['id']
    first_name = userInfo['first_name']
    last_name = userInfo['last_name']
    real_name = "{} {}".format(first_name, last_name)
    eth, sol, profit_eth, profit_sol = await sync_to_async(userManager.get_user_balance)(user_id)
    global g_UserStatus
    g_UserStatus[user_id]['invest_request'] = True
    g_UserStatus[user_id]['invest_token'] = token_type

    await query.message.edit_text(
        f"<b>-------- {real_name} ---------\n💵 Invest\n"+
        f"Token      Deposit      Profit\n"+
        f"---------      ----------      ----------\n"+
        f" ETH          {eth:.3f}          {profit_eth:.3f}\n"+
        f" SOL          {sol:.3f}          {profit_sol:.3f}\n\n"+
        f"Please input {token_type} amount to invest</b>",
        parse_mode=ParseMode.HTML,
    )
    return INVEST
async def _invest_handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: 
    text = update.message.text
    userInfo = update.message.from_user
    user_id = userInfo['id']
    print("======================",text)
    global g_UserStatus
    if g_UserStatus[user_id]['invest_request']:
        amount = 0
        try :
            amount = float(text)
        except Exception as e:
            print(f"-- _invest_handle_message : Error : {e} --")
        if amount == 0:
            await update.message.reply_text(
                "❌ Input correct number!",
            )
            return INVEST
        _, _, profit_eth, profit_sol = await sync_to_async(userManager.get_user_balance)(user_id)    
        balance = 0
        token_type = g_UserStatus[user_id]['invest_token']
        if token_type == 'ETH':
            balance = profit_eth
        elif token_type == 'SOL':
            balance = profit_sol
        if amount > balance :
            await update.message.reply_text(
                f"❌ Input correct number!\{token_type} : {format_float(balance, 3)}",
            )
            return INVEST

        first_name = userInfo['first_name']
        last_name = userInfo['last_name']
        real_name = "{} {}".format(first_name, last_name)
        await update.message.reply_text(
            f"<b>Hi, {real_name}!\nYou invest {token_type} : {amount}</b>",
            parse_mode=ParseMode.HTML
        )
        await sync_to_async(userManager.user_invest_profit)(user_id, token_type, amount)
        return MAIN
########################################################################
#                               +Trade                                 #
########################################################################
async def user_trade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    userInfo = update.message.from_user
    user_id = userInfo['id']
    first_name = userInfo['first_name']
    last_name = userInfo['last_name']
    real_name = "{} {}".format(first_name, last_name)
    isLock = await sync_to_async(userManager.get_user_lock)(user_id)
    if isLock:
        await update.message.reply_text(
            "⚠️ Your account is Locked! 🔒",
        )
        return MAIN

    keyboard = [
        [
            InlineKeyboardButton("Buy", callback_data="BuyToken"),
            InlineKeyboardButton("Sell", callback_data="SellToken"),
        ]
    ]
    await update.message.reply_text(
        f"<b>-------- {real_name} ---------\n🔁 Trade\n"+
        f"👇 Do you want to buy or sell?</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TRADE
async def _user_buy_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: 
    query = update.callback_query
    userInfo = query.from_user
    user_id = userInfo['id']
    first_name = userInfo['first_name']
    last_name = userInfo['last_name']
    real_name = "{} {}".format(first_name, last_name)

    global g_UserStatus
    g_UserStatus[user_id]['token_address_request'] = True

    await query.message.edit_text(
        f"<b>-------- {real_name} ---------\n🔁 Buy\n"+
        f"Please input token address on ETH or SOL</b>",
        parse_mode=ParseMode.HTML
    )
    return TRADE
async def _select_token_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: 
    query = update.callback_query
    params = query.data.split(":")
    print(params)
    user_id = query.from_user.id
    token_addr = params[2]
    global g_UserStatus
    st_token_info = g_UserStatus[user_id]['token_info']
    user_cnt, total_eth, total_sol = await sync_to_async(userManager.get_trade_able_token)()
    chain_type = params[1]

    match chain_type:
        case 'ETH':
            st_available = f"\nPlease select the correct amount of ETH\n{format_float(total_eth, 4)} ETH of {user_cnt} users is available!"
            keyboard = [
                [
                    InlineKeyboardButton("0.05 ETH",    callback_data=f"TradeBuy:ETH:0.05:{token_addr}"),
                    InlineKeyboardButton("0.1 ETH",     callback_data=f"TradeBuy:ETH:0.10:{token_addr}"),
                    InlineKeyboardButton("0.2 ETH",     callback_data=f"TradeBuy:ETH:0.20:{token_addr}"),
                ],
                [
                    InlineKeyboardButton("0.5 ETH",     callback_data=f"TradeBuy:ETH:0.50:{token_addr}"),
                    InlineKeyboardButton("1 ETH",       callback_data=f"TradeBuy:ETH:1.00:{token_addr}"),
                    InlineKeyboardButton("X ETH",       callback_data=f"TradeBuy:ETH:X:{token_addr}"),
                ]
            ]
        case 'SOL':
            st_available = f"\nPlease select the correct amount of SOL\n{format_float(total_sol, 3)} SOL of {user_cnt} users is available!"
            keyboard = [
                [
                    InlineKeyboardButton("1 SOL",   callback_data=f"TradeBuy:SOL:1:{token_addr}"),
                    InlineKeyboardButton("2 SOL",   callback_data=f"TradeBuy:SOL:2:{token_addr}"),
                    InlineKeyboardButton("4 SOL",   callback_data=f"TradeBuy:SOL:4:{token_addr}"),
                ],
                [
                    InlineKeyboardButton("10 SOL",  callback_data=f"TradeBuy:SOL:10:{token_addr}"),
                    InlineKeyboardButton("20 SOL",  callback_data=f"TradeBuy:SOL:20:{token_addr}"),
                    InlineKeyboardButton("X SOL",   callback_data=f"TradeBuy:SOL:X:{token_addr}"),
                ]
            ]
    await query.message.edit_text(
        st_token_info + st_available,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TRADE
async def _tradeBuy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    params = query.data.split(":")
    user_id = query.from_user.id
    token_type = params[1]
    token_amount = params[2]
    token_addr = params[3]
    user_cnt, total_eth, total_sol = await sync_to_async(userManager.get_trade_able_token)()
    global g_UserStatus
    st_available = ''
    match token_type:
        case 'ETH':
            st_available = f"\n{format_float(total_eth, 4)} ETH of {user_cnt} users is available!"
        case 'SOL':
            st_available = f"\n{format_float(total_sol, 3)} SOL of {user_cnt} users is available!"
    print("************************",params)
    if token_amount == 'X' :
        g_UserStatus[user_id]['token_input'] = True
        g_UserStatus[user_id]['token_input_type'] = token_type
        g_UserStatus[user_id]['token_input_addr'] = token_addr
        await query.message.edit_text(
            f"<b>Please Input the correct {token_type} amount{st_available}</b>",
            parse_mode = ParseMode.HTML
        )
    else :
        if (token_type == 'ETH' and float(token_amount) > total_eth) or (token_type == 'SOL' and float(token_amount) > total_sol): 
            user_initialize(user_id)
            await query.message.edit_text(
                f"You can't trade with {token_amount} {token_type}! Please retry from begin!",
            )
            return MAIN

        g_UserStatus[user_id]['slippage_request'] = True
        g_UserStatus[user_id]['slippage_meta'] = f"{token_type}:{token_addr}:{token_amount}"

        await query.message.edit_text(
            f"<b>Please input slippage.\nDefault : 2%</b>",
            parse_mode = ParseMode.HTML
        )
    return TRADE

async def _trade_handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: 
    text = update.message.text
    userInfo = update.message.from_user
    user_id = userInfo['id']
    print("======================",text)
    global g_UserStatus
    if g_UserStatus[user_id]['token_address_request']:
        token_type = ""

        is_trading = await sync_to_async(userManager.is_trading_token)(text)
        if is_trading:
            await update.message.reply_text(
                f"<b>Someone is already trading this token.\nPlease try other token address.</b>",
                parse_mode=ParseMode.HTML,
            )
            return TRADE

        if is_valid_ethereum_token_address(text):
            token_type = "ETH"
        if is_valid_solana_token_address(text):
            token_type = "SOL"
        
        if token_type == "":
            await update.message.reply_text(
                "❌ Input correct token address!",
            )
            return TRADE
        token_address = text
        user_cnt, total_eth, total_sol = await sync_to_async(userManager.get_trade_able_token)()
        token_info = await sync_to_async(get_name_marketcap_liqudity_price)(token_type, token_address)
        keyboard = [
            [
                InlineKeyboardButton("Buy", callback_data=f"SelectTokenAmount:{token_type}:{token_address}"),
            ]
        ]
        st_token_info = f"<B>⌛️ {token_info['name']} ({token_info['symbol']}) 🔗 {token_info['token_group']}\n{token_info['CA']}\n{token_info['LP']}\n\nLiquidity: {token_info['liquidity']}\n\n🧢 Market Cap | {token_info['market_cap']}\n⚖️ Taxes | {token_info['taxes']}\n\nCurrent slippage: 2%\nIn reserve : {format_float(total_eth, 4)} ETH for {user_cnt} users is available</B>"
        g_UserStatus[user_id]['token_info'] = st_token_info
        g_UserStatus[user_id]['token_address_request'] = False
        await update.message.reply_text(
            st_token_info,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return TRADE
    if g_UserStatus[user_id]['token_input']:
        token_amount = 0
        try :
            token_amount = float(text)
        except Exception as e:
            print(f"-- _trade_handle_message : Error : {e} --")
            await update.message.reply_text(
                f"Input Correct Number!",
            )
            return TRADE
        if token_amount == 0:
            await update.message.reply_text(
                f"Input Correct Number!",
            )
            return TRADE

        token_type = g_UserStatus[user_id]['token_input_type']
        if (token_type == 'ETH' and float(token_amount) > total_eth) or (token_type == 'SOL' and float(token_amount) > total_sol): 
            user_initialize(user_id)
            await update.message.reply_text(
                f"You can't trade with {token_amount} {token_type}! Please retry from begin!",
            )
            return MAIN
        token_addr = g_UserStatus[user_id]['token_input_addr']        
        g_UserStatus[user_id]['slippage_request'] = True
        g_UserStatus[user_id]['slippage_meta'] = f"{token_type}:{token_addr}:{token_amount}"

        await update.message.reply_text(
            f"<b>Please input slippage.\nDefault : 2%</b>",
            parse_mode = ParseMode.HTML
        )
        return TRADE
    if g_UserStatus[user_id]['slippage_request']:
        slippage = 2
        try :
            slippage = (int(text) % 100)
        except Exception as e:
            print(f"-- _trade_handle_message : Error : {e} --")
            await update.message.reply_text(
                f"Input Number from 0 to 100",
            )
            return TRADE
        meta = g_UserStatus[user_id]['slippage_meta']
        token_info = g_UserStatus[user_id]['token_info']
        user_initialize(user_id)
        params = meta.split(':')
        token_type = params[0]
        token_addr = params[1]
        token_amount = params[2]
        str_buy_token = f"{token_info}\n\n\n{token_type} : {token_amount}\nSlippage : {slippage}%\nPlease wait...⏰ This might take a few mins!"
        await update.message.reply_text(
            str_buy_token,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        await sync_to_async(userManager.trade_buy_token)(user_id, token_type, float(token_amount), token_addr, slippage)
        return MAIN
########################################################################
#                        +Message Handler                              #
########################################################################
async def _handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: 
    text = update.message.text
    userInfo = update.message.from_user
    user_id = userInfo['id']
    global g_UserStatus
##################################################################################################################################################################
##################################################################################################################################################################
    match text:
        case '🔄 Sell':
            trades = await sync_to_async(userManager.get_user_sell_tokens)(user_id)
            for trade in trades:
                print(trade)
                keyboard = [
                    [
                        InlineKeyboardButton("Sell", callback_data=f"TradeSell:{trade['chain_type']}:{trade['token_address']}"),
                    ]
                ]
                await update.message.reply_text(
                    f"Chain : {trade['chain_type']}\nAddress : {trade['token_address']}\nAmount : {format_float(trade['token_amount'], 1)}",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            keyboard = [
                [
                    InlineKeyboardButton("Home", callback_data="Home"),
                ]
            ]
            await update.message.reply_text(
                "If you want go back 👇",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return TRADE

##################################################################################################################################################################
##################################################################################################################################################################
    if g_UserStatus[user_id]['token_input'] :
        token_type = g_UserStatus[user_id]['token_input_type']
        token_addr= g_UserStatus[user_id]['token_input_addr']
        amount = 0
        try:
            amount = float(text)
            _, total_eth, total_sol = await sync_to_async(userManager.get_trade_able_token)()

            if (token_type == 'ETH' and amount > total_eth) or (token_type == 'SOL' and amount > total_sol): 
                g_UserStatus[user_id]['token_input'] = False
                g_UserStatus[user_id]['token_input_type'] = ''
                g_UserStatus[user_id]['token_input_addr'] = ''
                await update.message.reply_text(
                    f"You can't trade with {amount} {token_type}! Please retry from begin!",
                )
                return MAIN
            
            g_UserStatus[user_id]['token_input'] = False
            g_UserStatus[user_id]['token_input_type'] = ''
            g_UserStatus[user_id]['token_input_addr'] = ''

            g_UserStatus[user_id]['slippage_request'] = True
            g_UserStatus[user_id]['slippage_meta'] = f"{token_type}:{token_addr}:{amount}"

            await update.message.reply_text(
                f"<b>Please input slippage.\nDefault : 2%</b>",
            )
            return MAIN
        except Exception as e:
            print(e)
            await update.message.reply_text(
                "❌ Error!",
            )
##################################################################################################################################################################
##################################################################################################################################################################
    if g_UserStatus[user_id]['trade_request'] :
        params = text.split("/")
        chain_type = params[0].lower()
        token_addr = ""
        if len(params) > 1:
            token_addr = params[1]

        keyboard = [
            [
                InlineKeyboardButton("Retry", callback_data="RestartTrade"),
                InlineKeyboardButton("Cancel", callback_data="Home"),
            ]
        ]
        is_trading = await sync_to_async(userManager.is_trading_token)(token_addr)
        if is_trading:
            g_UserStatus[user_id]['trade_request'] = False
            await update.message.reply_text(
                "Someone is already trading this token.\nPlease try other token address.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return TRADE
        user_cnt, total_eth, total_sol = await sync_to_async(userManager.get_trade_able_token)()
        match chain_type:
            case 'eth':
                if is_valid_ethereum_address(token_addr):
                    if not is_valid_ethereum_token_address(token_addr):
                        await update.message.reply_text(
                            f"❌ Is really token address?\n{token_addr}❓",
                            reply_markup=InlineKeyboardMarkup(keyboard)
                        )
                        return TRADE

                    token_info = await sync_to_async(get_name_marketcap_liqudity_price)(chain_type, token_addr)
                    keyboard = [
                        [
                            InlineKeyboardButton("Buy", callback_data=f"BuyToken:ETH:{token_addr}"),
                            InlineKeyboardButton("Cancel", callback_data="Home"),
                        ]
                    ]
                    st_token_info = f"<B>⌛️ {token_info['name']} ({token_info['symbol']}) 🔗 {token_info['token_group']}\n{token_info['CA']}\n{token_info['LP']}\n\nLiquidity: {token_info['liquidity']}\n\n🧢 Market Cap | {token_info['market_cap']}\n⚖️ Taxes | {token_info['taxes']}\n\nCurrent slippage: 2%\nIn reserve : {format_float(total_eth, 4)} ETH for {user_cnt} users is available</B>"
                    g_UserStatus[user_id]['token_info'] = st_token_info
                    await update.message.reply_text(
                        st_token_info,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    await sync_to_async(userManager.send_message_group)(st_token_info)
                else:
                    await update.message.reply_text(
                        f"❌ Not ethereum address\n{token_addr}❓",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                return TRADE
            case 'sol':
                if is_valid_solana_address(token_addr):
                    token_info = await sync_to_async(get_name_marketcap_liqudity_price)(chain_type, token_addr)
                    keyboard = [
                        [
                            InlineKeyboardButton("Buy", callback_data=f"BuyToken:SOL:{token_addr}"),
                            InlineKeyboardButton("Cancel", callback_data="Home"),
                        ]
                    ]

                    st_token_info = f"<B>⌛️ {token_info['name']} ({token_info['symbol']}) 🔗 {token_info['token_group']}\n{token_info['CA']}\n{token_info['LP']}\n\nLiquidity: {token_info['liquidity']}\n\n🧢 Market Cap | {token_info['market_cap']}\n⚖️ Taxes | {token_info['taxes']}\n\nCurrent slippage: 2%\nIn reserve : {format_float(total_sol, 4)} SOL for {user_cnt} users is available</B>"
                    g_UserStatus[user_id]['token_info'] = st_token_info
                    await update.message.reply_text(
                        st_token_info,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                else:
                    await update.message.reply_text(
                        f"❌ Not solana address\n{token_addr}❓",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                     )
                return TRADE

async def _tradeSell(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    params = query.data.split(":")
    user_id = query.from_user.id
    token_type = params[1]
    token_address = params[2]

    str_sell_token = f"Chain : {token_type}\nAddress : {token_address}\nPlease wait. This might take get mins!"
    await query.message.edit_text(
        str_sell_token,
    )
    await sync_to_async(userManager.send_message_group)(str_sell_token)
    sellThread = threading.Thread(target=_trade_sell_token, args=(user_id, token_type, token_address), daemon=True)
    sellThread.start()   
    return MAIN

def _trade_sell_token(user_id : int, token_type : str, token_address : str):
    asyncio.run(sync_to_async(userManager.trade_sell_token)(user_id, token_type, token_address))

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

def user_initialize(user_id : int) -> None:
    global g_UserStatus
    g_UserStatus[user_id] = {
        "withdraw_request": False,
        "withdraw_token": "",
        "withdraw_amount": 0,
        "invest_request": False,
        "invest_token": "",
        "token_address_request" : False,
        "token_chain_type" : "",
        "token_info" : '',
        "token_input" : False,
        "token_input_type" : '',
        "token_input_addr" : '',
        "slippage_request" : False,      
        "slippage_meta" : '',      
    }
########################################################################
#                           Main Function                              #
########################################################################
def main() -> None:
    mnemonicManager.init()
    eth_w, sol_w = mnemonicManager.get_owner_wallet()
    userManager.set_owner_wallet(eth_w, sol_w)
    load_dotenv()
    time_scheduler = TimeScheduler()
    time_scheduler.set_setting(userManager)
    time_scheduler.start()
    token = os.getenv('BOT_TOKEN')
    application = ApplicationBuilder().token(token).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start),
                      CommandHandler("unlock", user_unlock),
                      CommandHandler("lock", user_lock),
                      CommandHandler("deposit", user_deposit),
                      CommandHandler("balance", user_balance),
                      CommandHandler("users", user_status),
                      CommandHandler("withdraw", user_withdraw),
                      CommandHandler("invest", user_invest),
                      CommandHandler("trade", user_trade),
                      CommandHandler("end", end)],
        states={
            MAIN:       [],
            WITHDRAW:   [CallbackQueryHandler(_user_withdraw_amount, pattern="^Withdraw"),
                        MessageHandler(filters.TEXT, _withdraw_handle_message)],        
            INVEST:    [CallbackQueryHandler(_user_invest_amount, pattern="^Invest"),
                        MessageHandler(filters.TEXT, _invest_handle_message)],        
            TRADE:     [CallbackQueryHandler(_user_buy_token, pattern="BuyToken"),
                        CallbackQueryHandler(_select_token_amount, pattern="^SelectTokenAmount"),
                        MessageHandler(filters.TEXT, _trade_handle_message),
                        CallbackQueryHandler(_tradeBuy, pattern="^TradeBuy"),
                        CallbackQueryHandler(_tradeSell, pattern="^TradeSell")],        
        },
        fallbacks=[CommandHandler("end", end)],
        allow_reentry=True,
    )
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()