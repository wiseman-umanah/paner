from platformdirs import user_config_dir
import pickle
import os
import re
from groq import Groq, AuthenticationError


config_path = user_config_dir(appname='paner', appauthor='wiseman-umanah', ensure_exists=True)
FILE = f'{config_path}/data.pkl'


def get_api_key() -> str:
    """
    Returns the api key from config file
    """
    if config_exists():
        with open(FILE, 'rb') as file:
            loaded_data = pickle.load(file)
            key = loaded_data.get('key', None)
            valid, msg = test_api_key(key)
            if not valid:
                raise ValueError(msg)
            return key
    else:
        raise FileNotFoundError("No key found")


def save_api_key(key: str) -> None:
    """
    Saves api key to config

    Raise if test fails
    """
    valid, msg = test_api_key(key)
    if not valid:
        raise ValueError(msg)

    data =  {'key': key}
    with open(FILE, 'wb') as file:
        pickle.dump(data, file, protocol=pickle.HIGHEST_PROTOCOL)


def config_exists() -> bool:
    """
    Check for config file existence
    """
    return os.path.isfile(FILE)


def test_api_key(api_key: str) -> tuple[bool, str]:
    """
    Confirm if api key is valid or not
    """
    if not api_key or not api_key.strip():
        return False, "API key cannot be empty."
    
    if not api_key.startswith("gsk_"):
        return False, "Invalid key. Groq API keys start with 'gsk_'."
    
    if len(api_key) != 56:
        return False, f"Invalid key length. Expected 56 characters, got {len(api_key)}."
    
    pattern = r'^gsk_[a-zA-Z0-9]{52}$'
    if not re.match(pattern, api_key):
        return False, "Invalid key format. Key contains unexpected characters."
    
    try:
        client = Groq(api_key=api_key)
        client.models.list()
        return True, "API key is valid!"
    except AuthenticationError:
        return False, "API key is invalid. Please check and try again."
    except Exception:
        return False, "Could not connect to Groq. Check your internet connection."
