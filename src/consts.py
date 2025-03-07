"""Project constants."""
import os
from pathlib import Path
from dotenv import dotenv_values

PROJECT_PATH = Path(__file__).parent.parent
ENV_PATH = PROJECT_PATH / ".env"
config_env = dotenv_values(ENV_PATH)

def check_env_or_raise(var_name: str):
    var_name = os.getenv(var_name, config_env.get(var_name))
    if not var_name:
        raise ValueError(f"{var_name} not found in environment variables or .env file")
    return var_name

BOT_TOKEN = check_env_or_raise("BOT_TOKEN")