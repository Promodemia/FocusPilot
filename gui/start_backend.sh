#!/bin/bash
# FocusPilot Backend Launcher (Linux/macOS)

echo "Starting FocusPilot Backend..."
echo

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Install with: brew install python3  (macOS) or apt install python3 (Linux)"
    exit 1
fi

# Navigate to script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check/create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements if needed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r backend/requirements.txt
fi

echo "Starting backend on http://0.0.0.0:8765..."
cd backend
python3 main.py
