# buy-бизнесмания

## Project Overview
Этот репозиторий содержит парсер данных рынка и Telegram-бота.

## Содержимое
- `parsing.py`, `ve_LVL.py`, `market.py` — парсеры и обработка данных.
- `bot.py`, `handlers.py`, `subscriptions.py` — Telegram-бот и обработчики.
- `utils.py`, `config.py` — утилиты и конфигурация.

## Запуск
1. Создать виртуальное окружение и установить зависимости:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

2. Установить переменные окружения (в `.env`) — минимум `API_TOKEN`.

3. Запустить бота:
```bash
python bot.py
```

## License
Проект лицензирован под MIT.