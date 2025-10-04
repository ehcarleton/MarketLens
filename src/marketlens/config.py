# src/marketlens/config.py
from pydantic_settings import BaseSettings
from platformdirs import user_config_path
from pathlib import Path
import yaml

class ProviderFMP(BaseSettings):
    api_key: str | None = None

class Database(BaseSettings):
    type: str = "duckdb"   # or "postgres"
    path: str = "./data/marketlens.duckdb"

class Settings(BaseSettings):
    database: Database = Database()
    fmp: ProviderFMP = ProviderFMP()
    class Config:
        env_prefix = "MARKETLENS_"

def load_settings() -> Settings:
    cfg_file = user_config_path("MarketLens") / "config.yaml"
    if not cfg_file.exists():
        return Settings()  # default
    with cfg_file.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return Settings(**data)
