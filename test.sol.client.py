class SOL_client:
    def __init__(self,user,RPC) -> None:
        self.client = AsyncClient(RPC)
        self.user = user

    async def get_token_info(self,address):
        d = await self.get_decimals(address)
        return None,None,None,d
    
    async def Get_sol_price(self):
        p , o = await self.get_token_per_sol("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
        return p
        
    async def Get_balance(self):
        balance = await self.client.get_balance(Pubkey(list(base58.b58decode(self.user.SOL_Adress.encode()))))
        return balance.value / 1e9

    async def get_decimals(self,address):
        token = AsyncToken(self.client, Pubkey(base58.b58decode(address.encode())), program_id=TOKEN_PROGRAM_ID,payer=base58.b58decode(self.user.SOL_Adress.encode()))
        
        return (await token.get_mint_info()).decimals
    
    async def get_supply(self,address):
        token = AsyncToken(self.client, Pubkey(base58.b58decode(address.encode())), program_id=TOKEN_PROGRAM_ID,payer=base58.b58decode(self.user.SOL_Adress.encode()))
        return await token.get_mint_info().supply
    
    async def get_token_price(self,address):
        try:
            jupiter = Jupiter(
            async_client=self.client,
            keypair=Keypair.from_bytes(base58.b58decode(self.user.SOL_key_export.encode())),
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
    
    async def swap_token(self,amount,address,slip,priorfee):
        """_summary_

        Args:
            amount: amount of sol 转lams
            address: contract of token
            slip : 百分比
            priorfee: gas费 转lams
        """
        try:
            pk = Keypair.from_bytes(base58.b58decode(self.user.SOL_key_export.encode()))
            jupiter = Jupiter(
                async_client=self.client,
                keypair=pk,
                quote_api_url=quote_api_url,
                swap_api_url=swap_api_url
            )
            transaction_data = await jupiter.swap(
                input_mint="So11111111111111111111111111111111111111112",
                output_mint=address,
                amount=int(amount),
                prioritization_fee_lamports=priorfee,
                slippage_bps=int(slip)
            )
            
            raw_transaction = VersionedTransaction.from_bytes(base64.b64decode(transaction_data))
            signature = pk.sign_message(message.to_bytes_versioned(raw_transaction.message))
            print(signature)
            signed_txn = VersionedTransaction.populate(raw_transaction.message, [signature])
            opts = TxOpts(skip_preflight=False, preflight_commitment=Processed)
            result = await self.client.send_raw_transaction(txn=bytes(signed_txn), opts=opts)
            return True

        except Exception as e:
            print(e)
            return False
    
    async def swap_sol(self,amount,address,slip,priorfee):
        """_summary_

        Args:
            amount: amount of sol 转lams
            address: contract of token
            slip : 百分比
            priorfee: gas费 转lams
        """
        try:
            pk = Keypair.from_bytes(base58.b58decode(self.user.SOL_key_export.encode()))
            jupiter = Jupiter(
                async_client=self.client,
                keypair=pk,
                quote_api_url=quote_api_url,
                swap_api_url=swap_api_url
            )
            transaction_data = await jupiter.swap(
                input_mint=address,
                output_mint="So11111111111111111111111111111111111111112",
                amount=int(amount),
                prioritization_fee_lamports=priorfee,
                slippage_bps=int(slip)
            )
            
            raw_transaction = VersionedTransaction.from_bytes(base64.b64decode(transaction_data))
            signature = pk.sign_message(message.to_bytes_versioned(raw_transaction.message))
            print(signature)
            signed_txn = VersionedTransaction.populate(raw_transaction.message, [signature])
            opts = TxOpts(skip_preflight=False, preflight_commitment=Processed)
            result = await self.client.send_raw_transaction(txn=bytes(signed_txn), opts=opts)
            confirmation = await self.client.confirm_transaction(signature)
            return True

        except Exception as e:
            print(e)
            return False
    
    async def transfer_sol(self,adress,amount):
        try:
            sender = Keypair.from_bytes(base58.b58decode(self.user.SOL_key_export.encode()))
            receiver_address = Pubkey(base58.b58decode(adress.encode()))
            lamports_to_send = amount * 1000000000
            transaction = Transaction()
            transaction.add(
                transfer(
                    TransferParams(
                        from_pubkey=sender.public_key,
                        to_pubkey=receiver_address,
                        lamports=lamports_to_send
                    )
                )
            )
            opts = TxOpts(skip_preflight=False, preflight_commitment=Confirmed)
            response = await self.client.send_transaction(transaction, sender, opts=opts)
            transaction_id = response['result']
            await self.client.confirm_transaction(transaction_id, commitment="finalized")
        except Exception as e:
            print(e)

    async def get_token_list(self):
        po = await self.client.get_token_accounts_by_owner_json_parsed(Pubkey.from_string(self.user.SOL_Adress),TokenAccountOpts(program_id=Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")),commitment=Confirmed)
        return po.to_json()
    
    async def get_token_balance_raw(self,address):
        tl = await self.get_token_list()
        pp = json.loads(tl)
        
        for i in pp["result"]["value"]:
            try: 
                if i["account"]["data"]["parsed"]["info"]["mint"] == address:
                    return i["account"]["data"]["parsed"]["info"]["tokenAmount"]["amount"] , i["account"]["data"]["parsed"]["info"]["tokenAmount"]["decimals"]
            except Exception as e:
                print(e)
                continue
        return 0
    
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
    
    async def get_token_per_sol(self,address):
        try:
            jupiter = Jupiter(
            async_client=self.client,
            keypair=Keypair.from_bytes(base58.b58decode(self.user.SOL_key_export.encode())),
            quote_api_url=quote_api_url,
            swap_api_url=swap_api_url
        )
            res = await jupiter.get_token_price("So11111111111111111111111111111111111111112",address)
            print(res)
            if res == {}:
                return 0
            else:
                print(res.get("So11111111111111111111111111111111111111112").get("price"))
                return res.get("So11111111111111111111111111111111111111112").get("price"),res.get("So11111111111111111111111111111111111111112").get("vsTokenSymbol")
        except Exception as e:
            print(f"get_token_price {e}")
            return 0

    async def get_sol_per_token(self,address):
        try:
            jupiter = Jupiter(
            async_client=self.client,
            keypair=Keypair.from_bytes(base58.b58decode(self.user.SOL_key_export.encode())),
            quote_api_url=quote_api_url,
            swap_api_url=swap_api_url
        )
        
            res = await jupiter.get_token_price(address,"So11111111111111111111111111111111111111112")
            print(res)
            if res == {}:
                return 0
            else:
                print(res.get(address).get("price"))
                return res.get(address).get("price")
        except Exception as e:
            print(f"get_token_price {e}")
            return 0

    async def buy_token(self,token_contract,amount):
        try:
            actually = amount * 0.99
            fee = amount * 0.01
            result = await self.swap_token(actually*1e9,token_contract,self.user.slippage*100,int(self.user.gas*1e9))
            print(result)
            if result:
                if self.user.inviter != None:
                    try:
                        inviter_address = (await user.Get_user(self.user.inviter)).SOL_Adress
                        await self.transfer_sol(inviter_address,fee*0.2)
                        await self.transfer_sol(neverwin,fee*0.4)
                        await self.transfer_sol(Jiuge,fee*0.4)
                    except:
                        await self.transfer_sol(neverwin,fee*0.5)
                        await self.transfer_sol(Jiuge,fee*0.5)
                else:
                    await self.transfer_sol(neverwin,fee*0.5)
                    await self.transfer_sol(Jiuge,fee*0.5)
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return False
    
    async def sell_token(self,token_contract,amount,sol_get):
        try:
            sol_get = sol_get *0.01
            result = await self.swap_sol(amount,token_contract,self.user.slippage*100,int(self.user.gas*1e9))
            if result:
                if self.user.inviter != None:
                    try:
                        inviter_address = (await user.Get_user(self.user.inviter)).SOL_Adress
                        await self.transfer_sol(inviter_address,sol_get*0.2)
                        await self.transfer_sol(neverwin,sol_get*0.4)
                        await self.transfer_sol(Jiuge,sol_get*0.4)
                    except:
                        await self.transfer_sol(neverwin,sol_get*0.5)
                        await self.transfer_sol(Jiuge,sol_get*0.5)
                else:
                    await self.transfer_sol(neverwin,sol_get*0.5)
                    await self.transfer_sol(Jiuge,sol_get*0.5)
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return False

