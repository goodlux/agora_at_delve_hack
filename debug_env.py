#!/usr/bin/env python3
"""
Debug script to check Python environment
"""

import sys
import platform

print(f"Python version: {platform.python_version()}")
print(f"Python executable: {sys.executable}")

try:
    import pydantic
    print(f"Pydantic version: {pydantic.__version__}")
except ImportError:
    print("Pydantic not installed")

try:
    import cryptography
    print(f"Cryptography version: {cryptography.__version__}")
except ImportError:
    print("Cryptography not installed")

try:
    import aiohttp
    print(f"Aiohttp version: {aiohttp.__version__}")
except ImportError:
    print("Aiohttp not installed")

print("\nPATH:")
for path in sys.path:
    print(f"  {path}")
