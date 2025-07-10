__all__ = ["load_config"]

import os

from dotenv import load_dotenv

WIKIJS_GRAPHQL_URL = os.getenv("WIKIJS_GRAPHQL_URL")
WIKIJS_API_TOKEN = os.getenv("WIKIJS_API_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def load_config():
    load_dotenv()
    config = {
        "OPENAI_API_KEY": OPENAI_API_KEY,
        "WIKIJS_GRAPHQL_URL": WIKIJS_GRAPHQL_URL,
        "WIKIJS_API_TOKEN": WIKIJS_API_TOKEN,
        "WIKIJS_LOCALE": os.getenv("WIKIJS_LOCALE", "zh-tw"),
        "WIKIJS_TIMEOUT": int(os.getenv("WIKIJS_TIMEOUT", 5)),
    }
    return config
