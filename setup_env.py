#!/usr/bin/env python3
"""
Script to set up Python environment for the project
This script will install required packages using pip
"""

import sys
import subprocess
import os
from pathlib import Path

def install_package(package_name):
    print(f"Installing {package_name}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ Successfully installed {package_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package_name}: {e}")
        return False

def main():
    print("Setting up Python environment for the project...")
    
    # List of required packages
    required_packages = [
        "pydantic",
        "cryptography",
        "aiohttp",
        "requests",
    ]
    
    # Try to ensure pip is installed
    try:
        subprocess.check_call([sys.executable, "-m", "ensurepip", "--upgrade"])
        print("✅ Pip is installed")
    except subprocess.CalledProcessError:
        print("⚠️ Could not ensure pip is installed. You may need to install it manually.")
    
    # Install each required package
    success_count = 0
    for package in required_packages:
        if install_package(package):
            success_count += 1
    
    # Print summary
    print("\nSummary:")
    print(f"Installed {success_count}/{len(required_packages)} required packages")
    
    if success_count == len(required_packages):
        print("\n✅ Setup complete! Your environment is ready.")
    else:
        print("\n⚠️ Some packages could not be installed. Please check the errors above.")
        print("You might need to install them manually using:")
        print("python3 -m pip install <package-name>")
    
    # Check versions of installed packages
    print("\nInstalled package versions:")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "list"])
    except subprocess.CalledProcessError:
        print("Could not list installed packages.")

if __name__ == "__main__":
    main()
