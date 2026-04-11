@echo off
python -c "import PIL" 2>nul
if errorlevel 1 (
    echo Installing Pillow...
    pip install Pillow
)
python "%~dp0main.py"
