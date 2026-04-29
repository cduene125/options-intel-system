import requests
from config import settings
def alpaca_headers(): return {'APCA-API-KEY-ID':settings.alpaca_api_key,'APCA-API-SECRET-KEY':settings.alpaca_secret_key,'accept':'application/json'}
def get_option_contracts(params):
    r=requests.get('https://paper-api.alpaca.markets/v2/options/contracts',headers=alpaca_headers(),params=params,timeout=20); r.raise_for_status(); return r.json()
def get_latest_option_quotes(symbols, feed='indicative'):
    if not symbols: return {}
    r=requests.get('https://data.alpaca.markets/v1beta1/options/quotes/latest',headers=alpaca_headers(),params={'symbols':','.join(symbols[:100]),'feed':feed},timeout=20); r.raise_for_status(); return r.json()
