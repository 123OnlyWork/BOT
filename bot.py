import logging
import asyncio
from aiogram import Bot, Dispatcher
from handlers import router
from subscriptions import load_subscriptions
from market import check_emergency, check_pars_VE
from utils import load_market_data_sync, save_sent_units
from config import API_TOKEN, MARKET_DATA_FILE, MARKET_DATA_VE_LVL_FILE

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
dp.include_router(router)
subscriptions = load_subscriptions()
sent_units = set()

async def periodic_check():
    while True:
        try:
            data1 = load_market_data_sync(MARKET_DATA_FILE)
            await check_emergency(bot, subscriptions, data1, sent_units)
            data2 = load_market_data_sync(MARKET_DATA_VE_LVL_FILE) 
            await check_pars_VE(bot, subscriptions, data2, sent_units)
            save_sent_units(sent_units)  # ← сохраняем после каждой проверки
        except Exception as e:
            logging.exception(f"Ошибка в периодической проверке: {e}")
        await asyncio.sleep(20)

async def send_broadcast_message():
    for user_id in subscriptions:
        try:
            await bot.send_message(user_id, "Бот работает, оставляю его в рабочем состоянии до выборов в Варшаве")  # ← Замените текст на нужный
        except Exception as e:
            logging.exception(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    # Запускаем периодическую проверку как фоновую задачу
    asyncio.create_task(periodic_check())

    # Запускаем polling — он блокирует выполнение до остановки
    try:
        await dp.start_polling(bot)
    finally:
        # Гарантированно закрываем ресурсы бота при завершении
        try:
            await bot.close()
        except Exception:
            pass

logging.basicConfig(level=logging.INFO)
if __name__ == '__main__':
    asyncio.run(main())
