from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import time
import random
from selenium.webdriver.chrome.service import Service
import os
import json
from datetime import datetime
from pytz import utc
from apscheduler.schedulers.background import BackgroundScheduler
from config import MARKET_DATA_VE_LVL_FILE

def delayed_action(action_description=""):
    time.sleep(random.uniform(1, 2))
    logging.info(f"Действие: {action_description}")

def start_browser(headless=True, profile_name="chrome-profile-parser2"):
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument(f"--user-data-dir={os.path.join(os.getcwd(), profile_name)}")
    options.add_argument("--profile-directory=Default")
    options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")  # Отключаем использование GPU
    options.add_argument("--disable-software-rasterizer")  # Отключаем программный растеризатор
    options.add_argument("--disable-extensions")  # Отключаем расширения для стабильности
    options.add_argument("--disable-background-networking")  # Отключаем фоновую сеть
    options.add_argument("--disable-sync")  # Отключаем синхронизацию
    options.add_argument("--disable-logging")  # Отключаем лишние логи браузера

  
    
    try:
        logging.debug("Запуск ChromeDriver...")
        service = Service()  # Убедитесь, что путь к chromedriver указан корректно
        driver = webdriver.Chrome(service=service, options=options)
        logging.debug("Открытие сайта https://bizmania.ru/market/units/...")
        driver.get("https://bizmania.ru/market/units/")  # Переходим на сайт
        logging.info("Браузер успешно запущен и сайт открыт.")
        return driver
    except Exception as e:
        logging.error(f"Ошибка при запуске ChromeDriver: {e}")
        logging.error("Проверьте путь к ChromeDriver, настройки браузера и совместимость с версией Chrome.")
        raise
   

def save_market_data_to_file(new_entries, file_path=MARKET_DATA_VE_LVL_FILE):
    try:
        old_entries = []

        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    if content.strip():  # Проверяем, что файл не пуст
                        existing_data = json.loads(content)
                        old_entries = existing_data.get("data", [])
                    else:
                        logging.warning(f"{file_path} пустой. Старые данные не загружены.")
            except Exception as e:
                logging.warning(f"Не удалось загрузить старые данные из {file_path}: {e}")
        
        # Добавляем текущую дату к новым записям
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        for entry in new_entries:
            if "date" not in entry or not entry["date"]:
                entry["date"] = now_str

        # Объединяем: новые данные сверху
        combined_entries = new_entries + old_entries

        # Удаляем дубликаты по unit_url или unit_name
        seen = set()
        unique_entries = []
        for entry in combined_entries:
            key = entry.get("unit_url") or entry.get("unit_name")
            if key and key not in seen:
                unique_entries.append(entry)
                seen.add(key)

        # Обновляем JSON структуру
        data_with_date = {
            "date": now_str,
            "data": unique_entries
        }

        # Создаем резервную копию
        if os.path.exists(file_path):
            backup_path = file_path + ".bak"
            os.replace(file_path, backup_path)
            logging.info(f"Создана резервная копия: {backup_path}")

        # Сохраняем файл
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data_with_date, file, ensure_ascii=False, indent=4)

        logging.info(f"Обновленные данные сохранены в {file_path}, всего записей: {len(unique_entries)}")

    except Exception as e:
        logging.error(f"Ошибка при сохранении данных в файл {file_path}: {e}")

def update_market_data():
    try:
        logging.info("Запуск браузера...")
        driver = start_browser(headless=True)
        data = []

        try:
            logging.info("Открытие страницы рынка...")
            driver.get("https://bizmania.ru/market/units/?location=23")
            WebDriverWait(driver, 90).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'table.datatable'))
            )
            delayed_action("Страница рынка успешно загружена.")
            # Находим элемент, который связан с сортировкой по уровню
            level_header = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Уровень')]")
            ))
            try:
                logging.info("Сортировка по уровню по возрастанию... Выполняем первый клик.")
                driver.execute_script("arguments[0].scrollIntoView(true);", level_header)
                level_header.click()

                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'table.datatable'))
                )
                delayed_action("Таблица успешно обновлена после первого клика.")
            except Exception as e:
                if "stale element reference" in str(e):
                    logging.warning("Элемент устарел, повторное нахождение элемента.")
                    level_header = WebDriverWait(driver, 30).until(
                        EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Уровень')]")
                    ))
                    driver.execute_script("arguments[0].scrollIntoView(true);", level_header)
                    level_header.click()

                    WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'table.datatable'))
                    )
                    delayed_action("Таблица успешно обновлена после повторного клика.")
                else:
                    logging.error(f"Ошибка при клике на элемент сортировки: {e}")
                    driver.refresh()  # Перезагрузка страницы
                    logging.info("Страница перезагружена. Повторяем попытку.")

            logging.info("Переключение на сортировку по убыванию... Выполняем второй клик.")
            level_header = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Уровень')]")
            ))
            level_header.click()

            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'table.datatable'))
            )
            delayed_action("Таблица успешно обновлена после второго клика.")


            logging.info("Начало парсинга страниц...")
            for page_num in range(1, 3):  #
                logging.info(f"Парсинг страницы {page_num}...")
                if page_num > 1:
                    page_to_click = WebDriverWait(driver, 30).until(
                        EC.element_to_be_clickable((By.XPATH, f"//span[text()='{page_num}']"))
                    )
                    driver.execute_script("arguments[0].scrollIntoView(true);", page_to_click)
                    page_to_click.click()
                    WebDriverWait(driver, 90).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'table.datatable'))
                    )
                    delayed_action(f"Страница {page_num} загружена.")

                logging.info(f"Обработка строк таблицы на странице {page_num}...")
                rows = driver.find_elements(By.CSS_SELECTOR, 'table.datatable tbody tr')
                for i in range(len(rows)):
                    try:
                        row = driver.find_elements(By.CSS_SELECTOR, 'table.datatable tbody tr')[i]
                        city = row.find_element(By.XPATH, './td[2]/a').text.strip()
                        unit_elem = row.find_element(By.XPATH, './td[4]/a')
                        unit_name = unit_elem.text.strip()
                        unit_url = unit_elem.get_attribute("href")
                        level = row.find_element(By.XPATH, './td[5]/div[@class="level"]').text.strip()
                        seller = row.find_element(By.XPATH, './td[7]/a').text.strip()
                        price = row.find_element(By.XPATH, './td[10]/a').text.strip()
                        assets = row.find_element(By.XPATH, './td[8]').text.strip()
                        discount = row.find_element(By.XPATH, './td[9]').text.strip()
                        datetime_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        data.append({
                            "city": city,
                            "unit_name": unit_name,
                            "unit_url": unit_url,
                            "level": level,
                            "seller": seller,
                            "price": price,
                            "assets": assets,
                            "discount": discount,
                            "date": datetime_now
                        })
                        logging.debug(f"Добавлена запись: {unit_name}, {city}, {price}")
                    except Exception as e:
                        logging.error(f"Ошибка при обработке строки: {e}")

            logging.info("Сохранение данных после парсинга...")
            save_market_data_to_file(data)
            delayed_action("Данные успешно сохранены.")
        except Exception as e:
            logging.error(f"Ошибка во время автоматического обновления данных: {e}")
    except Exception as e:
        logging.error(f"Ошибка в функции update_market_data: {e}")

def start_scheduler():
    scheduler = BackgroundScheduler(timezone=utc)
    scheduler.add_job(func=update_market_data, trigger="interval", seconds=30)
    scheduler.start()
    logging.info("Планировщик запущен. Парсер будет запускаться каждые 30 секунд.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("Запуск парсера...")
    start_scheduler()

    try:
        while True:
            time.sleep(1)  # Поддерживаем выполнение программы
    except (KeyboardInterrupt, SystemExit):
        logging.info("Остановка планировщика...")
        pass
