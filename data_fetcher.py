import requests
import pandas as pd
from config import MEXC_API

def fetch_candles(symbol, interval=None):
    url = f"{MEXC_API['BASE_URL']}{symbol}"
    params = {
        'interval': interval or MEXC_API['INTERVAL']
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        response_data = response.json()

        if not response_data.get('success', False):
            print(f"API Error for {symbol}: {response_data.get('message', 'Unknown error')}")
            return None

        data = response_data['data']

        # Convert the MEXC API response format to DataFrame
        df = pd.DataFrame({
            'timestamp': pd.to_datetime(data['time'], unit='s'),
            'open': data['open'],
            'high': data['high'],
            'low': data['low'],
            'close': data['close'],
            'volume': data['vol']
        })

        return df.set_index('timestamp')
    except Exception as e:
        print(f"Error fetching {symbol}: {str(e)}")
        return None