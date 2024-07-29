from django.shortcuts import render

def generateMnemonic():
    pass
# from bip44 import Wallet
# from mnemonic import Mnemonic

# # Generate a random mnemonic (seed phrase)
# mnemo = Mnemonic("english")
# seed_phrase = mnemo.generate(strength=128)
# print("Seed Phrase:", seed_phrase)

# # Create a wallet from the seed phrase
# wallet = Wallet(seed_phrase)

# # Generate multiple Ethereum addresses
# number_of_addresses = 5
# for i in range(number_of_addresses):
#     account = wallet.derive_path(f"m/44'/60'/0'/0/{i}")
#     private_key = account.private_key.hex()
#     address = account.address()
#     print(f"Address {i+1}:")
#     print("  Private Key:", private_key)
#     print("  Ethereum Address:", address)

# Explanation
# Mnemonic Seed Phrase: This script generates a mnemonic seed phrase, which is a human-readable form of the seed used to generate the master key of an HD wallet.

# Wallet Creation: We create an HD wallet from the mnemonic using the Wallet class from the bip44 library. This wallet can derive multiple addresses.

# Derivation Path: The path "m/44'/60'/0'/0/{i}" follows the BIP44 standard for Ethereum:

# "44'" is the purpose code for BIP44.
# "60'" is the coin type for Ethereum.
# "0'" is the account number.
# "0" is the external chain (as opposed to the change chain).
# "{i}" allows us to derive different addresses (0, 1, 2, ...).
# Generating Addresses: By iterating over a range, we derive multiple addresses using different indices.
