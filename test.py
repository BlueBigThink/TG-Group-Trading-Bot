from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import transfer, TransferParams
from solana.rpc.api import Client
from solana.transaction import Transaction
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes, Bip39MnemonicGenerator, Bip39WordsNum
from web3 import Web3
import base58
import asyncio
import time
import json

INFURA_ID = "e254d35aa64b4c16816163824d9d5b83"
ROUTER_ADDRESS = '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D'
RPC_URL = f"https://sepolia.infura.io/v3/{INFURA_ID}"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

ROUTER_CONTRACT = None
main_eth_address = ""
main_sol_address = ""
mnemonic = Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_24)
# print('mnemonic', mnemonic)
mnemonic = "daring write latin belt mosquito second carbon mix course gloom human steak"

def get_main_sol_eth_address(mnemonic):
    global main_eth_address, main_sol_address

    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
    
    bip44_eth_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)

    eth_acc = bip44_eth_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)

    main_eth_address = eth_acc.PublicKey().ToAddress()

    bip44_sol_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.SOLANA)

    sol_acc = bip44_sol_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
    sol_private_key = sol_acc.PrivateKey().Raw().ToBytes()
    sol_public_key = sol_acc.PublicKey().RawCompressed().ToBytes()
    sol_keypair = Keypair.from_seed(sol_private_key)

    main_sol_address = sol_keypair.pubkey()

    print(f"main_eth_address: {main_eth_address}")
    print(f"main_sol_address: {main_sol_address}")

def generate_eth_addresses(mnemonic):
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
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

def generate_sol_addresses(mnemonic):
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
    bip44_sol_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.SOLANA)

    sol_acc = bip44_sol_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
    sol_private_key = sol_acc.PrivateKey().Raw().ToBytes()
    sol_public_key = sol_acc.PublicKey().RawCompressed().ToBytes()
    sol_keypair = Keypair.from_seed(sol_private_key)

    print('sol_keypair:', type(sol_keypair))
    print("Address:", sol_keypair.pubkey())
    print("Private Key:", base58.b58encode(sol_keypair.secret() + base58.b58decode(str(sol_keypair.pubkey()))).decode('utf-8'))

    sol_acc1 = bip44_sol_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(1)
    sol_private_key1 = sol_acc1.PrivateKey().Raw().ToBytes()
    sol_public_key1 = sol_acc1.PublicKey().RawCompressed().ToBytes()
    sol_keypair1 = Keypair.from_seed(sol_private_key1)

    print("Address:", sol_keypair1.pubkey())
    print("Private Key:", base58.b58encode(sol_keypair1.secret() + base58.b58decode(str(sol_keypair1.pubkey()))).decode('utf-8'))

def transfer_eth_to_main_address(private_key, public_address):
    global main_eth_address

    balance = w3.eth.get_balance(public_address)
    nonce = w3.eth.get_transaction_count(public_address)
    chain_id = w3.eth.chain_id
    gas_price = w3.eth.gas_price

    tx = ({
        "chainId": chain_id,
        "from": public_address,
        "to": main_eth_address,
        "nonce": nonce,
        "gas": 21000,
        "gasPrice": gas_price,
        "value": balance - gas_price * 21000
    })

    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    send_tx = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = w3.eth.wait_for_transaction_receipt(send_tx)

def transfer_sol_to_main_address(sender_priv_key, sender_pub_key, receiver_pub_key):
    client = Client("https://api.devnet.solana.com")

    sender = Keypair.from_base58_string(sender_priv_key)
    receiver = Pubkey.from_string(receiver_pub_key)

    balance_response = client.get_balance(Pubkey.from_string(sender_pub_key))
    balance_lamports = balance_response.value

    transaction_fee = 5000
    amount = balance_lamports - transaction_fee

    transaction = Transaction()
    transfer_instruction = transfer(
        TransferParams(
            from_pubkey=sender.pubkey(),
            to_pubkey=receiver,
            lamports=amount
        )
    )

    transaction.add(transfer_instruction)

    result = client.send_transaction(transaction, sender)

def get_router_contract() -> None:
    abi = []
    with open("./abi/router_abi.json") as f:
        abi = json.load(f)

    global ROUTER_CONTRACT
    
    ROUTER_CONTRACT = w3.eth.contract(
        address=ROUTER_ADDRESS, abi=abi)

def swap_eth_to_tokens(token_address, owner_prv_key, recipient_address):
    global main_eth_address, ROUTER_CONTRACT

    get_router_contract()
    WETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

    amount_in_wei = w3.to_wei(0.001, 'ether')
    min_tokens_to_receive = 0
    deadline = int(time.time()) + 60 * 20

    path = [
        WETH_ADDRESS,  # ETH
        token_address  # Token
    ]

    nonce = w3.eth.get_transaction_count(main_eth_address)

    transaction = ROUTER_CONTRACT.functions.swapExactETHForTokens(
        min_tokens_to_receive,
        path,
        main_eth_address,
        deadline
    ).buildTransaction({
        'from': main_eth_address,
        'value': amount_in_wei,
        'gas': 200000,
        'gasPrice': w3.to_wei('30', 'gwei'),
        'nonce': nonce
    })

    # Sign the transaction with the private key
    signed_txn = w3.eth.account.sign_transaction(transaction, owner_prv_key)

    # Send the transaction
    txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

    # Wait for the transaction receipt
    receipt = w3.eth.wait_for_transaction_receipt(txn_hash)

def swap_token_to_eth(token_address, owner_prv_key, recipient_address):
    global main_eth_address, ROUTER_CONTRACT

    get_router_contract()
    WETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

    amount_in_tokens = w3.to_wei(100, 'ether')
    min_eth_to_receive = 0
    deadline = int(time.time()) + 60 * 20

    path = [
        token_address,
        WETH_ADDRESS
    ]

    token_abi = []
    with open("./abi/erc20_abi.json") as f:
        token_abi = json.load(f)

    token_contract = w3.eth.contract(address=token_address, abi=token_abi)
    approve_txn = token_contract.functions.approve(ROUTER_ADDRESS, amount_in_tokens).buildTransaction({
        'from': main_eth_address,
        'gas': 200000,
        'gasPrice': w3.to_wei('30', 'gwei'),
        'nonce': w3.eth.get_transaction_count(main_eth_address),
    })

    # Sign and send the approval transaction
    signed_approve_txn = w3.eth.account.sign_transaction(approve_txn, owner_prv_key)
    approve_txn_hash = w3.eth.send_raw_transaction(signed_approve_txn.rawTransaction)
    approve_receipt = w3.eth.wait_for_transaction_receipt(approve_txn_hash)
    print(f'Approval transaction hash: {approve_receipt}')

    nonce = w3.eth.get_transaction_count(main_eth_address)
    swap_txn = ROUTER_CONTRACT.functions.swapExactTokensForETH(
        amount_in_tokens,
        min_eth_to_receive,
        path,
        main_eth_address,
        deadline
    ).buildTransaction({
        'from': main_eth_address,
        'value': amount_in_wei,
        'gas': 200000,
        'gasPrice': w3.to_wei('30', 'gwei'),
        'nonce': nonce
    })

    # Sign and send the swap transaction
    signed_swap_txn = w3.eth.account.sign_transaction(swap_txn, owner_prv_key)
    swap_txn_hash = w3.eth.send_raw_transaction(signed_swap_txn.rawTransaction)

    # Wait for the swap transaction receipt
    swap_receipt = w3.eth.wait_for_transaction_receipt(swap_txn_hash)
    print(f'Swap transaction successful with hash: {swap_receipt}')

def get_reserver_amount(token_address):
    infura_url = f'https://mainnet.infura.io/v3/{INFURA_ID}'
    web3 = Web3(Web3.HTTPProvider(infura_url))

    UNISWAP_FACTORY_ADDRESS = '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f'
    uniswap_factory_abi = [
        {
            "constant": True,
            "inputs": [
                {
                    "internalType": "address",
                    "name": "",
                    "type": "address"
                },
                {
                    "internalType": "address",
                    "name": "",
                    "type": "address"
                }
            ],
            "name": "getPair",
            "outputs": [
                {
                    "internalType": "address",
                    "name": "",
                    "type": "address"
                }
            ],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        }
    ]

    factory_contract = web3.eth.contract(address=UNISWAP_FACTORY_ADDRESS, abi=uniswap_factory_abi)

    weth_address = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'  # Replace with the other token address (e.g., WETH)

    # Get the pair address
    pair_address = factory_contract.functions.getPair(token_address, weth_address).call()

    print('PAIR ADDRESS: ', pair_address)

    PAIR_ABI = []
    with open("./abi/pair_abi.json") as f:
        PAIR_ABI = json.load(f)
    pair_contract = web3.eth.contract(address=pair_address, abi=PAIR_ABI)

    # Get the reserves
    reserves = pair_contract.functions.getReserves().call()

    # Extract liquidity
    token_liquidity = reserves[0]
    weth_liquidity = reserves[1]

    print(f'Token Liquidity: {token_liquidity}')
    print(f'WETH Liquidity: {weth_liquidity}')

# get_main_sol_eth_address(mnemonic)

get_reserver_amount('0x393Bf304dD474f48210f5cE741F19A2a851703Ca')
# transfer_sol_to_main_address("54aK7GaZbYSJ6NKgKfcWbQ8LgfbcPMS8Z5SccjW1j1ru9ygzGexsHVL7aP2iDhTs2gMRhnLDcsirVkYm3ZgaXx47", "84Qv3WP6fz2WkzWCJzhoCUVgBUnZmJftbQwv8eQnFTpb", "WQSy7QTaG44zjnrooqvAxk71RALPYwJpnwtQaeK2D2P")
# transfer_eth_to_main_address('0d11dbfdb3e6b159ebba2d82d9c886e49c503dc9a0ad2d46b40c42e8aa0669e2', '0x1Dc2F5DF4FB2280bCe20eb33d36d95942A0b5FBD')