from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
import time
import pyperclip
from datetime import datetime

# --- USTAW DATĘ ---
target_date_str = "2025-01-07"
target_date = datetime.strptime(target_date_str, "%Y-%m-%d")

# --- START ---
driver = webdriver.Chrome()
driver.get("https://teslastats.no/")
driver.maximize_window()
time.sleep(2)

# --- KLIKNIJ W POLE DATY, ABY OTWORZYĆ KALENDARZ ---
try:
    driver.find_element(By.ID, "datebtn").click()
    time.sleep(1)
except:
    print("❌ Nie udało się kliknąć w pole daty.")
    driver.quit()
    exit()

# --- ZMIANA MIESIĄCA I ROKU W KALENDARZU ---
try:
    # Znajdź selecty do miesiąca i roku
    month_select = Select(driver.find_element(By.CSS_SELECTOR, ".dt-datetime-month"))
    year_select = Select(driver.find_element(By.CSS_SELECTOR, ".dt-datetime-year"))

    # Ustaw miesiąc (0-based index w select)
    month_select.select_by_value(str(target_date.month - 1))

    # Ustaw rok
    year_select.select_by_value(str(target_date.year))

    time.sleep(1)  # poczekaj aż kalendarz się przeładuje po zmianie

except NoSuchElementException:
    print("❌ Nie udało się znaleźć elementów select do miesiąca i roku.")
    driver.quit()
    exit()

# --- KLIKNIJ W KONKRETNĄ DATĘ ---
try:
    day_button = driver.find_element(By.CSS_SELECTOR, f'button[data-year="{target_date.year}"][data-month="{target_date.month - 1}"][data-day="{target_date.day}"]')
    day_button.click()
    print(f"📅 Kliknięto datę: {target_date_str}")
except NoSuchElementException:
    print(f"⚠️ Data {target_date_str} nie jest widoczna w obecnym kalendarzu.")
    driver.quit()
    exit()

# --- POCZEKAJ NA ZAŁADOWANIE DANYCH ---
time.sleep(6)

# --- ODCZYT I KOPIOWANIE ---
try:
    today_value = driver.find_element(By.ID, "today_models").text
    pyperclip.copy(today_value)
    print(f"✅ Wartość today_models: {today_value}")
    print("📋 Skopiowano do schowka.")
except:
    print("❌ Nie udało się odczytać danych.")

driver.quit()
