@echo off
echo 🚀 Setting up Telegram Memo Bot...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python first.
    pause
    exit /b 1
)

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt

REM Create .env file from template
if not exist .env (
    echo 📝 Creating .env file from template...
    copy .env.example .env
    echo ⚠️  Please edit .env file with your configuration
) else (
    echo ✅ .env file already exists
)

echo.
echo 🎉 Setup completed!
echo.
echo Next steps:
echo 1. Edit .env file with your Telegram Bot Token and Google credentials
echo 2. Place your service_account.json file in this directory
echo 3. Run: venv\Scripts\activate.bat ^&^& python telegram_memo_bot.py
echo.
echo 📖 For detailed setup instructions, see README.md
pause
