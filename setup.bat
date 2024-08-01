@echo off
echo Setting up the virtual environment and installing dependencies...
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
echo Setup complete. You can now run the script using start.bat.
pause
