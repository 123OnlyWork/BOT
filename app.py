import json
import logging
import asyncio
import time
from aiogram import Bot, Dispatcher
from handlers import router
from subscriptions import load_subscriptions
from market import check_emergency, check_pars_VE
from utils import load_market_data_sync,load_market_data_VE, save_sent_units
from config import API_TOKEN, MARKET_DATA_FILE, MARKET_DATA_VE_LVL_FILE
from parsing import update_market_data_sync
from ve_LVL import update_market_data
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import utc

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
dp.include_router(router)
subscriptions = load_subscriptions()
sent_units = set()

def display_menu():
    print("\n=== Меню ===")
    print("1. Обновить данные рынка")
    print("2. Показать данные рынка")
    print("3. Запустить проверку на чрезвычайные ситуации")
    print("4. Выйти")
    print("5. Запустить бота и парсер")

def show_market_data():
    try:
        with open(MARKET_DATA_FILE, "r", encoding="utf-8") as file:
            data1 = json.load(file)
            print(json.dumps(data1, ensure_ascii=False, indent=4))
        with open(MARKET_DATA_VE_LVL_FILE, "r", encoding="utf-8") as file:
            data2 = json.load(file)
            print(json.dumps(data2, ensure_ascii=False, indent=4))
    except Exception as e:
        logging.error(f"Ошибка при загрузке данных: {e}")

async def periodic_check():
    logging.debug("Запуск периодической проверки...")
    while True:
        try:
            logging.debug("Загрузка данных рынка...")
            data1 = load_market_data_sync(MARKET_DATA_FILE)
            await perform_sync_checks(data1)

            data2 = load_market_data_VE(MARKET_DATA_VE_LVL_FILE)
            await perform_ve_checks(data2)
        except Exception as e:
            logging.exception(f"Ошибка в периодической проверке: {e}")
        await asyncio.sleep(1)

async def perform_sync_checks(data1):
    logging.debug("Проверка на чрезвычайные ситуации (sync)...")
    await check_emergency(bot, subscriptions, data1, sent_units)
    logging.debug("Сохранение отправленных юнитов (sync)...")
    save_sent_units(sent_units)

async def perform_ve_checks(data2):
    logging.debug("Проверка на чрезвычайные ситуации (VE)...")
    await check_pars_VE(bot, subscriptions, data2, sent_units)
    logging.debug("Сохранение отправленных юнитов (VE)...")
    save_sent_units(sent_units)

async def run_bot_and_parser():
    logging.info("Запуск парсера...")
    retries = 3
    for attempt in range(retries):
        try:
            logging.debug(f"Попытка запуска парсера {attempt + 1}...")
            update_market_data_sync()
            logging.info("Парсер завершил работу.")
            break
        except Exception as e:
            logging.error(f"Попытка {attempt + 1} завершилась ошибкой: {e}")
            if attempt < retries - 1:
                logging.info("Повторная попытка запуска парсера...")
                time.sleep(5)  # Задержка перед повторной попыткой
            else:
                logging.error("Все попытки запуска парсера завершились неудачей.")
                return
    logging.info("Запуск бота...")
    await bot.delete_webhook()
    asyncio.create_task(periodic_check())
    await dp.start_polling(bot)

async def run_all():
    logging.info("Запуск всех компонентов: парсеры и бот...")

    # Инициализация планировщика
    scheduler = BackgroundScheduler(timezone=utc)
    scheduler.add_job(func=update_market_data, trigger="interval", seconds=60)
    scheduler.add_job(func=update_market_data_sync, trigger="interval", seconds=90)
    scheduler.start()
    logging.info("Планировщик запущен. Парсер будет запускаться каждые 30 секунд.")

    # Запуск первого парсера в отдельной задаче
    parser1_task = asyncio.create_task(asyncio.to_thread(update_market_data_sync))

    # Запуск второго парсера в отдельной задаче
    parser2_task = asyncio.create_task(asyncio.to_thread(update_market_data))

    # Запуск бота
    bot_task = asyncio.create_task(run_bot_and_parser())

    # Ожидание завершения всех задач
    await asyncio.gather(parser1_task, parser2_task, bot_task, return_exceptions=True)

if __name__ == "__main__":
    asyncio.run(run_all())