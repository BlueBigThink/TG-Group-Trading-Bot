import base58
import base64
import json

from solders import message
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction

from solana.rpc.types import TxOpts
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Processed

from jupiter_python_sdk.jupiter import Jupiter, Jupiter_DCA
import asyncio

RPC_URL = "https://api.devnet.solana.com"
# RPC_URL = "https://api.mainnet-beta.solana.com"

private_key = Keypair.from_bytes(base58.b58decode("2JNKp9G6aT3wmqr2xu3nRs9bQHNuvcrnVVJtBzqH58WPvVTS4Cb9K3tHGhhKa5GrudP9pprHRELfwYmX2b4jetup"))
async_client = AsyncClient(RPC_URL)
jupiter = Jupiter(
    async_client=async_client,
    keypair=private_key,
    quote_api_url="https://quote-api.jup.ag/v6/quote?",
    swap_api_url="https://quote-api.jup.ag/v6/swap",
    open_order_api_url="https://jup.ag/api/limit/v1/createOrder",
    cancel_orders_api_url="https://jup.ag/api/limit/v1/cancelOrders",
    query_open_orders_api_url="https://jup.ag/api/limit/v1/openOrders?wallet=",
    query_order_history_api_url="https://jup.ag/api/limit/v1/orderHistory",
    query_trade_history_api_url="https://jup.ag/api/limit/v1/tradeHistory"
)

async def swap() -> None :
    transaction_data = await jupiter.swap(
        input_mint="So11111111111111111111111111111111111111112",
        output_mint="DtR4D9FtVoTX2569gaL837ZgrB6wNjj6tkmnX9Rdk9B2",
        amount=5_000_000,
        slippage_bps=50,
    )
    # Returns str: serialized transactions to execute the swap.

    raw_transaction = VersionedTransaction.from_bytes(base64.b64decode(transaction_data))
    signature = private_key.sign_message(message.to_bytes_versioned(raw_transaction.message))
    signed_txn = VersionedTransaction.populate(raw_transaction.message, [signature])
    opts = TxOpts(skip_preflight=False, preflight_commitment=Processed)
    result = await async_client.send_raw_transaction(txn=bytes(signed_txn), opts=opts)
    transaction_id = json.loads(result.to_json())['result']
    print(f"Transaction sent: https://explorer.solana.com/tx/{transaction_id}")

async def swap_pair() -> None :
    pair_data = await jupiter.get_swap_pairs("So11111111111111111111111111111111111111112", "7gbEP2TAy5wM3TmMp5utCrRvdJ3FFqYjgN5KDpXiWPmo")
    print(pair_data)

asyncio.run(swap_pair())

