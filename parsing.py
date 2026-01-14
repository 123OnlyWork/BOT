import atexit
import logging
import time
import random
from pytz import utc
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import os
import json
from datetime import datetime
from config import MARKET_DATA_FILE
from apscheduler.schedulers.background import BackgroundScheduler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def delayed_action(action_description=""):
    time.sleep(random.uniform(1, 2))
    logging.info(f"Действие: {action_description}")

def start_browser(headless=False, profile_name="chrome-profile-parser2"):
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument(f"--user-data-dir={os.path.join(os.getcwd(), profile_name)}")
    options.add_argument("--profile-directory=Default")
    options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-logging")

    if headless:
        options.add_argument("--headless=new")

    try:
        logging.debug("Launching ChromeDriver...")
        service = Service()
        driver = webdriver.Chrome(service=service, options=options)
        logging.debug("Opening site https://bizmania.ru/market/units/...")
        driver.get("https://bizmania.ru/market/units/")
        logging.info("Browser successfully launched and site opened.")
        return driver
    except Exception as e:
        logging.error(f"Error launching ChromeDriver: {e}")
        raise

def check_authorized(driver):
    return "https://bizmania.ru/company/?id=" in driver.current_url

def save_market_data_to_file(new_entries, file_path=MARKET_DATA_FILE):
    logging.debug("Начало сохранения данных в файл...")
    try:
        old_entries = []

        if os.path.exists(file_path):
            try:
                logging.debug("Чтение существующих данных из файла...")
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    if content.strip():
                        existing_data = json.loads(content)
                        old_entries = existing_data.get("data", [])
                    else:
                        logging.warning(f"{file_path} пустой. Старые данные не загружены.")
            except Exception as e:
                logging.warning(f"Не удалось загрузить старые данные из {file_path}: {e}")
        
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        for entry in new_entries:
            if "date" not in entry or not entry["date"]:
                entry["date"] = now_str

        logging.debug("Объединение новых и старых данных...")
        combined_entries = new_entries + old_entries

        seen = set()
        unique_entries = []
        for entry in combined_entries:
            key = entry.get("unit_url") or entry.get("unit_name")
            if key and key not in seen:
                unique_entries.append(entry)
                seen.add(key)

        data_with_date = {
            "date": now_str,
            "data": unique_entries
        }

        if os.path.exists(file_path):
            logging.debug("Создание резервной копии файла...")
            backup_path = file_path + ".bak"
            os.replace(file_path, backup_path)
            logging.info(f"Создана резервная копия: {backup_path}")

        logging.debug("Сохранение обновленных данных в файл...")
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data_with_date, file, ensure_ascii=False, indent=4)

        logging.info(f"Обновленные данные сохранены в {file_path}, всего записей: {len(unique_entries)}")

    except Exception as e:
        logging.error(f"Ошибка при сохранении данных в файл {file_path}: {e}")

def update_market_data_sync():
    logging.debug("Начало обновления данных рынка...")
    try:
        driver = start_browser(headless=False)
        data = []

        try:
            logging.debug("Открытие страницы рынка...")
            driver.get("https://bizmania.ru/market/units/")
            WebDriverWait(driver, 90).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'table.datatable'))
            )
            
            logging.debug("Начало парсинга страниц...")
            # Получаем страницы с классом "pnav-sel"
            for page_num in range(1, 11):  # Перебираем первые 5 страниц
                logging.debug(f"Парсинг страницы {page_num}...")
                logging.info(f"Parsing page {page_num} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Снимаем класс с текущей страницы
                page_elements = driver.find_elements(By.CSS_SELECTOR, 'span.pnav-sel')
                for page_elem in page_elements:
                    driver.execute_script("arguments[0].classList.remove('pnav-sel');", page_elem)

                # Кликаем на нужную страницу
                page_to_click = driver.find_element(By.XPATH, f"//span[text()='{page_num}']")
                page_to_click.click()
                WebDriverWait(driver, 90).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'table.datatable'))
                )

                logging.debug(f"Обработка строк таблицы на странице {page_num}...")
                # Парсим таблицу с данными
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
                        datetime_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Include seconds

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
                    except Exception as e:
                        logging.error(f"Error processing row: {e}")

            logging.debug("Сохранение данных после парсинга...")
            save_market_data_to_file(data)
        except Exception as e:
            logging.error(f"Ошибка во время автоматического обновления данных: {e}")
    except Exception as e:
        logging.error(f"Ошибка в функции обновления данных рынка: {e}")

scheduler = BackgroundScheduler(timezone=utc)
scheduler.add_job(func=update_market_data_sync, trigger="interval", seconds=90)
scheduler.start()

# Ensure the scheduler shuts down properly on exit
atexit.register(lambda: scheduler.shutdown())

if __name__ == "__main__":
    update_market_data_sync()
