import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkcalendar import DateEntry
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime, timedelta
import time
import threading
import os

cancel_requested = False  # Flaga anulowania pracy wątku

def select_date(driver, target_date):
    """Ustawia wybraną datę w kalendarzu na stronie."""
    driver.find_element(By.ID, "datebtn").click()
    time.sleep(1)

    # Wybór miesiąca i roku z dropdownów
    month_select = Select(driver.find_element(By.CSS_SELECTOR, ".dt-datetime-month"))
    year_select = Select(driver.find_element(By.CSS_SELECTOR, ".dt-datetime-year"))

    month_select.select_by_value(str(target_date.month - 1))
    year_select.select_by_value(str(target_date.year))
    time.sleep(1)

    # Kliknięcie przycisku dnia w kalendarzu
    day_button = driver.find_element(By.CSS_SELECTOR,
        f'button[data-year="{target_date.year}"][data-month="{target_date.month - 1}"][data-day="{target_date.day}"]')
    day_button.click()

def daterange(start_date, end_date):
    """Generator dat od start_date do end_date (włącznie)."""
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def log_line(message):
    """Dodaje linię tekstu do logu z timestampem [HH:MM:SS.mmm]."""
    now = datetime.now().strftime("[%H:%M:%S.%f]")[:-3] + "]"
    log_text.config(state=tk.NORMAL)
    log_text.insert("1.0", f"{now} {message}\n")  # Najnowsze na górze
    log_text.config(state=tk.DISABLED)

def format_timedelta(td):
    """Formatuje timedelta na string HH:MM:SS."""
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def update_progress_text(text):
    """Aktualizuje tekst wyświetlany na pasku postępu."""
    progress_label.config(text=text)

def start_scraping(start_date, end_date, save_path):
    """
    Główna funkcja wykonująca pobieranie danych ze strony dla podanego zakresu dat.
    Na koniec zapisuje wyniki do pliku.
    """
    global cancel_requested
    cancel_requested = False

    max_date = datetime.now().date() - timedelta(days=1)
    if end_date.date() > max_date:
        end_date = datetime.combine(max_date, datetime.min.time())

    driver = webdriver.Chrome()
    driver.get("https://teslastats.no/")
    driver.maximize_window()
    time.sleep(2)

    results = []
    all_dates = list(daterange(start_date, end_date))
    total = len(all_dates)

    log_line("⏳ Rozpoczynam pobieranie danych...")
    progress_bar["maximum"] = total

    times = []
    operation_start_time = time.time()

    for idx, single_date in enumerate(all_dates, start=1):
        if cancel_requested:
            log_line("⛔ Przerwano przez użytkownika.")
            break

        step_start = time.time()
        # Formatowanie linii kroku z wyrównaniem - "   Krok   1/10"
        log_line(f"{'':<3}Krok {idx:>3}/{total:<3} - for {single_date.strftime('%Y-%m-%d')}")
        root.update_idletasks()
        progress_bar["value"] = idx

        try:
            select_date(driver, single_date)
            time.sleep(5)
            value = driver.find_element(By.ID, "today_models").text
            results.append((single_date.strftime("%Y-%m-%d"), value))
        except NoSuchElementException:
            results.append((single_date.strftime("%Y-%m-%d"), "Brak danych"))
        except Exception as e:
            results.append((single_date.strftime("%Y-%m-%d"), f"Błąd: {e}"))

        elapsed = time.time() - step_start
        times.append(elapsed)

        # Oblicz średni czas i pozostały czas do końca
        avg_time = sum(times) / len(times)
        remaining_steps = total - idx
        remaining_sec = avg_time * remaining_steps
        remaining_td = timedelta(seconds=int(remaining_sec))

        # Aktualizuj tekst na pasku postępu
        update_progress_text(f"Pozostało: {format_timedelta(remaining_td)}")

    driver.quit()

    total_elapsed = time.time() - operation_start_time

    if not cancel_requested:
        log_line("💾 Zapisuję dane do pliku...")
        with open(save_path, "w", encoding="utf-8") as f:
            for date_str, val in results:
                f.write(f"{date_str}\t{val}\n")
        log_line("✅ Gotowe! Dane zostały zapisane.")
        try:
            os.startfile(save_path)
        except Exception:
            pass

    # Po zakończeniu pracy wypisz średni czas kroku i czas całkowity
    if times:
        avg_td = timedelta(seconds=sum(times) / len(times))
        total_td = timedelta(seconds=total_elapsed)
        log_line(f"ℹ️ Średni czas kroku: {format_timedelta(avg_td)}")
        log_line(f"ℹ️ Całkowity czas operacji: {format_timedelta(total_td)}")

    start_btn.config(state=tk.NORMAL)
    stop_btn.grid_remove()
    progress_bar["value"] = 0
    update_progress_text("")  # Wyczyść tekst paska postępu

def browse_file():
    """Okno dialogowe do wyboru ścieżki zapisu pliku."""
    path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
    if path:
        file_path_entry.delete(0, tk.END)
        file_path_entry.insert(0, path)

def set_today(entry):
    """Ustawia datę na dzisiejszą w DateEntry."""
    entry.set_date(datetime.today())

def on_start():
    """
    Obsługa kliknięcia przycisku Start.
    Sprawdza poprawność dat i ścieżki, czyści logi,
    uruchamia wątek z pobieraniem danych.
    """
    global cancel_requested
    cancel_requested = False
    try:
        start_date = datetime.strptime(start_cal.get(), "%m/%d/%y")
        end_date = datetime.strptime(end_cal.get(), "%m/%d/%y")
        save_path = file_path_entry.get()
        today = datetime.now().date()

        # Czyść logi i dodaj separator na górze
        log_text.config(state=tk.NORMAL)
        log_text.delete("1.0", tk.END)
        log_text.insert(tk.END, "-" * 25 + "\n")
        log_text.config(state=tk.DISABLED)

        # Walidacje dat
        if start_date > end_date:
            messagebox.showerror("Błąd", "Data początkowa nie może być późniejsza niż końcowa.")
            return
        if start_date.date() > today:
            messagebox.showerror("Błąd", "Data początkowa nie może być w przyszłości.")
            return
        if not save_path:
            messagebox.showerror("Błąd", "Podaj ścieżkę zapisu pliku.")
            return

        # Zablokuj start i pokaż przycisk zatrzymaj
        start_btn.config(state=tk.DISABLED)
        stop_btn.grid()
        stop_btn.config(state=tk.NORMAL)

        # Uruchom pobieranie danych w osobnym wątku, aby GUI nie zamrozić
        threading.Thread(target=start_scraping, args=(start_date, end_date, save_path), daemon=True).start()

    except Exception as e:
        messagebox.showerror("Błąd", f"Wystąpił problem: {e}")

def on_stop():
    """Obsługa kliknięcia przycisku Zatrzymaj - ustawia flagę anulowania."""
    global cancel_requested
    cancel_requested = True
    stop_btn.config(state=tk.DISABLED)

# === GUI ===
root = tk.Tk()
root.title("Tesla Stats Scraper")
root.geometry("500x500")  # poszerzone okno

# Czcionka do logów mniejsza dla czytelności
log_font = ("Consolas", 9)

# Etykiety i kalendarze dla dat
tk.Label(root, text="Data początkowa:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
start_cal = DateEntry(root, width=12, background='darkblue', foreground='white', borderwidth=2)
start_cal.grid(row=0, column=1)
tk.Button(root, text="Dzisiaj", command=lambda: set_today(start_cal)).grid(row=0, column=2, padx=2)

tk.Label(root, text="Data końcowa:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
end_cal = DateEntry(root, width=12, background='darkblue', foreground='white', borderwidth=2)
end_cal.grid(row=1, column=1)
tk.Button(root, text="Dzisiaj", command=lambda: set_today(end_cal)).grid(row=1, column=2, padx=2)

# Ścieżka zapisu pliku i przycisk wyboru
tk.Label(root, text="Zapisz do pliku:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
file_path_entry = tk.Entry(root, width=22)
file_path_entry.grid(row=2, column=1)
tk.Button(root, text="Wybierz...", command=browse_file).grid(row=2, column=2, padx=2)

# Start i Stop
start_btn = tk.Button(root, text="Start", command=on_start, bg="green", fg="white", width=18)
start_btn.grid(row=3, column=0, columnspan=2, pady=10)

stop_btn = tk.Button(root, text="Zatrzymaj", command=on_stop, bg="red", fg="white", width=10)
stop_btn.grid(row=3, column=2)
stop_btn.grid_remove()

# Pasek postępu i etykieta z pozostałym czasem (na środku paska)
progress_frame = tk.Frame(root)
progress_frame.grid(row=4, column=0, columnspan=3, pady=5)

progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", length=400, mode="determinate")
progress_bar.pack()

progress_label = tk.Label(progress_frame, text="", font=("Consolas", 10))
progress_label.place(relx=0.5, rely=0.5, anchor="center")  # na środku paska

# Separator 25 znaków "-" na górze logów
separator_label = tk.Label(root, text="-" * 25, fg="gray", font=("Courier", 10))
separator_label.grid(row=5, column=0, columnspan=3, pady=(10,0))

# Ramka i pole tekstowe do logów z przewijaniem
log_frame = tk.Frame(root)
log_frame.grid(row=6, column=0, columnspan=3, padx=10, pady=5)

log_text = tk.Text(log_frame, height=15, width=60, wrap="word", state=tk.DISABLED, font=log_font)
log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scrollbar = tk.Scrollbar(log_frame, command=log_text.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

log_text.config(yscrollcommand=scrollbar.set)

root.mainloop()
