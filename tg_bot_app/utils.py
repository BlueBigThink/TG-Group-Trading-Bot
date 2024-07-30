from bip_utils import Bip39MnemonicGenerator, Bip39WordsNum
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