from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from solana.rpc.async_api import AsyncClient
from spl.token.async_client import AsyncToken

from jupiter_python_sdk.jupiter import Jupiter
from solana.rpc.commitment import Confirmed,Finalized
from solana.rpc.types import TxOpts ,TokenAccountOpts

import base58
from spl.token.constants import TOKEN_PROGRAM_ID
import json

quote_api_url="https://quote-api.jup.ag/v6/quote?"
swap_api_url="https://quote-api.jup.ag/v6/swap?"

class SOL_Client:
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