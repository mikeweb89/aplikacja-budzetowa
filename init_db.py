import sqlite3

connection = sqlite3.connect('budget.db')
cursor = connection.cursor()

# Tabela transakcji
cursor.execute('''
    CREATE TABLE IF NOT EXISTS transakcje (
        id INTEGER PRIMARY KEY AUTOINCREMENT, opis TEXT NOT NULL,
        kwota REAL NOT NULL, kategoria TEXT NOT NULL, data DATE NOT NULL
    )
''')
# Tabela kategorii
cursor.execute('''
    CREATE TABLE IF NOT EXISTS kategorie (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nazwa TEXT NOT NULL UNIQUE
    )
''')
# Tabela aktywów
cursor.execute('''
    CREATE TABLE IF NOT EXISTS aktywa (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nazwa TEXT NOT NULL,
        wartosc REAL NOT NULL, typ TEXT NOT NULL CHECK(typ IN ('płynne', 'nieruchomość'))
    )
''')
# Tabela pasywów
cursor.execute('''
    CREATE TABLE IF NOT EXISTS pasywa (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nazwa TEXT NOT NULL, wartosc REAL NOT NULL
    )
''')

# NOWA, POPRAWIONA Tabela na historię aktywów
cursor.execute('''
    CREATE TABLE IF NOT EXISTS aktywa_historia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data DATE NOT NULL,
        nazwa TEXT NOT NULL,  -- <-- DODALIŚMY NAZWĘ
        wartosc REAL NOT NULL
    )
''')

connection.commit()
connection.close()
print("Baza danych i wszystkie tabele zostały pomyślnie stworzone.")