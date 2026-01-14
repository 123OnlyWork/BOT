import json
import logging
import re
import os
import html

from config import MARKET_DATA_FILE, SENT_UNITS_FILE, MARKET_DATA_VE_LVL_FILE

def load_sent_units() -> set:
    if os.path.exists(SENT_UNITS_FILE):
        with open(SENT_UNITS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_sent_units(sent_units: set):
    # Load existing data from the file
    existing_units = load_sent_units()
    # Merge the new units with the existing ones
    combined_units = existing_units.union(sent_units)
    # Save the combined set back to the file
    with open(SENT_UNITS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(combined_units), f, ensure_ascii=False, indent=2)
        
def parse_float(value: str) -> float:
    try:
        match = re.search(r"\d+(?: \d+)*(?:\.\d+)?", value)
        if match:
            return float(match.group(0).replace(' ', ''))
    except ValueError:
        logging.error(f"Ошибка преобразования: {value}")
    return 0.0

def load_market_data_VE(filename=MARKET_DATA_VE_LVL_FILE) -> list:
    if not os.path.exists(filename):
        raise FileNotFoundError("Файл не найден.")

    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:  # Check if the file is empty
                logging.error(f"Файл {filename} пуст.")
                return []
            data2 = json.loads(content)

        # Ensure the returned data is a list of dictionaries
        if isinstance(data2, dict) and "data" in data2:
            return data2["data"]
        elif isinstance(data2, list):
            if all(isinstance(item, dict) for item in data2):
                return data2
            else:
                logging.error(f"Некорректный формат данных в файле {filename}: элементы списка не являются словарями.")
                return []
        else:
            logging.error(f"Неверный формат данных в файле {filename}.")
            return []
    except json.JSONDecodeError as e:
        logging.error(f"Ошибка декодирования JSON в файле {filename}: {e}")
        return []

def load_market_data_sync(filename=MARKET_DATA_FILE) -> list:
    if not os.path.exists(filename):
        raise FileNotFoundError("Файл не найден.")

    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:  # Check if the file is empty
                logging.error(f"Файл {filename} пуст.")
                return []
            data = json.loads(content)

        # Ensure the returned data is a list of dictionaries
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        elif isinstance(data, list):
            return data
        else:
            logging.error(f"Неверный формат данных в файле {filename}.")
            return []
    except json.JSONDecodeError as e:
        logging.error(f"Ошибка декодирования JSON в файле {filename}: {e}")
        return []

def format_entry(entry: dict, use_html=False) -> str:
    if use_html:
        return (
            f"<b>🏙 Город:</b> {html.escape(entry['city'])}\n"
            f"<b>🏭 Название:</b> <a href=\"{html.escape(entry['unit_url'])}\">{html.escape(entry['unit_name'])}</a>\n"
            f"<b>📈 Уровень:</b> {html.escape(entry['level'])}\n"
            f"<b>👤 Продавец:</b> {html.escape(entry['seller'])}\n"
            f"<b>💰 Цена:</b> {html.escape(entry['price'])}\n"
            f"<b>📊 Активы:</b> {html.escape(entry['assets'])}\n"
            f"<b>📉 Дисконт:</b> {html.escape(entry['discount'])}\n"
            f"<b>📅 Дата добавления:</b> {html.escape(entry['date'])}"
        )
    else:
        return (
            f"🏙 Город: {entry['city']}\n"
            f"🏭 Название: {entry['unit_name']} ({entry['unit_url']})\n"
            f"📈 Уровень: {entry['level']}\n"
            f"👤 Продавец: {entry['seller']}\n"
            f"💰 Цена: {entry['price']}\n"
            f"📊 Активы: {entry['assets']}\n"
            f"📉 Дисконт: {entry['discount']}\n"
            f"📅 Дата добавления: {entry['date']}"
        )

