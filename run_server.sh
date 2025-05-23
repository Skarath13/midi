#!/bin/bash

echo "🎵 Starting Music Transcriber on http://localhost:8001 🎵"
echo ""
echo "Setting up environment..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create static directory if it doesn't exist
mkdir -p static

# Start the Flask server
echo ""
echo "✨ Server starting on http://localhost:8001 ✨"
echo "Press Ctrl+C to stop the server"
echo ""
python app.py