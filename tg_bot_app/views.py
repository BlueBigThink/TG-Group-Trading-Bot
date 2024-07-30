from django.shortcuts import render
from bip_utils import Bip39MnemonicGenerator, Bip39WordsNum
from .models import MnemonicModel
from typing import Tuple

def generate_wallet_ETH(mnemonic : str, index : int) -> Tuple[str, str]:
    eth_private_key     = 'Ethereum Private Key'
    eth_public_key      = '0xETHEREUMWALLETADDRESS'
    return eth_private_key, eth_public_key

def generate_wallet_SOL(mnemonic : str, index : int) -> Tuple[str, str]:
    sol_private_key     = 'SOLANA Private Key'
    sol_public_key      = 'SOALANAWALLETADDRESS'
    return sol_private_key, sol_public_key

def generate_mnemonic() -> str:
    mnemonic = Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_24)
    return str(mnemonic)

######################################################################################
################################ 1. MnemonicManager ##################################
######################################################################################
class MnemonicManager():
    def __init__(self) -> None:
        self.index_key = -1
        pass

    def _is_exist_mnemonic(self) -> bool:
        return MnemonicModel.objects.filter(mnemonic__isnull=False).exists()

    def _read_mnemonic(self) -> str:
        if self._is_exist_mnemonic():
            mnemonics = MnemonicModel.objects.all()
            return mnemonics[0].mnemonic
        else:
            print('-- MnemonicManager >> Failed to read mnemonic --')
            return None

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

    def is_exist_user(self, user_id: int) -> bool:
        return User.objects.filter(user_id=user_id).exists()

    def register_user(self, user_id : int, user_name : str, real_name : str) -> None:
        if self.is_exist_user(user_id):
            print(f"-- UserManager >> {real_name} exist --")

            pass
        else:
            pass
