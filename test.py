# from solders.keypair import Keypair
# from mnemonic import Mnemonic
# import base58

# mnemo = Mnemonic("english")
# seed = mnemo.to_seed("pill tomorrow foster begin walnut borrow virtual kick shift mutual shoe scatter")
# print(len(seed[:32]))
# account = Keypair.from_seed(seed[:32])
# privateKey = base58.b58encode(account.secret() + base58.b58decode(str(account.pubkey()))).decode('utf-8')

# print(account.pubkey(), privateKey)

from solders.keypair import Keypair
from solana.rpc.api import Client
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes, Bip39MnemonicGenerator, Bip39WordsNum
import base58

mnemonic = Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_24)

seed_bytes = Bip39SeedGenerator(mnemonic).Generate()

##############################################################################################
bip44_eth_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)

eth_acc = bip44_eth_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
eth_address = eth_acc.PublicKey().ToAddress()
eth_private_key = eth_acc.PrivateKey().Raw().ToHex()

eth_acc1 = bip44_eth_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(1)
eth_address1 = eth_acc1.PublicKey().ToAddress()
eth_private_key1 = eth_acc1.PrivateKey().Raw().ToHex()

print("Ethereum Address:", eth_address)
print("Ethereum Private Key:", eth_private_key)
print("Ethereum Address:", eth_address1)
print("Ethereum Private Key:", eth_private_key1)
##############################################################################################
bip44_sol_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.SOLANA)

sol_acc = bip44_sol_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
sol_private_key = sol_acc.PrivateKey().Raw().ToBytes()
sol_public_key = sol_acc.PublicKey().RawCompressed().ToBytes()
sol_keypair = Keypair.from_seed(sol_private_key)

print("Address:", sol_keypair.pubkey())
print("Private Key:", base58.b58encode(sol_keypair.secret() + base58.b58decode(str(sol_keypair.pubkey()))).decode('utf-8'))

sol_acc1 = bip44_sol_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(1)
sol_private_key1 = sol_acc1.PrivateKey().Raw().ToBytes()
sol_public_key1 = sol_acc1.PublicKey().RawCompressed().ToBytes()
sol_keypair1 = Keypair.from_seed(sol_private_key1)

print("Address:", sol_keypair1.pubkey())
print("Private Key:", base58.b58encode(sol_keypair1.secret() + base58.b58decode(str(sol_keypair1.pubkey()))).decode('utf-8'))
