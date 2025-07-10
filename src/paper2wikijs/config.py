__all__ = [
    "OPENAI_API_KEY",
    "WIKIJS_GRAPHQL_URL",
    "WIKIJS_API_TOKEN",
    "WIKIJS_LOCALE",
    "WIKIJS_TIMEOUT",
]

import os

from dotenv import load_dotenv


def check_env_var(var_name):
    """Check if an environment variable is set."""
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"Environment variable '{var_name}' is not set.")
    return value


load_dotenv()

OPENAI_API_KEY = check_env_var("OPENAI_API_KEY")
WIKIJS_GRAPHQL_URL = check_env_var("WIKIJS_GRAPHQL_URL")
WIKIJS_API_TOKEN = check_env_var("WIKIJS_API_TOKEN")
WIKIJS_LOCALE = os.getenv("WIKIJS_LOCALE", "zh-tw").lower()
WIKIJS_TIMEOUT = int(os.getenv("WIKIJS_TIMEOUT", 5))
