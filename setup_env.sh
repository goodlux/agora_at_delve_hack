#!/bin/bash
# Script to set up Python environment for the project

echo "Setting up Python environment..."

# Install pip if not available
python3 -m ensurepip --upgrade || echo "Could not install pip, may need to install manually"

# Install required packages
python3 -m pip install pydantic
python3 -m pip install cryptography
python3 -m pip install aiohttp
python3 -m pip install requests

echo "Checking installed packages:"
python3 -m pip list | grep -E 'pydantic|cryptography|aiohttp|requests'

echo "Setup complete!"
