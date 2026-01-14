import os
from dotenv import load_dotenv

load_dotenv()

# Base directory for relative data files (BOT folder)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _rel(path: str) -> str:
	return os.path.join(BASE_DIR, path)

# Bot token (must be provided via environment or .env)
# Example: API_TOKEN=123:ABC
API_TOKEN = os.getenv('API_TOKEN', '')

# Paths to files (can be overridden via env variables)
SENT_UNITS_FILE = os.getenv('SENT_UNITS_FILE', _rel('sent_units.json'))
MARKET_DATA_FILE = os.getenv('MARKET_DATA_FILE', _rel('market_data.json'))
SUBSCRIPTIONS_FILE = os.getenv('SUBSCRIPTIONS_FILE', _rel('subscriptions.json'))
ANALYTICS_CITIES_FILE = os.getenv('ANALYTICS_CITIES_FILE', _rel('analytics_cities.json'))
MARKET_DATA_VE_LVL_FILE = os.getenv('MARKET_DATA_VE_LVL_FILE', _rel('market_data_ve_lvl.json'))

# Logical parameters (override with env vars if needed)
CHECK_INTERVAL_SECONDS = int(os.getenv('CHECK_INTERVAL_SECONDS', '20'))
DISCOUNT_THRESHOLD = float(os.getenv('DISCOUNT_THRESHOLD', '0.5'))
EMERGENCY_PRICE_LIMIT = int(os.getenv('EMERGENCY_PRICE_LIMIT', '10000000'))
EMERGENCY_RATIO = float(os.getenv('EMERGENCY_RATIO', '0.4'))

# Warn if sensitive values are not set
if not API_TOKEN:
	# Avoid raising on import — just warn so user sets up .env
	try:
		import logging
		logging.warning('API_TOKEN not set. Create a .env file or set API_TOKEN in the environment.')
	except Exception:
		pass
