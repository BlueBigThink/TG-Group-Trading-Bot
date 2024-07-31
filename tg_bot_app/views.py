from django.shortcuts import render
from .models import MnemonicModel, UserModel
from .utils import generate_wallet_ETH, generate_wallet_SOL, generate_mnemonic
from typing import Tuple
######################################################################################
################################ 1. MnemonicManager ##################################
######################################################################################
class MnemonicManager():
    def __init__(self) -> None:
        pass

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
            print('-- MnemonicManager >> Mnemonic exist --')
        else:
            self._create_admin_wallet()
######################################################################################
################################ 2. MnemonicManager ##################################
######################################################################################
class UserManager():
    def __init__(self) -> None:
        pass

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