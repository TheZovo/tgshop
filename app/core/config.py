from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    TELEGRAM_TOKEN: str
    DATABASE_URL: str
    CRYPTOMUS_API_KEY: str
    CRYPTOMUS_MERCHANT_ID: str
    LTC_API_URL: str = "https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()