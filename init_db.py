import sqlite3

# Łączymy się z bazą danych o nazwie 'budget.db'
# Jeśli plik nie istnieje, zostanie automatycznie stworzony.
connection = sqlite3.connect('budget.db')
cursor = connection.cursor()

# Tworzymy tabelę o nazwie 'transakcje' z kolumnami:
# id - unikalny numer, automatycznie zwiększany
# opis, kwota, kategoria - dane z naszego formularza
# data - data dodania transakcji
# "IF NOT EXISTS" zapobiega błędowi, jeśli uruchomimy ten skrypt ponownie.
cursor.execute('''
    CREATE TABLE IF NOT EXISTS transakcje (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        opis TEXT NOT NULL,
        kwota REAL NOT NULL,
        kategoria TEXT NOT NULL,
        data DATE NOT NULL
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS kategorie (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nazwa TEXT NOT NULL UNIQUE
    )
''')
# ------------------------------------

#------Tabele do śledzenia majątku netto ---
cursor.execute('''
    CREATE TABLE IF NOT EXISTS aktywa (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nazwa TEXT NOT NULL,
        wartosc REAL NOT NULL,
        typ TEXT NOT NULL CHECK(typ IN ('płynne', 'nieruchomość'))
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS pasywa (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nazwa TEXT NOT NULL,
        wartosc REAL NOT NULL
    )
''')
# --------------------------------------------------

# Zapisujemy zmiany w bazie danych
connection.commit()

# Zamykamy połączenie
connection.close()

print("Baza danych 'budget.db' i tabela 'transakcje' zostały pomyślnie stworzone.")