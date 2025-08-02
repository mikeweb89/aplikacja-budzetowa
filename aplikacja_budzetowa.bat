@echo off
echo Uruchamianie serwera aplikacji budzetowej...
echo Aby zatrzymac, zamknij to okno.

call venv\Scripts\activate
python app.py

pause