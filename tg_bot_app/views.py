from django.shortcuts import render
from .models import MnemonicModel, UserModel, DepositModel
from .utils import ( 
    generate_wallet_ETH, 
    generate_wallet_SOL, 
    generate_mnemonic,
    transfer_all_eth_to,
    transfer_all_sol_to
)
import time
import threading
from typing import Tuple
######################################################################################
################################ 1. MnemonicManager ##################################
######################################################################################
class MnemonicManager():
    def __init__(self) -> None:
        self.owner_eth_address = ''
        self.owner_sol_address = ''

    def get_owner_wallet(self) -> Tuple[str, str]:
        return self.owner_eth_address, self.owner_sol_address
    
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
                # transfer_all_sol_to(sol_prv_key, sol_wallet, self.owner_sol_wallet)
        except Exception as e:
            print(f"-- UserManager >> track_user_deposit Error:{e} --")

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
    interval = 3

    def set_setting(self, UM : UserManager):
        self.userManager = UM

    def timer(self):
        self.userManager.track_user_deposit()
        print(f"Number : {self.userManager.get_number_users()}")

