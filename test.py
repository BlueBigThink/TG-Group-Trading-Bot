from web3 import Web3

INFURA_ID = "e254d35aa64b4c16816163824d9d5b83"
RPC_URL = f"https://sepolia.infura.io/v3/{INFURA_ID}"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

try :
    public_address = "0x934EbC06bC2c027D46043ca3dfB7D3075c31dF4"
    balance = w3.eth.get_balance(public_address)

    if balance is not None:
        print(True)
    else:
        print(False)
except Exception as e:
    print(False)