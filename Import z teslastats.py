from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime, timedelta
import time

URL = r"C:\Users\konrd\Desktop\NAUKA\Phyton\Tesla cars\dates.txt"

def select_date(driver, target_date):
    """Ustawia datę w kalendarzu na stronie."""
    driver.find_element(By.ID, "datebtn").click()
    time.sleep(1)

    # Ustaw miesiąc i rok
    month_select = Select(driver.find_element(By.CSS_SELECTOR, ".dt-datetime-month"))
    year_select = Select(driver.find_element(By.CSS_SELECTOR, ".dt-datetime-year"))

    month_select.select_by_value(str(target_date.month - 1))  # miesiące 0-based
    year_select.select_by_value(str(target_date.year))
    time.sleep(1)

    # Kliknij konkretny dzień
    day_button = driver.find_element(By.CSS_SELECTOR,
        f'button[data-year="{target_date.year}"][data-month="{target_date.month - 1}"][data-day="{target_date.day}"]')
    day_button.click()
    print(f"📅 Kliknięto datę: {target_date.strftime('%Y-%m-%d')}")

def daterange(start_date, end_date):
    """Generator dat od start_date do end_date (włącznie)."""
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def main():
    # Wczytaj zakres dat z pliku (pierwsza i ostatnia linia)
    with open(URL, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    start_date = datetime.strptime(lines[0], "%Y-%m-%d")
    end_date = datetime.strptime(lines[1], "%Y-%m-%d")

    # Ustaw max datę na wczoraj (data systemowa - 1 dzień)
    max_date = datetime.now().date() - timedelta(days=1)
    if end_date.date() > max_date:
        end_date = datetime.combine(max_date, datetime.min.time())

    # Uruchom przeglądarkę
    driver = webdriver.Chrome()
    driver.get("https://teslastats.no/")
    driver.maximize_window()
    time.sleep(2)

    results = []

    for single_date in daterange(start_date, end_date):
        try:
            select_date(driver, single_date)
            time.sleep(5)  # czekaj na załadowanie danych

            value = driver.find_element(By.ID, "today_models").text
            results.append((single_date.strftime("%Y-%m-%d"), value))
            print(f"✅ {single_date.strftime('%Y-%m-%d')} -> {value}")

        except NoSuchElementException:
            print(f"⚠️ Data {single_date.strftime('%Y-%m-%d')} nie jest widoczna w kalendarzu, pomijam...")
        except Exception as e:
            print(f"❌ Błąd przy dacie {single_date.strftime('%Y-%m-%d')}: {e}")

    driver.quit()

    # Zapisz do pliku output.txt
    with open("output.txt", "w", encoding="utf-8") as f:
        for date_str, val in results:
            f.write(f"{date_str}\t{val}\n")

    print("✅ Gotowe! Dane zapisane w output.txt")

if __name__ == "__main__":
    main()
