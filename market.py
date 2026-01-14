from config import MARKET_DATA_FILE, MARKET_DATA_VE_LVL_FILE, SENT_UNITS_FILE
from utils import load_market_data_VE, load_market_data_sync, parse_float, format_entry, save_sent_units
import logging
async def send_entries(bot, message, entries: list, html=False):
    if not entries:
        await message.answer("❌ Нет подходящих предложений.")
        return
    for entry in entries:
        await message.answer(format_entry(entry, html), parse_mode="HTML" if html else None)

async def check_emergency(bot, subscriptions, market_data, sent_units: set):
    for entry in market_data:
        if not isinstance(entry, dict):
            logging.error(f"Некорректный формат записи: {entry}")
            continue

        unit_id = entry.get(MARKET_DATA_FILE)

        # Пропустить, если уже отправляли или если цена "Аукцион"
        if unit_id in sent_units or entry["price"].strip().startswith("Аукцион"):
            continue

        price = parse_float(entry['price'])
        assets = parse_float(entry['assets'])

        if price <= 10_000_000 or (assets > 0 and price / assets < 0.3):
            text = format_entry(entry, use_html=True)
            for user_id in subscriptions:
                await bot.send_message(user_id, f"⚠️ Экстренное предложение:\n{text}", parse_mode="HTML")
            sent_units.add(unit_id)
        
async def check_pars_VE(bot, subscriptions, market_data, sent_units: set):
    for entry in market_data:
        if not isinstance(entry, dict):
            logging.error(f"Некорректный формат записи: {entry}")
            continue

        unit_id = entry.get(MARKET_DATA_VE_LVL_FILE)
        # Пропустить, если уже отправляли или если цена "Аукцион"
        if unit_id in sent_units or entry["price"].strip().startswith("Аукцион"):
            continue

        city = entry['city']
        level = parse_float(entry['level'])

        # Проверка на города и уровень
        if (city == "Познань" or city == "Львов" or city == "Будапешт" or city == "Бухарест" or city == "Минск" or city == "Днепр" or city == "Варшава") and level >= 100:
                text = format_entry(entry, use_html=True)
                for user_id in subscriptions:
                    await bot.send_message(user_id, f"⚠️ Большое предприятие в ВЕ:\n{text}", parse_mode="HTML")
                sent_units.add(unit_id)

    # Сохранение обновлённого набора отправленных предложений в файл
    save_sent_units(sent_units)

async def check_market_data():
    try:
        data1 = load_market_data_sync(MARKET_DATA_FILE)
        data2 = load_market_data_VE(MARKET_DATA_VE_LVL_FILE)
        return data1, data2
    except Exception as e:
        logging.error(f"Ошибка при загрузке данных: {e}")
        return []