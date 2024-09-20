import asyncio
import requests
from typing import Tuple

async def getLP_SOL(mint1: str, mint2: str, solPrice: float = 150.0) -> Tuple[str, float, float]:
    url = f"https://api-v3.raydium.io/pools/info/mint?mint1={mint1}&mint2={mint2}&poolType=all&poolSortField=liquidity&sortType=desc&pageSize=100&page=1"
    lpAddres = ''
    liquidity = 0.0
    name = ''
    symbol = ''
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
                    else:
                        name = pair_data['mintA']['name']
                        symbol = pair_data['mintA']['symbol']
                if 'tvl' in pair_data:
                    liquidity += float(pair_data['tvl'])
    except Exception as e:
        print(e)
    return lpAddres, name, symbol, "{:,.2f}".format(liquidity), round(liquidity/solPrice, 2)

asyncio.run(getLP_SOL('So11111111111111111111111111111111111111112', '4v3UTV9jibkhPfHi5amevropw6vFKVWo7BmxwQzwEwq6', 142.85))