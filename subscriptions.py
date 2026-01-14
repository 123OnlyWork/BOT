import json
import os
from config import SUBSCRIPTIONS_FILE


def load_subscriptions() -> set:
    if os.path.exists(SUBSCRIPTIONS_FILE):
        with open(SUBSCRIPTIONS_FILE, "r", encoding="utf-8") as file:
            return set(json.load(file))
    return set()

def save_subscriptions(subs: set):
    with open(SUBSCRIPTIONS_FILE, "w", encoding="utf-8") as file:
        json.dump(list(subs), file)
