from django.shortcuts import render
from .models import MnemonicModel, UserModel, DepositModel, WithdrawModel, TradeModel
from django.db.models import Sum, Count
from .utils import ( 
    format_float,
    generate_wallet_ETH, 
    generate_wallet_SOL, 
    generate_mnemonic,
    transfer_all_eth_to,
    transfer_balance_eth_to,
    get_balanceOf_ERC20,
    transfer_all_sol_to,
    swap_eth_to_tokens,
    swap_tokens_to_eth,
    get_token_name_symbol_decimals
)
import time
import threading
import requests
from typing import Tuple, Dict, Any, List
import os
import json
from dotenv import load_dotenv
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
######################################################################################
################################ 1. MnemonicManager ##################################
######################################################################################
class MnemonicManager():
    def __init__(self) -> None:
        self.owner_eth_address = ''
        self.owner_sol_address = ''

    def get_owner_wallet(self) -> Tuple[str, str]:
        return self.owner_eth_address, self.owner_sol_address
    def get_owner_prv_key_from_db(self) -> Tuple[str, str]:
        mnemonic = MnemonicModel.objects.all().first()
        return mnemonic.eth_private_key, mnemonic.sol_private_key
    def _is_exist_mnemonic(self) -> bool:
        return MnemonicModel.objects.filter(mnemonic__isnull=False).exists()

    def _create_admin_wallet(self) -> None:
        try :
            mnemonic_data = generate_mnemonic()
            eth_private, eth_public = generate_wallet_ETH(mnemonic_data, 0)
            sol_private, sol_public = generate_wallet_SOL(mnemonic_data, 0)
            mnemonic =  MnemonicModel.objects.create(
                            mnemonic=mnemonic_data, 
                            index_key=0, 
                            eth_public_key=eth_public, 
                            eth_private_key=eth_private, 
                            sol_public_key=sol_public, 
                            sol_private_key=sol_private
                        )
            mnemonic.save()
            self.owner_eth_address = eth_public
            self.owner_sol_address = sol_public
            print('-- MnemonicManager >> Admin wallet created --')
        except Exception as e:
            print(f'-- MnemonicManager >> Failed to create admin wallet {e} --')

    def read_mnemonic(self) -> str:
        if self._is_exist_mnemonic():
            mnemonics = MnemonicModel.objects.all()
            return mnemonics[0].mnemonic
        else:
            print('-- MnemonicManager >> Failed to read mnemonic --')
            return None

    def get_index_key(self) -> int:
        if self._is_exist_mnemonic():
            mnemonics = MnemonicModel.objects.all()
            return mnemonics[0].index_key
        else:
            print('-- MnemonicManager >> Failed to read index_key --')
            return None

    def update_index_key(self, index : int) -> None:
        if self._is_exist_mnemonic():
            mnemonics = MnemonicModel.objects.all().first()
            mnemonics.index_key = index
            mnemonics.save()
        else:
            print('-- MnemonicManager >> Failed to update index_key --')

    def init(self) -> None:
        if self._is_exist_mnemonic():
            mnemonics = MnemonicModel.objects.all().first()
            self.owner_eth_address = mnemonics.eth_public_key
            self.owner_sol_address = mnemonics.sol_public_key
            print('-- MnemonicManager >> Mnemonic exist --')
        else:
            self._create_admin_wallet()
######################################################################################
################################ 2. MnemonicManager ##################################
######################################################################################
class UserManager():
    def __init__(self) -> None:
        self.owner_eth_wallet = ''
        self.owner_sol_wallet = ''

    def set_owner_wallet(self, eth_wallet : str, sol_wallet : str) -> None:
        self.owner_eth_wallet = eth_wallet
        self.owner_sol_wallet = sol_wallet

    def _is_exist_user(self, user_id: int) -> bool:
        return UserModel.objects.filter(user_id=user_id).exists()

    def _register_user(self, user_id : int, user_name : str, real_name : str, eth_prv_key : str, eth_pub_key : str, sol_prv_key : str, sol_pub_key : str) -> object:
        user =  UserModel.objects.create(
                    user_id=user_id, 
                    real_name=real_name, 
                    user_name=user_name,
                    eth_public_key=eth_pub_key,
                    eth_private_key=eth_prv_key,
                    sol_public_key=sol_pub_key,
                    sol_private_key=sol_prv_key
                )
        user.save()
        print(f"-- UserManager >> {real_name} created --")
    
    def _add_user_deposit(self, user_id : int, token_type : str, amount : float, tx : str) -> None:
        deposit =  DepositModel.objects.create(
                    user_id=user_id, 
                    token_type=token_type,
                    amount=amount,
                    tx=tx
                )
        deposit.save()
        print(f"-- UserManager >> Deposit, user : {user_id}  --")

    def _calculate_contribution(self, token_type : str) -> Dict[str, Any]:
        users = UserModel.objects.filter(account_lock=False)
        contribution = []
        match token_type:
            case 'ETH':
                available_ETH = UserModel.objects.filter(account_lock=False).aggregate(total_sum=Sum('balance_eth'))['total_sum']
                if available_ETH == 0 : 
                    return None
                for user in users:
                    user_cont = {
                        "user_id" : user.user_id,
                        "value" : user.balance_eth / available_ETH
                    }
                    contribution.append(user_cont)
            case 'SOL':
                available_SOL = UserModel.objects.filter(account_lock=False).aggregate(total_sum=Sum('balance_sol'))['total_sum']
                if available_SOL == 0 : 
                    return None
                for user in users:
                    user_cont = {
                        "user_id" : user.user_id,
                        "value" : user.balance_sol / available_SOL
                    }
                    contribution.append(user_cont)
        return contribution
    
    def get_trade_able_token(self) -> Tuple[int, float, float]:
        available_Users = UserModel.objects.filter(account_lock=False).aggregate(total_cnt=Count('balance_eth'))['total_cnt']
        available_ETH = UserModel.objects.filter(account_lock=False).aggregate(total_sum=Sum('balance_eth'))['total_sum']
        available_SOL = UserModel.objects.filter(account_lock=False).aggregate(total_sum=Sum('balance_sol'))['total_sum']
        return available_Users, available_ETH, available_SOL
    
    def get_user_wallet(self, user_id : int) -> Tuple[str, str]:
        if self._is_exist_user(user_id):
            user = UserModel.objects.get(user_id=user_id)
            return user.eth_public_key, user.sol_public_key
        else:
            return None, None

    def get_user_lock(self, user_id : int) -> bool:
        if self._is_exist_user(user_id):
            user = UserModel.objects.get(user_id=user_id)
            return user.account_lock
        return False

    def user_unlock(self, user_id : int) -> None:
        if self._is_exist_user(user_id):
            user = UserModel.objects.get(user_id=user_id)
            user.account_lock = False
            user.save()

    def user_lock(self, user_id : int) -> None:
        if self._is_exist_user(user_id):
            user = UserModel.objects.get(user_id=user_id)
            user.account_lock = True
            user.save()

    def get_user_balance(self, user_id : int) -> Tuple[float, float, float, float]:
        if self._is_exist_user(user_id):
            user = UserModel.objects.get(user_id=user_id)
            return user.balance_eth, user.balance_sol, user.profit_eth, user.profit_sol
        return None, None, None, None
    
    def get_all_user_status(self) -> List[Dict[str, Any]]:
        users = UserModel.objects.all()
        status = []
        for user in users:
            status.append({
                "name" : user.real_name,
                "status" : user.account_lock
            })
        return status
    
    def operation_balance(self, user_id : int, op_type : str, token_type : str, amount : int) -> None:
        try:
            user = UserModel.objects.get(user_id=user_id)
            de_eth, de_sol, pr_eth, pr_sol = user.balance_eth, user.balance_sol, user.profit_eth, user.profit_sol
            match op_type:
                case 'D2P':
                    match token_type:
                        case 'ETH':
                            delta = de_eth * float(amount / 100)
                            de_eth -= delta
                            pr_eth += delta
                        case 'SOL':
                            delta = de_sol * float(amount / 100)
                            de_sol -= delta
                            pr_sol += delta
                case 'P2D':
                    match token_type:
                        case 'ETH':
                            delta = pr_eth * float(amount / 100)
                            pr_eth -= delta
                            de_eth += delta
                        case 'SOL':
                            delta = pr_sol * float(amount / 100)
                            pr_sol -= delta
                            de_sol += delta
            user.balance_eth, user.balance_sol, user.profit_eth, user.profit_sol = de_eth, de_sol, pr_eth, pr_sol
            user.save()
        except Exception as e:
            print(f"-- UserManager >> error in operation_balance : {e}")
    
    def user_invest_profit(self, user_id : int, token_type : str, amount : float) -> None:
        try:
            user = UserModel.objects.get(user_id=user_id)
            match token_type:
                case 'ETH':
                    user.profit_eth -= amount
                    user.balance_eth += amount
                case 'SOL':
                    user.profit_sol -= amount
                    user.balance_sol += amount
            user.save()
        except Exception as e:
            print(f"-- UserManager >> user_invest_profit Error : {e}")

    def get_number_users(self) -> int:
        return len(UserModel.objects.all())
    
    def track_user_deposit(self) -> None:
        try:
            users = UserModel.objects.all()
            for user in users:
                user_id = user.user_id
                eth_wallet = user.eth_public_key
                eth_prv_key = user.eth_private_key
                # sol_wallet = user.sol_public_key
                # sol_prv_key = user.sol_private_key
                eth_dep_res = transfer_all_eth_to(eth_prv_key, eth_wallet, self.owner_eth_wallet)
                if not eth_dep_res == None:
                    amount = float(eth_dep_res['eth'])
                    user.balance_eth += amount
                    user.save()
                    self._add_user_deposit(user_id, "Ethereum", amount, eth_dep_res['tx'])
                    self.send_bot_message(user_id, f"✅ You Deposit {amount} ETH")
                # transfer_all_sol_to(sol_prv_key, sol_wallet, self.owner_sol_wallet)
        except Exception as e:
            print(f"-- UserManager >> track_user_deposit Error:{e} --")

    def send_bot_message(self, user_id : int, message : str) -> None:
        try :
            data = {
                "chat_id" : user_id,
                "text" : message
            }
            txt_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            requests.post(txt_url, data)
        except Exception as e:
            print(f"-- send_bot_message >> Error : {e} --")

    def send_message_group(self, message : str) -> None:
        try :
            txt_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHANNEL_ID}&text={message}&parse_mode=HTML&disable_web_page_preview=True"
            print(txt_url)
            requests.get(txt_url)
        except Exception as e:
            print(f"-- send_message_group >> Error : {e} --")

    def user_withdraw_balance(self, user_id : int, token_type : str, amount : float, receiver : str) -> None:
        mnemonicManager = MnemonicManager()
        eth_prv_key, sol_prv_key = mnemonicManager.get_owner_prv_key_from_db()
        user = UserModel.objects.get(user_id=user_id)
        match token_type:
            case 'ETH':
                resp_tx = transfer_balance_eth_to(eth_prv_key, self.owner_eth_wallet, receiver, amount)
                if resp_tx is not None and resp_tx['status'] == 1:
                    if user.profit_eth >= amount:
                        user.profit_eth -= amount
                    else:
                        user.profit_eth = 0
                        user.balance_eth -= (amount - user.profit_eth)
                    user.save()
                    withdraw = WithdrawModel.objects.create(user_id=user_id, token_type='ETH', amount=amount, tx=resp_tx['tx'])
                    withdraw.save()
                    str_message = f"Hi, {user.real_name}!\n✅ You withdraw {amount} ETH\n{resp_tx['tx']}"
                    self.send_message_group(str_message)
                    self.send_bot_message(user_id, str_message)
                else:
                    str_message = f"Hi, {user.real_name}!\n❌ Sorry! Your withdraw transaction failed!"
                    self.send_message_group(str_message)
                    self.send_bot_message(user_id, str_message)
            # case 'SOL':
            #     amount = profit_sol * (percent / 100)
            #     resp_tx = transfer_balance_sol_to()

    def _change_deposit_by_contribution(self, contribution : Dict[str, Any], token_type: str, token_amount : float) -> None:
        for user_cont in contribution:
            user = UserModel.objects.get(user_id=int(user_cont['user_id']))
            delta_bal = token_amount * float(user_cont['value'])
            match token_type:
                case 'ETH':
                    user.balance_eth += delta_bal
                case 'SOL':
                    user.balance_sol += delta_bal
            user.save()

    def _add_profit_by_contribution(self, contribution : Dict[str, Any], token_type: str, token_amount : float) -> None:
        for user_cont in contribution:
            user = UserModel.objects.get(user_id=int(user_cont['user_id']))
            delta_bal = token_amount * float(user_cont['value'])
            match token_type:
                case 'ETH':
                    user.profit_eth += delta_bal
                case 'SOL':
                    user.profit_sol += delta_bal
            user.save()

    def trade_sell_token(self, user_id : int, token_type : str, sell_token_addr : str) -> None:
        print("***** trade_sell_token **", user_id, token_type, sell_token_addr)
        mnemonicManager = MnemonicManager()
        eth_prv_key, sol_prv_key = mnemonicManager.get_owner_prv_key_from_db()
        # trade = TradeModel.objects.get(user_id=user_id, token_address=sell_token_addr)
        trades = TradeModel.objects.filter(user_id=user_id, token_address=sell_token_addr).exclude(buy_sell_status=0)
        trade = trades[0]
        if token_type == 'ETH':
            swap_res = swap_tokens_to_eth(sell_token_addr, eth_prv_key, self.owner_eth_wallet)
            in_gas_fee = swap_res['in_gas_fee']
            in_native_amount = swap_res['in_native_amount']
            contribution = json.loads(trade.user_contribution)
            print("***********", contribution)
            if swap_res['status'] == 1:
                self._add_profit_by_contribution(contribution, token_type, in_native_amount)
                trade.buy_sell_status = 0
                message = f"✅ You selled {sell_token_addr} \nGot {in_native_amount} {token_type}\n{swap_res['tx']}"
            else:
                self._change_deposit_by_contribution(contribution, token_type, -in_gas_fee)
                trade.buy_sell_status = -1
                message = f"❌ Trade failed : {swap_res['tx']}"
            trade.in_gas_fee = in_gas_fee
            trade.in_native_amount = in_native_amount
            trade.sell_tx = swap_res['tx']
            trade.save()
            self.send_bot_message(user_id, message)
            self.send_message_group(message)
            print("Swap Result >> ",swap_res)

    def trade_buy_token(self, user_id : int, token_type : str, token_amount : float, buy_token_addr : str, slippage : float) -> None:
        try :
            print("***** trade_buy_token >> **", user_id, token_type, token_amount, buy_token_addr)
            contribution = self._calculate_contribution(token_type)
            print("contribution = ",contribution)
            real_eth_sol_amount = token_amount * 0.99
            mnemonicManager = MnemonicManager()
            eth_prv_key, sol_prv_key = mnemonicManager.get_owner_prv_key_from_db()
            if token_type == 'ETH':
                swap_res = swap_eth_to_tokens(buy_token_addr, real_eth_sol_amount, eth_prv_key, self.owner_eth_wallet, slippage)
                self._change_deposit_by_contribution(contribution, token_type, -token_amount)
                if swap_res:
                    if swap_res['status'] == 1 :
                        b_s_status = 1
                        self._change_deposit_by_contribution(contribution, token_type, -swap_res['out_gas_fee'])
                    else:
                        b_s_status = -1
                        self._change_deposit_by_contribution(contribution, token_type, real_eth_sol_amount)
                    trade = TradeModel.objects.create(
                                user_id=user_id, 
                                token_address=buy_token_addr, 
                                token_amount=swap_res['token_amount'], 
                                chain_type=token_type, 
                                out_native_amount=swap_res['out_native_amount'],
                                out_gas_fee=swap_res['out_gas_fee'],
                                buy_sell_status=b_s_status,
                                buy_tx=swap_res['tx'],
                                user_contribution=json.dumps(contribution)
                            )
                    trade.save()
                    name, _, _ = get_token_name_symbol_decimals
                    message = f"✅ Bought {format_float(swap_res['token_amount'], 3)} {name}\nBy {swap_res['out_native_amount']} {token_type}\n{swap_res['tx']}"
                    self.send_bot_message(user_id, message)
                    self.send_message_group(message)
                    print("Swap Result >> ",swap_res)

            # elif token_type == 'SOL':
            #     swap_res = swap_sol_to_tokens(buy_token_addr, token_amount, sol_prv_key, self.owner_sol_wallet)
        except Exception as e:
            print("-- trade_buy_token : Error ", e)

    def is_trading_token(self, token_address : str) -> bool:
        return TradeModel.objects.filter(token_address=token_address, buy_sell_status=1).exists()

    def get_user_sell_tokens(self, user_id : int) -> List[Dict[str, Any]]:
        list = []
        trades = TradeModel.objects.filter(user_id=user_id).exclude(buy_sell_status=0)
        for trade in trades:
            list.append({
                "chain_type" : trade.chain_type,
                "token_address" : trade.token_address,
                "token_amount" : trade.token_amount,
                "buy_tx" : trade.buy_tx
            })
        return list

    def init(self, user_id : int, user_name : str, real_name : str) -> bool:
        if self._is_exist_user(user_id):
            print(f"-- UserManager >> {real_name} exist --")
        else:
            mnemonicMgr = MnemonicManager()
            mnemonic_data = mnemonicMgr.read_mnemonic()
            if mnemonic_data == None:
                return False
            index_key = mnemonicMgr.get_index_key()
            index_key += 1
            eth_private, eth_public = generate_wallet_ETH(mnemonic_data, index_key)
            sol_private, sol_public = generate_wallet_SOL(mnemonic_data, index_key)
            mnemonicMgr.update_index_key(index_key)
            self._register_user(user_id, user_name, real_name, eth_private, eth_public, sol_private, sol_public)
        
        return True
######################################################################################
###################################### 3. Timer ######################################
######################################################################################
class Timer(threading.Thread):
    def __init__(self):
        self._timer_runs = threading.Event()
        self._timer_runs.set()
        super().__init__()

    def run(self):
        while self._timer_runs.is_set():
            self.timer()
            time.sleep(self.__class__.interval)

    def stop(self):
        self._timer_runs.clear()

class TimeScheduler(Timer):
    interval = 10

    def set_setting(self, UM : UserManager):
        self.userManager = UM

    def timer(self):
        self.userManager.track_user_deposit()
        # print(f"Number : {self.userManager.get_number_users()}")

