from dataclasses import dataclass
import os
from dotenv import load_dotenv
load_dotenv()
@dataclass(frozen=True)
class Settings:
    alpaca_api_key: str = os.getenv('APCA_API_KEY_ID','').strip()
    alpaca_secret_key: str = os.getenv('APCA_API_SECRET_KEY','').strip()
    alpaca_paper: bool = os.getenv('APCA_PAPER','true').lower().strip() == 'true'
    news_api_key: str = os.getenv('NEWS_API_KEY','').strip()
    default_symbol: str = 'SPY'
    default_timeframe_minutes: int = 1
    lookback_days: int = 5
    opening_range_minutes: int = 15
    default_dte: int = 0
    option_stop_loss_pct: float = 0.30
    option_profit_target_pct: float = 0.50
    min_entry_confidence: int = 80
    correlation_symbols: tuple = ('QQQ','IWM','DIA','XLK','XLF','TLT','VXX')
settings = Settings()
