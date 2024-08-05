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
    is_valid_solana_address, 
    get_name_marketcap_liqudity_price 
)
from dotenv import load_dotenv
# import time
# import threading

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def format_float(value, decimals):
    formatted_value = f"{value:.{decimals}f}".rstrip('0').rstrip('.')
    return formatted_value

mnemonicManager = MnemonicManager()
userManager = UserManager()

MAIN, SETTINGS, WITHDRAW, TRADE = range(4)
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
    # print(str(await sync_to_async(userManager._calculate_contribution)('ETH')))
    # start_auto(update, context)
    # user = update.effective_user
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
        "trade_request" : False,
        "token_info" : '',
        "token_input" : False,
        "token_input_type" : '',
        "token_input_addr" : '',        
    }

    str_lock_status = "ACCOUNT LOCKED! 🔒"
    if not None and not isLock:
        str_lock_status = "ACCOUNT OPENED! 🔓"
    keyboard = [
        [
            KeyboardButton("⬇️ Deposit"),
            KeyboardButton("💳 Balance"),
            KeyboardButton("⬆️ Withdraw"),
        ],
        [
            KeyboardButton("⚙️ Setting"),
            KeyboardButton("🔄 Trade"),
        ]
        # ,
        # [
        #     KeyboardButton("👤 Admin"),
        # ],
    ]
    # reply_inline_markup = InlineKeyboardMarkup(keyboard)
    reply_keyboard_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        f'🏠 Home\n\nWelcome {real_name}!\n\n{str_lock_status}\n\nChange status 🫴   ⚙️ Setting',
        reply_markup=reply_keyboard_markup
    )
    return MAIN
async def _start(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    userInfo = query.from_user
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
        "trade_request" : False,
        "token_info" : '',
        "token_input" : False,
        "token_input_type" : '',        
        "token_input_addr" : '',        
    }
    str_lock_status = "ACCOUNT LOCKED! 🔒"
    if not None and not isLock:
        str_lock_status = "ACCOUNT OPENED! 🔓"
    await query.message.edit_text(
        f'🏠 Home\n\nWelcome {real_name}!\n\n{str_lock_status}\n\nChange status 🫴   ⚙️ Setting',
        reply_markup=InlineKeyboardMarkup([])
    )
    return MAIN
########################################################################
#                              +Profile                                #
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
    global g_UserStatus
##################################################################################################################################################################
##################################################################################################################################################################
    match text:
        case '⬇️ Deposit':
            eth_wallet, sol_wallet = await sync_to_async(userManager.get_user_wallet)(user_id)
            await update.message.reply_text(
                f"*ETH :*\n👉 `{eth_wallet}`\n*SOL :*\n👉 `{sol_wallet}`",
                parse_mode=ParseMode.MARKDOWN_V2
            )
        case '⬆️ Withdraw':
            g_UserStatus[user_id]['withdraw_request'] = True
            st_wallet = "*Input receiver address*\n```ex:\neth/0x934Eb8.....K1dF46\nsol/EDJJhDO.....MLT8FUm```"
            st_wallet=st_wallet.replace('.', '\.')
            await update.message.reply_text(
                f"*Please withdraw here\!*\n*__Withdraw only profits\nDeposit ➡️ Profit\(No Fee\)__*\n{st_wallet}",
                parse_mode=ParseMode.MARKDOWN_V2
            )
        case '💳 Balance':
            eth, sol, profit_eth, profit_sol = await sync_to_async(userManager.get_user_balance)(user_id)
            await update.message.reply_text(
                "Your Wallet 💳\n"+
                f"<pre>Token      Deposit    Profit\n"+
                      "-------    -------    -------\n"+
                     f" ETH       {eth:.3f}      {profit_eth:.3f}\n"+
                     f" SOL       {sol:.3f}      {profit_sol:.3f}</pre>",
                parse_mode=ParseMode.HTML
            )
        case '⚙️ Setting':
            isLock = await sync_to_async(userManager.get_user_lock)(user_id)
            eth, sol, profit_eth, profit_sol = await sync_to_async(userManager.get_user_balance)(user_id)
            ################################ Lock/Unlock ###################################
            keyboard = [
                [
                    InlineKeyboardButton("You would? 🔒 ➡️ 🔓", callback_data="Lock2Unlock"),
                ]
            ]
            str_lock_status = "Status : Locked🔒"
            if not None and not isLock:
                str_lock_status = "Status : Opened🔓"
                keyboard = [
                    [
                        InlineKeyboardButton("You would? 🔓 ➡️ 🔒", callback_data="Unlock2Lock"),
                    ]
                ]
            await update.message.reply_text(
                f"⚙️ Setting\n\n{str_lock_status}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            ################################ Profit -> Deposit ###################################
            keyboard = [
                [
                    InlineKeyboardButton(f"ETH🟰{format_float(profit_eth, 3)}", callback_data="P2D_ETH"),
                    InlineKeyboardButton(f"SOL🟰{format_float(profit_sol, 3)}", callback_data="P2D_SOL"),
                ]
            ]
            await update.message.reply_text(
                f"To trade, please here!\nProfit ➡️ Deposit(No Fee)",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            ################################ Deposit -> Profit ###################################
            keyboard = [
                [
                    InlineKeyboardButton(f"ETH🟰{format_float(eth, 3)}", callback_data="D2P_ETH"),
                    InlineKeyboardButton(f"SOL🟰{format_float(sol, 3)}", callback_data="D2P_SOL"),
                ]
            ]
            await update.message.reply_text(
                f"To withdraw, please here!\nDeposit ➡️ Profit(No Fee)",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            ####################################### Home ##########################################
            keyboard = [
                [
                    InlineKeyboardButton("Home", callback_data="Home"),
                ]
            ]
            await update.message.reply_text(
                "You have done? 👇",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return SETTINGS
        case '🔄 Trade':
            isLock = await sync_to_async(userManager.get_user_lock)(user_id)
            if isLock:
                await update.message.reply_text(
                    "⚠️ Your account is Locked! 🔒",
                )
                return MAIN
            g_UserStatus[user_id]['trade_request'] = True
            st_wallet = "*Input Token address*\n```ex:\neth/0x934Eb8.....K1dF46\nsol/EDJJhDO.....MLT8FUm```"
            st_wallet=st_wallet.replace('.', '\.')
            await update.message.reply_text(
                f"*Please trade here\!*\n*__Trade with only deposit\nProfit ➡️ Deposit\(No Fee\)__*\n{st_wallet}",
                parse_mode=ParseMode.MARKDOWN_V2
            )
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
            await update.message.reply_text(
                f"Token : {g_UserStatus[user_id]['token_input_addr']}\n{token_type} : {amount}\nPlease wait. This might take get mins!",
            )
            await sync_to_async(userManager.trade_buy_token)(user_id, token_type, amount, token_addr)
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
        match chain_type:
            case 'eth':
                if is_valid_ethereum_address(token_addr):
                    token_info = await sync_to_async(get_name_marketcap_liqudity_price)(chain_type, token_addr)
                    keyboard = [
                        [
                            InlineKeyboardButton("Buy", callback_data=f"BuyToken:ETH:{token_addr}"),
                            InlineKeyboardButton("Cancel", callback_data="Home"),
                        ]
                    ]
                    st_token_info = f"<pre> Field           | Value\n---------------------------------\n Name            | {token_info['name']}\n Symbol          | {token_info['symbol']}\n Market Cap      | ${token_info['market_cap']}\n Market Cap Rank | {token_info['market_cap_rank']}\n Price           | ${token_info['price']}\n H_24h           | ${token_info['high_24h']}\n L_24h           | ${token_info['low_24h']}\n Change_24h      | ${format_float(token_info['price_change_24h'], 10)}\n Percentage_24h  | {token_info['price_change_percentage_24h']}%\n Total Volume    | {token_info['total_volume']}\n Liquidity       | ${int(token_info['liquidity'])}</pre>"
                    g_UserStatus[user_id]['token_info'] = st_token_info
                    await update.message.reply_text(
                        st_token_info,
                        parse_mode=ParseMode.HTML,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
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
                    st_token_info = f"<pre> Field           | Value\n---------------------------------\n Name            | {token_info['name']}\n Symbol          | {token_info['symbol']}\n Market Cap      | ${token_info['market_cap']}\n Market Cap Rank | {token_info['market_cap_rank']}\n Price           | ${token_info['price']}\n H_24h           | ${token_info['high_24h']}\n L_24h           | ${token_info['low_24h']}\n Change_24h      | ${format_float(token_info['price_change_24h'], 10)}\n Percentage_24h  | {token_info['price_change_percentage_24h']}%\n Total Volume    | {token_info['total_volume']}\n Liquidity       | ${int(token_info['liquidity'])}</pre>"
                    g_UserStatus[user_id]['token_info'] = st_token_info
                    await update.message.reply_text(
                        st_token_info,
                        parse_mode=ParseMode.HTML,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                else:
                    await update.message.reply_text(
                        f"❌ Not solana address\n{token_addr}❓",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                return TRADE
##################################################################################################################################################################
##################################################################################################################################################################
    if g_UserStatus[user_id]['withdraw_request'] :
        params = text.split("/")
        chain_type = params[0].lower()
        recev_addr = ""
        if len(params) > 1:
            recev_addr = params[1]
        keyboard = [
            [
                InlineKeyboardButton("Retry", callback_data="RetryWithdraw"),
                InlineKeyboardButton("Cancel", callback_data="Home"),
            ]
        ]
        match chain_type:
            case 'eth':
                if is_valid_ethereum_address(recev_addr):
                    _, _, profit_eth, _ = await sync_to_async(userManager.get_user_balance)(user_id)
                    keyboard = [
                        [
                            InlineKeyboardButton("All", callback_data=f"Withdraw:ETH:100:{recev_addr}"),
                            InlineKeyboardButton("75%",  callback_data=f"Withdraw:ETH:75:{recev_addr}"),
                        ],
                        [
                            InlineKeyboardButton("50%",  callback_data=f"Withdraw:ETH:50:{recev_addr}"),
                            InlineKeyboardButton("25%",  callback_data=f"Withdraw:ETH:25:{recev_addr}"),
                        ],
                        [
                            InlineKeyboardButton("Cancel",  callback_data="Home"),
                        ]
                    ]
                    str_withdraw = f"✅ Receiver address\n{recev_addr}\nYour balance : <b>{profit_eth} ETH</b>\nAmount?"
                    if profit_eth < 0.002:
                        str_withdraw = f"⚠️ Sorry, you have no balance\nYour balance : <b>{profit_eth} ETH</b>"
                        keyboard = [
                            [
                                InlineKeyboardButton("Home",  callback_data="Home"),
                            ]
                        ]
                    await update.message.reply_text(
                        str_withdraw,
                        parse_mode=ParseMode.HTML,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                else:
                    await update.message.reply_text(
                        f"❌ Not ethereum address\n{recev_addr}❓",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                return WITHDRAW
            case 'sol':
                if is_valid_solana_address(recev_addr):
                    _, _, _, profit_sol = await sync_to_async(userManager.get_user_balance)(user_id)
                    keyboard = [
                        [
                            InlineKeyboardButton("All", callback_data=f"Withdraw:SOL:100:{recev_addr}"),
                            InlineKeyboardButton("75%",  callback_data=f"Withdraw:SOL:75:{recev_addr}"),
                        ],
                        [
                            InlineKeyboardButton("50%",  callback_data=f"Withdraw:SOL:50:{recev_addr}"),
                            InlineKeyboardButton("25%",  callback_data=f"Withdraw:SOL:25:{recev_addr}"),
                        ],
                        [
                            InlineKeyboardButton("Cancel",  callback_data="Home"),
                        ]
                    ]
                    str_withdraw = f"✅ Receiver address\n{recev_addr}\nYour balance : <b>{profit_sol} SOL</b>\nAmount?"
                    if profit_sol < 0.01:
                        str_withdraw = f"⚠️ Sorry, you have no balance\nYour balance : <b>{profit_sol} SOL</b>"
                        keyboard = [
                            [
                                InlineKeyboardButton("Home",  callback_data="Home"),
                            ]
                        ]
                    await update.message.reply_text(
                        str_withdraw,
                        parse_mode=ParseMode.HTML,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                else: 
                    await update.message.reply_text(
                        f"❌ Not Solana address\n{recev_addr}❓",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                return WITHDRAW
########################################################################
#                               +Trade                                 #
########################################################################
async def _restartTrade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    global g_UserStatus
    g_UserStatus[user_id]['trade_request'] = True
    st_wallet = "*Input token address*\n```ex:\neth/0x934Eb8.....K1dF46\nsol/EDJJhDO.....MLT8FUm```"
    st_wallet=st_wallet.replace('.', '\.')
    await query.message.edit_text(
        f"*Please trade here\!*\n*__Trade with only deposit\nProfit ➡️ Deposit\(No Fee\)__*\n{st_wallet}",
        parse_mode=ParseMode.MARKDOWN_V2
    )
    return MAIN
async def _buyToken(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:    
    query = update.callback_query
    params = query.data.split(":")
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
                ],
                [
                    InlineKeyboardButton("Cancel",      callback_data="Home"),
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
                ],
                [
                    InlineKeyboardButton("Cancel",  callback_data="Home"),
                ]
            ]
    await query.message.edit_text(
        st_token_info + st_available,
        parse_mode=ParseMode.HTML,
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
        g_UserStatus[user_id]['withdraw_request'] = False
        g_UserStatus[user_id]['trade_request'] = False
        g_UserStatus[user_id]['token_input'] = True
        g_UserStatus[user_id]['token_input_type'] = token_type
        g_UserStatus[user_id]['token_input_addr'] = token_addr
        await query.message.edit_text(
            f"Please Input the correct {token_type} amount{st_available}",
            reply_markup=InlineKeyboardMarkup([])
        )
    else :
        if (token_type == 'ETH' and float(token_amount) > total_eth) or (token_type == 'SOL' and float(token_amount) > total_sol): 
            await query.message.edit_text(
                f"You can't trade with {token_amount} {token_type}! Please retry from begin!",
            )
            return MAIN

        await query.message.edit_text(
            f"Token : {token_addr}\n{token_type} : {token_amount}\nPlease wait. This might take get mins!",
        )
        await sync_to_async(userManager.trade_buy_token)(user_id, token_type, float(token_amount), token_addr)
    return MAIN
########################################################################
#                              +Withdraw                               #
########################################################################
async def _retryWithdraw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    global g_UserStatus
    g_UserStatus[user_id]['withdraw_request'] = True
    st_wallet = "*Input receiver address*\n```ex:\neth/0x934Eb8.....K1dF46\nsol/EDJJhDO.....MLT8FUm```"
    st_wallet=st_wallet.replace('.', '\.')
    await query.message.edit_text(
        f"*Please withdraw here\!*\n*__Withdraw only profits\nDeposit ➡️ Profit\(No Fee\)__*\n{st_wallet}",
        parse_mode=ParseMode.MARKDOWN_V2
    )
    return MAIN
async def _withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    params = query.data.split(":")
    await query.message.edit_text(
        f"Please wait...⏰\n⚠️ Don't leave here!",
    )
    print("**********************", params)
    res_tx = await sync_to_async(userManager.user_withdraw_profit)(user_id, params[1], int(params[2]), params[3])
    print("**********************", res_tx)
    await query.message.edit_text(
        f"✅ Amount : {res_tx['amount']}\n <pre>{res_tx['tx']}</pre>",
        parse_mode=ParseMode.HTML,
    )
    return MAIN
########################################################################
#                              +Settings                               #
########################################################################
############################# Lock / Unlock ############################
async def _show_lock_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    keyboard = [
        [
            InlineKeyboardButton("You would? 🔒 ➡️ 🔓", callback_data="Lock2Unlock"),
        ]
    ]
    str_lock_status = "Status : Locked🔒"
    isLock = await sync_to_async(userManager.get_user_lock)(user_id)
    if not None and not isLock:
        str_lock_status = "Status : Opened🔓"
        keyboard = [
            [
                InlineKeyboardButton("You would? 🔓 ➡️ 🔒", callback_data="Unlock2Lock"),
            ]
        ]
    await query.message.edit_text(
        f"⚙️ Setting\n\n{str_lock_status}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
async def _lock_to_unlock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    await sync_to_async(userManager.user_unlock)(user_id)
    await _show_lock_result(update, context)
async def _unlock_to_lock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    await sync_to_async(userManager.user_lock)(user_id)
    await _show_lock_result(update, context)
############################# Profit -> Deposit ############################
async def _P2D_ETH(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    keyboard = [
        [
            InlineKeyboardButton("All", callback_data="P2D:ETH:100"),
            InlineKeyboardButton("75%",  callback_data="P2D:ETH:75"),
            InlineKeyboardButton("50%",  callback_data="P2D:ETH:50"),
            InlineKeyboardButton("25%",  callback_data="P2D:ETH:25"),
        ],
        [
            InlineKeyboardButton("Back",  callback_data="BACK:P2D"),
        ]
    ]
    _, _, profit_eth, _ = await sync_to_async(userManager.get_user_balance)(user_id)
    await query.message.edit_text(
        f"Profit ETH 🟰 {format_float(profit_eth,3)} 🔜 Deposit",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
async def _P2D_SOL(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    keyboard = [
        [
            InlineKeyboardButton("All", callback_data="P2D:SOL:100"),
            InlineKeyboardButton("75%",  callback_data="P2D:SOL:75"),
            InlineKeyboardButton("50%",  callback_data="P2D:SOL:50"),
            InlineKeyboardButton("25%",  callback_data="P2D:SOL:25"),
        ],
        [
            InlineKeyboardButton("Back",  callback_data="BACK:P2D"),
        ]
    ]
    _, _, _, profit_sol = await sync_to_async(userManager.get_user_balance)(user_id)
    await query.message.edit_text(
        f"Profit SOL 🟰 {format_float(profit_sol,3)} 🔜 Deposit",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
############################# Deposit -> Profit ############################
async def _D2P_ETH(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    keyboard = [
        [
            InlineKeyboardButton("All", callback_data="D2P:ETH:100"),
            InlineKeyboardButton("75%",  callback_data="D2P:ETH:75"),
            InlineKeyboardButton("50%",  callback_data="D2P:ETH:50"),
            InlineKeyboardButton("25%",  callback_data="D2P:ETH:25"),
        ],
        [
            InlineKeyboardButton("Back",  callback_data="BACK:D2P"),
        ]
    ]
    eth, _, _, _ = await sync_to_async(userManager.get_user_balance)(user_id)
    await query.message.edit_text(
        f"Deposit ETH 🟰 {format_float(eth,3)} 🔜 Profit",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
async def _D2P_SOL(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    keyboard = [
        [
            InlineKeyboardButton("All", callback_data="D2P:SOL:100"),
            InlineKeyboardButton("75%",  callback_data="D2P:SOL:75"),
            InlineKeyboardButton("50%",  callback_data="D2P:SOL:50"),
            InlineKeyboardButton("25%",  callback_data="D2P:SOL:25"),
        ],
        [
            InlineKeyboardButton("Back",  callback_data="BACK:D2P"),
        ]
    ]
    _, sol, _, _ = await sync_to_async(userManager.get_user_balance)(user_id)
    await query.message.edit_text(
        f"Deposit SOL 🟰 {format_float(sol,3)} 🔜 Profit",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
############################ Operation D2P, P2D ###########################
async def _operation_D2P_P2d(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    params= query.data.split(":")
    op_type = params[0]
    token_type = ""
    amount = 0
    if len(params) > 2:
        token_type = params[1]
        amount = int(params[2])
    await sync_to_async(userManager.operation_balance)(user_id, op_type, token_type, amount)
    await _back_d2p_p2d(update, op_type)
############################# BACK D2P & P2D ############################
async def _back_d2p_p2d(update: Update, branch : str) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    eth, sol, profit_eth, profit_sol = await sync_to_async(userManager.get_user_balance)(user_id)
    match branch:
        case 'P2D':
            ################################ Profit -> Deposit ###################################
            keyboard = [
                [
                    InlineKeyboardButton(f"ETH🟰{format_float(profit_eth, 3)}", callback_data="P2D_ETH"),
                    InlineKeyboardButton(f"SOL🟰{format_float(profit_sol, 3)}", callback_data="P2D_SOL"),
                ]
            ]
            await query.message.edit_text(
                f"To trade, please here!\nProfit ➡️ Deposit(No Fee)",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        case 'D2P':
            ################################ Deposit -> Profit ###################################
            keyboard = [
                [
                    InlineKeyboardButton(f"ETH🟰{format_float(eth, 3)}", callback_data="D2P_ETH"),
                    InlineKeyboardButton(f"SOL🟰{format_float(sol, 3)}", callback_data="D2P_SOL"),
                ]
            ]
            await query.message.edit_text(
                f"To withdraw, please here!\nDeposit ➡️ Profit(No Fee)",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
async def _Back_D2P_P2D(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    branch = query.data.split(":")[1]
    await _back_d2p_p2d(update, branch)
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
    eth_w, sol_w = mnemonicManager.get_owner_wallet()
    userManager.set_owner_wallet(eth_w, sol_w)
    load_dotenv()
    time_scheduler = TimeScheduler()
    time_scheduler.set_setting(userManager)
    time_scheduler.start()
    token = os.getenv('BOT_TOKEN')
    application = ApplicationBuilder().token(token).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN:       [CallbackQueryHandler(_func_profile, pattern="Profile"),
                        CallbackQueryHandler(start, pattern="Home"),
                        MessageHandler(filters.TEXT, _handle_message)],

            SETTINGS:   [CallbackQueryHandler(_lock_to_unlock, pattern="Lock2Unlock"),
                        CallbackQueryHandler(_unlock_to_lock, pattern="Unlock2Lock"),

                        CallbackQueryHandler(_P2D_ETH, pattern="P2D_ETH"),
                        CallbackQueryHandler(_P2D_SOL, pattern="P2D_SOL"),
                        CallbackQueryHandler(_operation_D2P_P2d, pattern="^P2D:"),                        
                        
                        CallbackQueryHandler(_D2P_ETH, pattern="D2P_ETH"),
                        CallbackQueryHandler(_D2P_SOL, pattern="D2P_SOL"),
                        CallbackQueryHandler(_operation_D2P_P2d, pattern="^D2P:"),                        

                        CallbackQueryHandler(_Back_D2P_P2D, pattern="^BACK:"),                        

                        CallbackQueryHandler(_start, pattern="Home")],
            WITHDRAW:   [CallbackQueryHandler(_start, pattern="Home"),
                        CallbackQueryHandler(_retryWithdraw, pattern="RetryWithdraw"),
                        CallbackQueryHandler(_withdraw, pattern="^Withdraw")],        
            TRADE:     [CallbackQueryHandler(_start, pattern="Home"),
                        CallbackQueryHandler(_restartTrade, pattern="RestartTrade"),
                        CallbackQueryHandler(_buyToken, pattern="^BuyToken"),
                        CallbackQueryHandler(_tradeBuy, pattern="^TradeBuy")],        
        },
        fallbacks=[CommandHandler("end", end)],
        allow_reentry=True,
    )
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()