#!/usr/bin/env python3
"""
Test if the Flask server can start properly
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app
    print("✅ App imported successfully")
    
    # Test if all required modules are available
    import audio_io
    print("✅ audio_io module loaded")
    
    import pitch_detect_improved
    print("✅ pitch_detect_improved module loaded")
    
    import midi_writer_improved
    print("✅ midi_writer_improved module loaded")
    
    import notation
    print("✅ notation module loaded")
    
    # Check if templates exist
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'index.html')
    if os.path.exists(template_path):
        print("✅ Template file exists")
    else:
        print("❌ Template file missing!")
    
    print("\n🎉 All checks passed! You can run the server with:")
    print("   python app.py")
    print("   or")
    print("   python quick_start.py")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nPlease make sure all dependencies are installed:")
    print("   pip install -r requirements.txt")