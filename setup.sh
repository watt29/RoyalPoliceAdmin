#!/bin/bash

# Setup script for Telegram Memo Bot
echo "🚀 Setting up Telegram Memo Bot..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create .env file from template
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🎉 Setup completed!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Telegram Bot Token and Google credentials"
echo "2. Place your service_account.json file in this directory"
echo "3. Run: source venv/bin/activate && python telegram_memo_bot.py"
echo ""
echo "📖 For detailed setup instructions, see README.md"
