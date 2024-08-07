# import base58
# import base64
# import json

# from solders import message
# from solders.pubkey import Pubkey
# from solders.keypair import Keypair
# from solders.transaction import VersionedTransaction

# from solana.rpc.types import TxOpts
# from solana.rpc.async_api import AsyncClient
# from solana.rpc.commitment import Processed

# from jupiter_python_sdk.jupiter import Jupiter, Jupiter_DCA
# import asyncio

# RPC_URL = "https://api.devnet.solana.com"
# # RPC_URL = "https://api.mainnet-beta.solana.com"

# private_key = Keypair.from_bytes(base58.b58decode("2JNKp9G6aT3wmqr2xu3nRs9bQHNuvcrnVVJtBzqH58WPvVTS4Cb9K3tHGhhKa5GrudP9pprHRELfwYmX2b4jetup"))
# async_client = AsyncClient(RPC_URL)
# jupiter = Jupiter(
#     async_client=async_client,
#     keypair=private_key,
#     quote_api_url="https://quote-api.jup.ag/v6/quote?",
#     swap_api_url="https://quote-api.jup.ag/v6/swap",
#     open_order_api_url="https://jup.ag/api/limit/v1/createOrder",
#     cancel_orders_api_url="https://jup.ag/api/limit/v1/cancelOrders",
#     query_open_orders_api_url="https://jup.ag/api/limit/v1/openOrders?wallet=",
#     query_order_history_api_url="https://jup.ag/api/limit/v1/orderHistory",
#     query_trade_history_api_url="https://jup.ag/api/limit/v1/tradeHistory"
# )

# async def swap() -> None :
#     transaction_data = await jupiter.swap(
#         input_mint="So11111111111111111111111111111111111111112",
#         output_mint="DtR4D9FtVoTX2569gaL837ZgrB6wNjj6tkmnX9Rdk9B2",
#         amount=5_000_000,
#         slippage_bps=50,
#     )
#     # Returns str: serialized transactions to execute the swap.

#     raw_transaction = VersionedTransaction.from_bytes(base64.b64decode(transaction_data))
#     signature = private_key.sign_message(message.to_bytes_versioned(raw_transaction.message))
#     signed_txn = VersionedTransaction.populate(raw_transaction.message, [signature])
#     opts = TxOpts(skip_preflight=False, preflight_commitment=Processed)
#     result = await async_client.send_raw_transaction(txn=bytes(signed_txn), opts=opts)
#     transaction_id = json.loads(result.to_json())['result']
#     print(f"Transaction sent: https://explorer.solana.com/tx/{transaction_id}")

# async def swap_pair() -> None :
#     pair_data = await jupiter.get_swap_pairs("So11111111111111111111111111111111111111112", "7gbEP2TAy5wM3TmMp5utCrRvdJ3FFqYjgN5KDpXiWPmo")
#     print(pair_data)

# asyncio.run(swap_pair())
from uniswap import Uniswap

address = "0xf900f49e59Ae5d787E7E562D2B4f2E819a1D82af" 
private_key = "a756f56503643e24a043d9c63767169cece8f0011f6d215a7c2496c224822af7"
version = 2

INFURA_ID = "e254d35aa64b4c16816163824d9d5b83"
# RPC_URL = f'https://mainnet.infura.io/v3/{INFURA_ID}'
RPC_URL = f"https://sepolia.infura.io/v3/{INFURA_ID}"
UNISWAP_ROUTER_ADDRESS = '0xC532a74256D3Db42D0Bf7a0400fEFDbad7694008'
UNISWAP_FACTORY_ADDRESS = '0x7E0987E5b3a30e3f2828572Bb659A548460a3003'
uniswap = Uniswap(address=address, private_key=private_key, version=version, provider=RPC_URL, router_contract_addr=UNISWAP_ROUTER_ADDRESS, factory_contract_addr=UNISWAP_FACTORY_ADDRESS)

def get_current_slippage(token_address : str) -> float:
    WETH = "0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9"
    token_amount = uniswap.get_price_input(WETH, token_address, 0.01*10**18)

    print(token_amount)

get_current_slippage("0x8f785c1165759684B3c638cC2fecf29c335C4e4c")