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


from web3 import Web3
from uniswap import Uniswap

# Connect to Infura
infura_url = 'https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID'
web3 = Web3(Web3.HTTPProvider(infura_url))

if not web3.isConnected():
    raise Exception("Failed to connect to the Ethereum network")

# Initialize Uniswap
uniswap = Uniswap(address=None, private_key=None, version=2)  # Uniswap V2

# Define token and WETH addresses
token_address = '0xYourTokenAddress'
weth_address = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'

# Get the pair address
pair_address = uniswap.get_pair(token_address, weth_address)

# Create a contract instance for the pair
pair_contract = web3.eth.contract(address=pair_address, abi=uniswap.PAIR_ABI)

# Get the reserves
reserves = pair_contract.functions.getReserves().call()

# Extract liquidity
token_liquidity = reserves[0]
weth_liquidity = reserves[1]

print(f'Token Liquidity: {token_liquidity}')
print(f'WETH Liquidity: {weth_liquidity}')
