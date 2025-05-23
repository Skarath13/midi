#!/usr/bin/env python3
"""
Quick start script for testing the Music Transcriber locally
"""

import os
import sys
import subprocess
import time
import webbrowser

def check_dependencies():
    """Check if required packages are installed"""
    required = ['flask', 'librosa', 'pretty_midi', 'music21', 'numpy']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print("Installing dependencies...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Dependencies installed!")
    else:
        print("✅ All dependencies are installed")

def main():
    print("🎵 Music Transcriber - Quick Start 🎵")
    print("=" * 40)
    
    # Check dependencies
    check_dependencies()
    
    # Create static directory
    os.makedirs('static', exist_ok=True)
    
    print("\n✨ Starting server on http://localhost:8001")
    print("The browser will open automatically in 3 seconds...")
    print("\nPress Ctrl+C to stop the server\n")
    
    # Start server in a subprocess
    try:
        # Wait a moment then open browser
        subprocess.Popen([sys.executable, 'app.py'])
        time.sleep(3)
        webbrowser.open('http://localhost:8001')
        
        # Keep the script running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Goodbye!")
        sys.exit(0)

if __name__ == '__main__':
    main()