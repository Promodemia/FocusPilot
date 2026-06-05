#!/bin/bash
# FocusPilot Frontend Launcher (Linux/macOS)

echo "Starting FocusPilot Frontend..."
echo

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed"
    echo "Install from: https://nodejs.org/ or use: brew install node (macOS)"
    exit 1
fi

# Check Rust
if ! command -v cargo &> /dev/null; then
    echo "Error: Rust is not installed"
    echo "Install from: https://rustup.rs/"
    exit 1
fi

# Navigate to script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/frontend"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

echo "Starting Tauri development server..."
npm run tauri:dev
