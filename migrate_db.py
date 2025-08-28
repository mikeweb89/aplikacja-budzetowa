import sqlite3

DB_NAME = 'budget.db'

print("Rozpoczynam bezpieczną migrację bazy danych...")

try:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Sprawdzamy, czy musimy przeprowadzić migrację
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='aktywa_historia_old'")
    if cursor.fetchone():
        print("Wygląda na to, że migracja została już przeprowadzona. Kończę pracę.")
    else:
        # Krok 1: Zmień nazwę starej tabeli na tymczasową
        print("-> Krok 1/4: Zmieniam nazwę 'aktywa_historia' na 'aktywa_historia_old'...")
        cursor.execute("ALTER TABLE aktywa_historia RENAME TO aktywa_historia_old")

        # Krok 2: Stwórz nową tabelę z poprawną strukturą
        print("-> Krok 2/4: Tworzę nową, poprawną tabelę 'aktywa_historia'...")
        cursor.execute('''
            CREATE TABLE aktywa_historia (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data DATE NOT NULL,
                nazwa TEXT NOT NULL,
                wartosc REAL NOT NULL
            )
        ''')

        # Krok 3: Skopiuj dane ze starej tabeli do nowej, pobierając nazwy z tabeli 'aktywa'
        print("-> Krok 3/4: Kopiuję dane i uzupełniam brakujące nazwy...")
        cursor.execute('''
            INSERT INTO aktywa_historia (data, nazwa, wartosc)
            SELECT old.data, a.nazwa, old.wartosc
            FROM aktywa_historia_old old
            JOIN aktywa a ON old.aktywa_id = a.id
        ''')
        print(f"   Skopiowano {cursor.rowcount} wierszy historycznych.")

        # Krok 4: Usuń starą tabelę tymczasową
        print("-> Krok 4/4: Usuwam tabelę tymczasową...")
        cursor.execute("DROP TABLE aktywa_historia_old")

        conn.commit()
        print("\nMigracja zakończona sukcesem! Twoje dane są bezpieczne i gotowe do użycia.")

except sqlite3.Error as e:
    print(f"\nWystąpił błąd bazy danych: {e}")
    print("Migracja mogła się nie udać. Nie wprowadzono trwałych zmian.")
finally:
    if conn:
        conn.close()