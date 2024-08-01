from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes, Bip39MnemonicGenerator, Bip39WordsNum
from web3 import Web3
import base58
from typing import Tuple

INFURA_ID = "e254d35aa64b4c16816163824d9d5b83"
RPC_URL = f"https://sepolia.infura.io/v3/{INFURA_ID}"
w3 = Web3(Web3.HTTPProvider(RPC_URL))
client = Client("https://api.devnet.solana.com")

def generate_wallet_ETH(mnemonic : str, index : int) -> Tuple[str, str]:
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
    bip44_eth_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)

    eth_acc = bip44_eth_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(index)
    eth_address = eth_acc.PublicKey().ToAddress()
    eth_private_key = eth_acc.PrivateKey().Raw().ToHex()

    print(f"-- Utils >> Ethereum Address : {eth_address} --")
    print("-- Utils >> Ethereum Private Key Created --")

    return eth_private_key, eth_address

def generate_wallet_SOL(mnemonic : str, index : int) -> Tuple[str, str]:
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
    bip44_sol_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.SOLANA)

    sol_acc = bip44_sol_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(index)
    sol_private_key = sol_acc.PrivateKey().Raw().ToBytes()
    sol_keypair = Keypair.from_seed(sol_private_key)

    sol_address = sol_keypair.pubkey()
    sol_private_key = base58.b58encode(sol_keypair.secret() + base58.b58decode(str(sol_keypair.pubkey()))).decode('utf-8')
    
    print(f"-- Utils >> Solana Address : {sol_address} --")
    print("-- Utils >> Solana Private Key Created --" )

    return sol_private_key, sol_address

def generate_mnemonic() -> str:
    mnemonic = Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_24)
    return str(mnemonic)

def is_valid_solana_address(address : str) -> bool:
    try :
        balance_response = client.get_balance(Pubkey.from_string(address))
        balance_lamports = balance_response.value

        if balance_lamports is not None:
            return True
        else:
            return False
    except Exception as e:
        return False

def is_valid_ethereum_address(address : str) -> bool:
    try :
        balance = w3.eth.get_balance(address)
        if balance is not None:
            return True
        else:
            return False
    except Exception as e:
        return False