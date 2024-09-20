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
import asyncio

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
# from uniswap import Uniswap

# address = "0xf900f49e59Ae5d787E7E562D2B4f2E819a1D82af" 
# private_key = "a756f56503643e24a043d9c63767169cece8f0011f6d215a7c2496c224822af7"
# version = 2

# INFURA_ID = "e254d35aa64b4c16816163824d9d5b83"
# # RPC_URL = f'https://mainnet.infura.io/v3/{INFURA_ID}'
# RPC_URL = f"https://sepolia.infura.io/v3/{INFURA_ID}"
# UNISWAP_ROUTER_ADDRESS = '0xC532a74256D3Db42D0Bf7a0400fEFDbad7694008'
# UNISWAP_FACTORY_ADDRESS = '0x7E0987E5b3a30e3f2828572Bb659A548460a3003'
# uniswap = Uniswap(address=address, private_key=private_key, version=version, provider=RPC_URL, router_contract_addr=UNISWAP_ROUTER_ADDRESS, factory_contract_addr=UNISWAP_FACTORY_ADDRESS)

# def get_current_slippage(token_address : str) -> float:
#     WETH = "0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9"
#     token_amount = uniswap.get_price_input(WETH, token_address, 0.01*10**18)

#     print(token_amount)

# get_current_slippage("0x8f785c1165759684B3c638cC2fecf29c335C4e4c")

from solders import message
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction,Transaction
from solders.system_program import transfer, TransferParams

from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TxOpts ,TokenAccountOpts
from solana.rpc.commitment import Processed
from spl.token.async_client import AsyncToken
from jupiter_python_sdk.jupiter import Jupiter
from solana.rpc.commitment import Confirmed,Finalized

import base64
import json

quote_api_url="https://quote-api.jup.ag/v6/quote?"
swap_api_url="https://quote-api.jup.ag/v6/swap?"

import base58
from spl.token.constants import TOKEN_PROGRAM_ID


class SOL_client:
    def __init__(self, prv_key : str, pub_key:str,  RPC : str) -> None:
        self.client = AsyncClient(RPC)
        self.prv_key = prv_key
        self.pub_key = pub_key

    async def get_token_info(self, address : str):
        d = await self.get_decimals(address)
        return None,None,None,d

    async def get_decimals(self, address : str) -> int:
        token = AsyncToken(self.client, Pubkey(base58.b58decode(address.encode())), program_id=TOKEN_PROGRAM_ID, payer=base58.b58decode(self.prv_key))
        return (await token.get_mint_info()).decimals
    
    async def get_sol_usdc_price(self):
        p , o = await self.get_token_per_sol("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
        return p

    async def get_token_per_sol(self, address : str):
        try:
            jupiter = Jupiter(
            async_client=self.client,
            keypair=Keypair.from_base58_string(self.prv_key),
            quote_api_url=quote_api_url,
            swap_api_url=swap_api_url
        )
            res = await jupiter.get_token_price("So11111111111111111111111111111111111111112", address)
            print(f"get_token_per_sol >> {res}")
            if res == {}:
                return 0, 0
            else:
                print(res.get("So11111111111111111111111111111111111111112").get("price"))
                return res.get("So11111111111111111111111111111111111111112").get("price"), res.get("So11111111111111111111111111111111111111112").get("vsTokenSymbol")
        except Exception as e:
            print(f"get_token_price {e}")
            return 0, 0
        
    async def get_sol_balance(self):
        balance = await self.client.get_balance(Pubkey.from_string(self.pub_key))
        return balance.value / 1e9
 
    async def get_token_price(self, address : str):
        try:
            jupiter = Jupiter(
            async_client=self.client,
            keypair=Keypair.from_base58_string(self.prv_key),
            quote_api_url=quote_api_url,
            swap_api_url=swap_api_url
        )
        
            res = await jupiter.get_token_price(address,"EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
            print(res)
            if res == {}:
                return 0,"none"
            else:
                print(res.get(address).get("price"))
                return res.get(address).get("price"),res.get(address).get("mintSymbol")
            
        except Exception as e:
            print(f"get_token_price {e}")
            return 0 , "none"

    async def get_sol_per_token(self, address : str):
        try:
            jupiter = Jupiter(
            async_client=self.client,
            keypair=Keypair.from_base58_string(self.prv_key),
            quote_api_url=quote_api_url,
            swap_api_url=swap_api_url
        )
        
            res = await jupiter.get_token_price(address,"So11111111111111111111111111111111111111112")
            if res == {}:
                return 0
            else:
                return res.get(address).get("price")
        except Exception as e:
            print(f"get_sol_per_token {e}")
            return 0

    async def get_token_list(self, pub_key : str=""):
        if pub_key == "":
            pub_key = self.pub_key
        po = await self.client.get_token_accounts_by_owner_json_parsed(Pubkey.from_string(pub_key),TokenAccountOpts(program_id=Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")),commitment=Confirmed)
        return po.to_json()
    
    # async def get_supply(self, address : str):
    #     token = AsyncToken(self.client, Pubkey(base58.b58decode(address.encode())), program_id=TOKEN_PROGRAM_ID,payer=base58.b58decode(self.prv_key))
    #     return await token.get_mint_info().supply
    
    # async def swap_token(self,amount,address,slip,priorfee):
    #     """_summary_

    #     Args:
    #         amount: amount of sol 转lams
    #         address: contract of token
    #         slip : 百分比
    #         priorfee: gas费 转lams
    #     """
    #     try:
    #         pk = Keypair.from_bytes(base58.b58decode(self.user.SOL_key_export.encode()))
    #         jupiter = Jupiter(
    #             async_client=self.client,
    #             keypair=pk,
    #             quote_api_url=quote_api_url,
    #             swap_api_url=swap_api_url
    #         )
    #         transaction_data = await jupiter.swap(
    #             input_mint="So11111111111111111111111111111111111111112",
    #             output_mint=address,
    #             amount=int(amount),
    #             prioritization_fee_lamports=priorfee,
    #             slippage_bps=int(slip)
    #         )
            
    #         raw_transaction = VersionedTransaction.from_bytes(base64.b64decode(transaction_data))
    #         signature = pk.sign_message(message.to_bytes_versioned(raw_transaction.message))
    #         print(signature)
    #         signed_txn = VersionedTransaction.populate(raw_transaction.message, [signature])
    #         opts = TxOpts(skip_preflight=False, preflight_commitment=Processed)
    #         result = await self.client.send_raw_transaction(txn=bytes(signed_txn), opts=opts)
    #         return True

    #     except Exception as e:
    #         print(e)
    #         return False
    
    # async def swap_sol(self,amount,address,slip,priorfee):
    #     """_summary_

    #     Args:
    #         amount: amount of sol 转lams
    #         address: contract of token
    #         slip : 百分比
    #         priorfee: gas费 转lams
    #     """
    #     try:
    #         pk = Keypair.from_bytes(base58.b58decode(self.user.SOL_key_export.encode()))
    #         jupiter = Jupiter(
    #             async_client=self.client,
    #             keypair=pk,
    #             quote_api_url=quote_api_url,
    #             swap_api_url=swap_api_url
    #         )
    #         transaction_data = await jupiter.swap(
    #             input_mint=address,
    #             output_mint="So11111111111111111111111111111111111111112",
    #             amount=int(amount),
    #             prioritization_fee_lamports=priorfee,
    #             slippage_bps=int(slip)
    #         )
            
    #         raw_transaction = VersionedTransaction.from_bytes(base64.b64decode(transaction_data))
    #         signature = pk.sign_message(message.to_bytes_versioned(raw_transaction.message))
    #         print(signature)
    #         signed_txn = VersionedTransaction.populate(raw_transaction.message, [signature])
    #         opts = TxOpts(skip_preflight=False, preflight_commitment=Processed)
    #         result = await self.client.send_raw_transaction(txn=bytes(signed_txn), opts=opts)
    #         confirmation = await self.client.confirm_transaction(signature)
    #         return True

    #     except Exception as e:
    #         print(e)
    #         return False
    
    # async def transfer_sol(self,adress,amount):
    #     try:
    #         sender = Keypair.from_bytes(base58.b58decode(self.user.SOL_key_export.encode()))
    #         receiver_address = Pubkey(base58.b58decode(adress.encode()))
    #         lamports_to_send = amount * 1000000000
    #         transaction = Transaction()
    #         transaction.add(
    #             transfer(
    #                 TransferParams(
    #                     from_pubkey=sender.public_key,
    #                     to_pubkey=receiver_address,
    #                     lamports=lamports_to_send
    #                 )
    #             )
    #         )
    #         opts = TxOpts(skip_preflight=False, preflight_commitment=Confirmed)
    #         response = await self.client.send_transaction(transaction, sender, opts=opts)
    #         transaction_id = response['result']
    #         await self.client.confirm_transaction(transaction_id, commitment="finalized")
    #     except Exception as e:
    #         print(e)
    
    # async def get_token_balance_raw(self,address):
    #     tl = await self.get_token_list()
    #     pp = json.loads(tl)
        
    #     for i in pp["result"]["value"]:
    #         try: 
    #             if i["account"]["data"]["parsed"]["info"]["mint"] == address:
    #                 return i["account"]["data"]["parsed"]["info"]["tokenAmount"]["amount"] , i["account"]["data"]["parsed"]["info"]["tokenAmount"]["decimals"]
    #         except Exception as e:
    #             print(e)
    #             continue
    #     return 0
    
    async def get_token_balance(self,address):
        tl = await self.get_token_list()
        pp = json.loads(tl)
        
        for i in pp["result"]["value"]:
            try: 
                if i["account"]["data"]["parsed"]["info"]["mint"] == address:
                    return i["account"]["data"]["parsed"]["info"]["tokenAmount"]["uiAmount"]
            except Exception as e:
                print(e)
                continue
        return 0
    
    # async def buy_token(self,token_contract,amount):
    #     try:
    #         actually = amount * 0.99
    #         fee = amount * 0.01
    #         result = await self.swap_token(actually*1e9,token_contract,self.user.slippage*100,int(self.user.gas*1e9))
    #         print(result)
    #         if result:
    #             if self.user.inviter != None:
    #                 try:
    #                     inviter_address = (await user.Get_user(self.user.inviter)).SOL_Adress
    #                     await self.transfer_sol(inviter_address,fee*0.2)
    #                     await self.transfer_sol(neverwin,fee*0.4)
    #                     await self.transfer_sol(Jiuge,fee*0.4)
    #                 except:
    #                     await self.transfer_sol(neverwin,fee*0.5)
    #                     await self.transfer_sol(Jiuge,fee*0.5)
    #             else:
    #                 await self.transfer_sol(neverwin,fee*0.5)
    #                 await self.transfer_sol(Jiuge,fee*0.5)
    #             return True
    #         else:
    #             return False
    #     except Exception as e:
    #         print(e)
    #         return False
    
    # async def sell_token(self,token_contract,amount,sol_get):
    #     try:
    #         sol_get = sol_get *0.01
    #         result = await self.swap_sol(amount,token_contract,self.user.slippage*100,int(self.user.gas*1e9))
    #         if result:
    #             if self.user.inviter != None:
    #                 try:
    #                     inviter_address = (await user.Get_user(self.user.inviter)).SOL_Adress
    #                     await self.transfer_sol(inviter_address,sol_get*0.2)
    #                     await self.transfer_sol(neverwin,sol_get*0.4)
    #                     await self.transfer_sol(Jiuge,sol_get*0.4)
    #                 except:
    #                     await self.transfer_sol(neverwin,sol_get*0.5)
    #                     await self.transfer_sol(Jiuge,sol_get*0.5)
    #             else:
    #                 await self.transfer_sol(neverwin,sol_get*0.5)
    #                 await self.transfer_sol(Jiuge,sol_get*0.5)
    #             return True
    #         else:
    #             return False
    #     except Exception as e:
    #         print(e)
    #         return False


sol_client = SOL_client("B7retLYFbq2w34nRRddG4S7oUJSmQHhpZHCsWkgSUT2Kqp6uiSqtJ83cRbjvKNRN21ySsuvxnVN3ZchJoPrzgja", "7VAMJuHeM1FvR5fkkku56bTTu7TmUJjMPprW56muzLhv", "https://api.mainnet-beta.solana.com")
# sol_client = SOL_client("", "", "https://api.mainnet-beta.solana.com")
async def test():
    print(await sol_client.get_token_balance("DtR4D9FtVoTX2569gaL837ZgrB6wNjj6tkmnX9Rdk9B2"))
    # print(await sol_client.get_token_list("MJKqp326RZCHnAAbew9MDdui3iCKWco7fsK9sVuZTX2"))

asyncio.run(test())