# Na górze importujemy nową funkcję 'render_template'
from flask import Flask, render_template, request, url_for, redirect
import sqlite3
from datetime import date
import pandas as pd 
import webbrowser
from threading import Timer
import os

app = Flask(__name__)

# Ta funkcja pomoże nam stworzyć "słowniki" z wyników z bazy danych,
# co ułatwi dostęp do danych w szablonie HTML.
def get_db_connection():
    conn = sqlite3.connect('budget.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    # --- Odczyt wybranego okresu (bez zmian) ---
    try:
        selected_year = int(request.args.get('rok', date.today().year))
        selected_month = int(request.args.get('miesiac', date.today().month))
    except (ValueError, TypeError):
        selected_year = date.today().year
        selected_month = date.today().month
    
    conn = get_db_connection()

    # --- Obliczenia dla WYBRANEGO miesiąca (bez zmian) ---
    przychody_cursor = conn.execute("SELECT SUM(kwota) FROM transakcje WHERE kwota > 0 AND strftime('%Y-%m', data) = ?", (f"{selected_year}-{selected_month:02d}",)).fetchone()
    total_przychody = przychody_cursor[0] if przychody_cursor[0] is not None else 0

    wydatki_cursor = conn.execute("SELECT SUM(kwota) FROM transakcje WHERE kwota < 0 AND strftime('%Y-%m', data) = ?", (f"{selected_year}-{selected_month:02d}",)).fetchone()
    total_wydatki = wydatki_cursor[0] if wydatki_cursor[0] is not None else 0
    bilans = total_przychody + total_wydatki
    
    # --- NOWA CZĘŚĆ: Obliczenia dla POPRZEDNIEGO miesiąca ---
    # Obliczamy, jaki był poprzedni miesiąc i rok
    prev_month = selected_month - 1
    prev_year = selected_year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1

    # Pobieramy dane dla poprzedniego miesiąca
    poprzednie_przychody_cursor = conn.execute("SELECT SUM(kwota) FROM transakcje WHERE kwota > 0 AND strftime('%Y-%m', data) = ?", (f"{prev_year}-{prev_month:02d}",)).fetchone()
    poprzednie_total_przychody = poprzednie_przychody_cursor[0] if poprzednie_przychody_cursor[0] is not None else 0

    poprzednie_wydatki_cursor = conn.execute("SELECT SUM(kwota) FROM transakcje WHERE kwota < 0 AND strftime('%Y-%m', data) = ?", (f"{prev_year}-{prev_month:02d}",)).fetchone()
    poprzednie_total_wydatki = poprzednie_wydatki_cursor[0] if poprzednie_wydatki_cursor[0] is not None else 0
    poprzedni_bilans = poprzednie_total_przychody + poprzednie_total_wydatki

    # Obliczamy różnice
    roznica_wydatki = total_wydatki - poprzednie_total_wydatki
    roznica_bilans = bilans - poprzedni_bilans
    # ----------------------------------------------------------------

    # --- Reszta funkcji (dane do wykresu, lista transakcji) bez zmian ---
    # ... (kod dla danych do wykresu i listy transakcji) ...
    query = "SELECT kategoria, kwota FROM transakcje WHERE kwota < 0 AND strftime('%Y-%m', data) = ?"
    params = (f"{selected_year}-{selected_month:02d}",)
    df_wydatki = pd.read_sql_query(query, conn, params=params)

    if not df_wydatki.empty:
        df_wydatki['kwota'] = df_wydatki['kwota'].abs()
        wydatki_po_kategorii = df_wydatki.groupby('kategoria')['kwota'].sum().reset_index()
        chart_labels = wydatki_po_kategorii['kategoria'].tolist()
        chart_values = wydatki_po_kategorii['kwota'].tolist()
    else:
        chart_labels = []
        chart_values = []
    
    kategorie = conn.execute('SELECT * FROM kategorie ORDER BY nazwa').fetchall()

    transakcje = conn.execute("SELECT * FROM transakcje WHERE strftime('%Y-%m', data) = ? ORDER BY data DESC, id DESC", (f"{selected_year}-{selected_month:02d}",)).fetchall()
    conn.close()
    
    # Przekazujemy do szablonu nowe zmienne z różnicami
    return render_template(
        'index.html', 
        transakcje=transakcje,
        total_przychody=total_przychody,
        total_wydatki=total_wydatki,
        bilans=bilans,
        chart_labels=chart_labels,
        chart_values=chart_values,
        selected_year=selected_year,
        selected_month=selected_month,
        kategorie=kategorie,
        roznica_wydatki=roznica_wydatki, # <-- NOWE
        roznica_bilans=roznica_bilans    # <-- NOWE
    )

@app.route('/add', methods=['POST'])
def add_transaction():
    opis = request.form['opis']
    kwota = request.form['kwota']
    kategoria = request.form['kategoria']
    dzisiejsza_data = date.today()

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO transakcje (opis, kwota, kategoria, data) VALUES (?, ?, ?, ?)",
        (opis, kwota, kategoria, dzisiejsza_data)
    )
    conn.commit()
    conn.close()

    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_transaction(id):
    conn = get_db_connection()
    # Wykonujemy polecenie SQL, aby usunąć wiersz o konkretnym id
    conn.execute('DELETE FROM transakcje WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    # Po usunięciu przekierowujemy użytkownika z powrotem na stronę główną
    return redirect(url_for('index'))

@app.route('/edit/<int:id>')
def edit_transaction(id):
    conn = get_db_connection()
    # Pobieramy z bazy konkretną transakcję o podanym id
    transakcja = conn.execute('SELECT * FROM transakcje WHERE id = ?', (id,)).fetchone()
    conn.close()
    # Renderujemy nowy szablon 'edit.html', przekazując do niego dane tej transakcji
    return render_template('edit.html', transakcja=transakcja)

# --- NOWA FUNKCJA DO ZAPISYWANIA ZMIAN ---
@app.route('/update/<int:id>', methods=['POST'])
def update_transaction(id):
    # Pobieramy zaktualizowane dane z formularza
    opis = request.form['opis']
    kwota = request.form['kwota']
    kategoria = request.form['kategoria']

    conn = get_db_connection()
    # Wykonujemy polecenie SQL UPDATE, aby zaktualizować wiersz o konkretnym id
    conn.execute(
        'UPDATE transakcje SET opis = ?, kwota = ?, kategoria = ? WHERE id = ?',
        (opis, kwota, kategoria, id)
    )
    conn.commit()
    conn.close()
    # Po aktualizacji przekierowujemy użytkownika z powrotem na stronę główną
    return redirect(url_for('index'))

# Wyświetla stronę z listą kategorii i formularzem do dodawania nowych
@app.route('/kategorie')
def manage_categories():
    conn = get_db_connection()
    kategorie = conn.execute('SELECT * FROM kategorie ORDER BY nazwa').fetchall()
    conn.close()
    return render_template('kategorie.html', kategorie=kategorie)

# Obsługuje dodawanie nowej kategorii
@app.route('/kategorie/add', methods=['POST'])
def add_category():
    nazwa_kategorii = request.form['nazwa']
    if nazwa_kategorii:
        conn = get_db_connection()
        # Używamy 'OR IGNORE', aby uniknąć błędu przy próbie dodania istniejącej kategorii
        conn.execute('INSERT OR IGNORE INTO kategorie (nazwa) VALUES (?)', (nazwa_kategorii,))
        conn.commit()
        conn.close()
    return redirect(url_for('manage_categories'))

# Obsługuje usuwanie kategorii
@app.route('/kategorie/delete/<int:id>')
def delete_category(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM kategorie WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('manage_categories'))

# ----------------------------------------------------

@app.route('/majatek')
def net_worth_page():
    conn = get_db_connection()

    # Pobieramy aktywa i pasywa
    aktywa = conn.execute('SELECT * FROM aktywa').fetchall()
    pasywa = conn.execute('SELECT * FROM pasywa').fetchall()

    # Obliczamy sumy
    suma_aktywów = conn.execute('SELECT SUM(wartosc) FROM aktywa').fetchone()[0] or 0
    suma_pasywów = conn.execute('SELECT SUM(wartosc) FROM pasywa').fetchone()[0] or 0

    aktywa_płynne = conn.execute("SELECT SUM(wartosc) FROM aktywa WHERE typ = 'płynne'").fetchone()[0] or 0
    wartosc_nieruchomosci = conn.execute("SELECT SUM(wartosc) FROM aktywa WHERE typ = 'nieruchomość'").fetchone()[0] or 0

    conn.close()

    # Obliczamy majątek netto
    majatek_netto_calkowity = suma_aktywów - suma_pasywów
    majatek_netto_plynny = aktywa_płynne - suma_pasywów

    return render_template(
        'majatek.html',
        aktywa=aktywa,
        pasywa=pasywa,
        majatek_netto_plynny=majatek_netto_plynny,
        wartosc_nieruchomosci=wartosc_nieruchomosci,
        majatek_netto_calkowity=majatek_netto_calkowity,
        chart_labels=[],
        chart_values=[]
    )
# ------------------------------------------------

@app.route('/majatek/add_asset', methods=['POST'])
def add_asset():
    nazwa = request.form['nazwa']
    wartosc = request.form['wartosc']
    typ = request.form['typ']

    if nazwa and wartosc and typ:
        conn = get_db_connection()
        conn.execute('INSERT INTO aktywa (nazwa, wartosc, typ) VALUES (?, ?, ?)', (nazwa, wartosc, typ))
        conn.commit()
        conn.close()
    return redirect(url_for('net_worth_page'))

@app.route('/majatek/add_liability', methods=['POST'])
def add_liability():
    nazwa = request.form['nazwa']
    wartosc = request.form['wartosc']

    if nazwa and wartosc:
        conn = get_db_connection()
        conn.execute('INSERT INTO pasywa (nazwa, wartosc) VALUES (?, ?)', (nazwa, wartosc))
        conn.commit()
        conn.close()
    return redirect(url_for('net_worth_page'))

@app.route('/majatek/delete_asset/<int:id>')
def delete_asset(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM aktywa WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('net_worth_page'))

@app.route('/majatek/delete_liability/<int:id>')
def delete_liability(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM pasywa WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('net_worth_page'))

# ----------------------------------------------------

@app.route('/cel')
def retirement_goal_page():
    conn = get_db_connection()
    # Pobieramy sumę tylko płynnych aktywów, ignorując pasywa
    plynne_aktywa_cursor = conn.execute("SELECT SUM(wartosc) FROM aktywa WHERE typ = 'płynne'").fetchone()
    conn.close()

    # Zmienne
    cel = 1000000
    zebrane_srodki = plynne_aktywa_cursor[0] if plynne_aktywa_cursor[0] is not None else 0
    
    # Obliczenia
    pozostalo = cel - zebrane_srodki
    progres_procent = (zebrane_srodki / cel) * 100 if cel > 0 else 0
    
    # Obliczenie czasu do emerytury
    data_urodzenia = date(1989, 6, 1)
    dzisiaj = date.today()
    wiek = dzisiaj.year - data_urodzenia.year - ((dzisiaj.month, dzisiaj.day) < (data_urodzenia.month, data_urodzenia.day))
    
    lata_do_emerytury = 65 - wiek
    miesiace_do_emerytury = lata_do_emerytury * 12

    wymagane_oszczednosci = pozostalo / miesiace_do_emerytury if miesiace_do_emerytury > 0 else 0

    return render_template(
        'cel.html',
        cel=cel,
        zebrane_srodki=zebrane_srodki,
        pozostalo=pozostalo,
        progres_procent=progres_procent,
        lata_do_emerytury=lata_do_emerytury,
        miesiace_do_emerytury=miesiace_do_emerytury,
        wymagane_oszczednosci=wymagane_oszczednosci,
        chart_labels=[],  # Puste dane dla wykresu, aby uniknąć błędu
        chart_values=[]
    )
# ------------------------------------------------

@app.route('/raporty')
def reports_page():
    conn = get_db_connection()

    # To zapytanie SQL grupuje wszystkie transakcje po miesiącu,
    # a następnie dla każdego miesiąca oblicza sumę przychodów i wydatków.
    query = """
        SELECT
            strftime('%Y-%m', data) as miesiac,
            SUM(CASE WHEN kwota > 0 THEN kwota ELSE 0 END) as przychody,
            SUM(CASE WHEN kwota < 0 THEN kwota ELSE 0 END) as wydatki
        FROM transakcje
        GROUP BY miesiac
        ORDER BY miesiac DESC
        LIMIT 12
    """
    # Używamy Pandas do wczytania i przetworzenia danych
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Obliczamy bilans dla każdego miesiąca
    df['bilans'] = df['przychody'] + df['wydatki']
    
    # Odwracamy kolejność danych, aby na wykresie były od najstarszego do najnowszego
    df = df.iloc[::-1]

    # Przygotowujemy listy z danymi, które wyślemy do szablonu
    chart_labels = df['miesiac'].tolist()
    chart_values = df['bilans'].tolist()

    # Musimy też przekazać puste dane dla wykresu kołowego z base.html
    # żeby uniknąć błędu, który mieliśmy wcześniej.
    return render_template(
        'raporty.html',
        chart_labels=chart_labels,
        chart_values=chart_values
    )
# ----------------------------------------------------

if __name__ == '__main__':
    # Sprawdzamy, czy serwer nie jest w trybie przeładowania
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        def open_browser():
            webbrowser.open_new('http://127.0.0.1:5000')
        Timer(1, open_browser).start()

    # Uruchamiamy aplikację
    app.run(debug=True)