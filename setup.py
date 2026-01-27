#!/usr/bin/env python3
"""
Setup script for Doctor-Patient Translation Service
"""

import os
import sys
import subprocess

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True,
                              capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_api_key():
    """Check if API key is configured"""
    from config import SARVAM_API_KEY

    if SARVAM_API_KEY == 'your_api_key_here':
        print("\n⚠️  API Key Not Configured")
        print("Please:")
        print("1. Get your API key from: https://dashboard.sarvam.ai/")
        print("2. Edit config.py and set: SARVAM_API_KEY = 'your_actual_api_key'")
        return False
    return True

def main():
    """Main setup function"""
    print("🏥 Doctor-Patient Translation Service Setup")
    print("=" * 50)

    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        sys.exit(1)

    print(f"✅ Python {sys.version.split()[0]} detected")

    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing dependencies"):
        print("❌ Failed to install dependencies. Please install manually:")
        print("   pip install -r requirements.txt")
        sys.exit(1)

    # Check API key
    if not check_api_key():
        print("\n💡 You can still run the app, but translations won't work without an API key")
        print("   Run: python main.py")

    # Run tests
    if run_command("python -c \"import sys; sys.path.append('.'); from sarvam_service import SarvamService; print('✅ Import test passed')\"", "Testing imports"):
        print("\n🎉 Setup completed successfully!")
        print("\n🚀 To run the application:")
        print("   python main.py")
        print("\n📚 For help:")
        print("   cat README.md")

if __name__ == "__main__":
    main()
