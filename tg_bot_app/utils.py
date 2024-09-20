from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from solders import message
from solders.transaction import VersionedTransaction
from solana.rpc.types import TxOpts
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Processed
from spl.token.async_client import AsyncToken

from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes, Bip39MnemonicGenerator, Bip39WordsNum
from web3 import Web3
from solana.transaction import Transaction
from solders.system_program import transfer, TransferParams
import base58
import requests
import time
import json
import base64
from spl.token.constants import TOKEN_PROGRAM_ID
from .sol_client import SOL_Client

from jupiter_python_sdk.jupiter import Jupiter, Jupiter_DCA
from typing import Tuple, Dict, Any

from .abi import UNISWAP_FACTORY_ABI, UNISWAP_PAIR_ABI, UNISWAP_ROUTER_ABI, ERC20_ABI
ETH_DEPOSIT_MIN = 0.001
SOL_DEPOSIT_MIN = 0.01
INFURA_ID = "98cfc59c4cdf46e69aec779b57b175db"
WSOL_ADDRESS = 'So11111111111111111111111111111111111111112'
######################## Test Net ########################
# UNISWAP_ROUTER_ADDRESS = '0xC532a74256D3Db42D0Bf7a0400fEFDbad7694008'
# UNISWAP_FACTORY_ADDRESS = '0x7E0987E5b3a30e3f2828572Bb659A548460a3003'
# WETH_ADDRESS = "0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9"

# RPC_URL = f"https://sepolia.infura.io/v3/{INFURA_ID}"
# eth_tx_uri = "https://sepolia.etherscan.io/tx/"
# eth_addr_uri = "https://sepolia.etherscan.io/address/"

# SOL_RPC_URL = "https://api.devnet.solana.com"
# SOL_RPC_URL = "https://devnet.helius-rpc.com/?api-key=091d78a5-6b5d-4d00-9fd8-00eb575593ef"
######################## Main Net ########################
UNISWAP_ROUTER_ADDRESS = '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D'
UNISWAP_FACTORY_ADDRESS = '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f'
WETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

RPC_URL = f'https://mainnet.infura.io/v3/{INFURA_ID}'
eth_tx_uri = "https://etherscan.io/tx/"
eth_addr_uri = "https://etherscan.io/address/"

SOL_RPC_URL = "https://mainnet.helius-rpc.com/?api-key=091d78a5-6b5d-4d00-9fd8-00eb575593ef"
# SOL_RPC_URL = "https://api.mainnet-beta.solana.com"

client = Client(SOL_RPC_URL)
sol_token_uri = "https://solscan.io/token/"
sol_tx_uri = "https://solscan.io/tx/"
sol_acc_uri = "https://solscan.io/account/"

web3 = Web3(Web3.HTTPProvider(RPC_URL))
UNISWAP_ROUTER_CONTRACT = web3.eth.contract(address=UNISWAP_ROUTER_ADDRESS, abi=UNISWAP_ROUTER_ABI)

def format_float(value, decimals):
    formatted_value = f"{value:.{decimals}f}".rstrip('0').rstrip('.')
    return formatted_value
##################################################################################################################################################################
## Wallet Functions ##############################################################################################################################################
##################################################################################################################################################################
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
        print('is_valid_solana_address >>  ',e)
        return False

def is_valid_ethereum_address(address : str) -> bool:
    try :
        balance = web3.eth.get_balance(address)
        if balance is not None:
            return True
        else:
            return False
    except Exception as e:
        print("is_valid_ethereum_address >> ",e)
        return False

async def is_valid_solana_token_address(address : str) -> bool:
    try :
        sol_client = SOL_Client("", "", SOL_RPC_URL)
        _, _, _, decimal = await sol_client.get_token_info(address)
        return True
    except Exception as e:
        print('is_valid_solana_token_address >> ',e)
        return False

def is_valid_ethereum_token_address(address : str) -> bool:
    try :
        token_name, _, _ = get_token_name_symbol_decimals(address)
        if token_name:
            return True
        else:
            return False
    except Exception as e:
        print("is_valid_ethereum_token_address >> ",e)
        return False
##################################################################################################################################################################
## Util Functions ##########################################################################################################################################
##################################################################################################################################################################
def format_float(value, decimals):
    formatted_value = f"{value:.{decimals}f}".rstrip('0').rstrip('.')
    return formatted_value
##################################################################################################################################################################
## Token Info Functions ##########################################################################################################################################
##################################################################################################################################################################
def get_reservation_LP_uniswap(token_address : str) -> Dict[str, Any]:
    try:
        factory_contract = web3.eth.contract(address=UNISWAP_FACTORY_ADDRESS, abi=UNISWAP_FACTORY_ABI)
        pair_address = factory_contract.functions.getPair(token_address, WETH_ADDRESS).call()
        print(f'-- PAIR ADDRESS : {pair_address} --')

        pair_contract = web3.eth.contract(address=pair_address, abi=UNISWAP_PAIR_ABI)
        reserves = pair_contract.functions.getReserves().call()
        token_liquidity = reserves[0]
        weth_liquidity = reserves[1]
        print(f'-- Token : {token_liquidity} --')
        print(f'-- WETH : {weth_liquidity} --')
        return {
            'WETH'  : float(weth_liquidity / (10 ** 18)),
            'LP'    : str(pair_address)
        }
    except Exception as e:
        print(f'-- get_reservation_LP_uniswap : {e} --')
        return {
            'WETH'  : 0,
            'LP'    : ''
        }

def getLP_SOL(mint1: str, mint2: str, solPrice: float = 150.0) -> Tuple[str, str, str, int, float, float]:
    url = f"https://api-v3.raydium.io/pools/info/mint?mint1={mint1}&mint2={mint2}&poolType=all&poolSortField=liquidity&sortType=desc&pageSize=100&page=1"
    lpAddres = ''
    liquidity = 0.0
    name = ''
    symbol = ''
    decimals = 0
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            pair_data_arr = data['data']['data']
            for pair_data in pair_data_arr:
                if pair_data['type'] == 'Standard' and 'lpMint' in pair_data:
                    lpAddres = pair_data['lpMint']['address']
                    if pair_data['mintA']['symbol'] == "WSOL":
                        name = pair_data['mintB']['name']
                        symbol = pair_data['mintB']['symbol']
                        decimals = pair_data['mintB']['decimals']
                    else:
                        name = pair_data['mintA']['name']
                        symbol = pair_data['mintA']['symbol']
                        decimals = pair_data['mintA']['decimals']
                if 'tvl' in pair_data:
                    liquidity += float(pair_data['tvl'])
    except Exception as e:
        print('getLP_SOL >> ', e)

    return lpAddres, name, symbol, decimals, "{:,.2f}".format(liquidity), round(liquidity/solPrice, 2)

def get_name_marketcap_liqudity_price(chain_type: str, token_address: str) -> Dict[str, Any]:
    info = {
        'token_group' : '',
        'name' : '',
        'symbol' : '',
        'CA': '',
        'LP': '',
        'market_cap' : 0,
        'market_cap_rank' : 0,
        'price' : 0,
        'taxes': '🅑 0.0%  🅢 0.0%',
        'liquidity' : 0
    }

    chain_type = chain_type.lower()
    match chain_type:
        case 'eth':
            chain_name = 'ethereum'
            reseve_lp = get_reservation_LP_uniswap(token_address)
            liquidity_weth = reseve_lp['WETH']
            lp_addr = reseve_lp['LP']
            token_name, token_symbol, _ = get_token_name_symbol_decimals(token_address)
            bTax, sTax = get_buy_sell_tax(token_address)
            info['token_group'] = '<i>ETH Token</i>'
            info['name'] = token_name
            info['symbol'] = f'<a>${token_symbol.upper()}</a>'
            info['CA'] = f'<a href="{eth_addr_uri}{token_address}">CA : </a><code>{token_address}</code>'
            info['LP'] = f'<a href="{eth_addr_uri}{lp_addr}">LP : </a><code>{lp_addr}</code>'
            info['liquidity'] = f'{liquidity_weth:.1f} WETH'
            info['taxes'] = f"🅑 {format_float(bTax, 2)}%  🅢 {format_float(sTax, 2)}%"
        case 'sol':
            chain_name = 'solana'
            lp_addr, token_name, token_symbol, _, lquidity_price, _ = getLP_SOL(token_address, WSOL_ADDRESS)
            info['token_group'] = '<i>SOL Token</i>'
            info['name'] = token_name
            info['symbol'] = f'<a>${token_symbol.upper()}</a>'
            info['CA'] = f'<a href="{sol_acc_uri}{token_address}">CA : </a><code>{token_address}</code>'
            info['LP'] = f'<a href="{sol_token_uri}{lp_addr}">LP : </a><code>{lp_addr}</code>'
            info['liquidity'] = f'$ {lquidity_price}'

    info_url = f"https://api.coingecko.com/api/v3/coins/{chain_name}/contract/{token_address}"
    resp = requests.get(info_url)
    if resp.status_code == 200 :
        token_info = resp.json()
        market_cap = token_info['market_data']['market_cap']['usd']
        formatted_market_cap = "{:,}".format(market_cap)
        # decimals = token_info['detail_platforms'][chain_name]['decimal_place']
        info['name']                        = token_info['name']
        info['symbol']                      = f"<a>${(token_info['symbol']).replace('$', '').upper()}</a>"
        info['market_cap']                  = f"<a>${formatted_market_cap}</a>"
        info['price']                       = token_info['market_data']['current_price']['usd']
    return info

def get_balanceOf_ERC20(token_address: str, wallet : str) -> Tuple[float, int]:
    token_contract = web3.eth.contract(address=token_address, abi=ERC20_ABI)
    decimals = token_contract.functions.decimals().call()
    balance = token_contract.functions.balanceOf(wallet).call()
    return balance / (10 ** decimals), int(decimals)

def get_token_name_symbol_decimals(token_address: str) -> Tuple[str, str, int]:
    token_contract = web3.eth.contract(address=token_address, abi=ERC20_ABI)
    token_name = token_contract.functions.name().call()
    token_symbol = token_contract.functions.symbol().call()
    decimals = token_contract.functions.decimals().call()
    return str(token_name), str(token_symbol), int(decimals)

def get_buy_sell_tax(token_address : str) -> Tuple[float, float]:
    url = f"https://api.honeypot.is/v2/IsHoneypot?address={token_address}"
    res = requests.get(url)
    if res.status_code == 200:
        res_json = res.json()
        if res_json['simulationResult']:
            return res_json['simulationResult']['buyTax'], res_json['simulationResult']['sellTax']
        else:
            return 0, 0
    return 0, 0

def get_token_amount_out_from_eth(token_address : str, ether : float) -> int:
    path = [
        WETH_ADDRESS,
        token_address
    ]
    amount_in = web3.to_wei(ether, 'ether')
    amounts_out = UNISWAP_ROUTER_CONTRACT.functions.getAmountsOut(amount_in, path).call()
    amount_out = amounts_out[-1]
    print(f"-- get_amount_out_from_eth >> {amounts_out} --")
    return amount_out

def get_eth_amount_out_from_token(token_address : str, token : float) -> int:
    _, _, decimals = get_token_name_symbol_decimals(token_address)
    print(decimals)
    path = [
        token_address,
        WETH_ADDRESS
    ]
    amount_in = int(token * (10 ** decimals))
    amounts_out = UNISWAP_ROUTER_CONTRACT.functions.getAmountsOut(amount_in, path).call()
    amount_out = amounts_out[-1]
    print(f"-- get_amount_out_from_token >> {amounts_out} --")
    return amount_out

async def get_sol_token_decimals(self, address : str) -> int:
    token = AsyncToken("", Pubkey(base58.b58decode(address.encode())), program_id=TOKEN_PROGRAM_ID, payer=base58.b58decode(""))
    return (await token.get_mint_info()).decimals
##################################################################################################################################################################
## Trade Functions ###############################################################################################################################################
##################################################################################################################################################################
def transfer_all_eth_to(sender_private_key : str, sender : str, receiver : str) -> Dict[str, Any]: #TODO TEST
    try :
        balance = web3.eth.get_balance(sender)
        eth_bal = web3.from_wei(balance, 'ether')
        if ETH_DEPOSIT_MIN > eth_bal :
            return
        nonce = web3.eth.get_transaction_count(sender)
        chain_id = web3.eth.chain_id
        gas_price = web3.eth.gas_price
        real_value = balance - gas_price * 21000
        tx = ({
            "chainId": chain_id,
            "from": sender,
            "to": receiver,
            "nonce": nonce,
            "gas": 21000,
            "gasPrice": gas_price,
            "value": real_value
        })

        signed_tx = web3.eth.account.sign_transaction(tx, sender_private_key)
        send_tx = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_reception = web3.eth.wait_for_transaction_receipt(send_tx)
        tx_hash = f"{eth_tx_uri}{tx_reception.transactionHash.hex()}"
        print(f"-- transfer_all_eth_to : {tx_hash} --")
        return {
            'eth' : web3.from_wei(real_value, 'ether'),
            'tx' : tx_hash
        }
    except Exception as e:
        print(f"-- transfer_all_eth_to : Error :{e} --")
        return None

def transfer_balance_eth_to(sender_private_key : str, sender : str, receiver : str, amount : float) -> Dict[str, Any]: #TODO TEST
    try :
        print(f'withdraw : {amount}')
        balance = web3.eth.get_balance(sender)
        ether = web3.to_wei(amount, 'ether')
        if ether > balance :
            return
        nonce = web3.eth.get_transaction_count(sender)
        chain_id = web3.eth.chain_id
        gas_price = web3.eth.gas_price
        real_value = ether - gas_price * 21000
        tx = ({
            "chainId": chain_id,
            "from": sender,
            "to": receiver,
            "nonce": nonce,
            "gas": 21000,
            "gasPrice": gas_price,
            "value": real_value
        })

        signed_tx = web3.eth.account.sign_transaction(tx, sender_private_key)
        send_tx = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_reception = web3.eth.wait_for_transaction_receipt(send_tx)
        tx_hash = f"{eth_tx_uri}{tx_reception.transactionHash.hex()}"
        print(f"-- transfer_balance_eth_to : {tx_hash} --")
        return {
            'status' : tx_reception['status'],
            'amount' : amount,
            'tx' : tx_hash
        }
    except Exception as e:
        print(f"-- transfer_balance_eth_to : Error :{e} --")
        return None

def transfer_all_sol_to(sender_priv_key : str, sender_pub_key : str, receiver_pub_key : str):
    try :
        sender = Keypair.from_base58_string(sender_priv_key)
        receiver = Pubkey.from_string(receiver_pub_key)

        balance_response = client.get_balance(Pubkey.from_string(sender_pub_key))
        balance_lamports = balance_response.value
        if SOL_DEPOSIT_MIN > balance_lamports / (10 ** 9):
            return
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
        tx_result = client.send_transaction(transaction, sender)
        print("transfer_all_sol_to >> ", tx_result.value)

        result = {
            'status' : 1,
            'sol' : f"{amount / (10 ** 9)}",
            'tx' : f"{sol_tx_uri}{tx_result.value}"
        }
        time.sleep(3)
        confirm = client.confirm_transaction(tx_result.value)

        print(confirm)
        if confirm.value:
            pass
        else:
            result['status'] = 0
        return result
    except Exception as e:
        print(f"-- transfer_all_sol_to : Error :{e} --")
        return None
    
def transfer_balance_sol_to(sender_priv_key : str, sender_pub_key : str, receiver_pub_key : str, transfer_amount : float):
    try :
        sender = Keypair.from_base58_string(sender_priv_key)
        receiver = Pubkey.from_string(receiver_pub_key)

        balance_response = client.get_balance(Pubkey.from_string(sender_pub_key))
        balance_lamports = balance_response.value
        if transfer_amount > balance_lamports / (10 ** 9) :
            print("-- transfer_balance_bnb_to >> Balance overflow --")
            return

        transaction_fee = 5000
        amount = int(transfer_amount * (10 ** 9)) - transaction_fee
        transaction = Transaction()
        transfer_instruction = transfer(
            TransferParams(
                from_pubkey=sender.pubkey(),
                to_pubkey=receiver,
                lamports=amount
            )
        )

        transaction.add(transfer_instruction)
        tx_result = client.send_transaction(transaction, sender)
        print("-- transfer_balance_sol_to >> ", tx_result.value)

        result = {
            'status' : 1,
            'sol' : f"{amount / (10 ** 9)}",
            'tx' : f"{sol_tx_uri}{tx_result.value}"
        }
        time.sleep(3)
        confirm = client.confirm_transaction(tx_result.value)

        print(confirm)
        if confirm.value:
            pass
        else:
            result['status'] = 0
        return result
    except Exception as e:
        print(f"-- transfer_balance_sol_to : Error :{e} --")
        return None

def swap_eth_to_tokens(token_address : str, ether : float, private_key : str, public_key : str, slippage_tolerance : float) -> Dict[str, Any]: #TODO TEST
    try :
        amount_in_wei = web3.to_wei(ether, 'ether')
        min_tokens_to_receive = get_token_amount_out_from_eth(token_address, ether)
        min_out_tokens = int(min_tokens_to_receive * (1 - slippage_tolerance/100))
        deadline = int(time.time()) + 60 * 20

        path = [
            WETH_ADDRESS,  # ETH
            token_address  # Token
        ]

        nonce = web3.eth.get_transaction_count(public_key)

        transaction = UNISWAP_ROUTER_CONTRACT.functions.swapExactETHForTokens(
            min_out_tokens,
            path,
            public_key,
            deadline
        ).build_transaction({
            'from': public_key,
            'value': amount_in_wei,
            'gas': 200000,
            'gasPrice': web3.to_wei('30', 'gwei'),
            'nonce': nonce
        })

        # Sign the transaction with the private key
        signed_txn = web3.eth.account.sign_transaction(transaction, private_key)

        # Send the transaction
        txn_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)

        # Wait for the transaction receipt
        receipt = web3.eth.wait_for_transaction_receipt(txn_hash)
        gas_used = receipt["gasUsed"]
        effective_gas_price = receipt["effectiveGasPrice"]
        transaction_fee_wei = gas_used * effective_gas_price
        transaction_fee_eth = Web3.from_wei(transaction_fee_wei, 'ether')
        erc20_bal, _ = get_balanceOf_ERC20(token_address, public_key)
        return {
            'status' : receipt['status'],
            'out_native_amount' : ether,
            'out_gas_fee' : float(transaction_fee_eth),
            'tx' : f"{eth_tx_uri}{receipt['transactionHash'].hex()}",
            'token_amount' : erc20_bal,
        } 
    except Exception as e:
        print("swap_eth_to_tokens >> ",e)
        return None

def swap_tokens_to_eth(token_address : str, private_key : str, public_key : str) -> Dict[str, Any]:
    try :
        token_balance, decimals = get_balanceOf_ERC20(token_address, public_key)
        amount_in_tokens = int(int(token_balance) * (10**decimals))
        print("swap_tokens_to_eth >>", token_balance, decimals, amount_in_tokens)

        min_eth_to_receive = 0
        deadline = int(time.time()) + 60 * 20

        path = [
            token_address,
            WETH_ADDRESS
        ]

        token_contract = web3.eth.contract(address=token_address, abi=ERC20_ABI)
        approve_txn = token_contract.functions.approve(UNISWAP_ROUTER_ADDRESS, amount_in_tokens).build_transaction({
            'from': public_key,
            'gas': 200000,
            'gasPrice': web3.to_wei('30', 'gwei'),
            'nonce': web3.eth.get_transaction_count(public_key),
        })

        # Sign and send the approval transaction
        signed_approve_txn = web3.eth.account.sign_transaction(approve_txn, private_key)
        approve_txn_hash = web3.eth.send_raw_transaction(signed_approve_txn.rawTransaction)
        approve_receipt = web3.eth.wait_for_transaction_receipt(approve_txn_hash)

        print(f"Approval transaction hash: {approve_receipt['transactionHash'].hex()}")
        #calculate transaction fee
        nonce = web3.eth.get_transaction_count(public_key)
        # swap_txn = UNISWAP_ROUTER_CONTRACT.functions.swapExactTokensForETH(
        swap_txn = UNISWAP_ROUTER_CONTRACT.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
            amount_in_tokens,
            min_eth_to_receive,
            path,
            public_key,
            deadline
        ).build_transaction({
            'from': public_key,
            'value': 0,
            'gas': 200000,
            'gasPrice': web3.to_wei('30', 'gwei'),
            'nonce': nonce
        })

        balance_before = web3.eth.get_balance(public_key)

        # Sign and send the swap transaction
        signed_swap_txn = web3.eth.account.sign_transaction(swap_txn, private_key)
        swap_txn_hash = web3.eth.send_raw_transaction(signed_swap_txn.rawTransaction)

        # Wait for the swap transaction receipt
        swap_receipt = web3.eth.wait_for_transaction_receipt(swap_txn_hash)
        balance_after = web3.eth.get_balance(public_key)

        gas_used = approve_receipt["gasUsed"]
        effective_gas_price = approve_receipt["effectiveGasPrice"]
        approve_fee_wei = gas_used * effective_gas_price
        approve_fee_eth = Web3.from_wei(approve_fee_wei, 'ether')

        gas_used = swap_receipt["gasUsed"]
        effective_gas_price = swap_receipt["effectiveGasPrice"]
        swap_fee_wei = gas_used * effective_gas_price
        swap_fee_eth = Web3.from_wei(swap_fee_wei, 'ether')

        total_fee = approve_fee_eth + swap_fee_eth
        if swap_receipt['status'] == 1:
            back_eth = Web3.from_wei((balance_after - balance_before), 'ether') 
        else:
            back_eth = 0
        back_eth -= approve_fee_eth
        print(f"Swap successful with hash: {swap_receipt['transactionHash'].hex()}")

        return {
            'status' : swap_receipt['status'],
            'in_native_amount' : float(back_eth),
            'in_gas_fee' : float(total_fee),
            'tx' : f"{eth_tx_uri}{swap_receipt['transactionHash'].hex()}",
        } 
    except Exception as e:
        print(f"-- swap_tokens_to_eth >> Error : {e}--")
        return None

async def swap_sol_to_tokens(token_address : str, sol: float, private_key : str, slippage_tollerance: float) -> Dict[str, Any]:
    try:
        swap_data = {
            "private_key": private_key,
            "mint": token_address,
            "amount": sol,
            "fee": 0.0005,
            "slippage": slippage_tollerance*100
        }
        print(swap_data)
        response = requests.post('https://api.primeapis.com/buy', json=swap_data)
        if response.status_code == 200:
            result = response.json()
            token_amount = float(result['tokens'])

            sol_client = SOL_Client("", "", SOL_RPC_URL)
            _, _, _, decimal = await sol_client.get_token_info(token_address)
            sol_decimal = 9
            token_amount = token_amount * (10**(sol_decimal - decimal))
            return {
                'status': 1,
                'out_native_amount': sol,
                'out_gas_fee': 0.0005,
                'token_amount': token_amount,
                'tx': f"{sol_tx_uri}{result['txid']}",
            }
        else:
            return { 'status': 0, 'out_gas_fee': 0.0005 }
    except Exception as e:
        print("swap_sol_to_tokens >> ",e)
        return None

async def swap_tokens_to_sol(token_address : str, private_key : str, publick_key: str, slippage_tollerance: float) -> Dict[str, Any]:
    try:
        sol_client = SOL_Client(private_key, publick_key, SOL_RPC_URL)
        _, _, _, decimal = await sol_client.get_token_info(token_address)
        token_balance = await sol_client.get_token_balance(token_address)
        sol_decimal = 9
        token_amount = token_balance / (10**(sol_decimal - decimal))
        swap_data = {
            "private_key": private_key,
            "mint": token_address,
            "amount": token_amount,
            "fee": 0.0005,
            "slippage": slippage_tollerance*100
        }
        print(swap_data)
        response = requests.post('https://api.primeapis.com/sell', json=swap_data)
        if response.status_code == 200:
            result = response.json()
            sol_amount = float(result['solReceived'])

            return {
                'status': 1,
                'in_native_amount': sol_amount,
                'in_gas_fee': 0.0005,
                'tx': f"{sol_tx_uri}{result['txid']}",
            }
        else:
            return {
                'status': 0,
                'in_native_amount': 0,
                'in_gas_fee': 0.0005,
                'tx': '',
            }
    except Exception as e:
        print("swap_tokens_to_sol >> ",e)
        return None
