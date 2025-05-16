#!/usr/bin/env python
import os
import sys
import shutil

def ensure_directories():
    """Ensure all necessary directories exist"""
    directories = ["downloads", "handlers", "utils"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        # Create __init__.py if it doesn't exist
        init_file = os.path.join(directory, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write("# This file ensures the directory is treated as a Python package\n")

def fix_imports():
    """Check and fix any import issues"""
    print("Checking and fixing import paths...")
    # Make sure imports are absolute rather than relative
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                with open(filepath, "r") as f:
                    content = f.read()
                
                # Fix relative imports if needed
                if "from ." in content:
                    print(f"Fixing relative imports in {filepath}")
                    content = content.replace("from .", "from ")
                    with open(filepath, "w") as f:
                        f.write(content)

def setup_heroku():
    """Set up the project for Heroku deployment"""
    print("Setting up project for Heroku deployment...")
    ensure_directories()
    fix_imports()
    
    # Create downloads directory
    os.makedirs("downloads", exist_ok=True)
    
    print("Setup complete. Your project is ready for Heroku deployment.")
    print("Remember to set all required environment variables in Heroku:")
    print("- API_ID")
    print("- API_HASH")
    print("- BOT_TOKEN")
    print("- SESSION_STRING")

if __name__ == "__main__":
    setup_heroku()
