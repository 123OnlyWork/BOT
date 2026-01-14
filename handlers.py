from aiogram import types, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import MARKET_DATA_FILE
from utils import load_market_data_sync,load_market_data_VE, parse_float
from subscriptions import save_subscriptions, load_subscriptions
from market import send_entries
from config import ANALYTICS_CITIES_FILE
import json

router = Router()

# Определение состояний
class FilterStates(StatesGroup):
    choosing_region = State()
    choosing_city = State()

# Инициализация
subscriptions = load_subscriptions()

# Загрузка данных из файла analytics_cities.json
def load_analytics_cities_data(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

# Команды
help_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Помощь")]],
    resize_keyboard=True,
    one_time_keyboard=False  # Всегда видна
)

# Обработка команды /start
@router.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Добро пожаловать!", reply_markup=help_keyboard)

# Обработка нажатия на кнопку "Помощь"
@router.message(lambda m: m.text == "Помощь")
async def help_command(message: types.Message):
    await message.answer(
        "Доступные команды:\n"
        "/start - Начать\n"
        "/market - Показать рынок\n"
        "/subscribe - Подписаться на уведомления\n"
        "/unsubscribe - Отписаться от уведомлений\n"
        "/status - Проверить статус подписки\n"
        "/filter - Фильтровать по региону и городу"
    )

@router.message(Command("market"))
async def market(message: types.Message):
    try:
        data = load_market_data_sync(MARKET_DATA_FILE)
        filtered = [
            entry for entry in data
            if not entry['price'].startswith("Аукцион")
            and parse_float(entry['assets']) > 0
            and parse_float(entry['price']) / parse_float(entry['assets']) < 0.5
        ]
        await send_entries(message.bot, message, filtered)
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@router.message(Command("subscribe"))
async def subscribe(message: types.Message):
    user_id = message.from_user.id
    if user_id in subscriptions:
        await message.answer("Вы уже подписаны.")
    else:
        subscriptions.add(user_id)
        save_subscriptions(subscriptions)
        await message.answer("Подписка оформлена.")

@router.message(Command("unsubscribe"))
async def unsubscribe(message: types.Message):
    user_id = message.from_user.id
    if user_id in subscriptions:
        subscriptions.remove(user_id)
        save_subscriptions(subscriptions)
        await message.answer("Отписка оформлена.")
    else:
        await message.answer("Вы не подписаны.")

@router.message(Command("status"))
async def status(message: types.Message):
    user_id = message.from_user.id
    if user_id in subscriptions:
        await message.answer("Вы подписаны.")
    else:
        await message.answer("Вы не подписаны.")

@router.message(Command("filter"))
async def choose_filter(message: types.Message, state: FSMContext):
    # Загрузка данных о городах и регионах
    cities_data = load_analytics_cities_data(ANALYTICS_CITIES_FILE)
    
    # Извлекаем уникальные регионы из данных analytics_cities.json
    regions = sorted(set(city["country"] for city in cities_data))

    # Если регионы не найдены
    if not regions:
        await message.answer("Не найдено доступных регионов.")
        return

    # Создание клавиатуры для выбора региона
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=region, callback_data=f"region_{region}")]
        for region in regions
    ])

    await state.set_state(FilterStates.choosing_region)
    await message.answer("Выберите регион:", reply_markup=keyboard)

@router.callback_query(StateFilter(FilterStates.choosing_city), lambda c: c.data.startswith("city_") or c.data == "show_all")
async def show_filtered(callback_query: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    region = user_data["region"]

    # Загрузка данных о рынке
    market_data = load_market_data_sync(MARKET_DATA_FILE)

    if callback_query.data == "show_all":
        # Отобразить все предприятия, находящиеся в городах выбранного региона
        region = user_data["region"]
        cities_data = load_analytics_cities_data(ANALYTICS_CITIES_FILE)
        cities_in_region = {city["city"] for city in cities_data if city["country"] == region}
        filtered = [entry for entry in market_data if entry.get("city") in cities_in_region]
    else:
        city = callback_query.data.split("_", 1)[1]
        filtered = [entry for entry in market_data if entry.get("city") == city]

    await send_entries(callback_query.bot, callback_query.message, filtered)
    await state.clear()

@router.callback_query(StateFilter(FilterStates.choosing_region), lambda c: c.data.startswith("region_"))
async def choose_city(callback_query: types.CallbackQuery, state: FSMContext):
    region = callback_query.data.split("_", 1)[1]
    await state.update_data(region=region)

    # Загрузка данных о городах и фильтрация по выбранному региону
    cities_data = load_analytics_cities_data(ANALYTICS_CITIES_FILE)
    cities = sorted({city["city"] for city in cities_data if city["country"] == region})

    # Если города не найдены
    if not cities:
        await callback_query.message.edit_text(f"В регионе {region} нет доступных городов.")
        await state.clear()
        return

    # Создаем клавиатуру с городами, каждый город в отдельной строке
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=city, callback_data=f"city_{city}")] for city in cities
    ] + [
        [InlineKeyboardButton(text="Показать все предприятия региона", callback_data="show_all")]
    ])  # Кнопка "Показать все предприятия" теперь в отдельной строке

    await state.set_state(FilterStates.choosing_city)
    await callback_query.message.edit_text(
        f"Вы выбрали регион: {region}\nТеперь выберите город:",
        reply_markup=keyboard
    )