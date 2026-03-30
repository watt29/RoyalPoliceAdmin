#!/bin/bash

# Smart Police Bot Management Script for Linux/WSL

SESSION_NAME="police_bot"
PYTHON_EXEC="./.venv/Scripts/python.exe"
if [ ! -f "$PYTHON_EXEC" ]; then
    PYTHON_EXEC="./.venv/bin/python"
fi

case "$1" in
    start)
        echo "🚀 Starting Bot in tmux session: $SESSION_NAME"
        # Check if session already exists
        if tmux has-session -t $SESSION_NAME 2>/dev/null; then
            echo "⚠️ Session '$SESSION_NAME' already exists. Attaching to it."
            tmux attach-session -t $SESSION_NAME
        else
            tmux new-session -d -s $SESSION_NAME "$PYTHON_EXEC main_bot.py"
            echo "✅ Bot is running in the background in tmux. Use './manage.sh logs' to see it."
        fi
        ;;
    stop)
        echo "🛑 Stopping Bot session..."
        tmux kill-session -t $SESSION_NAME 2>/dev/null
        # Also try to kill the process directly in case tmux session was already gone
        pkill -f "main_bot.py" 2>/dev/null
        echo "✅ Bot stopped."
        ;;
    logs|attach)
        echo "📡 Attaching to Bot session (Press Ctrl+B then D to detach)..."
        if tmux has-session -t $SESSION_NAME 2>/dev/null; then
            tmux attach-session -t $SESSION_NAME
        else
            echo "❌ No tmux session named '$SESSION_NAME' found. Bot might not be running."
            echo "Use './manage.sh start' to start the bot."
        fi
        ;;
    status)
        if tmux has-session -t $SESSION_NAME 2>/dev/null; then
            echo "🟢 Bot is RUNNING in tmux session: $SESSION_NAME"
        else
            echo "🔴 Bot is NOT running."
        fi
        ;;
    test)
        echo "🧪 Running AI Extraction Test..."
        $PYTHON_EXEC test_extraction.py
        ;;
    manual)
        echo "✍️ Running Manual Save Script..."
        $PYTHON_EXEC manual_save.py
        ;;
    search)
        if [ -z "$2" ]; then
            echo "❌ Usage: ./manage.sh search [term]"
        else
            echo "🔍 Searching for '$2' in project files..."
            grep -rnE "$2" . --exclude-dir=.venv --exclude-dir=.git
        fi
        ;;
    clean)
        echo "🧹 Cleaning up Python cache files..."
        find . -type d -name "__pycache__" -exec rm -rf {} +
        echo "✅ Clean up complete."
        ;;
    *)
        echo "Usage: ./manage.sh {start|test|manual|search|clean}"
        exit 1
        ;;
esac
