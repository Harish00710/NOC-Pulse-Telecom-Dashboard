@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo [NOC Pulse] Virtual environment not found.
  echo Run the setup commands in README.md first.
  pause
  exit /b 1
)
call ".venv\Scripts\activate.bat"
python -m streamlit run app.py
